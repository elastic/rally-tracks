
Baseline race:
  - Race ID: `a583725a-f526-41cf-a994-dd37af96f5a3`
  - Race timestamp: 2025-10-27 17:27:45
  - Challenge: logging-querying
  - Car: external
  - User tags: `created-by=esbench, division=engineering, env-id=2241ac07-93d6-44fc-a1f2-fea5c2074e86, git-username=eyalkoren, 
    host-username=eyalkoren, name=timestamp-date, org=obs, project=logs-plus, setup=esbench, team=obs-experience`

Contender race:
  - Race ID: `254fbf8c-8ab4-4051-91f2-6cb5ca710fdc`
  - Race timestamp: 2025-10-27 15:58:44
  - Challenge: logging-querying
  - Car: external
  - User tags: `created-by=esbench, division=engineering, env-id=2241ac07-93d6-44fc-a1f2-fea5c2074e86, git-username=eyalkoren, 
    host-username=eyalkoren, name=timestamp-date_nanos, org=obs, project=logs-plus, setup=esbench, team=obs-experience`



|                                                        Metric |                                                              Task |        Baseline |       Contender |         Diff |   Unit |   Diff % |
|--------------------------------------------------------------:|------------------------------------------------------------------:|----------------:|----------------:|-------------:|-------:|---------:|
|                    Cumulative indexing time of primary shards |                                                                   |    96.3037      |    93.591       |     -2.7127  |    min |   -2.82% |
|             Min cumulative indexing time across primary shard |                                                                   |     0           |     0           |      0       |    min |    0.00% |
|          Median cumulative indexing time across primary shard |                                                                   |     2.66157     |     2.49139     |     -0.17017 |    min |   -6.39% |
|             Max cumulative indexing time across primary shard |                                                                   |    43.1999      |    42.4526      |     -0.74728 |    min |   -1.73% |
|           Cumulative indexing throttle time of primary shards |                                                                   |     0           |     0           |      0       |    min |    0.00% |
|    Min cumulative indexing throttle time across primary shard |                                                                   |     0           |     0           |      0       |    min |    0.00% |
| Median cumulative indexing throttle time across primary shard |                                                                   |     0           |     0           |      0       |    min |    0.00% |
|    Max cumulative indexing throttle time across primary shard |                                                                   |     0           |     0           |      0       |    min |    0.00% |
|                       Cumulative merge time of primary shards |                                                                   |    22.6517      |    25.0355      |      2.3838  |    min |  +10.52% |
|                      Cumulative merge count of primary shards |                                                                   |    55           |    47           |     -8       |        |  -14.55% |
|                Min cumulative merge time across primary shard |                                                                   |     0           |     0           |      0       |    min |    0.00% |
|             Median cumulative merge time across primary shard |                                                                   |     0.405808    |     0.334483    |     -0.07132 |    min |  -17.58% |
|                Max cumulative merge time across primary shard |                                                                   |    11.3036      |    14.3409      |      3.0373  |    min |  +26.87% |
|              Cumulative merge throttle time of primary shards |                                                                   |     3.10212     |     3.73952     |      0.6374  |    min |  +20.55% |
|       Min cumulative merge throttle time across primary shard |                                                                   |     0           |     0           |      0       |    min |    0.00% |
|    Median cumulative merge throttle time across primary shard |                                                                   |     0.04295     |     0.0310917   |     -0.01186 |    min |  -27.61% |
|       Max cumulative merge throttle time across primary shard |                                                                   |     1.28555     |     2.1481      |      0.86255 |    min |  +67.10% |
|                     Cumulative refresh time of primary shards |                                                                   |     1.03238     |     1.01728     |     -0.0151  |    min |   -1.46% |
|                    Cumulative refresh count of primary shards |                                                                   |   260           |   251           |     -9       |        |   -3.46% |
|              Min cumulative refresh time across primary shard |                                                                   |     0           |     0           |      0       |    min |    0.00% |
|           Median cumulative refresh time across primary shard |                                                                   |     0.04485     |     0.0413583   |     -0.00349 |    min |   -7.79% |
|              Max cumulative refresh time across primary shard |                                                                   |     0.294933    |     0.324583    |      0.02965 |    min |  +10.05% |
|                       Cumulative flush time of primary shards |                                                                   |     5.14727     |     6.2953      |      1.14803 |    min |  +22.30% |
|                      Cumulative flush count of primary shards |                                                                   |   153           |   153           |      0       |        |    0.00% |
|                Min cumulative flush time across primary shard |                                                                   |     3.33333e-05 |     3.33333e-05 |      0       |    min |    0.00% |
|             Median cumulative flush time across primary shard |                                                                   |     0.155558    |     0.193008    |      0.03745 |    min |  +24.07% |
|                Max cumulative flush time across primary shard |                                                                   |     2.16503     |     2.68782     |      0.52278 |    min |  +24.15% |
|                                       Total Young Gen GC time |                                                                   |    11.373       |    11.279       |     -0.094   |      s |   -0.83% |
|                                      Total Young Gen GC count |                                                                   |   707           |   715           |      8       |        |   +1.13% |
|                                         Total Old Gen GC time |                                                                   |     0           |     0           |      0       |      s |    0.00% |
|                                        Total Old Gen GC count |                                                                   |     0           |     0           |      0       |        |    0.00% |
|                                                  Dataset size |                                                                   |     2.63516     |     2.65654     |      0.02138 |     GB |   +0.81% |
|                                                    Store size |                                                                   |     2.63516     |     2.65654     |      0.02138 |     GB |   +0.81% |
|                                                 Translog size |                                                                   |     7.17118e-07 |     7.17118e-07 |      0       |     GB |    0.00% |
|                                        Heap used for segments |                                                                   |     0           |     0           |      0       |     MB |    0.00% |
|                                      Heap used for doc values |                                                                   |     0           |     0           |      0       |     MB |    0.00% |
|                                           Heap used for terms |                                                                   |     0           |     0           |      0       |     MB |    0.00% |
|                                           Heap used for norms |                                                                   |     0           |     0           |      0       |     MB |    0.00% |
|                                          Heap used for points |                                                                   |     0           |     0           |      0       |     MB |    0.00% |
|                                   Heap used for stored fields |                                                                   |     0           |     0           |      0       |     MB |    0.00% |
|                                                 Segment count |                                                                   |    13           |    13           |      0       |        |    0.00% |
|                                   Total Ingest Pipeline count |                                                                   |     4.7056e+07  |     4.7056e+07  |      0       |        |    0.00% |
|                                    Total Ingest Pipeline time |                                                                   |     2.84009e+06 |     2.79824e+06 | -41841       |     ms |   -1.47% |
|                                  Total Ingest Pipeline failed |                                                                   |     0           |     0           |      0       |        |    0.00% |
|                                                Min Throughput |                                                  insert-pipelines |    16.1773      |    15.7795      |     -0.39777 |  ops/s |   -2.46% |
|                                               Mean Throughput |                                                  insert-pipelines |    16.1773      |    15.7795      |     -0.39777 |  ops/s |   -2.46% |
|                                             Median Throughput |                                                  insert-pipelines |    16.1773      |    15.7795      |     -0.39777 |  ops/s |   -2.46% |
|                                                Max Throughput |                                                  insert-pipelines |    16.1773      |    15.7795      |     -0.39777 |  ops/s |   -2.46% |
|                                      100th percentile latency |                                                  insert-pipelines |   898.501       |   922.074       |     23.573   |     ms |   +2.62% |
|                                 100th percentile service time |                                                  insert-pipelines |   898.501       |   922.074       |     23.573   |     ms |   +2.62% |
|                                                    error rate |                                                  insert-pipelines |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                                        insert-ilm |    24.8075      |    24.7475      |     -0.06001 |  ops/s |   -0.24% |
|                                               Mean Throughput |                                                        insert-ilm |    24.8075      |    24.7475      |     -0.06001 |  ops/s |   -0.24% |
|                                             Median Throughput |                                                        insert-ilm |    24.8075      |    24.7475      |     -0.06001 |  ops/s |   -0.24% |
|                                                Max Throughput |                                                        insert-ilm |    24.8075      |    24.7475      |     -0.06001 |  ops/s |   -0.24% |
|                                      100th percentile latency |                                                        insert-ilm |    39.793       |    39.8753      |      0.08229 |     ms |   +0.21% |
|                                 100th percentile service time |                                                        insert-ilm |    39.793       |    39.8753      |      0.08229 |     ms |   +0.21% |
|                                                    error rate |                                                        insert-ilm |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                            validate-package-template-installation |    47.3414      |    47.5453      |      0.20393 |  ops/s |   +0.43% |
|                                               Mean Throughput |                            validate-package-template-installation |    47.3414      |    47.5453      |      0.20393 |  ops/s |   +0.43% |
|                                             Median Throughput |                            validate-package-template-installation |    47.3414      |    47.5453      |      0.20393 |  ops/s |   +0.43% |
|                                                Max Throughput |                            validate-package-template-installation |    47.3414      |    47.5453      |      0.20393 |  ops/s |   +0.43% |
|                                      100th percentile latency |                            validate-package-template-installation |    20.8523      |    20.729       |     -0.12331 |     ms |   -0.59% |
|                                 100th percentile service time |                            validate-package-template-installation |    20.8523      |    20.729       |     -0.12331 |     ms |   -0.59% |
|                                                    error rate |                            validate-package-template-installation |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                   update-custom-package-templates |    33.187       |    34.5606      |      1.37362 |  ops/s |   +4.14% |
|                                               Mean Throughput |                                   update-custom-package-templates |    33.187       |    34.5606      |      1.37362 |  ops/s |   +4.14% |
|                                             Median Throughput |                                   update-custom-package-templates |    33.187       |    34.5606      |      1.37362 |  ops/s |   +4.14% |
|                                                Max Throughput |                                   update-custom-package-templates |    33.187       |    34.5606      |      1.37362 |  ops/s |   +4.14% |
|                                      100th percentile latency |                                   update-custom-package-templates |   361.326       |   346.93        |    -14.3959  |     ms |   -3.98% |
|                                 100th percentile service time |                                   update-custom-package-templates |   361.326       |   346.93        |    -14.3959  |     ms |   -3.98% |
|                                                    error rate |                                   update-custom-package-templates |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                                        bulk-index |   871.851       |   965.11        |     93.2596  | docs/s |  +10.70% |
|                                               Mean Throughput |                                                        bulk-index | 34812           | 35705.7         |    893.624   | docs/s |   +2.57% |
|                                             Median Throughput |                                                        bulk-index | 35921.3         | 36866.4         |    945.025   | docs/s |   +2.63% |
|                                                Max Throughput |                                                        bulk-index | 36475.1         | 37581.6         |   1106.46    | docs/s |   +3.03% |
|                                       50th percentile latency |                                                        bulk-index |   151.32        |   150.217       |     -1.10355 |     ms |   -0.73% |
|                                       90th percentile latency |                                                        bulk-index |   360.533       |   351.956       |     -8.57698 |     ms |   -2.38% |
|                                       99th percentile latency |                                                        bulk-index |   828.519       |   768.271       |    -60.2483  |     ms |   -7.27% |
|                                     99.9th percentile latency |                                                        bulk-index |  3492.57        |  4003.29        |    510.725   |     ms |  +14.62% |
|                                    99.99th percentile latency |                                                        bulk-index |  4948.24        |  6818.59        |   1870.35    |     ms |  +37.80% |
|                                      100th percentile latency |                                                        bulk-index |  6793.5         | 10855.1         |   4061.58    |     ms |  +59.79% |
|                                  50th percentile service time |                                                        bulk-index |   151.682       |   148.498       |     -3.18334 |     ms |   -2.10% |
|                                  90th percentile service time |                                                        bulk-index |   360.473       |   351.117       |     -9.35521 |     ms |   -2.60% |
|                                  99th percentile service time |                                                        bulk-index |   830.948       |   754.284       |    -76.6633  |     ms |   -9.23% |
|                                99.9th percentile service time |                                                        bulk-index |  3512.74        |  4000.05        |    487.31    |     ms |  +13.87% |
|                               99.99th percentile service time |                                                        bulk-index |  4943.31        |  6818.81        |   1875.5     |     ms |  +37.94% |
|                                 100th percentile service time |                                                        bulk-index |  6793.5         | 10855.1         |   4061.58    |     ms |  +59.79% |
|                                                    error rate |                                                        bulk-index |     0           |     0.00212513  |      0.00213 |      % |    0.00% |
|                                       50th percentile latency |                                                 compression-stats | 10999.1         | 10999           |     -0.07031 |     ms |   -0.00% |
|                                       90th percentile latency |                                                 compression-stats | 11000.2         | 11000.4         |      0.23809 |     ms |    0.00% |
|                                      100th percentile latency |                                                 compression-stats | 11000.7         | 11000.8         |      0.13379 |     ms |    0.00% |
|                                  50th percentile service time |                                                 compression-stats | 10999.1         | 10999           |     -0.07031 |     ms |   -0.00% |
|                                  90th percentile service time |                                                 compression-stats | 11000.2         | 11000.4         |      0.23809 |     ms |    0.00% |
|                                 100th percentile service time |                                                 compression-stats | 11000.7         | 11000.8         |      0.13379 |     ms |    0.00% |
|                                                    error rate |                                                 compression-stats |   100           |   100           |      0       |      % |    0.00% |
|                                                Min Throughput |                                 discovery-search-request-size-100 |    15.6499      |    13.3528      |     -2.29707 |  ops/s |  -14.68% |
|                                               Mean Throughput |                                 discovery-search-request-size-100 |    19.1815      |    18.0982      |     -1.08329 |  ops/s |   -5.65% |
|                                             Median Throughput |                                 discovery-search-request-size-100 |    19.1815      |    18.0982      |     -1.08329 |  ops/s |   -5.65% |
|                                                Max Throughput |                                 discovery-search-request-size-100 |    22.7131      |    22.8436      |      0.13049 |  ops/s |   +0.57% |
|                                       50th percentile latency |                                 discovery-search-request-size-100 |    35.3245      |    32.6375      |     -2.68707 |     ms |   -7.61% |
|                                       90th percentile latency |                                 discovery-search-request-size-100 |    47.9298      |    50.8722      |      2.94239 |     ms |   +6.14% |
|                                      100th percentile latency |                                 discovery-search-request-size-100 |   181.326       |   233.781       |     52.4556  |     ms |  +28.93% |
|                                  50th percentile service time |                                 discovery-search-request-size-100 |    35.3245      |    32.6375      |     -2.68707 |     ms |   -7.61% |
|                                  90th percentile service time |                                 discovery-search-request-size-100 |    47.9298      |    50.8722      |      2.94239 |     ms |   +6.14% |
|                                 100th percentile service time |                                 discovery-search-request-size-100 |   181.326       |   233.781       |     52.4556  |     ms |  +28.93% |
|                                                    error rate |                                 discovery-search-request-size-100 |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                 discovery-search-request-size-500 |    13.8525      |    13.3694      |     -0.48311 |  ops/s |   -3.49% |
|                                               Mean Throughput |                                 discovery-search-request-size-500 |    14           |    13.7989      |     -0.20111 |  ops/s |   -1.44% |
|                                             Median Throughput |                                 discovery-search-request-size-500 |    13.9356      |    13.9002      |     -0.0354  |  ops/s |   -0.25% |
|                                                Max Throughput |                                 discovery-search-request-size-500 |    14.2119      |    14.1271      |     -0.08482 |  ops/s |   -0.60% |
|                                       50th percentile latency |                                 discovery-search-request-size-500 |    73.9577      |    71.7074      |     -2.25029 |     ms |   -3.04% |
|                                       90th percentile latency |                                 discovery-search-request-size-500 |    78.956       |    77.5988      |     -1.35719 |     ms |   -1.72% |
|                                      100th percentile latency |                                 discovery-search-request-size-500 |    89.7063      |   100.337       |     10.6306  |     ms |  +11.85% |
|                                  50th percentile service time |                                 discovery-search-request-size-500 |    73.9577      |    71.7074      |     -2.25029 |     ms |   -3.04% |
|                                  90th percentile service time |                                 discovery-search-request-size-500 |    78.956       |    77.5988      |     -1.35719 |     ms |   -1.72% |
|                                 100th percentile service time |                                 discovery-search-request-size-500 |    89.7063      |   100.337       |     10.6306  |     ms |  +11.85% |
|                                                    error rate |                                 discovery-search-request-size-500 |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                discovery-search-request-size-1000 |     8.16484     |     8.66704     |      0.50221 |  ops/s |   +6.15% |
|                                               Mean Throughput |                                discovery-search-request-size-1000 |     8.32709     |     8.73102     |      0.40394 |  ops/s |   +4.85% |
|                                             Median Throughput |                                discovery-search-request-size-1000 |     8.30659     |     8.689       |      0.38241 |  ops/s |   +4.60% |
|                                                Max Throughput |                                discovery-search-request-size-1000 |     8.49103     |     8.83596     |      0.34493 |  ops/s |   +4.06% |
|                                       50th percentile latency |                                discovery-search-request-size-1000 |   111.947       |   105.826       |     -6.12085 |     ms |   -5.47% |
|                                       90th percentile latency |                                discovery-search-request-size-1000 |   130.119       |   127.706       |     -2.41283 |     ms |   -1.85% |
|                                      100th percentile latency |                                discovery-search-request-size-1000 |   164.815       |   135.147       |    -29.6673  |     ms |  -18.00% |
|                                  50th percentile service time |                                discovery-search-request-size-1000 |   111.947       |   105.826       |     -6.12085 |     ms |   -5.47% |
|                                  90th percentile service time |                                discovery-search-request-size-1000 |   130.119       |   127.706       |     -2.41283 |     ms |   -1.85% |
|                                 100th percentile service time |                                discovery-search-request-size-1000 |   164.815       |   135.147       |    -29.6673  |     ms |  -18.00% |
|                                                    error rate |                                discovery-search-request-size-1000 |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                                   discover/search |     0.00343566  |     0.00343566  |     -0       |  ops/s |   -0.00% |
|                                               Mean Throughput |                                                   discover/search |     0.00354769  |     0.00354769  |      0       |  ops/s |    0.00% |
|                                             Median Throughput |                                                   discover/search |     0.00354769  |     0.00354769  |      0       |  ops/s |    0.00% |
|                                                Max Throughput |                                                   discover/search |     0.00365972  |     0.00365972  |      0       |  ops/s |    0.00% |
|                                       50th percentile latency |                                                   discover/search |   324.883       |   325.029       |      0.14621 |     ms |   +0.05% |
|                                      100th percentile latency |                                                   discover/search |   606.335       |   606.574       |      0.23883 |     ms |   +0.04% |
|                                  50th percentile service time |                                                   discover/search |   322.888       |   322.976       |      0.0882  |     ms |   +0.03% |
|                                 100th percentile service time |                                                   discover/search |   323.556       |   323.479       |     -0.07767 |     ms |   -0.02% |
|                                                    error rate |                                                   discover/search |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                                discover/visualize |     0.00231602  |     0.00231602  |      0       |  ops/s |    0.00% |
|                                               Mean Throughput |                                                discover/visualize |     0.00486777  |     0.00486777  |      0       |  ops/s |    0.00% |
|                                             Median Throughput |                                                discover/visualize |     0.00518902  |     0.00518902  |     -0       |  ops/s |   -0.00% |
|                                                Max Throughput |                                                discover/visualize |     0.00686522  |     0.00686522  |      0       |  ops/s |    0.00% |
|                                       50th percentile latency |                                                discover/visualize |   320.846       |   319.95        |     -0.89572 |     ms |   -0.28% |
|                                      100th percentile latency |                                                discover/visualize |   323.868       |   325.046       |      1.17798 |     ms |   +0.36% |
|                                  50th percentile service time |                                                discover/visualize |   318.814       |   317.915       |     -0.89873 |     ms |   -0.28% |
|                                 100th percentile service time |                                                discover/visualize |   322.662       |   323.103       |      0.44046 |     ms |   +0.14% |
|                                                    error rate |                                                discover/visualize |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                                             kafka |     0.00502541  |     0.00502541  |      0       |  ops/s |    0.00% |
|                                               Mean Throughput |                                                             kafka |     0.0110764   |     0.0110764   |     -0       |  ops/s |   -0.00% |
|                                             Median Throughput |                                                             kafka |     0.00971793  |     0.00971793  |     -0       |  ops/s |   -0.00% |
|                                                Max Throughput |                                                             kafka |     0.0187323   |     0.0187323   |     -0       |  ops/s |   -0.00% |
|                                       50th percentile latency |                                                             kafka |   319.302       |   318.844       |     -0.45872 |     ms |   -0.14% |
|                                      100th percentile latency |                                                             kafka |   328.983       |   326.454       |     -2.52911 |     ms |   -0.77% |
|                                  50th percentile service time |                                                             kafka |   316.716       |   316.915       |      0.19901 |     ms |   +0.06% |
|                                 100th percentile service time |                                                             kafka |   328.338       |   325.24        |     -3.09808 |     ms |   -0.94% |
|                                                    error rate |                                                             kafka |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                                             nginx |     0.00645896  |     0.00645915  |      0       |  ops/s |    0.00% |
|                                               Mean Throughput |                                                             nginx |     0.0233973   |     0.0233976   |      0       |  ops/s |    0.00% |
|                                             Median Throughput |                                                             nginx |     0.0241379   |     0.0241385   |      0       |  ops/s |    0.00% |
|                                                Max Throughput |                                                             nginx |     0.0347959   |     0.0347963   |      0       |  ops/s |    0.00% |
|                                       50th percentile latency |                                                             nginx |  1725.49        |  1725.8         |      0.30444 |     ms |   +0.02% |
|                                       90th percentile latency |                                                             nginx |  2646.4         |  2644.44        |     -1.9668  |     ms |   -0.07% |
|                                      100th percentile latency |                                                             nginx |  3683.81        |  3684.73        |      0.92358 |     ms |   +0.03% |
|                                  50th percentile service time |                                                             nginx |  1683.23        |  1683.55        |      0.31934 |     ms |   +0.02% |
|                                  90th percentile service time |                                                             nginx |  1726.31        |  1726.79        |      0.48745 |     ms |   +0.03% |
|                                 100th percentile service time |                                                             nginx |  1752.1         |  1752.06        |     -0.03796 |     ms |   -0.00% |
|                                                    error rate |                                                             nginx |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                                            apache |     0.0450341   |     0.0450345   |      0       |  ops/s |    0.00% |
|                                               Mean Throughput |                                                            apache |     0.0940559   |     0.0940597   |      0       |  ops/s |    0.00% |
|                                             Median Throughput |                                                            apache |     0.0977321   |     0.0977358   |      0       |  ops/s |    0.00% |
|                                                Max Throughput |                                                            apache |     0.158549    |     0.158562    |      1e-05   |  ops/s |    0.01% |
|                                       50th percentile latency |                                                            apache |   317.621       |   317.183       |     -0.43845 |     ms |   -0.14% |
|                                       90th percentile latency |                                                            apache |   330.113       |   330.221       |      0.10738 |     ms |   +0.03% |
|                                      100th percentile latency |                                                            apache |   373.418       |   373.853       |      0.43442 |     ms |   +0.12% |
|                                  50th percentile service time |                                                            apache |   314.8         |   314.938       |      0.1377  |     ms |   +0.04% |
|                                  90th percentile service time |                                                            apache |   327.96        |   327.805       |     -0.15448 |     ms |   -0.05% |
|                                 100th percentile service time |                                                            apache |   329.826       |   330.658       |      0.83234 |     ms |   +0.25% |
|                                                    error rate |                                                            apache |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                                       system/auth |     0.0655624   |     0.0655626   |      0       |  ops/s |    0.00% |
|                                               Mean Throughput |                                                       system/auth |     0.120339    |     0.120341    |      0       |  ops/s |    0.00% |
|                                             Median Throughput |                                                       system/auth |     0.118771    |     0.118772    |      0       |  ops/s |    0.00% |
|                                                Max Throughput |                                                       system/auth |     0.153317    |     0.153319    |      0       |  ops/s |    0.00% |
|                                       50th percentile latency |                                                       system/auth |   324.278       |   323.967       |     -0.31087 |     ms |   -0.10% |
|                                       90th percentile latency |                                                       system/auth |   381.112       |   381.36        |      0.248   |     ms |   +0.07% |
|                                      100th percentile latency |                                                       system/auth |   593.546       |   593.436       |     -0.10931 |     ms |   -0.02% |
|                                  50th percentile service time |                                                       system/auth |   321.91        |   321.7         |     -0.20999 |     ms |   -0.07% |
|                                  90th percentile service time |                                                       system/auth |   330.834       |   329.217       |     -1.61676 |     ms |   -0.49% |
|                                 100th percentile service time |                                                       system/auth |   415.781       |   415.768       |     -0.01291 |     ms |   -0.00% |
|                                                    error rate |                                                       system/auth |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                           system/syslog/dashboard |     0.0408357   |     0.0408356   |     -0       |  ops/s |   -0.00% |
|                                               Mean Throughput |                                           system/syslog/dashboard |     0.0535934   |     0.0535933   |     -0       |  ops/s |   -0.00% |
|                                             Median Throughput |                                           system/syslog/dashboard |     0.0520764   |     0.0520761   |     -0       |  ops/s |   -0.00% |
|                                                Max Throughput |                                           system/syslog/dashboard |     0.0694827   |     0.0694826   |     -0       |  ops/s |   -0.00% |
|                                       50th percentile latency |                                           system/syslog/dashboard |   318.126       |   318.167       |      0.04085 |     ms |   +0.01% |
|                                       90th percentile latency |                                           system/syslog/dashboard |   401.214       |   401.526       |      0.31228 |     ms |   +0.08% |
|                                      100th percentile latency |                                           system/syslog/dashboard |   593.801       |   593.626       |     -0.17535 |     ms |   -0.03% |
|                                  50th percentile service time |                                           system/syslog/dashboard |   316.093       |   316.084       |     -0.00891 |     ms |   -0.00% |
|                                  90th percentile service time |                                           system/syslog/dashboard |   320.933       |   320.868       |     -0.06463 |     ms |   -0.02% |
|                                 100th percentile service time |                                           system/syslog/dashboard |   322.296       |   322.206       |     -0.08969 |     ms |   -0.03% |
|                                                    error rate |                                           system/syslog/dashboard |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                                system/syslog/lens |     0.0113596   |     0.0113596   |      0       |  ops/s |    0.00% |
|                                               Mean Throughput |                                                system/syslog/lens |     0.0191301   |     0.01913     |     -0       |  ops/s |   -0.00% |
|                                             Median Throughput |                                                system/syslog/lens |     0.0163199   |     0.0163198   |     -0       |  ops/s |   -0.00% |
|                                                Max Throughput |                                                system/syslog/lens |     0.0512786   |     0.0512784   |     -0       |  ops/s |   -0.00% |
|                                       50th percentile latency |                                                system/syslog/lens |   322.509       |   323.444       |      0.93448 |     ms |   +0.29% |
|                                       90th percentile latency |                                                system/syslog/lens |   855.678       |   855.89        |      0.21179 |     ms |   +0.02% |
|                                      100th percentile latency |                                                system/syslog/lens |   875.748       |   875.931       |      0.1828  |     ms |   +0.02% |
|                                  50th percentile service time |                                                system/syslog/lens |   320.089       |   319.619       |     -0.46954 |     ms |   -0.15% |
|                                  90th percentile service time |                                                system/syslog/lens |   852.846       |   852.895       |      0.04944 |     ms |    0.01% |
|                                 100th percentile service time |                                                system/syslog/lens |   854.832       |   854.884       |      0.05249 |     ms |    0.01% |
|                                                    error rate |                                                system/syslog/lens |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                                   mysql/dashboard |     0.00336287  |     0.00336287  |      0       |  ops/s |    0.00% |
|                                               Mean Throughput |                                                   mysql/dashboard |     0.00888061  |     0.00888061  |      0       |  ops/s |    0.00% |
|                                             Median Throughput |                                                   mysql/dashboard |     0.00851366  |     0.00851367  |      0       |  ops/s |    0.00% |
|                                                Max Throughput |                                                   mysql/dashboard |     0.0150139   |     0.0150139   |     -0       |  ops/s |   -0.00% |
|                                       50th percentile latency |                                                   mysql/dashboard |   311.695       |   312.066       |      0.37019 |     ms |   +0.12% |
|                                       90th percentile latency |                                                   mysql/dashboard |   329.769       |   329.402       |     -0.36735 |     ms |   -0.11% |
|                                      100th percentile latency |                                                   mysql/dashboard |   549.315       |   547.704       |     -1.61115 |     ms |   -0.29% |
|                                  50th percentile service time |                                                   mysql/dashboard |   309.552       |   309.614       |      0.06128 |     ms |   +0.02% |
|                                  90th percentile service time |                                                   mysql/dashboard |   319.084       |   318.619       |     -0.46483 |     ms |   -0.15% |
|                                 100th percentile service time |                                                   mysql/dashboard |   331.379       |   331.759       |      0.37991 |     ms |   +0.11% |
|                                                    error rate |                                                   mysql/dashboard |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                                             redis |     0.00958889  |     0.00958889  |      0       |  ops/s |    0.00% |
|                                               Mean Throughput |                                                             redis |     0.040273    |     0.040273    |      0       |  ops/s |    0.00% |
|                                             Median Throughput |                                                             redis |     0.0410647   |     0.0410646   |     -0       |  ops/s |   -0.00% |
|                                                Max Throughput |                                                             redis |     0.0726225   |     0.0726225   |      0       |  ops/s |    0.00% |
|                                       50th percentile latency |                                                             redis |   322.709       |   323.299       |      0.59003 |     ms |   +0.18% |
|                                       90th percentile latency |                                                             redis |   400.301       |   400.098       |     -0.20337 |     ms |   -0.05% |
|                                      100th percentile latency |                                                             redis |   785.169       |   784.856       |     -0.31366 |     ms |   -0.04% |
|                                  50th percentile service time |                                                             redis |   321.719       |   322.095       |      0.37601 |     ms |   +0.12% |
|                                  90th percentile service time |                                                             redis |   332.401       |   332.304       |     -0.09732 |     ms |   -0.03% |
|                                 100th percentile service time |                                                             redis |   784.053       |   783.885       |     -0.16742 |     ms |   -0.02% |
|                                                    error rate |                                                             redis |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                                        mysql/lens |     0.00680639  |     0.00680638  |     -0       |  ops/s |   -0.00% |
|                                               Mean Throughput |                                                        mysql/lens |     0.0273108   |     0.0273108   |     -0       |  ops/s |   -0.00% |
|                                             Median Throughput |                                                        mysql/lens |     0.0281678   |     0.0281678   |     -0       |  ops/s |   -0.00% |
|                                                Max Throughput |                                                        mysql/lens |     0.047013    |     0.0470134   |      0       |  ops/s |    0.00% |
|                                       50th percentile latency |                                                        mysql/lens |   318.068       |   317.823       |     -0.24464 |     ms |   -0.08% |
|                                       90th percentile latency |                                                        mysql/lens |   983.433       |   982.574       |     -0.85917 |     ms |   -0.09% |
|                                      100th percentile latency |                                                        mysql/lens |  1000.73        |  1000.13        |     -0.60083 |     ms |   -0.06% |
|                                  50th percentile service time |                                                        mysql/lens |   316.92        |   315.376       |     -1.54443 |     ms |   -0.49% |
|                                  90th percentile service time |                                                        mysql/lens |   535.986       |   536.64        |      0.65446 |     ms |   +0.12% |
|                                 100th percentile service time |                                                        mysql/lens |   998.652       |   998.53        |     -0.12152 |     ms |   -0.01% |
|                                                    error rate |                                                        mysql/lens |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                               postgresql/overview |     0.00513624  |     0.00513626  |      0       |  ops/s |    0.00% |
|                                               Mean Throughput |                                               postgresql/overview |     0.0581881   |     0.0581883   |      0       |  ops/s |    0.00% |
|                                             Median Throughput |                                               postgresql/overview |     0.0620372   |     0.0620373   |      0       |  ops/s |    0.00% |
|                                                Max Throughput |                                               postgresql/overview |     0.0894029   |     0.0894028   |     -0       |  ops/s |   -0.00% |
|                                       50th percentile latency |                                               postgresql/overview |  1011.66        |  1011.98        |      0.3251  |     ms |   +0.03% |
|                                       90th percentile latency |                                               postgresql/overview |  1501.11        |  1500.16        |     -0.94684 |     ms |   -0.06% |
|                                      100th percentile latency |                                               postgresql/overview |  2142.54        |  2139.76        |     -2.7854  |     ms |   -0.13% |
|                                  50th percentile service time |                                               postgresql/overview |  1007.38        |  1007.27        |     -0.11078 |     ms |   -0.01% |
|                                  90th percentile service time |                                               postgresql/overview |  1047.39        |  1046.96        |     -0.43503 |     ms |   -0.04% |
|                                 100th percentile service time |                                               postgresql/overview |  1672.64        |  1673.45        |      0.8114  |     ms |   +0.05% |
|                                                    error rate |                                               postgresql/overview |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                               postgresql/duration |     0.0224605   |     0.0224605   |     -0       |  ops/s |   -0.00% |
|                                               Mean Throughput |                                               postgresql/duration |     0.0643453   |     0.0643452   |     -0       |  ops/s |   -0.00% |
|                                             Median Throughput |                                               postgresql/duration |     0.0679207   |     0.0679206   |     -0       |  ops/s |   -0.00% |
|                                                Max Throughput |                                               postgresql/duration |     0.0802623   |     0.0802622   |     -0       |  ops/s |   -0.00% |
|                                       50th percentile latency |                                               postgresql/duration |   313.758       |   313.166       |     -0.59235 |     ms |   -0.19% |
|                                       90th percentile latency |                                               postgresql/duration |   414.694       |   413.985       |     -0.70875 |     ms |   -0.17% |
|                                      100th percentile latency |                                               postgresql/duration |   740.586       |   740.838       |      0.25238 |     ms |   +0.03% |
|                                  50th percentile service time |                                               postgresql/duration |   311.87        |   311.608       |     -0.26282 |     ms |   -0.08% |
|                                  90th percentile service time |                                               postgresql/duration |   317.833       |   317.94        |      0.10676 |     ms |   +0.03% |
|                                 100th percentile service time |                                               postgresql/duration |   319.85        |   319.487       |     -0.36304 |     ms |   -0.11% |
|                                                    error rate |                                               postgresql/duration |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                  esql_basic_count_group_0_limit_0 |    46.9628      |    64.1562      |     17.1934  |  ops/s |  +36.61% |
|                                               Mean Throughput |                                  esql_basic_count_group_0_limit_0 |    46.9628      |    64.1562      |     17.1934  |  ops/s |  +36.61% |
|                                             Median Throughput |                                  esql_basic_count_group_0_limit_0 |    46.9628      |    64.1562      |     17.1934  |  ops/s |  +36.61% |
|                                                Max Throughput |                                  esql_basic_count_group_0_limit_0 |    46.9628      |    64.1562      |     17.1934  |  ops/s |  +36.61% |
|                                       50th percentile latency |                                  esql_basic_count_group_0_limit_0 |     4.47457     |     4.02173     |     -0.45283 |     ms |  -10.12% |
|                                       90th percentile latency |                                  esql_basic_count_group_0_limit_0 |     5.89645     |     6.03744     |      0.14099 |     ms |   +2.39% |
|                                      100th percentile latency |                                  esql_basic_count_group_0_limit_0 |     6.25584     |     6.70334     |      0.4475  |     ms |   +7.15% |
|                                  50th percentile service time |                                  esql_basic_count_group_0_limit_0 |     4.47457     |     4.02173     |     -0.45283 |     ms |  -10.12% |
|                                  90th percentile service time |                                  esql_basic_count_group_0_limit_0 |     5.89645     |     6.03744     |      0.14099 |     ms |   +2.39% |
|                                 100th percentile service time |                                  esql_basic_count_group_0_limit_0 |     6.25584     |     6.70334     |      0.4475  |     ms |   +7.15% |
|                                                    error rate |                                  esql_basic_count_group_0_limit_0 |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                  esql_basic_count_group_1_limit_0 |   215.987       |   189.84        |    -26.1464  |  ops/s |  -12.11% |
|                                               Mean Throughput |                                  esql_basic_count_group_1_limit_0 |   215.987       |   189.84        |    -26.1464  |  ops/s |  -12.11% |
|                                             Median Throughput |                                  esql_basic_count_group_1_limit_0 |   215.987       |   189.84        |    -26.1464  |  ops/s |  -12.11% |
|                                                Max Throughput |                                  esql_basic_count_group_1_limit_0 |   215.987       |   189.84        |    -26.1464  |  ops/s |  -12.11% |
|                                       50th percentile latency |                                  esql_basic_count_group_1_limit_0 |     3.57116     |     4.19162     |      0.62046 |     ms |  +17.37% |
|                                       90th percentile latency |                                  esql_basic_count_group_1_limit_0 |     4.35844     |     5.26705     |      0.9086  |     ms |  +20.85% |
|                                      100th percentile latency |                                  esql_basic_count_group_1_limit_0 |     5.15062     |     5.54127     |      0.39065 |     ms |   +7.58% |
|                                  50th percentile service time |                                  esql_basic_count_group_1_limit_0 |     3.57116     |     4.19162     |      0.62046 |     ms |  +17.37% |
|                                  90th percentile service time |                                  esql_basic_count_group_1_limit_0 |     4.35844     |     5.26705     |      0.9086  |     ms |  +20.85% |
|                                 100th percentile service time |                                  esql_basic_count_group_1_limit_0 |     5.15062     |     5.54127     |      0.39065 |     ms |   +7.58% |
|                                                    error rate |                                  esql_basic_count_group_1_limit_0 |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                  esql_basic_count_group_2_limit_0 |   261.588       |   249.594       |    -11.994   |  ops/s |   -4.59% |
|                                               Mean Throughput |                                  esql_basic_count_group_2_limit_0 |   261.588       |   249.594       |    -11.994   |  ops/s |   -4.59% |
|                                             Median Throughput |                                  esql_basic_count_group_2_limit_0 |   261.588       |   249.594       |    -11.994   |  ops/s |   -4.59% |
|                                                Max Throughput |                                  esql_basic_count_group_2_limit_0 |   261.588       |   249.594       |    -11.994   |  ops/s |   -4.59% |
|                                       50th percentile latency |                                  esql_basic_count_group_2_limit_0 |     3.19665     |     3.30961     |      0.11296 |     ms |   +3.53% |
|                                       90th percentile latency |                                  esql_basic_count_group_2_limit_0 |     3.61625     |     3.71475     |      0.09851 |     ms |   +2.72% |
|                                      100th percentile latency |                                  esql_basic_count_group_2_limit_0 |     4.09853     |     4.30215     |      0.20362 |     ms |   +4.97% |
|                                  50th percentile service time |                                  esql_basic_count_group_2_limit_0 |     3.19665     |     3.30961     |      0.11296 |     ms |   +3.53% |
|                                  90th percentile service time |                                  esql_basic_count_group_2_limit_0 |     3.61625     |     3.71475     |      0.09851 |     ms |   +2.72% |
|                                 100th percentile service time |                                  esql_basic_count_group_2_limit_0 |     4.09853     |     4.30215     |      0.20362 |     ms |   +4.97% |
|                                                    error rate |                                  esql_basic_count_group_2_limit_0 |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                  esql_basic_count_group_3_limit_0 |   231.135       |   222.176       |     -8.95892 |  ops/s |   -3.88% |
|                                               Mean Throughput |                                  esql_basic_count_group_3_limit_0 |   231.135       |   222.176       |     -8.95892 |  ops/s |   -3.88% |
|                                             Median Throughput |                                  esql_basic_count_group_3_limit_0 |   231.135       |   222.176       |     -8.95892 |  ops/s |   -3.88% |
|                                                Max Throughput |                                  esql_basic_count_group_3_limit_0 |   231.135       |   222.176       |     -8.95892 |  ops/s |   -3.88% |
|                                       50th percentile latency |                                  esql_basic_count_group_3_limit_0 |     3.76972     |     3.94922     |      0.1795  |     ms |   +4.76% |
|                                       90th percentile latency |                                  esql_basic_count_group_3_limit_0 |     4.38499     |     4.50246     |      0.11747 |     ms |   +2.68% |
|                                      100th percentile latency |                                  esql_basic_count_group_3_limit_0 |     4.50567     |     4.65552     |      0.14985 |     ms |   +3.33% |
|                                  50th percentile service time |                                  esql_basic_count_group_3_limit_0 |     3.76972     |     3.94922     |      0.1795  |     ms |   +4.76% |
|                                  90th percentile service time |                                  esql_basic_count_group_3_limit_0 |     4.38499     |     4.50246     |      0.11747 |     ms |   +2.68% |
|                                 100th percentile service time |                                  esql_basic_count_group_3_limit_0 |     4.50567     |     4.65552     |      0.14985 |     ms |   +3.33% |
|                                                    error rate |                                  esql_basic_count_group_3_limit_0 |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                  esql_basic_count_group_4_limit_0 |   246.741       |   299.483       |     52.7415  |  ops/s |  +21.38% |
|                                               Mean Throughput |                                  esql_basic_count_group_4_limit_0 |   246.741       |   299.483       |     52.7415  |  ops/s |  +21.38% |
|                                             Median Throughput |                                  esql_basic_count_group_4_limit_0 |   246.741       |   299.483       |     52.7415  |  ops/s |  +21.38% |
|                                                Max Throughput |                                  esql_basic_count_group_4_limit_0 |   246.741       |   299.483       |     52.7415  |  ops/s |  +21.38% |
|                                       50th percentile latency |                                  esql_basic_count_group_4_limit_0 |     2.94397     |     2.64897     |     -0.29501 |     ms |  -10.02% |
|                                       90th percentile latency |                                  esql_basic_count_group_4_limit_0 |     3.33602     |     3.08173     |     -0.25429 |     ms |   -7.62% |
|                                      100th percentile latency |                                  esql_basic_count_group_4_limit_0 |     4.33007     |     3.84426     |     -0.48581 |     ms |  -11.22% |
|                                  50th percentile service time |                                  esql_basic_count_group_4_limit_0 |     2.94397     |     2.64897     |     -0.29501 |     ms |  -10.02% |
|                                  90th percentile service time |                                  esql_basic_count_group_4_limit_0 |     3.33602     |     3.08173     |     -0.25429 |     ms |   -7.62% |
|                                 100th percentile service time |                                  esql_basic_count_group_4_limit_0 |     4.33007     |     3.84426     |     -0.48581 |     ms |  -11.22% |
|                                                    error rate |                                  esql_basic_count_group_4_limit_0 |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |   115.675       |   105.034       |    -10.6411  |  ops/s |   -9.20% |
|                                               Mean Throughput |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |   115.675       |   105.034       |    -10.6411  |  ops/s |   -9.20% |
|                                             Median Throughput |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |   115.675       |   105.034       |    -10.6411  |  ops/s |   -9.20% |
|                                                Max Throughput |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |   115.675       |   105.034       |    -10.6411  |  ops/s |   -9.20% |
|                                       50th percentile latency |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |     5.57662     |     6.17024     |      0.59362 |     ms |  +10.64% |
|                                       90th percentile latency |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |     6.74759     |     7.16941     |      0.42181 |     ms |   +6.25% |
|                                      100th percentile latency |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |     7.80328     |     7.83489     |      0.03161 |     ms |   +0.41% |
|                                  50th percentile service time |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |     5.57662     |     6.17024     |      0.59362 |     ms |  +10.64% |
|                                  90th percentile service time |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |     6.74759     |     7.16941     |      0.42181 |     ms |   +6.25% |
|                                 100th percentile service time |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |     7.80328     |     7.83489     |      0.03161 |     ms |   +0.41% |
|                                                    error rate |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |   188.756       |   211.592       |     22.8362  |  ops/s |  +12.10% |
|                                               Mean Throughput | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |   188.756       |   211.592       |     22.8362  |  ops/s |  +12.10% |
|                                             Median Throughput | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |   188.756       |   211.592       |     22.8362  |  ops/s |  +12.10% |
|                                                Max Throughput | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |   188.756       |   211.592       |     22.8362  |  ops/s |  +12.10% |
|                                       50th percentile latency | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |     4.62531     |     3.90701     |     -0.7183  |     ms |  -15.53% |
|                                       90th percentile latency | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |     5.19485     |     4.67243     |     -0.52242 |     ms |  -10.06% |
|                                      100th percentile latency | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |     5.8241      |     5.07373     |     -0.75037 |     ms |  -12.88% |
|                                  50th percentile service time | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |     4.62531     |     3.90701     |     -0.7183  |     ms |  -15.53% |
|                                  90th percentile service time | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |     5.19485     |     4.67243     |     -0.52242 |     ms |  -10.06% |
|                                 100th percentile service time | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |     5.8241      |     5.07373     |     -0.75037 |     ms |  -12.88% |
|                                                    error rate | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                           esql_dissect_duration_and_stats_limit_0 |   278.832       |   285.388       |      6.55588 |  ops/s |   +2.35% |
|                                               Mean Throughput |                           esql_dissect_duration_and_stats_limit_0 |   278.832       |   285.388       |      6.55588 |  ops/s |   +2.35% |
|                                             Median Throughput |                           esql_dissect_duration_and_stats_limit_0 |   278.832       |   285.388       |      6.55588 |  ops/s |   +2.35% |
|                                                Max Throughput |                           esql_dissect_duration_and_stats_limit_0 |   278.832       |   285.388       |      6.55588 |  ops/s |   +2.35% |
|                                       50th percentile latency |                           esql_dissect_duration_and_stats_limit_0 |     2.57894     |     2.44128     |     -0.13766 |     ms |   -5.34% |
|                                       90th percentile latency |                           esql_dissect_duration_and_stats_limit_0 |     3.04003     |     2.83782     |     -0.20221 |     ms |   -6.65% |
|                                      100th percentile latency |                           esql_dissect_duration_and_stats_limit_0 |     3.73966     |     3.03821     |     -0.70145 |     ms |  -18.76% |
|                                  50th percentile service time |                           esql_dissect_duration_and_stats_limit_0 |     2.57894     |     2.44128     |     -0.13766 |     ms |   -5.34% |
|                                  90th percentile service time |                           esql_dissect_duration_and_stats_limit_0 |     3.04003     |     2.83782     |     -0.20221 |     ms |   -6.65% |
|                                 100th percentile service time |                           esql_dissect_duration_and_stats_limit_0 |     3.73966     |     3.03821     |     -0.70145 |     ms |  -18.76% |
|                                                    error rate |                           esql_dissect_duration_and_stats_limit_0 |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                          esql_basic_count_group_0 |   107.093       |   111.08        |      3.98747 |  ops/s |   +3.72% |
|                                               Mean Throughput |                                          esql_basic_count_group_0 |   107.093       |   111.08        |      3.98747 |  ops/s |   +3.72% |
|                                             Median Throughput |                                          esql_basic_count_group_0 |   107.093       |   111.08        |      3.98747 |  ops/s |   +3.72% |
|                                                Max Throughput |                                          esql_basic_count_group_0 |   107.093       |   111.08        |      3.98747 |  ops/s |   +3.72% |
|                                       50th percentile latency |                                          esql_basic_count_group_0 |     6.10857     |     5.29433     |     -0.81424 |     ms |  -13.33% |
|                                       90th percentile latency |                                          esql_basic_count_group_0 |     6.99559     |     6.73093     |     -0.26466 |     ms |   -3.78% |
|                                      100th percentile latency |                                          esql_basic_count_group_0 |     7.55527     |     7.80563     |      0.25036 |     ms |   +3.31% |
|                                  50th percentile service time |                                          esql_basic_count_group_0 |     6.10857     |     5.29433     |     -0.81424 |     ms |  -13.33% |
|                                  90th percentile service time |                                          esql_basic_count_group_0 |     6.99559     |     6.73093     |     -0.26466 |     ms |   -3.78% |
|                                 100th percentile service time |                                          esql_basic_count_group_0 |     7.55527     |     7.80563     |      0.25036 |     ms |   +3.31% |
|                                                    error rate |                                          esql_basic_count_group_0 |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                          esql_basic_count_group_1 |     3.5104      |     3.3263      |     -0.1841  |  ops/s |   -5.24% |
|                                               Mean Throughput |                                          esql_basic_count_group_1 |     3.5554      |     3.43065     |     -0.12475 |  ops/s |   -3.51% |
|                                             Median Throughput |                                          esql_basic_count_group_1 |     3.55896     |     3.44781     |     -0.11114 |  ops/s |   -3.12% |
|                                                Max Throughput |                                          esql_basic_count_group_1 |     3.56756     |     3.48585     |     -0.08171 |  ops/s |   -2.29% |
|                                       50th percentile latency |                                          esql_basic_count_group_1 |   275.083       |   280.099       |      5.01611 |     ms |   +1.82% |
|                                       90th percentile latency |                                          esql_basic_count_group_1 |   290.657       |   289.156       |     -1.50045 |     ms |   -0.52% |
|                                      100th percentile latency |                                          esql_basic_count_group_1 |   330.031       |   319.378       |    -10.6527  |     ms |   -3.23% |
|                                  50th percentile service time |                                          esql_basic_count_group_1 |   275.083       |   280.099       |      5.01611 |     ms |   +1.82% |
|                                  90th percentile service time |                                          esql_basic_count_group_1 |   290.657       |   289.156       |     -1.50045 |     ms |   -0.52% |
|                                 100th percentile service time |                                          esql_basic_count_group_1 |   330.031       |   319.378       |    -10.6527  |     ms |   -3.23% |
|                                                    error rate |                                          esql_basic_count_group_1 |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                          esql_basic_count_group_2 |     0.854504    |     0.923581    |      0.06908 |  ops/s |   +8.08% |
|                                               Mean Throughput |                                          esql_basic_count_group_2 |     1.14733     |     1.2163      |      0.06898 |  ops/s |   +6.01% |
|                                             Median Throughput |                                          esql_basic_count_group_2 |     1.18643     |     1.25901     |      0.07258 |  ops/s |   +6.12% |
|                                                Max Throughput |                                          esql_basic_count_group_2 |     1.32138     |     1.3893      |      0.06792 |  ops/s |   +5.14% |
|                                       50th percentile latency |                                          esql_basic_count_group_2 |   579.716       |   598.748       |     19.0323  |     ms |   +3.28% |
|                                       90th percentile latency |                                          esql_basic_count_group_2 |   612.418       |   605.976       |     -6.44249 |     ms |   -1.05% |
|                                      100th percentile latency |                                          esql_basic_count_group_2 |   636.498       |   606.506       |    -29.992   |     ms |   -4.71% |
|                                  50th percentile service time |                                          esql_basic_count_group_2 |   579.716       |   598.748       |     19.0323  |     ms |   +3.28% |
|                                  90th percentile service time |                                          esql_basic_count_group_2 |   612.418       |   605.976       |     -6.44249 |     ms |   -1.05% |
|                                 100th percentile service time |                                          esql_basic_count_group_2 |   636.498       |   606.506       |    -29.992   |     ms |   -4.71% |
|                                                    error rate |                                          esql_basic_count_group_2 |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                          esql_basic_count_group_3 |     0.727249    |     0.665153    |     -0.0621  |  ops/s |   -8.54% |
|                                               Mean Throughput |                                          esql_basic_count_group_3 |     0.796287    |     0.786837    |     -0.00945 |  ops/s |   -1.19% |
|                                             Median Throughput |                                          esql_basic_count_group_3 |     0.80027     |     0.799056    |     -0.00121 |  ops/s |   -0.15% |
|                                                Max Throughput |                                          esql_basic_count_group_3 |     0.859265    |     0.854176    |     -0.00509 |  ops/s |   -0.59% |
|                                       50th percentile latency |                                          esql_basic_count_group_3 |   951.8         |   946.676       |     -5.12405 |     ms |   -0.54% |
|                                       90th percentile latency |                                          esql_basic_count_group_3 |  1067.57        |   956.251       |   -111.321   |     ms |  -10.43% |
|                                      100th percentile latency |                                          esql_basic_count_group_3 |  1424.22        |   959.152       |   -465.067   |     ms |  -32.65% |
|                                  50th percentile service time |                                          esql_basic_count_group_3 |   951.8         |   946.676       |     -5.12405 |     ms |   -0.54% |
|                                  90th percentile service time |                                          esql_basic_count_group_3 |  1067.57        |   956.251       |   -111.321   |     ms |  -10.43% |
|                                 100th percentile service time |                                          esql_basic_count_group_3 |  1424.22        |   959.152       |   -465.067   |     ms |  -32.65% |
|                                                    error rate |                                          esql_basic_count_group_3 |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                          esql_basic_count_group_4 |     0.368945    |     0.382821    |      0.01388 |  ops/s |   +3.76% |
|                                               Mean Throughput |                                          esql_basic_count_group_4 |     0.375159    |     0.386834    |      0.01167 |  ops/s |   +3.11% |
|                                             Median Throughput |                                          esql_basic_count_group_4 |     0.375878    |     0.387479    |      0.0116  |  ops/s |   +3.09% |
|                                                Max Throughput |                                          esql_basic_count_group_4 |     0.3787      |     0.389838    |      0.01114 |  ops/s |   +2.94% |
|                                       50th percentile latency |                                          esql_basic_count_group_4 |  2592.57        |  2537.01        |    -55.5618  |     ms |   -2.14% |
|                                       90th percentile latency |                                          esql_basic_count_group_4 |  2629.32        |  2570.33        |    -58.9871  |     ms |   -2.24% |
|                                      100th percentile latency |                                          esql_basic_count_group_4 |  2634.95        |  2584.25        |    -50.7036  |     ms |   -1.92% |
|                                  50th percentile service time |                                          esql_basic_count_group_4 |  2592.57        |  2537.01        |    -55.5618  |     ms |   -2.14% |
|                                  90th percentile service time |                                          esql_basic_count_group_4 |  2629.32        |  2570.33        |    -58.9871  |     ms |   -2.24% |
|                                 100th percentile service time |                                          esql_basic_count_group_4 |  2634.95        |  2584.25        |    -50.7036  |     ms |   -1.92% |
|                                                    error rate |                                          esql_basic_count_group_4 |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |          esql_time_range_and_date_histogram_two_groups_pre_filter |     2.81442     |     3.29442     |      0.48    |  ops/s |  +17.05% |
|                                               Mean Throughput |          esql_time_range_and_date_histogram_two_groups_pre_filter |     3.56687     |     3.79415     |      0.22729 |  ops/s |   +6.37% |
|                                             Median Throughput |          esql_time_range_and_date_histogram_two_groups_pre_filter |     3.71066     |     3.87188     |      0.16122 |  ops/s |   +4.34% |
|                                                Max Throughput |          esql_time_range_and_date_histogram_two_groups_pre_filter |     4.07088     |     4.13845     |      0.06757 |  ops/s |   +1.66% |
|                                       50th percentile latency |          esql_time_range_and_date_histogram_two_groups_pre_filter |   204.78        |   207.09        |      2.30956 |     ms |   +1.13% |
|                                       90th percentile latency |          esql_time_range_and_date_histogram_two_groups_pre_filter |   236.096       |   218.34        |    -17.756   |     ms |   -7.52% |
|                                      100th percentile latency |          esql_time_range_and_date_histogram_two_groups_pre_filter |   243.314       |   225.867       |    -17.4472  |     ms |   -7.17% |
|                                  50th percentile service time |          esql_time_range_and_date_histogram_two_groups_pre_filter |   204.78        |   207.09        |      2.30956 |     ms |   +1.13% |
|                                  90th percentile service time |          esql_time_range_and_date_histogram_two_groups_pre_filter |   236.096       |   218.34        |    -17.756   |     ms |   -7.52% |
|                                 100th percentile service time |          esql_time_range_and_date_histogram_two_groups_pre_filter |   243.314       |   225.867       |    -17.4472  |     ms |   -7.17% |
|                                                    error rate |          esql_time_range_and_date_histogram_two_groups_pre_filter |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |         esql_time_range_and_date_histogram_two_groups_post_filter |     0.289828    |     0.282856    |     -0.00697 |  ops/s |   -2.41% |
|                                               Mean Throughput |         esql_time_range_and_date_histogram_two_groups_post_filter |     0.296831    |     0.28533     |     -0.0115  |  ops/s |   -3.87% |
|                                             Median Throughput |         esql_time_range_and_date_histogram_two_groups_post_filter |     0.297909    |     0.285609    |     -0.0123  |  ops/s |   -4.13% |
|                                                Max Throughput |         esql_time_range_and_date_histogram_two_groups_post_filter |     0.300667    |     0.286406    |     -0.01426 |  ops/s |   -4.74% |
|                                       50th percentile latency |         esql_time_range_and_date_histogram_two_groups_post_filter |  3284.24        |  3484.8         |    200.562   |     ms |   +6.11% |
|                                       90th percentile latency |         esql_time_range_and_date_histogram_two_groups_post_filter |  3339.42        |  3535           |    195.581   |     ms |   +5.86% |
|                                      100th percentile latency |         esql_time_range_and_date_histogram_two_groups_post_filter |  3427.6         |  3664.6         |    236.998   |     ms |   +6.91% |
|                                  50th percentile service time |         esql_time_range_and_date_histogram_two_groups_post_filter |  3284.24        |  3484.8         |    200.562   |     ms |   +6.11% |
|                                  90th percentile service time |         esql_time_range_and_date_histogram_two_groups_post_filter |  3339.42        |  3535           |    195.581   |     ms |   +5.86% |
|                                 100th percentile service time |         esql_time_range_and_date_histogram_two_groups_post_filter |  3427.6         |  3664.6         |    236.998   |     ms |   +6.91% |
|                                                    error rate |         esql_time_range_and_date_histogram_two_groups_post_filter |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                   esql_dissect_duration_and_stats |     3.49274     |     6.83947     |      3.34672 |  ops/s |  +95.82% |
|                                               Mean Throughput |                                   esql_dissect_duration_and_stats |     5.06635     |     8.60092     |      3.53456 |  ops/s |  +69.77% |
|                                             Median Throughput |                                   esql_dissect_duration_and_stats |     5.06635     |     8.60092     |      3.53456 |  ops/s |  +69.77% |
|                                                Max Throughput |                                   esql_dissect_duration_and_stats |     6.63997     |    10.3624      |      3.7224  |  ops/s |  +56.06% |
|                                       50th percentile latency |                                   esql_dissect_duration_and_stats |    70.8461      |    70.2079      |     -0.63816 |     ms |   -0.90% |
|                                       90th percentile latency |                                   esql_dissect_duration_and_stats |    98.4276      |    76.1954      |    -22.2322  |     ms |  -22.59% |
|                                      100th percentile latency |                                   esql_dissect_duration_and_stats |   140.25        |    87.1486      |    -53.1013  |     ms |  -37.86% |
|                                  50th percentile service time |                                   esql_dissect_duration_and_stats |    70.8461      |    70.2079      |     -0.63816 |     ms |   -0.90% |
|                                  90th percentile service time |                                   esql_dissect_duration_and_stats |    98.4276      |    76.1954      |    -22.2322  |     ms |  -22.59% |
|                                 100th percentile service time |                                   esql_dissect_duration_and_stats |   140.25        |    87.1486      |    -53.1013  |     ms |  -37.86% |
|                                                    error rate |                                   esql_dissect_duration_and_stats |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                           term_query_with_matches |    14.1069      |    19.0473      |      4.94037 |  ops/s |  +35.02% |
|                                               Mean Throughput |                                           term_query_with_matches |    17.8471      |    19.5729      |      1.72574 |  ops/s |   +9.67% |
|                                             Median Throughput |                                           term_query_with_matches |    19.4559      |    19.4295      |     -0.02645 |  ops/s |   -0.14% |
|                                                Max Throughput |                                           term_query_with_matches |    19.9786      |    20.2419      |      0.26329 |  ops/s |   +1.32% |
|                                       50th percentile latency |                                           term_query_with_matches |    44.4056      |    53.3954      |      8.98981 |     ms |  +20.24% |
|                                       90th percentile latency |                                           term_query_with_matches |    81.8093      |    80.4971      |     -1.31221 |     ms |   -1.60% |
|                                      100th percentile latency |                                           term_query_with_matches |   105.273       |   102.462       |     -2.81078 |     ms |   -2.67% |
|                                  50th percentile service time |                                           term_query_with_matches |    44.4056      |    53.3954      |      8.98981 |     ms |  +20.24% |
|                                  90th percentile service time |                                           term_query_with_matches |    81.8093      |    80.4971      |     -1.31221 |     ms |   -1.60% |
|                                 100th percentile service time |                                           term_query_with_matches |   105.273       |   102.462       |     -2.81078 |     ms |   -2.67% |
|                                                    error rate |                                           term_query_with_matches |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                  term_query_with_matches_argument |    74.3252      |    63.4785      |    -10.8467  |  ops/s |  -14.59% |
|                                               Mean Throughput |                                  term_query_with_matches_argument |    74.3252      |    63.4785      |    -10.8467  |  ops/s |  -14.59% |
|                                             Median Throughput |                                  term_query_with_matches_argument |    74.3252      |    63.4785      |    -10.8467  |  ops/s |  -14.59% |
|                                                Max Throughput |                                  term_query_with_matches_argument |    74.3252      |    63.4785      |    -10.8467  |  ops/s |  -14.59% |
|                                       50th percentile latency |                                  term_query_with_matches_argument |    11.5467      |    14.3266      |      2.77991 |     ms |  +24.08% |
|                                       90th percentile latency |                                  term_query_with_matches_argument |    12.4101      |    15.3865      |      2.97639 |     ms |  +23.98% |
|                                      100th percentile latency |                                  term_query_with_matches_argument |    14.582       |    16.3427      |      1.76066 |     ms |  +12.07% |
|                                  50th percentile service time |                                  term_query_with_matches_argument |    11.5467      |    14.3266      |      2.77991 |     ms |  +24.08% |
|                                  90th percentile service time |                                  term_query_with_matches_argument |    12.4101      |    15.3865      |      2.97639 |     ms |  +23.98% |
|                                 100th percentile service time |                                  term_query_with_matches_argument |    14.582       |    16.3427      |      1.76066 |     ms |  +12.07% |
|                                                    error rate |                                  term_query_with_matches_argument |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                    term_query_empty_template_term |   184.267       |   187.084       |      2.81694 |  ops/s |   +1.53% |
|                                               Mean Throughput |                                    term_query_empty_template_term |   184.267       |   187.084       |      2.81694 |  ops/s |   +1.53% |
|                                             Median Throughput |                                    term_query_empty_template_term |   184.267       |   187.084       |      2.81694 |  ops/s |   +1.53% |
|                                                Max Throughput |                                    term_query_empty_template_term |   184.267       |   187.084       |      2.81694 |  ops/s |   +1.53% |
|                                       50th percentile latency |                                    term_query_empty_template_term |     4.05468     |     4.02868     |     -0.02599 |     ms |   -0.64% |
|                                       90th percentile latency |                                    term_query_empty_template_term |     4.38576     |     4.41209     |      0.02633 |     ms |   +0.60% |
|                                      100th percentile latency |                                    term_query_empty_template_term |     4.7327      |     4.92927     |      0.19657 |     ms |   +4.15% |
|                                  50th percentile service time |                                    term_query_empty_template_term |     4.05468     |     4.02868     |     -0.02599 |     ms |   -0.64% |
|                                  90th percentile service time |                                    term_query_empty_template_term |     4.38576     |     4.41209     |      0.02633 |     ms |   +0.60% |
|                                 100th percentile service time |                                    term_query_empty_template_term |     4.7327      |     4.92927     |      0.19657 |     ms |   +4.15% |
|                                                    error rate |                                    term_query_empty_template_term |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                    term_query_empty_argument_term |   166.222       |   172.24        |      6.01797 |  ops/s |   +3.62% |
|                                               Mean Throughput |                                    term_query_empty_argument_term |   166.222       |   172.24        |      6.01797 |  ops/s |   +3.62% |
|                                             Median Throughput |                                    term_query_empty_argument_term |   166.222       |   172.24        |      6.01797 |  ops/s |   +3.62% |
|                                                Max Throughput |                                    term_query_empty_argument_term |   166.222       |   172.24        |      6.01797 |  ops/s |   +3.62% |
|                                       50th percentile latency |                                    term_query_empty_argument_term |     4.64536     |     4.32766     |     -0.3177  |     ms |   -6.84% |
|                                       90th percentile latency |                                    term_query_empty_argument_term |     5.26491     |     4.71742     |     -0.54749 |     ms |  -10.40% |
|                                      100th percentile latency |                                    term_query_empty_argument_term |     5.56797     |     5.17021     |     -0.39775 |     ms |   -7.14% |
|                                  50th percentile service time |                                    term_query_empty_argument_term |     4.64536     |     4.32766     |     -0.3177  |     ms |   -6.84% |
|                                  90th percentile service time |                                    term_query_empty_argument_term |     5.26491     |     4.71742     |     -0.54749 |     ms |  -10.40% |
|                                 100th percentile service time |                                    term_query_empty_argument_term |     5.56797     |     5.17021     |     -0.39775 |     ms |   -7.14% |
|                                                    error rate |                                    term_query_empty_argument_term |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |              phrase_query_with_matches_template_many_term_matches |     5.4073      |     5.88589     |      0.4786  |  ops/s |   +8.85% |
|                                               Mean Throughput |              phrase_query_with_matches_template_many_term_matches |     6.46004     |     6.66852     |      0.20848 |  ops/s |   +3.23% |
|                                             Median Throughput |              phrase_query_with_matches_template_many_term_matches |     6.73244     |     6.84489     |      0.11245 |  ops/s |   +1.67% |
|                                                Max Throughput |              phrase_query_with_matches_template_many_term_matches |     7.24039     |     7.27478     |      0.03439 |  ops/s |   +0.47% |
|                                       50th percentile latency |              phrase_query_with_matches_template_many_term_matches |   117.303       |   120.845       |      3.54237 |     ms |   +3.02% |
|                                       90th percentile latency |              phrase_query_with_matches_template_many_term_matches |   123.242       |   130           |      6.75796 |     ms |   +5.48% |
|                                      100th percentile latency |              phrase_query_with_matches_template_many_term_matches |   131.153       |   140.647       |      9.49455 |     ms |   +7.24% |
|                                  50th percentile service time |              phrase_query_with_matches_template_many_term_matches |   117.303       |   120.845       |      3.54237 |     ms |   +3.02% |
|                                  90th percentile service time |              phrase_query_with_matches_template_many_term_matches |   123.242       |   130           |      6.75796 |     ms |   +5.48% |
|                                 100th percentile service time |              phrase_query_with_matches_template_many_term_matches |   131.153       |   140.647       |      9.49455 |     ms |   +7.24% |
|                                                    error rate |              phrase_query_with_matches_template_many_term_matches |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                   phrase_query_with_matches_argument_and_template |     4.6679      |     4.7983      |      0.1304  |  ops/s |   +2.79% |
|                                               Mean Throughput |                   phrase_query_with_matches_argument_and_template |     4.77065     |     4.87287     |      0.10222 |  ops/s |   +2.14% |
|                                             Median Throughput |                   phrase_query_with_matches_argument_and_template |     4.78592     |     4.88511     |      0.09919 |  ops/s |   +2.07% |
|                                                Max Throughput |                   phrase_query_with_matches_argument_and_template |     4.84285     |     4.92296     |      0.08011 |  ops/s |   +1.65% |
|                                       50th percentile latency |                   phrase_query_with_matches_argument_and_template |   199.995       |   197.872       |     -2.12267 |     ms |   -1.06% |
|                                       90th percentile latency |                   phrase_query_with_matches_argument_and_template |   200.81        |   199.312       |     -1.49779 |     ms |   -0.75% |
|                                      100th percentile latency |                   phrase_query_with_matches_argument_and_template |   211.516       |   201.083       |    -10.4329  |     ms |   -4.93% |
|                                  50th percentile service time |                   phrase_query_with_matches_argument_and_template |   199.995       |   197.872       |     -2.12267 |     ms |   -1.06% |
|                                  90th percentile service time |                   phrase_query_with_matches_argument_and_template |   200.81        |   199.312       |     -1.49779 |     ms |   -0.75% |
|                                 100th percentile service time |                   phrase_query_with_matches_argument_and_template |   211.516       |   201.083       |    -10.4329  |     ms |   -4.93% |
|                                                    error rate |                   phrase_query_with_matches_argument_and_template |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                              phrase_query_empty_with_term_matches |    12.0778      |    12.6171      |      0.53937 |  ops/s |   +4.47% |
|                                               Mean Throughput |                              phrase_query_empty_with_term_matches |    12.2363      |    12.6171      |      0.38084 |  ops/s |   +3.11% |
|                                             Median Throughput |                              phrase_query_empty_with_term_matches |    12.2363      |    12.6171      |      0.38084 |  ops/s |   +3.11% |
|                                                Max Throughput |                              phrase_query_empty_with_term_matches |    12.3948      |    12.6171      |      0.2223  |  ops/s |   +1.79% |
|                                       50th percentile latency |                              phrase_query_empty_with_term_matches |    75.8763      |    75.0075      |     -0.86882 |     ms |   -1.15% |
|                                       90th percentile latency |                              phrase_query_empty_with_term_matches |    77.0569      |    76.3659      |     -0.69092 |     ms |   -0.90% |
|                                      100th percentile latency |                              phrase_query_empty_with_term_matches |    86.8786      |    81.8351      |     -5.04356 |     ms |   -5.81% |
|                                  50th percentile service time |                              phrase_query_empty_with_term_matches |    75.8763      |    75.0075      |     -0.86882 |     ms |   -1.15% |
|                                  90th percentile service time |                              phrase_query_empty_with_term_matches |    77.0569      |    76.3659      |     -0.69092 |     ms |   -0.90% |
|                                 100th percentile service time |                              phrase_query_empty_with_term_matches |    86.8786      |    81.8351      |     -5.04356 |     ms |   -5.81% |
|                                                    error rate |                              phrase_query_empty_with_term_matches |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                        search_basic_count_group_0 |     3.62523     |     2.69752     |     -0.92771 |  ops/s |  -25.59% |
|                                               Mean Throughput |                                        search_basic_count_group_0 |     3.83276     |     2.71026     |     -1.1225  |  ops/s |  -29.29% |
|                                             Median Throughput |                                        search_basic_count_group_0 |     3.88208     |     2.71342     |     -1.16866 |  ops/s |  -30.10% |
|                                                Max Throughput |                                        search_basic_count_group_0 |     3.90853     |     2.71783     |     -1.1907  |  ops/s |  -30.46% |
|                                       50th percentile latency |                                        search_basic_count_group_0 |   250.134       |   367.096       |    116.962   |     ms |  +46.76% |
|                                       90th percentile latency |                                        search_basic_count_group_0 |   264.897       |   379.399       |    114.502   |     ms |  +43.23% |
|                                      100th percentile latency |                                        search_basic_count_group_0 |   277.739       |   407.494       |    129.755   |     ms |  +46.72% |
|                                  50th percentile service time |                                        search_basic_count_group_0 |   250.134       |   367.096       |    116.962   |     ms |  +46.76% |
|                                  90th percentile service time |                                        search_basic_count_group_0 |   264.897       |   379.399       |    114.502   |     ms |  +43.23% |
|                                 100th percentile service time |                                        search_basic_count_group_0 |   277.739       |   407.494       |    129.755   |     ms |  +46.72% |
|                                                    error rate |                                        search_basic_count_group_0 |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                        search_basic_count_group_1 |   346.577       |   453.188       |    106.611   |  ops/s |  +30.76% |
|                                               Mean Throughput |                                        search_basic_count_group_1 |   346.577       |   453.188       |    106.611   |  ops/s |  +30.76% |
|                                             Median Throughput |                                        search_basic_count_group_1 |   346.577       |   453.188       |    106.611   |  ops/s |  +30.76% |
|                                                Max Throughput |                                        search_basic_count_group_1 |   346.577       |   453.188       |    106.611   |  ops/s |  +30.76% |
|                                       50th percentile latency |                                        search_basic_count_group_1 |     2.20762     |     1.66244     |     -0.54518 |     ms |  -24.70% |
|                                       90th percentile latency |                                        search_basic_count_group_1 |     2.53833     |     1.76456     |     -0.77377 |     ms |  -30.48% |
|                                      100th percentile latency |                                        search_basic_count_group_1 |     2.80718     |     1.99522     |     -0.81196 |     ms |  -28.92% |
|                                  50th percentile service time |                                        search_basic_count_group_1 |     2.20762     |     1.66244     |     -0.54518 |     ms |  -24.70% |
|                                  90th percentile service time |                                        search_basic_count_group_1 |     2.53833     |     1.76456     |     -0.77377 |     ms |  -30.48% |
|                                 100th percentile service time |                                        search_basic_count_group_1 |     2.80718     |     1.99522     |     -0.81196 |     ms |  -28.92% |
|                                                    error rate |                                        search_basic_count_group_1 |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                        search_basic_count_group_2 |     0.137002    |     0.163062    |      0.02606 |  ops/s |  +19.02% |
|                                               Mean Throughput |                                        search_basic_count_group_2 |     0.138065    |     0.163687    |      0.02562 |  ops/s |  +18.56% |
|                                             Median Throughput |                                        search_basic_count_group_2 |     0.137807    |     0.163725    |      0.02592 |  ops/s |  +18.81% |
|                                                Max Throughput |                                        search_basic_count_group_2 |     0.139461    |     0.164382    |      0.02492 |  ops/s |  +17.87% |
|                                       50th percentile latency |                                        search_basic_count_group_2 |  7152.32        |  6132.18        |  -1020.14    |     ms |  -14.26% |
|                                      100th percentile latency |                                        search_basic_count_group_2 |  7216.07        |  6260.74        |   -955.329   |     ms |  -13.24% |
|                                  50th percentile service time |                                        search_basic_count_group_2 |  7152.32        |  6132.18        |  -1020.14    |     ms |  -14.26% |
|                                 100th percentile service time |                                        search_basic_count_group_2 |  7216.07        |  6260.74        |   -955.329   |     ms |  -13.24% |
|                                                    error rate |                                        search_basic_count_group_2 |     0           |     0           |      0       |      % |    0.00% |
|                                                Min Throughput |                                        search_basic_count_group_3 |     0.1007      |     0.111436    |      0.01074 |  ops/s |  +10.66% |
|                                               Mean Throughput |                                        search_basic_count_group_3 |     0.102188    |     0.112717    |      0.01053 |  ops/s |  +10.30% |
|                                             Median Throughput |                                        search_basic_count_group_3 |     0.102524    |     0.11318     |      0.01066 |  ops/s |  +10.39% |
|                                                Max Throughput |                                        search_basic_count_group_3 |     0.103342    |     0.113535    |      0.01019 |  ops/s |   +9.86% |
|                                       50th percentile latency |                                        search_basic_count_group_3 |  9444.6         |  8724.46        |   -720.143   |     ms |   -7.62% |
|                                      100th percentile latency |                                        search_basic_count_group_3 |  9478.12        |  8753.33        |   -724.784   |     ms |   -7.65% |
|                                  50th percentile service time |                                        search_basic_count_group_3 |  9444.6         |  8724.46        |   -720.143   |     ms |   -7.62% |
|                                 100th percentile service time |                                        search_basic_count_group_3 |  9478.12        |  8753.33        |   -724.784   |     ms |   -7.65% |
|                                                    error rate |                                        search_basic_count_group_3 |     0           |     0           |      0       |      % |    0.00% |
|                                       50th percentile latency |                                        search_basic_count_group_4 | 10999.6         | 10601.6         |   -397.955   |     ms |   -3.62% |
|                                      100th percentile latency |                                        search_basic_count_group_4 | 11000.7         | 10997.5         |     -3.18945 |     ms |   -0.03% |
|                                  50th percentile service time |                                        search_basic_count_group_4 | 10999.6         | 10601.6         |   -397.955   |     ms |   -3.62% |
|                                 100th percentile service time |                                        search_basic_count_group_4 | 11000.7         | 10997.5         |     -3.18945 |     ms |   -0.03% |
|                                                    error rate |                                        search_basic_count_group_4 |   100           |    66.6667      |    -33.3333  |      % |  -33.33% |

