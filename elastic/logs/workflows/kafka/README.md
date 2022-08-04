Queries in this folder represent a user using the Kafka logs dashboard in Kibana. 
Specifically this involves executing the following steps:

1. Opening the `[Logs Kafka] Overview` dashboard with a timespan set to `now-15m` to `now`
2. Expanding the time range to `now-24h` to `now`
3. Applying a filter to the field `kafka.log.trace.class` with the value `java.io.IOException`
4. Search for a specific ip address `10.12.9.219`
5. Open edit view for the visualization `Log levels over time [Logs Kafka]`
6. Edit the `Log levels over time [Logs Kafka]` visualization by adding a terms agg on the field `kafka.log.class` 
with size 10
