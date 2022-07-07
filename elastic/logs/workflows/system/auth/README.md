Queries in this folder represent a user using the System Auth dashboards in Kibana. 
Specifically this involves executing the following steps:

1. Opening the `[Logs System] Sudo commands` dashboard with a timespan set to `now-15m` to `now`
2. Expand time range to `now-24h` 
3. Select `user.name: root` 
4. Switch to `[Logs System] SSH login attempts` dashboard
5. Change time range to `now-6h`
6. Add filter `system.auth.ssh.event: Failed`
7. Zoom into Shanghai, apply filter `source.geo.country_iso_code: CN`
8. Filter to `user.name: "root"` using KQL and autocomplete
9.  Switch to the dashboard `[Logs System] New users and groups`
10. Filter to `system.auth.useradd.home: /home/elasticsearch`
11. Add filter for `system.auth.useradd.shell: /sbin/nologin`
12. Reverse filter from 12
13. Edit visualization `New users by home directory [Logs System]`
14. Add slice by `host.id`, Move slice to first field and `Update`
