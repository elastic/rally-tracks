#!/usr/bin/env python3
"""
Pre-download Rally track data for offline use.

For tracks that define corpora in track.json (Jinja2 templates), renders the
template with default parameters and downloads every referenced corpus file.
For tracks that still use a static files.txt, that is used as a fallback.

Usage:
  ./download.py TRACK [--max-total-download-gb N] [--no-cache]

Examples:
  ./download.py geonames
  ./download.py elastic/logs
  ./download.py elastic/security
  ./download.py elastic/logs --max-total-download-gb 36
"""

import argparse
import functools
import json
import re
import shutil
import ssl
import subprocess
import sys
import tarfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

RALLY_CDN = "https://rally-tracks.elastic.co"
ROOT = Path(".rally/benchmarks")
REPO_URL = "https://github.com/elastic/rally-tracks.git"


class TemplateRenderError(Exception):
    """Raised when a Jinja2 track.json cannot be rendered."""


# ---------------------------------------------------------------------------
# Template rendering
# ---------------------------------------------------------------------------


def _extract_corpora(rendered: str) -> list | None:
    """
    Locate and parse the corpora array from a partially-invalid rendered
    template using bracket-depth matching.

    A simple regex like r'"corpora"\\s*:\\s*(\\[.*?\\])' will stop at the
    first closing bracket it finds — which is typically the end of the first
    nested "documents" array, not the end of the full corpora array.  Walking
    bracket depth handles arbitrary nesting correctly.
    """
    m = re.search(r'"corpora"\s*:\s*\[', rendered)
    if not m:
        return None

    start = m.end() - 1  # index of the opening '['
    depth = 0
    in_string = False
    i = start

    while i < len(rendered):
        ch = rendered[i]
        if in_string:
            if ch == "\\":
                i += 2  # skip escaped character
                continue
            if ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(rendered[start : i + 1])
                    except json.JSONDecodeError:
                        return None
        i += 1

    return None


def render_track_json(track_dir: Path, extra_vars: dict) -> dict | None:
    """
    Render track.json (which may be a Jinja2 template) and return the parsed
    dict.  Returns None when the file is absent, Jinja2 is unavailable, or
    parsing fails.
    """
    path = track_dir / "track.json"
    if not path.exists():
        return None

    source = path.read_text()

    # Plain JSON — no rendering needed
    if "{%" not in source and "{{" not in source:
        try:
            return json.loads(source)
        except json.JSONDecodeError:
            return None

    try:
        import jinja2
    except ImportError:
        raise TemplateRenderError(
            "jinja2 is not installed; cannot render templated track.json. " "Install esrally or run `pip install jinja2` and retry."
        )

    # rally.helpers provides a `collect` macro that globs and inlines other
    # JSON files (used for challenges/operations, never for corpora).
    # Stub it out so it emits an empty string — the rendered corpora array
    # will still be valid JSON.
    mock_helpers = "{% macro collect(parts) %}{% endmacro %}"

    loader = jinja2.ChoiceLoader(
        [
            jinja2.DictLoader({"rally.helpers": mock_helpers}),
            jinja2.FileSystemLoader(str(track_dir)),
        ]
    )
    env = jinja2.Environment(loader=loader, undefined=jinja2.Undefined)
    env.filters["tojson"] = json.dumps

    try:
        rendered = env.from_string(source).render(build_flavor="oss", **extra_vars)
    except Exception as exc:
        raise TemplateRenderError(f"template rendering failed: {exc}") from exc

    try:
        return json.loads(rendered)
    except json.JSONDecodeError as exc:
        print(
            f"Warning: rendered template is not fully valid JSON ({exc}); " "attempting to extract the corpora section only.",
            file=sys.stderr,
        )
        # Salvage just the corpora array using bracket-depth matching so that
        # nested arrays (e.g. "documents": [...]) are not mistaken for the end
        # of the corpora array.
        corpora = _extract_corpora(rendered)
        if corpora is not None:
            return {"corpora": corpora}
        raise TemplateRenderError(f"rendered template is not valid JSON and corpora section could not be extracted: {exc}") from exc


# ---------------------------------------------------------------------------
# Corpus file enumeration
# ---------------------------------------------------------------------------


def corpus_files(track_data: dict) -> list[tuple[str, str]]:
    """
    Return de-duplicated (full_url, local_relative_path) pairs for every
    source-file referenced in the track's corpora section.

    Rally uses two different on-disk layouts depending on the download source:

    - CDN (rally-tracks.elastic.co): files are stored under the URL path,
      e.g. observability/logging/apache/apache.access/raw/document-0.json.bz2

    - Non-CDN (e.g. storage.googleapis.com): files are stored under the corpus
      name, e.g. k8s-container/doc-ds-metrics-kubernetes.container.json.bz2
      matching loader.py: local.dataset.cache/{corpus.name}/{source-file}
    """
    cdn = RALLY_CDN.rstrip("/")
    seen: set[str] = set()
    result: list[tuple[str, str]] = []

    for corpus in track_data.get("corpora", []):
        corpus_name = corpus.get("name", "")
        # base-url may appear at corpus level, document level, or both.
        corpus_base = corpus.get("base-url", "").rstrip("/")

        for doc in corpus.get("documents", []):
            base = doc.get("base-url", corpus_base).rstrip("/")
            source = doc.get("source-file", "")
            if not source:
                continue

            url = f"{base}/{source}"
            if url in seen:
                continue
            seen.add(url)

            if url.startswith(cdn + "/"):
                rel = urllib.parse.urlparse(url).path.lstrip("/")
            else:
                rel = f"{corpus_name}/{source}"

            result.append((url, rel))

    return result


def files_txt_entries(track_dir: Path, track: str) -> list[tuple[str, str]]:
    """Read files.txt and return (url, local_relative_path) pairs."""
    p = track_dir / "files.txt"
    if not p.exists():
        return []

    entries = []
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        url = f"{RALLY_CDN}/{track}/{line}"
        rel = f"{track}/{line}"
        entries.append((url, rel))
    return entries


# ---------------------------------------------------------------------------
# Download helper
# ---------------------------------------------------------------------------


@functools.lru_cache(maxsize=1)
def _ssl_context() -> ssl.SSLContext:
    """
    Return an SSL context backed by certifi's CA bundle when available
    (esrally depends on certifi, so it is usually present), otherwise fall
    back to the default system context.

    On macOS, the Python.org installer ships its own OpenSSL that is NOT
    linked to the system keychain, causing CERTIFICATE_VERIFY_FAILED errors
    with the bare default context.  certifi carries its own up-to-date CA
    bundle and sidesteps this entirely.
    """
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


_DOWNLOAD_TIMEOUT_S = 600  # 10 minutes; covers both connect and read


def download_file(url: str, dest: Path) -> bool:
    """Download url to dest, streaming in chunks.  Returns True on success."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  ↓  {url}")
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, context=_ssl_context(), timeout=_DOWNLOAD_TIMEOUT_S) as resp:
            with open(tmp, "wb") as fh:
                shutil.copyfileobj(resp, fh)
        tmp.replace(dest)
        return True
    except TimeoutError:
        print(f"     WARN download timed out after  300 s — {url}", file=sys.stderr)
    except ssl.SSLCertVerificationError as exc:
        print(
            f"     SSL certificate verification failed: {exc}\n"
            f"     Fix options:\n"
            f"       • pip install certifi\n"
            f"       • On macOS: open /Applications/Python*/Install\\ Certificates.command",
            file=sys.stderr,
        )
    except urllib.error.HTTPError as exc:
        print(f"     WARN {exc.code} {exc.reason} — {url}", file=sys.stderr)
    except urllib.error.URLError as exc:
        print(f"     WARN {exc.reason} — {url}", file=sys.stderr)
    finally:
        if tmp.exists():
            tmp.unlink()
    return False


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "track",
        metavar="TRACK",
        help="Track name, e.g. geonames or elastic/logs",
    )
    ap.add_argument(
        "--no-cache",
        action="store_true",
        default=False,
        help="Re-download files even if they already exist locally.",
    )
    ap.add_argument(
        "--max-total-download-gb",
        type=int,
        default=None,
        metavar="N",
        dest="max_total_download_gb",
        help=(
            "Maps directly to the track parameter max_total_download_gb. "
            "Controls how many document files are downloaded per corpus: "
            "files_per_corpus = max(N / num_corpora, 1). "
            "Defaults to the track's own default (typically 2 × num_corpora, "
            "e.g. 36 for elastic/logs with 18 corpora → 2 files per corpus)."
        ),
    )
    args = ap.parse_args()

    track = args.track
    home = Path.home()
    repo_target = home / ROOT / "tracks" / "default"
    data_root = home / ROOT / "data"

    # ── 1. Clone or reuse the rally-tracks repository ────────────────────
    if not repo_target.exists():
        if not shutil.which("git"):
            print("error: 'git' is required to clone rally-tracks but was not found on PATH.", file=sys.stderr)
            print("       Install git (https://git-scm.com) and re-run this script.", file=sys.stderr)
            sys.exit(1)
        print(f"Cloning rally-tracks → {repo_target} …")
        repo_target.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", REPO_URL, str(repo_target)], check=True)

    track_dir = repo_target / track
    if not track_dir.is_dir():
        print(
            f"Error: track '{track}' does not exist in {repo_target}.",
            file=sys.stderr,
        )
        sys.exit(1)

    # ── 2. Collect files to download ─────────────────────────────────────
    extra: dict = {}
    if args.max_total_download_gb is not None:
        extra["max_total_download_gb"] = args.max_total_download_gb

    try:
        track_data = render_track_json(track_dir, extra)
    except TemplateRenderError as exc:
        # Rendering failed — only safe to continue if a files.txt fallback exists.
        fallback = files_txt_entries(track_dir, track)
        if fallback:
            print(f"Warning: {exc}", file=sys.stderr)
            print(f"Falling back to files.txt ({len(fallback)} file(s)).")
            to_download = fallback
        else:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        if track_data and track_data.get("corpora"):
            to_download = corpus_files(track_data)
            print(f"Found {len(to_download)} corpus file(s) from track.json.")
        else:
            to_download = files_txt_entries(track_dir, track)
            if to_download:
                print(f"Found {len(to_download)} file(s) from files.txt.")
            else:
                print("No downloadable data files found; packaging track description only.")

    # ── 3. Download missing files ─────────────────────────────────────────
    print()
    local_files: list[Path] = []
    failed_urls: list[str] = []
    for url, rel in to_download:
        dest = data_root / rel
        if dest.exists() and not args.no_cache:
            print(f"  ✓  {dest.relative_to(home)}  (cached)")
            local_files.append(dest)
        else:
            if download_file(url, dest):
                local_files.append(dest)
            else:
                print(f"\nError: download failed for {url}", file=sys.stderr)
                print("Aborting — fix the error above and retry.", file=sys.stderr)
                sys.exit(1)

    # ── 4. Build tar archive ──────────────────────────────────────────────
    archive_name = f"rally-track-data-{track.replace('/', '-')}.tar"
    # Write next to this script, not in cwd, so the archive is never inside
    # a directory being archived (which would cause it to include itself).
    archive_path = Path(__file__).parent.resolve() / archive_name

    def _exclude_archive(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo | None:
        """Drop the archive file itself if it happens to sit inside a source tree."""
        return None if Path(tarinfo.name).resolve() == archive_path else tarinfo

    print(f"\nBuilding {archive_name} …")
    with tarfile.open(archive_path, "w") as tar:
        # Always include the full cloned track repository
        tar.add(repo_target, arcname=str(repo_target.relative_to(home)), filter=_exclude_archive)
        # Add each downloaded data file at its correct relative path
        for dest in local_files:
            tar.add(dest, arcname=str(dest.relative_to(home)), filter=_exclude_archive)

    print(f"\nCreated {archive_name}. Next steps:")
    print("  1. Copy it to the user home directory on the target machine(s).")
    print(f"  2. Extract with:  tar -xf {archive_name}   (extracts to ~/{ROOT})")


if __name__ == "__main__":
    main()
