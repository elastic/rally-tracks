Queries in this folder represent a user using the Mysql logs dashboards in Kibana. 
Specifically this involves executing the following steps:

1. Open the `[Logs MySQL] Overview` for `now-24hrs`
2. Search for `mysql.slowlog.query : UPDATE*`
3. Add a filter for `user.name: is one of amandabennett, ortizmichael, vpotter` 
4. Clear the filter
5. Query for ``
6. Edit the visualization `Error logs over time [Logs MySQL]`
7. Split the series by `log.level`
8. Split the series again by `kubernetes.pod.name` 
9. Save and return to the dashboard