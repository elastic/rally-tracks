Queries in this folder represent a user using the Postgresql logs dashboards in Kibana. 
Specifically this involves executing the following steps:

1. Open the `[Logs PostgreSQL] Overview` for `now-24hrs`
2. Filter to `log.level: ERROR` (using table click)
3. Change time range to `now-1hr`
4. Create new visual - select `TSVB`
5. Set index pattern to `logs-*` and time field to `@timestamp`
6. Add panel filter for `data_stream.dataset : "postgresql.log"`
7. Add an aggregation `Max(event.duration)`
8. Add a child metric to (7) `Moving Average(Max of event.duration)`
9. Group by `Terms(Kubernetes.pod.name)`
10. Add a new metric `Percentile(event.duration)`
11. Change the percentile to `99`
12. Group by `Terms(Kubernetes.pod.name)`
13. Add a child metric to (10) `Moving Average(Percentile of event.duration (99.0))`
14. Move both to a separate axis
15. Save and add to the dashboard