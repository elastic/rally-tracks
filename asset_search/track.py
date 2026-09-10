import random
import uuid
from datetime import datetime, timezone, timedelta
from faker import Faker

ASSET_TYPES = ["design", "image", "video", "presentation", "document"]
STATUSES = ["published", "draft", "archived"]
TAGS = [
    "template", "social-media", "marketing", "branding", "infographic",
    "presentation", "poster", "flyer", "banner", "logo", "icon",
    "illustration", "photo", "background", "layout", "typography",
    "minimal", "colorful", "business", "creative",
]

# Captured once at startup so all param source instances share the same reference point
_NOW = datetime.now(timezone.utc)

# Seed offsets for entity UUID pools. Large values keep them well clear of
# per-batch document seeds (which are base_seed + global_batch_num, typically
# in the range 0..num_batches). Offsets are spaced 1M apart for safety.
_WORKSPACE_POOL_SEED_OFFSET = 10_000_000
_TEAM_POOL_SEED_OFFSET      = 11_000_000
_OWNER_POOL_SEED_OFFSET     = 12_000_000
_FOLDER_POOL_SEED_OFFSET    = 13_000_000


def _make_uuid_pool(seed: int, size: int) -> list:
    """Generate a deterministic list of UUID strings from a seeded RNG.

    Uses random.Random directly rather than Faker to avoid touching Faker's
    global seed state during pool construction.
    """
    rng = random.Random(seed)
    return [str(uuid.UUID(int=rng.getrandbits(128))) for _ in range(size)]


def _make_doc(
    fake: Faker,
    rand: random.Random,
    date_range_days: int,
    workspace_pool: list,
    team_pool: list,
    owner_pool: list,
    folder_pool: list,
) -> dict:
    created = _NOW - timedelta(days=rand.randint(0, max(date_range_days, 0)))
    updated = created + timedelta(days=rand.randint(0, 30))
    if updated > _NOW:
        updated = _NOW

    return {
        "asset_id":     fake.uuid4(),                    # unique per document
        "title":        fake.sentence(nb_words=rand.randint(4, 8)).rstrip("."),
        "description":  fake.text(max_nb_chars=280),
        "content":      fake.text(max_nb_chars=250),
        "asset_type":   rand.choice(ASSET_TYPES),
        "owner_id":     rand.choice(owner_pool),         # bounded cardinality
        "team_id":      rand.choice(team_pool),          # bounded cardinality
        "workspace_id": rand.choice(workspace_pool),     # bounded cardinality
        "folder_id":    rand.choice(folder_pool),        # bounded cardinality
        "tags":         rand.sample(TAGS, k=rand.randint(2, 5)),
        "status":       rand.choices(STATUSES, weights=[70, 20, 10])[0],
        "created_at":   created.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "updated_at":   updated.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "view_count":   rand.randint(0, 1_000_000),
        "file_size_bytes": rand.randint(10_240, 104_857_600),
    }


class AssetSearchParamSource:
    """
    Parameter source for the asset_search track following Rally's ParamSource protocol:
      - partition() is called once per client to create a per-client instance
      - params() is called repeatedly to return each bulk payload

    Determinism guarantees:
      - Each batch is seeded from (base_seed + global_batch_num)
      - global_batch_num = partition_index + (local_batch * total_partitions)
      - No document overlap across clients
      - Retries are safe: Rally holds the yielded payload in memory and
        retries the same bytes without calling params() again
      - Entity UUID pools are generated from fixed seed offsets so all
        partition instances produce the same pool contents

    Parameters (all optional, with defaults):
      bulk-size         Documents per bulk request (default: 500)
      number-of-docs    Total documents to index across all clients (default: 1_000_000)
      seed              Base random seed for deterministic generation (default: 42)
      index-name        Target index name (default: rally-asset-search)
      date-range-days   Spread of created_at timestamps in days before now (default: 730)
                        Use 730 for historical/reload data, 1 for steady-state new ingest
      num-workspaces    Cardinality of workspace_id field (default: 10_000)
      num-teams         Cardinality of team_id field (default: 50_000)
      num-owners        Cardinality of owner_id field (default: 200_000)
      num-folders       Cardinality of folder_id field (default: 500_000)
    """

    # Tells Rally's completed-by scheduler that this source is finite
    # (will raise StopIteration when docs are exhausted)
    infinite = False

    def __init__(self, track, params, **kwargs):
        self.track = track
        self._params = params
        self._bulk_size = params.get("bulk-size", 500)
        self._number_of_docs = params.get("number-of-docs", 1_000_000)
        self._base_seed = params.get("seed", 42)
        self._index_name = params.get("index-name", "rally-asset-search")
        self._date_range_days = params.get("date-range-days", 730)
        self._partition_index = params.get("client-index", 0)
        self._total_partitions = params.get("num-clients", 1)

        self._docs_per_client = self._number_of_docs // self._total_partitions
        # Last partition absorbs any remainder
        if self._partition_index == self._total_partitions - 1:
            self._docs_per_client += self._number_of_docs % self._total_partitions

        self._local_batch = 0
        self._docs_sent = 0

        # Entity UUID pools — bounded cardinality for realistic aggregation and
        # filter query behavior. All partitions share the same pools because pool
        # seeds are derived solely from base_seed + a fixed offset.
        self._workspace_pool = _make_uuid_pool(
            self._base_seed + _WORKSPACE_POOL_SEED_OFFSET,
            params.get("num-workspaces", 10_000),
        )
        self._team_pool = _make_uuid_pool(
            self._base_seed + _TEAM_POOL_SEED_OFFSET,
            params.get("num-teams", 50_000),
        )
        self._owner_pool = _make_uuid_pool(
            self._base_seed + _OWNER_POOL_SEED_OFFSET,
            params.get("num-owners", 200_000),
        )
        self._folder_pool = _make_uuid_pool(
            self._base_seed + _FOLDER_POOL_SEED_OFFSET,
            params.get("num-folders", 500_000),
        )

    def partition(self, partition_index, total_partitions):
        return AssetSearchParamSource(
            self.track,
            {
                **self._params,
                "client-index": partition_index,
                "num-clients": total_partitions,
            },
        )

    def params(self):
        if self._docs_sent >= self._docs_per_client:
            raise StopIteration()

        global_batch = self._partition_index + (self._local_batch * self._total_partitions)

        fake = Faker()
        Faker.seed(self._base_seed + global_batch)
        rand = random.Random(self._base_seed + global_batch)

        batch_size = min(self._bulk_size, self._docs_per_client - self._docs_sent)

        body = []
        for _ in range(batch_size):
            body.append({"index": {"_index": self._index_name}})
            body.append(_make_doc(
                fake, rand, self._date_range_days,
                self._workspace_pool, self._team_pool,
                self._owner_pool, self._folder_pool,
            ))

        self._docs_sent += batch_size
        self._local_batch += 1

        return {
            "body": body,
            "bulk-size": batch_size,
            "unit": "docs",
            "action-metadata-present": True,
        }


_SEARCH_TERMS = [
    "design template",
    "presentation layout",
    "social media",
    "marketing banner",
    "logo icon",
    "photo background",
    "business infographic",
    "creative poster",
]


class AssetSearchQueryParamSource:
    """
    Parameter source for entity-scoped search queries. Reconstructs the same
    UUID pools used during indexing (same seed + offsets) so every UUID in a
    generated query is guaranteed to exist in the index.

    Each partition is seeded with (base_seed + partition_index) so concurrent
    search clients issue different query sequences.

    Parameters (all optional, with defaults):
      query-type    One of: workspace-term, owner-term, bool-workspace-asset-type,
                    bool-owner-text, bool-folder-status
      seed          Must match the seed used during indexing (default: 42)
      index-name    Target index/alias (default: rally-asset-search)
      num-workspaces, num-teams, num-owners, num-folders: must match indexing params
    """

    infinite = True

    def __init__(self, track, params, **kwargs):
        self.track = track
        self._params = params
        self._base_seed = params.get("seed", 42)
        self._index_name = params.get("index-name", "rally-asset-search")
        self._query_type = params.get("query-type", "workspace-term")
        self._partition_index = params.get("client-index", 0)
        self._workspace_pool = _make_uuid_pool(
            self._base_seed + _WORKSPACE_POOL_SEED_OFFSET,
            params.get("num-workspaces", 10_000),
        )
        self._team_pool = _make_uuid_pool(
            self._base_seed + _TEAM_POOL_SEED_OFFSET,
            params.get("num-teams", 50_000),
        )
        self._owner_pool = _make_uuid_pool(
            self._base_seed + _OWNER_POOL_SEED_OFFSET,
            params.get("num-owners", 200_000),
        )
        self._folder_pool = _make_uuid_pool(
            self._base_seed + _FOLDER_POOL_SEED_OFFSET,
            params.get("num-folders", 500_000),
        )
        self._rng = random.Random(self._base_seed + self._partition_index)

    def partition(self, partition_index, total_partitions):
        return AssetSearchQueryParamSource(
            self.track,
            {**self._params, "client-index": partition_index},
        )

    def params(self):
        qt = self._query_type
        if qt == "workspace-term":
            body = {
                "query": {"term": {"workspace_id": self._rng.choice(self._workspace_pool)}}
            }
        elif qt == "owner-term":
            body = {
                "query": {"term": {"owner_id": self._rng.choice(self._owner_pool)}}
            }
        elif qt == "bool-workspace-asset-type":
            body = {
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"workspace_id": self._rng.choice(self._workspace_pool)}},
                            {"term": {"asset_type": self._rng.choice(ASSET_TYPES)}},
                        ]
                    }
                }
            }
        elif qt == "bool-owner-text":
            body = {
                "query": {
                    "bool": {
                        "must": [{"match": {"title": self._rng.choice(_SEARCH_TERMS)}}],
                        "filter": [{"term": {"owner_id": self._rng.choice(self._owner_pool)}}],
                    }
                }
            }
        elif qt == "bool-folder-status":
            body = {
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"folder_id": self._rng.choice(self._folder_pool)}},
                            {"term": {"status": "published"}},
                        ]
                    }
                }
            }
        else:
            raise ValueError(f"Unknown query-type: {qt!r}")
        return {"index": self._index_name, "body": body}


def register(registry):
    registry.register_param_source("asset-search-source", AssetSearchParamSource)
    registry.register_param_source("asset-search-query-source", AssetSearchQueryParamSource)
