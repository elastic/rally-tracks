## Geoshape-large track

Administrative boundaries and long road routes. The geometries are large on purpose, which is the case the OSM `geoshape` track does not cover: most of those shapes are short road segments and building footprints.

The default challenge indexes two corpora:

* `boundaries`: OSM `admin_level` 2–8 polygons from Geofabrik extracts. Polygons over 20,000 vertices are simplified into this index.
* `routes`: road routes generated with OSRM on Germany, France, Spain and Great Britain, bucketed by vertex count.

Three more challenges stay off the default run:

* `scales`: Natural Earth admin-0 and admin-1 at 1:10m, 1:50m and 1:110m.
* `stress`: the 40 largest original boundaries that still fit in one bulk request (under the default 100 MB HTTP limit).
* `cartesian`: Web Mercator copies of the capped boundaries and routes, indexed as `shape`.

### Example boundary

```json
{
  "name": "Roeser",
  "admin_level": 8,
  "vertex_count": 86,
  "region": "luxembourg",
  "osm_id": "relation/407913",
  "shape": "POLYGON((6.1 49.5, 6.2 49.5, 6.2 49.6, 6.1 49.6, 6.1 49.5))"
}
```

### Example route

```json
{
  "route_id": "germany-1000-000123",
  "region": "germany",
  "vertex_count": 1400,
  "distance_m": 42000.0,
  "bucket": "1000",
  "shape": "LINESTRING(6.9 50.9, 6.91 50.91)"
}
```

### Queries

Relation queries are `STATS count` over a fixed polygon, so the result does not depend on Lucene doc order. Per-document `ST_ENVELOPE`, `ST_SIMPLIFY`, `ST_SIMPLIFYPRESERVETOPOLOGY` and `ST_BUFFER` filter on `vertex_count`. Grid aggregations pass an explicit Paris bounds and a precision that stays under the 10,000-cell ES|QL limit.

### Elasticsearch version

The track requires Elasticsearch 9.6.0 or later. `ST_GEOHASH`, `ST_GEOTILE`, and `ST_GEOHEX` accept `geo_shape` values only from 9.6.0, and the default challenge calls those functions. `ST_BUFFER` and `ST_SIMPLIFYPRESERVETOPOLOGY` were added in 9.4, so they are not what sets the minimum version.

There is no spatial join yet. `boundaries` is a separate index from `geoshape`'s `osm*` indices so a later `LOOKUP JOIN` on `ST_INTERSECTS` can be added without changing the OSM nightly.

### Parameters

* `boundary_bulk_size` (default: 10)
* `route_bulk_size` (default: 20)
* `scale_bulk_size` (default: 50)
* `stress_bulk_size` (default: 1)
* `bulk_indexing_clients` (default: 4)
* `ingest_percentage` (default: 100)
* `number_of_replicas` (default: 0)
* `number_of_shards` (default: 1)
* `max_num_segments` (default: 1)
* `source_enabled` (default: true)
* `index_settings`
* `cluster_health` (default: `green`)
* `error_level` (default: `non-fatal`)
* `post_ingest_sleep` (default: false)
* `post_ingest_sleep_duration` (default: 30)

### Building the corpora

`_tools/build_corpus.py` downloads Geofabrik `.osm.pbf` extracts one country at a time, keeps administrative boundaries, and deletes the extract before the next country. Route countries are then routed with a local OSRM. The script refuses to start a step when free disk drops below 12 GiB. It does not delete other Rally data or Elasticsearch data directories.

```
python3 geoshape-large/_tools/build_corpus.py all
```

Finished files are hard-linked into `~/.rally/benchmarks/data/<corpus>/` and written under `geoshape-large/dist/`. Publish both the full files and the `-1k` test-mode files to `https://rally-tracks.elastic.co/geoshape-large/`. Corpora with at most 1,000 documents, such as `boundaries-stress`, have no `-1k` file because test mode uses the full file.

Document counts below are filled in by the build.

<!-- corpus-stats:start -->
| Corpus | Documents | Compressed | Uncompressed | Vertex-count histogram |
|---|---:|---:|---:|---|
| `boundaries.json.bz2` | 224,742 | 932 MiB | 3184 MiB | 50-99: 26027, 0-49: 27350, 200-499: 62405, 100-199: 38324, 500-999: 35507, 1000-1999: 19926, 2000-4999: 10479, 10000-19999: 1631, 5000-9999: 3093 |
| `boundaries-xy.json.bz2` | 224,742 | 964 MiB | 3170 MiB | 50-99: 26027, 0-49: 27350, 200-499: 62405, 100-199: 38324, 500-999: 35507, 1000-1999: 19926, 2000-4999: 10479, 10000-19999: 1631, 5000-9999: 3093 |
| `routes.json.bz2` | 180,000 | 3101 MiB | 9347 MiB | 200-499: 31467, 100-199: 30991, 50-99: 7542, 500-999: 11411, 1000-1999: 40713, 2000-4999: 17876, 5000-9999: 29681, 10000-19999: 10284, 20000-49999: 35 |
| `routes-xy.json.bz2` | 180,000 | 3223 MiB | 9315 MiB | 200-499: 31467, 100-199: 30991, 50-99: 7542, 500-999: 11411, 1000-1999: 40713, 2000-4999: 17876, 5000-9999: 29681, 10000-19999: 10284, 20000-49999: 35 |
| `boundary-scales.json.bz2` | 5,594 | 13 MiB | 37 MiB | 0-49: 1454, 50-99: 918, 100-199: 1178, 200-499: 1296, 500-999: 437, 2000-4999: 75, 1000-1999: 206, 10000-19999: 12, 5000-9999: 18 |
| `boundaries-stress.json.bz2` | 40 | 36 MiB | 125 MiB | 50000-99999: 6, 100000-499999: 34 |
<!-- corpus-stats:end -->

### Vertex distribution

`vertex_count` is stored on every document. The histogram above is the one to read before comparing doc-value formats: fixed per-document overhead dominates the OSM `geoshape` track and is a small fraction of these shapes.

Polygons that cross the antimeridian are left out of the main, cartesian, and stress indexes. Web Mercator copies also drop geometries within 5 degrees of a pole.

### License

OSM boundaries and the routes derived from the OSM road network are [ODbL](https://opendatacommons.org/licenses/odbl/), © OpenStreetMap contributors. Extracts come from [Geofabrik](https://download.geofabrik.de).

Natural Earth is public domain. https://www.naturalearthdata.com/
