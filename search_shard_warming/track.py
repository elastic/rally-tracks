import json
import time
import logging

logger = logging.getLogger(__name__)


def put_settings(es, params):
    es.cluster.put_settings(body=params["body"])


async def relocate_shard(es, params):
    """
    Force a shard to relocate to a different node by using allocation exclude
    settings. This triggers search shard recovery which initiates offline
    blob cache warming.

    Required params:
        index: The index whose shards to relocate.
    Optional params:
        target_node: Specific node to relocate to. If not set, exclude
                     current node to force relocation.
        shard_id: The shard number to relocate (default 0).
    """
    index = params["index"]
    shard_id = params.get("shard_id", 0)
    target_node = params.get("target_node", None)

    # Get current shard allocation info
    shard_info = await es.cat.shards(index=index, format="json")
    current_node = None
    for shard in shard_info:
        if int(shard["shard"]) == shard_id and shard["prirep"] == "p":
            current_node = shard["node"]
            break

    if current_node is None:
        raise Exception(
            f"Could not find primary shard {shard_id} for index {index}"
        )

    logger.info(
        "Shard [%s][%d] currently on node [%s]", index, shard_id, current_node
    )

    if target_node:
        # Use cluster reroute to move shard to a specific node
        body = {
            "commands": [
                {
                    "move": {
                        "index": index,
                        "shard": shard_id,
                        "from_node": current_node,
                        "to_node": target_node,
                    }
                }
            ]
        }
        await es.cluster.reroute(body=body)
        logger.info(
            "Initiated reroute of [%s][%d] from [%s] to [%s]",
            index,
            shard_id,
            current_node,
            target_node,
        )
    else:
        # Exclude the current node to force relocation elsewhere
        await es.cluster.put_settings(
            body={
                "transient": {
                    "cluster.routing.allocation.exclude._name": current_node
                }
            }
        )
        logger.info(
            "Excluded node [%s] to force shard [%s][%d] relocation",
            current_node,
            index,
            shard_id,
        )

    return {
        "weight": 1,
        "unit": "ops",
        "success": True,
        "relocated_from": current_node,
    }


async def wait_for_recovery(es, params):
    """
    Wait for shard recovery to complete on the target index. Polls the
    recovery API until no active recoveries remain or a timeout is reached.

    Required params:
        index: The index to monitor.
    Optional params:
        timeout_seconds: Maximum seconds to wait (default 300).
        poll_interval_seconds: Seconds between polls (default 2).
    """
    index = params["index"]
    timeout_seconds = params.get("timeout_seconds", 300)
    poll_interval = params.get("poll_interval_seconds", 2)

    start_time = time.time()
    recovery_detected = False

    while time.time() - start_time < timeout_seconds:
        recovery_info = await es.indices.recovery(index=index, active_only=True)

        active_recoveries = []
        if index in recovery_info:
            shards = recovery_info[index].get("shards", [])
            for shard in shards:
                stage = shard.get("stage", "")
                if stage not in ("DONE",):
                    active_recoveries.append(shard)

        if active_recoveries:
            recovery_detected = True
            for rec in active_recoveries:
                logger.info(
                    "Recovery in progress: shard [%s] stage=[%s] "
                    "source=[%s] target=[%s]",
                    rec.get("id"),
                    rec.get("stage"),
                    rec.get("source", {}).get("name", "n/a"),
                    rec.get("target", {}).get("name", "n/a"),
                )
        elif recovery_detected:
            # Recovery was active but is now complete
            elapsed = time.time() - start_time
            logger.info(
                "Recovery completed for index [%s] in %.1f seconds",
                index,
                elapsed,
            )
            return {
                "weight": 1,
                "unit": "ops",
                "success": True,
                "recovery_time_seconds": elapsed,
            }

        time.sleep(poll_interval)

    elapsed = time.time() - start_time
    if not recovery_detected:
        logger.warning(
            "No active recovery detected for index [%s] within %.1f seconds. "
            "Shard may have already recovered.",
            index,
            elapsed,
        )
        return {
            "weight": 1,
            "unit": "ops",
            "success": True,
            "recovery_time_seconds": 0,
        }

    raise Exception(
        f"Recovery for index [{index}] did not complete within "
        f"{timeout_seconds} seconds"
    )


async def clear_allocation_exclusions(es, params):
    """
    Remove any cluster-level allocation exclusions that were set to force
    shard relocation. Should be called after recovery completes.
    """
    await es.cluster.put_settings(
        body={
            "transient": {
                "cluster.routing.allocation.exclude._name": None
            }
        }
    )
    logger.info("Cleared allocation exclusion settings")
    return {"weight": 1, "unit": "ops", "success": True}


async def wait_for_green(es, params):
    """
    Wait for the cluster to reach green health for a specific index,
    with no relocating shards.

    Required params:
        index: The index to check health for.
    Optional params:
        timeout: Timeout string for the cluster health API (default '5m').
    """
    index = params["index"]
    timeout = params.get("timeout", "5m")

    result = await es.cluster.health(
        index=index,
        wait_for_status="green",
        wait_for_no_relocating_shards=True,
        timeout=timeout,
    )

    timed_out = result.get("timed_out", False)
    if timed_out:
        raise Exception(
            f"Cluster health did not reach green for index [{index}] "
            f"within {timeout}"
        )

    logger.info(
        "Cluster green for index [%s]: %d shards, %d relocating",
        index,
        result.get("active_shards", 0),
        result.get("relocating_shards", 0),
    )
    return {"weight": 1, "unit": "ops", "success": True}


async def record_shard_stats(es, params):
    """
    Capture a snapshot of shard-level stats (store size, query cache, request
    cache, fielddata) for later comparison. Results are logged and returned
    in the service_time metadata.

    Required params:
        index: The index to gather stats for.
    Optional params:
        label: A label for this stats snapshot (e.g. 'before_relocation').
    """
    index = params["index"]
    label = params.get("label", "snapshot")

    stats = await es.indices.stats(index=index)
    total = stats.get("_all", {}).get("total", {})

    result = {
        "label": label,
        "store_size_bytes": total.get("store", {}).get("size_in_bytes", 0),
        "query_cache_size": total.get("query_cache", {}).get(
            "memory_size_in_bytes", 0
        ),
        "request_cache_size": total.get("request_cache", {}).get(
            "memory_size_in_bytes", 0
        ),
        "fielddata_size": total.get("fielddata", {}).get(
            "memory_size_in_bytes", 0
        ),
        "search_query_total": total.get("search", {}).get("query_total", 0),
        "search_query_time_ms": total.get("search", {}).get(
            "query_time_in_millis", 0
        ),
    }

    logger.info("Shard stats [%s]: %s", label, json.dumps(result))
    return {"weight": 1, "unit": "ops", "success": True, **result}


def register(registry):
    try:
        from esrally.driver.runner import PutSettings
    except ImportError:
        registry.register_runner("put-settings", put_settings)

    registry.register_runner(
        "relocate-shard", relocate_shard, async_runner=True
    )
    registry.register_runner(
        "wait-for-recovery", wait_for_recovery, async_runner=True
    )
    registry.register_runner(
        "clear-allocation-exclusions",
        clear_allocation_exclusions,
        async_runner=True,
    )
    registry.register_runner(
        "wait-for-green", wait_for_green, async_runner=True
    )
    registry.register_runner(
        "record-shard-stats", record_shard_stats, async_runner=True
    )
