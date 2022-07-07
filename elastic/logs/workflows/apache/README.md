Queries in this folder represent a user using the Apache logs dashboard in Kibana. 
Specifically this involves executing the following steps:

1. Open the `[Logs Apache] Access and error logs` dashboard with the last 15 mins of data.
2. Expand the time frame to the last 12 hrs.
3. Filter to `http.response.status_code: 404` errors
4. Filter to `user_agent.name: Firefox`
5. Edit visualization `Response codes over time [Logs Apache]`
    - a. Open visualization Response codes over time [Logs Apache]
    - b. Modify Y-Axis from `count` to `sum(http.response.body.bytes)`
    - c. Add x-axis split on field `kubernetes.pod.name` with size `10`
