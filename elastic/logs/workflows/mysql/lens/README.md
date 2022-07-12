Queries in this folder represent a user using the Mysql logs dashboards in Kibana and adding a Lens visuals. 
Specifically this involves executing the following steps:

1. Open the `[Logs MySQL] Overview` for `now-24hrs`
2. Click `Create visualization`
3. Drag `@timestamp` on to the x-axis
4. Drag `mysql.slowlog.lock_time.sec` onto the Vertical axis, replacing `Count of Records`
5. Change the metric to a `sum`
6. Select the line chart visualization, and add the field `event.duration` to the y-axis
7. Switch the `event.duration` to `Average` and move it to the right axis
8. Save the visual and add to the dashboard