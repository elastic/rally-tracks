Queries in this folder represent a user using the redis logs dashboards in Kibana. 
Specifically this involves executing the following steps:

1. Open the `[Logs Redis] Overview` for `now-15m`
2. Expand the time frame to `now-24h`
3. Filter to `redis.slowlog.duration.us>= 2000`
4. Filter to `redis.slowlog.cmd: BRPOP`
5. Create Lens visualization - `Create visualization`
6. Clear query in Lens
7. Add `@timestamp` to horizontal axis
8. Drag `redis.slowlog.duration.us` to vertical axis
9. Change metric on `redis.slowlog.duration.us` to `sum`
10. Drag `redis.slowlog.key` to `Break down by`
11. Increase `Break down by` to 10
12. Save and add to dashboard
13. Remove the filter added in (4)
14. Remove the search request