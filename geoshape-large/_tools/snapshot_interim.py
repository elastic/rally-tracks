#!/usr/bin/env python3
"""Package regions that have already finished into Rally corpora.

The downloader keeps writing the current region. This reads only directories
whose ``.boundaries.done`` marker exists, plus the finished route and Natural
Earth files. Output goes to ``dist-interim/`` and is linked into the local
Rally corpus cache. ``track.json`` byte counts are updated to match.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
OUT = ROOT / "dist-interim"
RALLY_DATA = Path.home() / ".rally" / "benchmarks" / "data"
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_corpus import (  # noqa: E402
    HIST_EDGES,
    select_stress,
    update_readme,
    update_track_json,
)


def log(msg: str) -> None:
    print(msg, flush=True)


def done_slugs() -> list[str]:
    slugs = []
    for marker in sorted((WORK / "markers").glob("*.boundaries.done")):
        slugs.append(marker.name[: -len(".boundaries.done")])
    return slugs


def existing(paths: list[Path]) -> list[Path]:
    return [path for path in paths if path.exists() and path.stat().st_size > 0]


def boundary_paths(slugs: list[str], prefix: str) -> list[Path]:
    paths = []
    for bucket in range(5):
        for slug in slugs:
            paths.append(WORK / "regions" / slug / f"{prefix}{bucket}.jsonl")
    return existing(paths)


def route_paths(suffix: str) -> list[Path]:
    paths = []
    for band in ("100", "1000", "10000", "50000"):
        name = f"{band}{suffix}.jsonl"
        paths.extend(sorted((WORK / "routes").glob(f"*/{name}")))
    return existing(paths)


def scale_paths(prefix: str) -> list[Path]:
    return existing([WORK / "scales" / f"{prefix}{bucket}.jsonl" for bucket in range(5)])


def vertex_bin(line: bytes) -> str | None:
    token = b'"vertex_count":'
    start = line.find(token)
    if start < 0:
        return None
    start += len(token)
    end = start
    while end < len(line) and 48 <= line[end] <= 57:
        end += 1
    if end == start:
        return None
    verts = int(line[start:end])
    for lower, upper in zip(HIST_EDGES, HIST_EDGES[1:]):
        if lower <= verts < upper:
            return f"{lower}-{upper - 1}" if upper < 10**9 else f"{lower}+"
    return None


def compress(paths: list[Path], dest: Path, limit: int | None = None) -> tuple[int, int, int, dict[str, int]]:
    """Compress JSON lines with bzip2. Returns documents, compressed bytes, raw bytes, histogram."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_suffix(dest.suffix + ".partial")
    if partial.exists():
        partial.unlink()
    proc = subprocess.Popen(["bzip2", "-9", "-c"], stdin=subprocess.PIPE, stdout=partial.open("wb"))
    assert proc.stdin is not None
    docs = 0
    raw = 0
    counts: dict[str, int] = {}
    try:
        for path in paths:
            with path.open("rb") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    if not line.endswith(b"\n"):
                        line += b"\n"
                    proc.stdin.write(line)
                    docs += 1
                    raw += len(line)
                    label = vertex_bin(line)
                    if label is not None:
                        counts[label] = counts.get(label, 0) + 1
                    if docs % 50000 == 0:
                        log(f"  {dest.name}: {docs} documents")
                    if limit is not None and docs >= limit:
                        break
            if limit is not None and docs >= limit:
                break
    finally:
        proc.stdin.close()
        code = proc.wait()
    if code != 0:
        partial.unlink(missing_ok=True)
        raise RuntimeError(f"bzip2 failed for {dest.name} with exit {code}")
    partial.replace(dest)
    return docs, dest.stat().st_size, raw, counts


def compress_job(job: tuple) -> dict:
    corpus, filename, paths = job
    log(f"compressing {filename} from {len(paths)} files")
    docs, compressed, raw, counts = compress(paths, OUT / filename)
    one_k = None
    if docs > 1000:
        one_k_name = filename.replace(".json.bz2", "-1k.json.bz2")
        one_k_docs, one_k_compressed, one_k_raw, _one_k_counts = compress(paths, OUT / one_k_name, limit=1000)
        one_k = {
            "file": one_k_name,
            "documents": one_k_docs,
            "compressed_bytes": one_k_compressed,
            "uncompressed_bytes": one_k_raw,
        }
    log(f"finished {filename}: {docs} docs, {compressed / 1024**2:.0f} MiB compressed")
    return {
        "corpus": corpus,
        "file": filename,
        "documents": docs,
        "compressed_bytes": compressed,
        "uncompressed_bytes": raw,
        "test_mode": one_k,
        "histogram": counts,
    }


def link_into_rally(meta: dict) -> None:
    cache = RALLY_DATA / meta["corpus"]
    cache.mkdir(parents=True, exist_ok=True)
    names = [meta["file"]]
    if meta["test_mode"]:
        names.append(meta["test_mode"]["file"])
    for name in names:
        source = OUT / name
        target = cache / name
        if target.exists() or target.is_symlink():
            target.unlink()
        try:
            os.link(source, target)
        except OSError:
            import shutil

            shutil.copy2(source, target)


def main() -> None:
    slugs = done_slugs()
    if not slugs:
        raise SystemExit("no finished regions to snapshot")
    log(f"snapshotting {len(slugs)} finished regions; the in-progress download is excluded")
    stress_paths = existing([WORK / "regions" / slug / "stress.jsonl" for slug in slugs])
    stress_file = select_stress(stress_paths) if stress_paths else []
    jobs = [
        ("geoshape-large-boundaries", "boundaries.json.bz2", boundary_paths(slugs, "b")),
        ("geoshape-large-boundaries-xy", "boundaries-xy.json.bz2", boundary_paths(slugs, "xy")),
        ("geoshape-large-routes", "routes.json.bz2", route_paths("")),
        ("geoshape-large-routes-xy", "routes-xy.json.bz2", route_paths("-xy")),
        ("geoshape-large-boundary-scales", "boundary-scales.json.bz2", scale_paths("b")),
        ("geoshape-large-boundaries-stress", "boundaries-stress.json.bz2", stress_file),
    ]
    jobs = [job for job in jobs if job[2]]
    published = {}
    # Four large compressions at once. bzip2 itself is single-threaded.
    with ProcessPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(compress_job, job) for job in jobs]
        for future in as_completed(futures):
            meta = future.result()
            published[meta["corpus"]] = meta
    for meta in published.values():
        link_into_rally(meta)
    manifest = {
        "regions": slugs,
        "corpora": published,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))
    update_track_json(published)
    update_readme(published)
    readme = ROOT / "README.md"
    text = readme.read_text()
    note = (
        "Interim snapshot of finished regions only. The download is still running, "
        f"and these counts cover {len(slugs)} regions: {', '.join(slugs)}."
    )
    text = text.replace(
        "<!-- corpus-stats:start -->\n",
        "<!-- corpus-stats:start -->\n" + note + "\n\n",
        1,
    )
    readme.write_text(text)
    log("track.json and the Rally cache now match dist-interim/")


if __name__ == "__main__":
    main()
