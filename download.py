#!/usr/bin/env python3
"""
Pre-download Rally track data for offline use.

Renders track.json (including Jinja2 templates) with default parameters and
downloads every referenced corpus file. Local paths match Rally's layout:
~/.rally/benchmarks/data/<corpus_name>/<source-file>, except elastic/logs and
elastic/security which use ~/.rally/benchmarks/data/<track>/<corpus_name>/<source-file>.

Usage:
  ./download.py TRACK [--track-param KEY=VALUE ...] [--track-params STR] [--no-cache]

Examples:
  ./download.py geonames
  ./download.py elastic/logs
  ./download.py elastic/security
  ./download.py elastic/logs --track-param=max_total_download_gb=36
  ./download.py elastic/logs --track-params="max_total_download_gb:36"
"""

import argparse
import functools
import json
import os
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
RALLY_ROOT = Path(".rally/benchmarks")
REPO_URL = "https://github.com/elastic/rally-tracks.git"


def rally_confdir():
    default_home = os.path.expanduser("~")
    return os.path.join(os.getenv("RALLY_HOME", default_home), ".rally")


class TemplateRenderError(Exception):
    """Raised when a Jinja2 track.json cannot be rendered."""


def _convert_param_value(value: str):
    """Coerce a track-param string to a Python value (mirrors esrally.utils.opts)."""
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if value.lower() in ("none", "null"):
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    if (value.startswith("{") and value.endswith("}")) or (value.startswith("[") and value.endswith("]")):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass
    return value


def parse_track_param(spec: str) -> tuple[str, object]:
    """Parse a single KEY=VALUE or KEY:VALUE track parameter."""
    for sep in ("=", ":"):
        if sep in spec:
            key, value = spec.split(sep, 1)
            return key.strip(), _convert_param_value(value.strip())
    raise argparse.ArgumentTypeError(f"track parameter must be KEY=VALUE or KEY:VALUE, got: {spec!r}")


def parse_track_params(spec: str) -> dict:
    """
    Parse Rally-style --track-params (comma-separated key:value pairs).

    Same format as esrally: ``max_total_download_gb:36,number_of_replicas:0``.
    """
    if not spec:
        return {}
    try:
        from esrally.utils import opts

        return opts.to_dict(spec)
    except ImportError:
        pass
    result = {}
    for item in spec.split(","):
        item = item.strip()
        if not item:
            continue
        key, value = parse_track_param(item)
        result[key] = value
    return result


def build_track_params(track_param_args: list[str], track_params: str) -> dict:
    """Merge --track-param and --track-params into a single template-vars dict."""
    params = parse_track_params(track_params)
    for spec in track_param_args:
        key, value = parse_track_param(spec)
        params[key] = value
    return params


# ---------------------------------------------------------------------------
# Template rendering
# ---------------------------------------------------------------------------


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

    try:
        return json.loads(source)
    except json.JSONDecodeError:
        pass

    try:
        import jinja2
    except ImportError:
        raise TemplateRenderError(
            "jinja2 is not installed; cannot render templated track.json. Install esrally or run `pip install jinja2` and retry."
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
        raise TemplateRenderError(f"rendered template is not valid JSON: {exc}") from exc


# ---------------------------------------------------------------------------
# Corpus file enumeration
# ---------------------------------------------------------------------------

# Tracks using shared DataGenerator, which downloads under data_root/<track.name>/.
_TRACK_PREFIXED_DATA = frozenset({"elastic/logs", "elastic/security"})


def corpus_rel_path(track: str, corpus_name: str, source: str) -> str:
    """
    Local path under ~/.rally/benchmarks/data for a corpus source file.

    Default (standard Rally tracks): <corpus_name>/<source-file>
    elastic/logs and elastic/security (DataGenerator): <track>/<corpus_name>/<source-file>
    """
    if track in _TRACK_PREFIXED_DATA:
        return f"{track}/{corpus_name}/{source}"
    return f"{corpus_name}/{source}"


def corpus_files(track_data: dict, track: str) -> list[tuple[str, str]]:
    """
    Return de-duplicated (full_url, local_relative_path) pairs for every
    source-file referenced in the track's corpora section.
    """
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

            result.append((url, corpus_rel_path(track, corpus_name, source)))

    return result


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
        "--track-param",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        dest="track_param",
        help=(
            "Track parameter for track.json Jinja rendering (repeatable). "
            "Use KEY=VALUE or KEY:VALUE. Example: --track-param=max_total_download_gb=36"
        ),
    )
    ap.add_argument(
        "--track-params",
        default="",
        help=(
            "Comma-separated key:value pairs, same format as esrally --track-params. Example: --track-params='max_total_download_gb:36,number_of_replicas:0'"
        ),
    )
    args = ap.parse_args()

    track = args.track
    rally_home = Path(rally_confdir())
    repo_target = rally_home / "benchmarks" / "tracks" / "default"
    data_root = rally_home / "benchmarks" / "data"

    # ── 1. Clone or reuse the rally-tracks repository ────────────────────
    if not repo_target.exists():
        if not shutil.which("git"):
            print("error: 'git' is required to clone rally-tracks but was not found on PATH.", file=sys.stderr)
            print("       Install git and re-run this script.", file=sys.stderr)
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
    track_params = build_track_params(args.track_param, args.track_params)
    if track_params:
        print(f"Track parameters: {', '.join(f'{k}={v!r}' for k, v in sorted(track_params.items()))}")

    try:
        track_data = render_track_json(track_dir, track_params)
    except TemplateRenderError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if track_data and track_data.get("corpora"):
        to_download = corpus_files(track_data, track)
        print(f"Found {len(to_download)} corpus file(s) from track.json.")
    else:
        print("No downloadable data files found; packaging track description only.")
        to_download = []

    # ── 3. Download missing files ─────────────────────────────────────────
    print()
    local_files: list[Path] = []
    for url, rel in to_download:
        dest = data_root / rel
        if dest.exists() and not args.no_cache:
            print(f"  ✓  {dest.relative_to(rally_home.parent)}  (cached)")
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

    # Tar paths are relative to rally_home.parent so that extracting at ~
    # (or wherever rally_home lives) places everything correctly.
    tar_base = rally_home.parent
    print(f"\nBuilding {archive_name} …")
    with tarfile.open(archive_path, "w") as tar:
        # Always include the full cloned track repository
        tar.add(repo_target, arcname=str(repo_target.relative_to(tar_base)), filter=_exclude_archive)
        # Add each downloaded data file at its correct relative path
        for dest in local_files:
            tar.add(dest, arcname=str(dest.relative_to(tar_base)), filter=_exclude_archive)

    rel_root = rally_home.relative_to(tar_base)
    print(f"\nCreated {archive_name}. Next steps:")
    print(f"  1. Copy it to {tar_base} on the target machine(s).")
    print(f"  2. Extract with:  tar -xf {archive_name}   (extracts to ~/{rel_root}/benchmarks)")


if __name__ == "__main__":
    main()
