Queries in this folder represent a user using the discover view in Kibana. 
Specifically this involves executing the following steps:

1. Open Discover for the `now-24h` to `now` time span. Use default index pattern `logs-*`.
2. Issue a text search for the keyword `error`.
3. Issue a field search for `http.response.status_code:500`
4. Restrict the time range to `now-1h` to `now`, preserving the query from step 3.