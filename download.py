#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "esrally",
# ]
# ///
"""
Pre-download Rally track data for offline use.

Renders track.json (including Jinja2 templates) with default parameters and
downloads every referenced corpus file. Local paths match Rally's layout:
~/.rally/benchmarks/data/<corpus_name>/<source-file>, except elastic/logs and
elastic/security which use ~/.rally/benchmarks/data/<track>/<corpus_name>/<source-file>.

Usage:
  uv run download.py TRACK [--track-params STR] [--no-cache]

Examples:
  uv run download.py geonames
  uv run download.py elastic/logs
  uv run download.py elastic/security
  uv run download.py elastic/logs --track-params="max_total_download_gb:36"
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

import esrally.utils.opts

REPO_URL = "https://github.com/elastic/rally-tracks.git"


def rally_confdir():
    default_home = os.path.expanduser("~")
    return os.path.join(os.getenv("RALLY_HOME", default_home), ".rally")


class TemplateRenderError(Exception):
    """Raised when track.json cannot be rendered or parsed."""


class DownloadError(Exception):
    """Raised when a corpus file download fails."""


# ---------------------------------------------------------------------------
# Template rendering
# ---------------------------------------------------------------------------


def render_track_json(track_dir: Path, track_params: dict) -> dict:
    """
    Load or render track.json and return the parsed dict.

    Plain JSON is returned as-is. Templated tracks are rendered with esrally's
    render_template_from_file (same as esrally race / render-track).
    """
    path = track_dir / "track.json"
    if not path.exists():
        raise TemplateRenderError(f"track.json not found in {track_dir}")

    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        pass

    from esrally.track.loader import render_template_from_file

    try:
        rendered = render_template_from_file(
            str(path),
            track_params,
            build_flavor="oss",
        )
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


def download_file(url: str, dest: Path) -> None:
    """Download url to dest using esrally.utils.net.download."""
    from esrally.utils import net

    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  ↓  {url}")
    try:
        net.download(url, str(dest))
    except Exception as exc:
        raise DownloadError(f"download failed for {url}: {exc}") from exc


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
        help="Re-download files even if they already exist locally.",
    )
    ap.add_argument(
        "--track-params",
        default="",
        help="Same as esrally race --track-params: comma-separated key:value pairs or a JSON file.",
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
    track_params = esrally.utils.opts.to_dict(args.track_params)
    if track_params:
        print(f"Track parameters: {', '.join(f'{k}={v!r}' for k, v in sorted(track_params.items()))}")

    try:
        track_data = render_track_json(track_dir, track_params)
    except TemplateRenderError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if track_data.get("corpora"):
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
            try:
                download_file(url, dest)
                local_files.append(dest)
            except DownloadError as exc:
                print(f"\nError: {exc}", file=sys.stderr)
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
