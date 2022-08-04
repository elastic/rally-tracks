Queries in this folder represent a user using the Nginx logs dashboards in Kibana. 
Specifically this involves executing the following steps:

1. Opening the `[Logs Nginx] Overview` dashboard with a timespan set to `now-15m` to `now`
2. Expanding the time range to `now-24h` to `now`
3. Applying a geo filter to North America via `source.geo.continent_name: North America`
4. Restrict to 400 response codes via `http.response.status_code >= 400 and http.response.status_code <= 500`
5. Apply a filter to `user_agent.version: 68.0.` and `user_agent.name: Firefox`
6. Navigate to the dashboard `Nginx access and error logs`
7. Restrict to last hr 
8. Search for `"access forbidden"`
