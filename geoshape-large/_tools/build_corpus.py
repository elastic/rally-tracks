#!/usr/bin/env python3
"""Build the geoshape-large Rally corpora.

Boundaries come from Geofabrik OSM extracts (ODbL): administrative relations,
admin_level 2-8. Polygons over 20_000 vertices are simplified into the main
index. The 40 largest originals that fit in one bulk request are kept in a
stress corpus. Routes are road routes from OSRM on a few of those extracts,
stratified by vertex count. Natural Earth supplies a small public-domain
scale ladder. Web Mercator copies are written for the cartesian challenge.

The script is resumable. A finished region is recorded under work/markers and
is not downloaded again. It stops rather than filling the disk.
"""

from __future__ import annotations

import argparse
import bz2
import json
import math
import os
import random
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from collections import Counter
from heapq import heappush, heappushpop
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRACK_ROOT = ROOT.parent
WORK = ROOT / "work"
DIST = ROOT / "dist"
VENV_PY = Path(__file__).resolve().parent / ".venv" / "bin" / "python"
RALLY_DATA = Path.home() / ".rally" / "benchmarks" / "data"
GEOFABRIK_INDEX = "https://download.geofabrik.de/index-v1.json"

EARTH = 6378137.0
VERTEX_CAP = 20_000
STRESS_KEEP = 40
STRESS_MAX_BYTES = 80_000_000
MAX_FINE = 320_000  # admin_level >= 7 across the whole corpus
MIN_FREE_GIB = 12
US_PBF_LIMIT = 6 * 1024**3

ROUTE_REGIONS = ["germany", "france", "spain", "great-britain"]
# Europe first so the level>=7 cap fills with municipalities, not one country's villages.
# Coarse levels are always kept, including coastlines processed later.
BOUNDARY_REGIONS = ROUTE_REGIONS + [
    "italy",
    "poland",
    "czech-republic",
    "netherlands",
    "belgium",
    "austria",
    "switzerland",
    "portugal",
    "greece",
    "norway",
    "sweden",
    "finland",
    "denmark",
    "ireland-and-northern-ireland",
    "japan",
    "philippines",
    "indonesia",
    "turkey",
    "brazil",
    "mexico",
    "argentina",
    "colombia",
    "taiwan",
    "thailand",
    "vietnam",
    "south-korea",
    "canada",
    "australia",
    "new-zealand",
    "south-africa",
    "nigeria",
    "egypt",
    "us",
]
US_PARTS = ["us-northeast", "us-midwest", "us-south", "us-west", "us-pacific", "us/alaska"]

ROUTE_QUOTA = {"100": 70_000, "1000": 70_000, "10000": 40_000, "50000": 8_000}
ROUTE_ATTEMPTS = {"100": 50_000, "1000": 50_000, "10000": 25_000, "50000": 8_000}
ROUTE_BAND_KM = {
    "100": (1.5, 12.0),
    "1000": (20.0, 90.0),
    "10000": (150.0, 500.0),
    "50000": (600.0, 2200.0),
}
ROUTE_TARGET_VERTS = {"100": 150, "1000": 1500, "10000": 12_000, "50000": 50_000}
OSRM_PORT = 5505

SCALES = [
    ("10m", 0, "https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_0_countries.zip"),
    ("10m", 1, "https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_1_states_provinces.zip"),
    ("50m", 0, "https://naciscdn.org/naturalearth/50m/cultural/ne_50m_admin_0_countries.zip"),
    ("50m", 1, "https://naciscdn.org/naturalearth/50m/cultural/ne_50m_admin_1_states_provinces.zip"),
    ("110m", 0, "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"),
    ("110m", 1, "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_1_states_provinces.zip"),
]

HIST_EDGES = [0, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 500000, 10**9]


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def ensure_venv() -> None:
    if Path(sys.executable) == VENV_PY:
        return
    if not VENV_PY.exists():
        log("creating a venv with shapely and pyogrio")
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV_PY.parent.parent)])
        subprocess.check_call([str(VENV_PY), "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([str(VENV_PY), "-m", "pip", "install", "shapely", "pyogrio"])
    os.execv(str(VENV_PY), [str(VENV_PY), *sys.argv])


def free_gib() -> float:
    return shutil.disk_usage(TRACK_ROOT).free / (1024**3)


def require_free(gib: float, why: str) -> None:
    free = free_gib()
    if free < gib:
        raise SystemExit(f"Only {free:.1f} GiB free; need {gib:.0f} GiB before {why}. Not deleting anything else.")


def slug(region: str) -> str:
    return region.replace("/", "__")


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        log(f"already have {dest.name}")
        return
    require_free(MIN_FREE_GIB, f"downloading {dest.name}")
    partial = dest.with_suffix(dest.suffix + ".partial")
    log(f"downloading {url}")
    subprocess.check_call(["curl", "-L", "--fail", "--retry", "5", "--retry-delay", "2", "-C", "-", "-o", str(partial), url])
    partial.replace(dest)


def content_length(url: str) -> int | None:
    try:
        text = subprocess.check_output(["curl", "-sI", "-L", url], text=True, timeout=60)
    except subprocess.CalledProcessError:
        return None
    length = None
    for line in text.splitlines():
        if line.lower().startswith("content-length:"):
            try:
                length = int(line.split(":", 1)[1].strip())
            except ValueError:
                pass
    return length


def load_geofabrik() -> dict[str, str]:
    path = WORK / "geofabrik-index.json"
    download(GEOFABRIK_INDEX, path)
    data = json.loads(path.read_text())
    return {feat["properties"]["id"]: feat["properties"]["urls"]["pbf"] for feat in data["features"]}


def expand_regions(regions: list[str], urls: dict[str, str]) -> list[str]:
    out = []
    for region in regions:
        if region == "us":
            size = content_length(urls["us"])
            if size and size > US_PBF_LIMIT:
                log(f"us pbf is {size / 1024**3:.1f} GiB; using regional extracts instead")
                out.extend(US_PARTS)
                continue
        if region not in urls:
            raise SystemExit(f"unknown Geofabrik id {region}")
        out.append(region)
    # Preserve order, drop duplicates.
    seen = set()
    unique = []
    for region in out:
        if region not in seen:
            seen.add(region)
            unique.append(region)
    return unique


def run(cmd: list[str], **kwargs) -> None:
    log(" ".join(str(c) for c in cmd[:8]))
    subprocess.check_call(["nice", "-n", "10", *cmd], **kwargs)


def vertex_count(geom) -> int:
    kind = geom.geom_type
    if kind == "Polygon":
        return len(geom.exterior.coords) + sum(len(ring.coords) for ring in geom.interiors)
    if kind == "MultiPolygon":
        return sum(vertex_count(part) for part in geom.geoms)
    if kind == "LineString":
        return len(geom.coords)
    if kind == "MultiLineString":
        return sum(len(part.coords) for part in geom.geoms)
    return 0


def polygonal(geom):
    from shapely import make_valid
    from shapely.ops import unary_union

    if geom is None or geom.is_empty:
        return None
    geom = make_valid(geom)
    if geom.is_empty:
        return None
    kind = geom.geom_type
    if kind in ("Polygon", "MultiPolygon"):
        return geom
    if kind == "GeometryCollection":
        parts = [part for part in geom.geoms if part.geom_type in ("Polygon", "MultiPolygon") and not part.is_empty]
        if not parts:
            return None
        merged = unary_union(parts)
        if merged.geom_type in ("Polygon", "MultiPolygon") and not merged.is_empty:
            return merged
    return None


def cap_vertices(geom, cap: int):
    from shapely import make_valid, simplify

    if vertex_count(geom) <= cap:
        return geom
    tolerance = 1e-5
    while tolerance <= 5:
        candidate = polygonal(make_valid(simplify(geom, tolerance, preserve_topology=True)))
        if candidate is not None and vertex_count(candidate) <= cap:
            return candidate
        tolerance *= 2
    return None


def crosses_dateline(geom) -> bool:
    minx, _miny, maxx, _maxy = geom.bounds
    return (maxx - minx) > 180 and minx < -90 and maxx > 90


def to_mercator(geom):
    from shapely.ops import transform

    minx, miny, maxx, maxy = geom.bounds
    if maxy > 85 or miny < -85 or crosses_dateline(geom):
        return None

    def _xy(x, y, z=None):
        mx = EARTH * math.radians(x)
        my = EARTH * math.log(math.tan(math.pi / 4 + math.radians(y) / 2))
        return (mx, my) if z is None else (mx, my, z)

    projected = transform(_xy, geom)
    if projected.geom_type in ("LineString", "MultiLineString"):
        return projected if not projected.is_empty else None
    return polygonal(projected)


def parse_level(value) -> int | None:
    if value is None:
        return None
    try:
        level = int(str(value).split(";")[0].strip())
    except ValueError:
        return None
    if 2 <= level <= 8:
        return level
    return None


def boundary_bucket(verts: int) -> int:
    if verts < 100:
        return 0
    if verts < 400:
        return 1
    if verts < 1000:
        return 2
    if verts < 4000:
        return 3
    return 4


def dump(doc: dict) -> str:
    return json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n"


def marker(name: str) -> Path:
    return WORK / "markers" / name


def load_seen() -> set[str]:
    seen = set()
    for path in (WORK / "regions").glob("*/ids.txt"):
        region_marker = marker(path.parent.name + ".boundaries.done")
        if not region_marker.exists():
            continue
        seen.update(line.strip() for line in path.read_text().splitlines() if line.strip())
    return seen


def fine_count() -> int:
    path = WORK / "fine_count.txt"
    if not path.exists():
        return 0
    return int(path.read_text().strip() or "0")


def set_fine_count(value: int) -> None:
    (WORK / "fine_count.txt").write_text(str(value))


def process_boundaries(region: str, urls: dict[str, str], seen: set[str]) -> int:
    from shapely import force_2d, to_wkt
    from shapely.geometry import shape

    name = slug(region)
    done = marker(f"{name}.boundaries.done")
    if done.exists():
        count = int(done.read_text().strip() or "0")
        log(f"{region}: boundaries already built ({count} docs)")
        return count

    region_dir = WORK / "regions" / name
    if region_dir.exists():
        shutil.rmtree(region_dir)
    region_dir.mkdir(parents=True)
    pbf = WORK / "pbf" / f"{name}.osm.pbf"
    admin = WORK / "pbf" / f"{name}.admin.osm.pbf"
    exported = WORK / "pbf" / f"{name}.jsonl"
    download(urls[region], pbf)
    require_free(MIN_FREE_GIB, f"filtering {region}")
    run(
        [
            "osmium",
            "tags-filter",
            "-o",
            str(admin),
            "--overwrite",
            "--progress",
            str(pbf),
            "r/boundary=administrative",
        ]
    )
    run(
        [
            "osmium",
            "export",
            "-a",
            "type,id",
            "--geometry-types=polygon",
            "-f",
            "geojsonseq",
            "-o",
            str(exported),
            "--overwrite",
            "--progress",
            str(admin),
        ]
    )
    admin.unlink(missing_ok=True)

    bucket_files = [open(region_dir / f"b{i}.jsonl", "w") for i in range(5)]
    xy_files = [open(region_dir / f"xy{i}.jsonl", "w") for i in range(5)]
    centroids = open(region_dir / "centroids.csv", "w")
    ids = open(region_dir / "ids.txt", "w")
    stress_heap: list[tuple[int, int, str]] = []
    stress_seq = 0
    kept = 0
    fine = fine_count()
    stats = Counter()
    try:
        with exported.open() as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    feature = json.loads(line)
                except json.JSONDecodeError:
                    stats["badjson"] += 1
                    continue
                props = feature.get("properties") or {}
                if props.get("boundary") != "administrative":
                    continue
                level = parse_level(props.get("admin_level"))
                if level is None:
                    stats["bad_level"] += 1
                    continue
                if level >= 7 and fine >= MAX_FINE:
                    stats["skipped_fine"] += 1
                    continue
                osm_id = props.get("@id")
                if osm_id is None:
                    continue
                key = f"{props.get('@type', 'relation')}/{osm_id}"
                if key in seen:
                    stats["dupes"] += 1
                    continue
                try:
                    geom = polygonal(force_2d(shape(feature["geometry"])))
                except Exception:
                    stats["invalid"] += 1
                    continue
                if geom is None or geom.area <= 0:
                    stats["invalid"] += 1
                    continue
                raw_verts = vertex_count(geom)
                if raw_verts < 4:
                    continue
                label = " ".join(str(props.get("name") or "").split())[:256] or key
                base = {
                    "name": label,
                    "admin_level": level,
                    "region": region,
                    "osm_id": key,
                }
                if raw_verts > VERTEX_CAP:
                    original = dict(base, vertex_count=raw_verts, shape=to_wkt(geom, rounding_precision=6))
                    encoded = dump(original)
                    if len(encoded.encode("utf-8")) <= STRESS_MAX_BYTES:
                        stress_seq += 1
                        item = (raw_verts, stress_seq, encoded)
                        if len(stress_heap) < STRESS_KEEP:
                            heappush(stress_heap, item)
                        else:
                            heappushpop(stress_heap, item)
                if crosses_dateline(geom):
                    stats["dateline"] += 1
                    seen.add(key)
                    ids.write(key + "\n")
                    continue
                capped = cap_vertices(geom, VERTEX_CAP)
                if capped is None:
                    stats["uncappable"] += 1
                    seen.add(key)
                    ids.write(key + "\n")
                    continue
                verts = vertex_count(capped)
                doc = dict(base, vertex_count=verts, shape=to_wkt(capped, rounding_precision=6))
                bucket_files[boundary_bucket(verts)].write(dump(doc))
                projected = to_mercator(capped)
                if projected is not None and not projected.is_empty:
                    xy_doc = dict(doc, vertex_count=vertex_count(projected), shape=to_wkt(projected, rounding_precision=1))
                    xy_files[boundary_bucket(verts)].write(dump(xy_doc))
                    stats["xy"] += 1
                if level >= 6 and raw_verts < 8000:
                    point = geom.representative_point()
                    centroids.write(f"{point.x:.6f},{point.y:.6f}\n")
                seen.add(key)
                ids.write(key + "\n")
                kept += 1
                if level >= 7:
                    fine += 1
                stats["kept"] += 1
    finally:
        for handle in [*bucket_files, *xy_files, centroids, ids]:
            handle.close()
    exported.unlink(missing_ok=True)
    stress_path = region_dir / "stress.jsonl"
    with stress_path.open("w") as handle:
        for _verts, _seq, encoded in sorted(stress_heap, reverse=True):
            handle.write(encoded if encoded.endswith("\n") else encoded + "\n")
    set_fine_count(fine)
    if region not in ROUTE_REGIONS:
        pbf.unlink(missing_ok=True)
    done.parent.mkdir(parents=True, exist_ok=True)
    done.write_text(str(kept))
    log(f"{region}: kept {kept} boundaries ({dict(stats)})")
    return kept


def haversine_km(a, b) -> float:
    lon1, lat1 = map(math.radians, a)
    lon2, lat2 = map(math.radians, b)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * 6371.0 * math.asin(min(1.0, math.sqrt(h)))


def route_bucket(verts: int) -> str | None:
    if 50 <= verts <= 400:
        return "100"
    if 500 <= verts <= 4000:
        return "1000"
    if 5000 <= verts <= 30000:
        return "10000"
    if verts >= 40_000:
        return "50000"
    return None


def osrm_profile() -> Path:
    prefix = subprocess.check_output(["brew", "--prefix", "osrm-backend"], text=True).strip()
    for relative in ("share/osrm/profiles/car.lua", "share/osrm-backend/profiles/car.lua"):
        path = Path(prefix) / relative
        if path.exists():
            return path
    raise SystemExit("osrm car.lua profile not found")


def wait_for_port(port: int, timeout: float = 180) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return
        except OSError:
            time.sleep(0.5)
    raise SystemExit(f"osrm-routed did not listen on {port}")


def fetch_route(a, b) -> dict | None:
    url = f"http://127.0.0.1:{OSRM_PORT}/route/v1/driving/{a[0]},{a[1]};{b[0]},{b[1]}?overview=full&geometries=geojson&steps=false"
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            body = json.loads(response.read().decode())
    except Exception:
        return None
    if body.get("code") != "Ok" or not body.get("routes"):
        return None
    return body["routes"][0]


def process_routes(region: str, urls: dict[str, str], quota: Counter) -> None:
    from shapely import force_2d, to_wkt
    from shapely.geometry import LineString, shape

    name = slug(region)
    done = marker(f"{name}.routes.done")
    if done.exists():
        log(f"{region}: routes already built")
        return
    if not marker(f"{name}.boundaries.done").exists():
        raise SystemExit(f"{region}: boundaries must be built before routes")
    centroids = []
    for line in (WORK / "regions" / name / "centroids.csv").read_text().splitlines():
        if not line.strip():
            continue
        lon, lat = line.split(",")
        centroids.append((float(lon), float(lat)))
    if len(centroids) < 100:
        log(f"{region}: only {len(centroids)} centroids, skipping routes")
        done.parent.mkdir(parents=True, exist_ok=True)
        done.write_text("0")
        return
    if len(centroids) > 20_000:
        rng = random.Random(region)
        centroids = rng.sample(centroids, 20_000)

    pbf = WORK / "pbf" / f"{name}.osm.pbf"
    download(urls[region], pbf)
    pbf_gib = pbf.stat().st_size / (1024**3)
    require_free(max(MIN_FREE_GIB, pbf_gib * 3 + 8), f"OSRM extract of {region}")
    osrm_dir = WORK / "osrm" / name
    if osrm_dir.exists():
        shutil.rmtree(osrm_dir)
    osrm_dir.mkdir(parents=True)
    osrm_pbf = osrm_dir / "region.osm.pbf"
    pbf.replace(osrm_pbf)
    profile = osrm_profile()
    run(["osrm-extract", "-p", str(profile), "-t", "6", str(osrm_pbf)])
    osrm_pbf.unlink(missing_ok=True)
    dataset = osrm_dir / "region.osrm"
    run(["osrm-partition", str(dataset)])
    run(["osrm-customize", str(dataset)])
    log_path = osrm_dir / "routed.log"
    log_handle = open(log_path, "w")
    routed = subprocess.Popen(
        ["osrm-routed", "--algorithm", "mld", "--port", str(OSRM_PORT), "--threads", "4", str(dataset)],
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    out_dir = WORK / "routes" / name
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    writers = {band: open(out_dir / f"{band}.jsonl", "w") for band in ROUTE_QUOTA}
    xy_writers = {band: open(out_dir / f"{band}-xy.jsonl", "w") for band in ROUTE_QUOTA}
    kept = Counter()
    try:
        wait_for_port(OSRM_PORT)
        rng = random.Random(f"routes-{region}")
        for band, (dmin, dmax) in ROUTE_BAND_KM.items():
            samples = []
            calls = 0
            misses = 0
            retargeted = False
            while calls < ROUTE_ATTEMPTS[band] and quota[band] < ROUTE_QUOTA[band]:
                origin = centroids[rng.randrange(len(centroids))]
                dest = None
                distance = 0.0
                for _ in range(40):
                    candidate = centroids[rng.randrange(len(centroids))]
                    distance = haversine_km(origin, candidate)
                    if dmin <= distance <= dmax:
                        dest = candidate
                        break
                if dest is None:
                    misses += 1
                    if misses > 2000:
                        log(f"{region} {band}: giving up, centroids do not span {dmin:.0f}-{dmax:.0f} km")
                        break
                    continue
                misses = 0
                calls += 1
                if calls % 2000 == 0:
                    log(f"{region} {band}: routed {calls}, kept {kept[band]}, quota {quota[band]}/{ROUTE_QUOTA[band]}")
                route = fetch_route(origin, dest)
                if route is None:
                    continue
                try:
                    geom = force_2d(shape(route["geometry"]))
                except Exception:
                    continue
                if geom.geom_type != "LineString" or geom.is_empty:
                    continue
                verts = vertex_count(geom)
                landed = route_bucket(verts)
                if landed is None or quota[landed] >= ROUTE_QUOTA[landed]:
                    if len(samples) < 200:
                        samples.append((distance, verts))
                    continue
                route_id = f"{name}-{landed}-{quota[landed]:06d}"
                doc = {
                    "route_id": route_id,
                    "region": region,
                    "vertex_count": verts,
                    "distance_m": round(float(route.get("distance") or 0.0), 1),
                    "bucket": landed,
                    "shape": to_wkt(geom, rounding_precision=6),
                }
                writers[landed].write(dump(doc))
                # Cartesian copy uses the same bucket files' sibling.
                projected = to_mercator(geom)
                if projected is not None and projected.geom_type == "LineString":
                    xy = dict(doc, vertex_count=vertex_count(projected), shape=to_wkt(projected, rounding_precision=1))
                    xy_writers[landed].write(dump(xy))
                quota[landed] += 1
                kept[landed] += 1
                if len(samples) < 40:
                    samples.append((distance, verts))
                if not retargeted and len(samples) >= 30:
                    ratios = [v / d for d, v in samples if d > 0]
                    if ratios:
                        ratio = sorted(ratios)[len(ratios) // 2]
                        if ratio > 0:
                            center = ROUTE_TARGET_VERTS[band] / ratio
                            dmin = max(0.5, center * 0.6)
                            dmax = max(dmin + 1, center * 1.5)
                            log(f"{region} {band}: retarget {dmin:.0f}-{dmax:.0f} km ({ratio:.0f} verts/km)")
                    retargeted = True
            log(f"{region} {band}: kept {kept[band]} after {calls} routed calls")
    finally:
        for handle in [*writers.values(), *xy_writers.values()]:
            handle.close()
        routed.terminate()
        try:
            routed.wait(timeout=20)
        except subprocess.TimeoutExpired:
            routed.kill()
        log_handle.close()
        shutil.rmtree(osrm_dir, ignore_errors=True)
    done.parent.mkdir(parents=True, exist_ok=True)
    done.write_text(json.dumps(kept))
    log(f"{region}: routes {dict(kept)}")


def build_scales() -> None:
    import pyogrio.raw
    from shapely import from_wkb, to_wkt

    done = marker("scales.done")
    if done.exists():
        log("scales already built")
        return
    out = WORK / "scales"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    buckets = [open(out / f"b{i}.jsonl", "w") for i in range(5)]
    xy_buckets = [open(out / f"xy{i}.jsonl", "w") for i in range(5)]
    kept = 0
    try:
        for scale, level, url in SCALES:
            archive = WORK / "natural-earth" / Path(url).name
            download(url, archive)
            extract = WORK / "natural-earth" / archive.stem
            if extract.exists():
                shutil.rmtree(extract)
            shutil.unpack_archive(archive, extract)
            shapefiles = list(extract.rglob("*.shp"))
            if not shapefiles:
                raise SystemExit(f"no shapefile in {archive}")
            meta, _fids, geoms, columns = pyogrio.raw.read(shapefiles[0], force_2d=True, return_fids=True)
            names = [str(field) for field in meta["fields"]]
            by_name = {field.lower(): columns[index] for index, field in enumerate(names)}

            def column(*keys):
                for key in keys:
                    if key in by_name:
                        return by_name[key]
                return None

            name_col = column("name", "name_en", "admin")
            code_col = column("adm0_a3", "iso_a3", "iso_3166_2", "postal", "code_local")
            for index, geom in enumerate(geoms):
                if geom is None:
                    continue
                if isinstance(geom, (bytes, memoryview)):
                    geom = from_wkb(geom)
                geom = polygonal(geom)
                if geom is None or crosses_dateline(geom):
                    continue
                capped = cap_vertices(geom, VERTEX_CAP)
                if capped is None:
                    continue
                verts = vertex_count(capped)

                def text(value) -> str:
                    if value is None:
                        return ""
                    if isinstance(value, bytes):
                        value = value.decode("utf-8", "replace")
                    return " ".join(str(value).split())

                label = text(name_col[index])[:256] if name_col is not None else ""
                code = text(code_col[index])[:32] if code_col is not None else ""
                doc = {
                    "name": label or code or f"{scale}-{level}-{index}",
                    "code": code,
                    "admin_level": level,
                    "scale": scale,
                    "vertex_count": verts,
                    "shape": to_wkt(capped, rounding_precision=6),
                }
                buckets[boundary_bucket(verts)].write(dump(doc))
                projected = to_mercator(capped)
                if projected is not None:
                    xy = dict(doc, vertex_count=vertex_count(projected), shape=to_wkt(projected, rounding_precision=1))
                    xy_buckets[boundary_bucket(verts)].write(dump(xy))
                kept += 1
    finally:
        for handle in [*buckets, *xy_buckets]:
            handle.close()
    done.parent.mkdir(parents=True, exist_ok=True)
    done.write_text(str(kept))
    log(f"scales: {kept} documents")


def write_compressed(paths: list[Path], dest: Path, limit: int | None = None) -> tuple[int, int, int]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    docs, raw = _write_compressed_lines(dest, paths, limit)
    return docs, dest.stat().st_size, raw


def _write_compressed_lines(dest: Path, paths: list[Path], limit: int | None) -> tuple[int, int]:
    docs = 0
    raw = 0
    with bz2.open(dest, "wt", encoding="utf-8", compresslevel=9) as out:
        for path in paths:
            if not path.exists():
                continue
            with path.open() as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    if not line.endswith("\n"):
                        line += "\n"
                    out.write(line)
                    docs += 1
                    raw += len(line.encode("utf-8"))
                    if limit is not None and docs >= limit:
                        return docs, raw
    return docs, raw


def histogram(paths: list[Path]) -> dict[str, int]:
    counts = Counter()
    for path in paths:
        if not path.exists():
            continue
        with path.open() as handle:
            for line in handle:
                if not line.strip():
                    continue
                # vertex_count is a small integer near the start of each document.
                match = re.search(r'"vertex_count":(\d+)', line)
                if not match:
                    continue
                verts = int(match.group(1))
                for lower, upper in zip(HIST_EDGES, HIST_EDGES[1:]):
                    if lower <= verts < upper:
                        label = f"{lower}-{upper - 1}" if upper < 10**9 else f"{lower}+"
                        counts[label] += 1
                        break
    return dict(counts)


def publish(corpus: str, filename: str, paths: list[Path]) -> dict:
    dest = DIST / filename
    docs, compressed, raw = write_compressed(paths, dest)
    one_k = None
    if docs > 1000:
        one_k_name = filename.replace(".json.bz2", "-1k.json.bz2")
        one_k_docs, one_k_compressed, one_k_raw = write_compressed(paths, DIST / one_k_name, limit=1000)
        one_k = {"file": one_k_name, "documents": one_k_docs, "compressed_bytes": one_k_compressed, "uncompressed_bytes": one_k_raw}
    cache = RALLY_DATA / corpus
    cache.mkdir(parents=True, exist_ok=True)
    for produced in [dest, *([DIST / one_k["file"]] if one_k else [])]:
        target = cache / produced.name
        if target.exists() or target.is_symlink():
            target.unlink()
        try:
            os.link(produced, target)
        except OSError:
            shutil.copy2(produced, target)
    meta = {
        "corpus": corpus,
        "file": filename,
        "documents": docs,
        "compressed_bytes": compressed,
        "uncompressed_bytes": raw,
        "test_mode": one_k,
        "histogram": histogram(paths),
    }
    log(f"published {filename}: {docs} docs, {compressed / 1024**2:.0f} MiB compressed, {raw / 1024**2:.0f} MiB raw")
    return meta


def completed_slugs(kind: str) -> set[str]:
    suffix = f".{kind}.done"
    return {path.name[: -len(suffix)] for path in (WORK / "markers").glob(f"*{suffix}")}


def existing_paths(pattern: str) -> list[Path]:
    """Glob corpus inputs, skipping regions whose completion marker is absent."""
    boundary_done = completed_slugs("boundaries")
    route_done = completed_slugs("routes")
    scales_done = marker("scales.done").exists()
    paths = []
    for path in sorted(WORK.glob(pattern)):
        parts = path.relative_to(WORK).parts
        if parts[0] == "regions" and parts[1] not in boundary_done:
            continue
        if parts[0] == "routes" and parts[1] not in route_done:
            continue
        if parts[0] == "scales" and not scales_done:
            continue
        paths.append(path)
    return paths


def finalize() -> None:
    DIST.mkdir(parents=True, exist_ok=True)
    datasets = {
        "geoshape-large-boundaries": ("boundaries.json.bz2", [f"regions/*/b{i}.jsonl" for i in range(5)]),
        "geoshape-large-boundaries-xy": ("boundaries-xy.json.bz2", [f"regions/*/xy{i}.jsonl" for i in range(5)]),
        "geoshape-large-routes": (
            "routes.json.bz2",
            ["routes/* /100.jsonl", "routes/*/1000.jsonl", "routes/*/10000.jsonl", "routes/*/50000.jsonl"],
        ),
        "geoshape-large-routes-xy": (
            "routes-xy.json.bz2",
            ["routes/*/*-xy.jsonl"],
        ),
        "geoshape-large-boundary-scales": ("boundary-scales.json.bz2", [f"scales/b{i}.jsonl" for i in range(5)]),
        "geoshape-large-boundaries-stress": ("boundaries-stress.json.bz2", ["regions/*/stress.jsonl"]),
    }
    # The xy route glob above is not bucket-ordered. Rebuild that list explicitly.
    datasets["geoshape-large-routes-xy"] = (
        "routes-xy.json.bz2",
        [f"routes/*/{band}-xy.jsonl" for band in ("100", "1000", "10000", "50000")],
    )
    # Stress keeps the largest geometries, not the small-first test-mode order.
    published = {}
    for corpus, (filename, patterns) in datasets.items():
        paths = []
        for pattern in patterns:
            paths.extend(existing_paths(pattern.replace(" ", "")))
        if corpus == "geoshape-large-boundaries-stress":
            paths = select_stress(paths)
        if not paths:
            log(f"no files for {corpus}, skipping")
            continue
        published[corpus] = publish(corpus, filename, paths)
    stats_path = WORK / "corpus_stats.json"
    stats_path.write_text(json.dumps(published, indent=2))
    update_track_json(published)
    update_readme(published)
    log(f"wrote {stats_path}")


def select_stress(paths: list[Path]) -> list[Path]:
    """Keep the STRESS_KEEP largest documents across per-region shortlists.

    The scan records positions only. The bodies of the chosen documents are
    read afterwards, so a multi-megabyte coastline is not held for every candidate.
    """
    index = []
    for path in paths:
        with path.open() as handle:
            for line_no, line in enumerate(handle):
                match = re.search(r'"vertex_count":(\d+)', line)
                if match:
                    index.append((int(match.group(1)), path, line_no))
    index.sort(reverse=True)
    chosen = index[:STRESS_KEEP]
    by_path: dict[Path, dict[int, int]] = {}
    for verts, path, line_no in chosen:
        by_path.setdefault(path, {})[line_no] = verts
    ranked = []
    for path, wanted in by_path.items():
        with path.open() as handle:
            for line_no, line in enumerate(handle):
                if line_no in wanted:
                    if not line.endswith("\n"):
                        line += "\n"
                    ranked.append((wanted[line_no], line))
    ranked.sort()  # smallest of the stress set first, for test mode
    dest = WORK / "stress-selected.jsonl"
    with dest.open("w") as handle:
        for _verts, line in ranked:
            handle.write(line)
    return [dest]


def update_track_json(published: dict) -> None:
    path = ROOT / "track.json"
    text = path.read_text()
    file_to_corpus = {meta["file"]: meta for meta in published.values()}
    pattern = re.compile(
        r'("source-file": "(?P<file>[^"]+)",\n\s*"document-count": )\d+(,\n\s*"compressed-bytes": )\d+(,\n\s*"uncompressed-bytes": )\d+'
    )

    def replace(match: re.Match) -> str:
        meta = file_to_corpus.get(match.group("file"))
        if meta is None:
            return match.group(0)
        return (
            f'{match.group(1)}{meta["documents"]}{match.group(3)}{meta["compressed_bytes"]}' f'{match.group(4)}{meta["uncompressed_bytes"]}'
        )

    path.write_text(pattern.sub(replace, text))


def update_readme(published: dict) -> None:
    path = ROOT / "README.md"
    text = path.read_text()
    lines = ["| Corpus | Documents | Compressed | Uncompressed | Vertex-count histogram |", "|---|---:|---:|---:|---|"]
    for meta in published.values():
        hist = ", ".join(f"{label}: {count}" for label, count in meta["histogram"].items())
        lines.append(
            f"| `{meta['file']}` | {meta['documents']:,} | {meta['compressed_bytes'] / 1024**2:.0f} MiB | "
            f"{meta['uncompressed_bytes'] / 1024**2:.0f} MiB | {hist} |"
        )
    block = "\n".join(lines)
    start = "<!-- corpus-stats:start -->"
    end = "<!-- corpus-stats:end -->"
    if start not in text:
        text += f"\n\n{start}\n{block}\n{end}\n"
    else:
        text = re.sub(f"{re.escape(start)}.*?{re.escape(end)}", f"{start}\n{block}\n{end}", text, flags=re.S)
    path.write_text(text)


def count_built_boundaries() -> int:
    total = 0
    for path in (WORK / "markers").glob("*.boundaries.done"):
        try:
            total += int(path.read_text().strip() or "0")
        except ValueError:
            pass
    return total


def load_route_quota() -> Counter:
    quota = Counter()
    done = completed_slugs("routes")
    for path in WORK.glob("routes/*/*.jsonl"):
        if path.parent.name not in done:
            continue
        band = path.stem
        if band.endswith("-xy"):
            continue
        with path.open() as handle:
            quota[band] += sum(1 for line in handle if line.strip())
    return quota


def main() -> None:
    ensure_venv()
    parser = argparse.ArgumentParser(description="Build geoshape-large corpora")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("all")
    sub.add_parser("scales")
    sub.add_parser("finalize")
    boundaries = sub.add_parser("boundaries")
    boundaries.add_argument("--regions", default=",".join(BOUNDARY_REGIONS))
    routes = sub.add_parser("routes")
    routes.add_argument("--regions", default=",".join(ROUTE_REGIONS))
    args = parser.parse_args()
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / "markers").mkdir(parents=True, exist_ok=True)
    (WORK / "pbf").mkdir(parents=True, exist_ok=True)
    if args.cmd == "all":
        # Fix quota across resumed route regions by counting files inside process_routes.
        command_all_fixed()
    elif args.cmd == "scales":
        build_scales()
    elif args.cmd == "finalize":
        finalize()
    elif args.cmd == "boundaries":
        urls = load_geofabrik()
        regions = expand_regions(args.regions.split(","), urls)
        seen = load_seen()
        for region in regions:
            process_boundaries(region, urls, seen)
    elif args.cmd == "routes":
        urls = load_geofabrik()
        quota = load_route_quota()
        for region in args.regions.split(","):
            process_routes(region, urls, quota)


def command_all_fixed() -> None:
    """Full build. Route quotas include documents already on disk."""
    build_scales()
    urls = load_geofabrik()
    regions = expand_regions(BOUNDARY_REGIONS, urls)
    seen = load_seen()
    quota = load_route_quota()
    for region in regions:
        if region not in ROUTE_REGIONS and count_built_boundaries() >= 450_000:
            log(f"boundary document cap reached, skipping {region}")
            continue
        try:
            process_boundaries(region, urls, seen)
        except Exception as exc:
            log(f"{region}: FAILED boundaries: {exc}")
            with (WORK / "failures.txt").open("a") as handle:
                handle.write(f"{region} boundaries: {exc}\n")
            continue
        if region in ROUTE_REGIONS:
            try:
                process_routes(region, urls, quota)
            except Exception as exc:
                log(f"{region}: FAILED routes: {exc}")
                with (WORK / "failures.txt").open("a") as handle:
                    handle.write(f"{region} routes: {exc}\n")
    finalize()


if __name__ == "__main__":
    main()
