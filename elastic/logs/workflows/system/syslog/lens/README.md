Queries in this folder represent a user using the System syslog data to build a Lens visualization. 

1. Opening the `[Logs System] Syslog dashboard` dashboard with a timespan set to `now-15m` to `now`
2. Build Lens Visualization `Edit` -> `Create visualization`. Select `Pie`.
3. Set time range to `now-24h`
4. Filter to `data_stream.dataset: system.syslog` - Allow autocomplete to fill values.
5. Add `host.os.name` to slice by
6. Set `Number of values` to 10; Break down by by `host.os.kernel`; Save as `OS and Versions` and add to dashboard; Allow dashboard to load