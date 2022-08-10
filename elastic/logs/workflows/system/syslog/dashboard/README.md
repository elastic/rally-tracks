Queries in this folder represent a user using the System syslog dashboards in Kibana. 
Specifically this involves executing the following steps:

1. Opening the `[Logs System] Syslog dashboard` dashboard with a timespan set to `now-15m` to `now`
2. Expand the timeframe to the last 24 hrs
3. Apply a filter for `process.name: kernel`
4. Add a query `not host.hostname : packer*`
5. Add to query in (4) `and DST=46.101.87.151`
6. Clear query 
7. Add filter to `host.os.name: Fedora`