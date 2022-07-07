Queries in this folder represent a user using the discover view in Kibana. 
Specifically this involves executing the following steps:

1. Opening discover for the `now-15m` to `now`. Default index pattern is `logs-*`.
2. Expand the date range to `now-24hr`
3. Click `host.name` on the field browser and Click Visualize
4. Increase Top Values to 10
5. Switch visualization to `Date Histogram` on `@timestamp`