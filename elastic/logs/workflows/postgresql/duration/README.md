Queries in this folder represent a user using the Postgresql logs dashboards in Kibana. 
Specifically this involves executing the following steps:

1. Open the `[Logs PostgreSQL] Query Duration Overview` for `now-1hr`
2. Add a filter `and event.duration >= 200000000`
3. Expand date range to `now-24hr`
4. add `and not "copy pgbench_accounts from stdin"` to query
5. Remove `and event.duration >= 200000000 and not "copy pgbench_accounts from stdin"`
6. Add a new Lens visualization using `Create visualization`
7. Add `event.duration` to visual as vertical axis
8. Switch to line, then switch metric from `Median` to `Maximum`
9. Breakdown by `postgresql.log.query_name`
10. Increase top values to 10
11. Switch to vertical stacked bar, then save and add to dashboard
