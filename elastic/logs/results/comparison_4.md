Baseline:
  - Race ID: `9f486856-bd6e-40a5-8ae2-a4f99477e389`
  - Race timestamp: 2025-10-29 13:39:45
  - Challenge: logging-querying 
  - Car: external 
  - User tags: `created-by=esbench, division=engineering, env-id=2241ac07-93d6-44fc-a1f2-fea5c2074e86, git-username=eyalkoren, 
    host-username=eyalkoren, name=timestamp-date, org=obs, project=logs-plus, setup=esbench, team=obs-experience`

Contender:
  - Race ID: `876c3f81-bc0f-442a-9a56-f5b3f4aa0505`
  - Race timestamp: 2025-10-29 12:10:00 
  - Challenge: logging-querying 
  - Car: external 
  - User tags: `created-by=esbench, division=engineering, env-id=2241ac07-93d6-44fc-a1f2-fea5c2074e86, git-username=eyalkoren,
    host-username=eyalkoren, name=timestamp-date_nanos, org=obs, project=logs-plus, setup=esbench, team=obs-experience`

|                                                        Metric |                                                              Task |        Baseline |       Contender |        Diff |   Unit |   Diff % |
|--------------------------------------------------------------:|------------------------------------------------------------------:|----------------:|----------------:|------------:|-------:|---------:|
|                    Cumulative indexing time of primary shards |                                                                   |    96.4249      |    95.2672      |    -1.1577  |    min |   -1.20% |
|             Min cumulative indexing time across primary shard |                                                                   |     0           |     0           |     0       |    min |    0.00% |
|          Median cumulative indexing time across primary shard |                                                                   |     2.61382     |     2.57352     |    -0.04031 |    min |   -1.54% |
|             Max cumulative indexing time across primary shard |                                                                   |    43.5752      |    42.6623      |    -0.913   |    min |   -2.10% |
|           Cumulative indexing throttle time of primary shards |                                                                   |     0           |     0           |     0       |    min |    0.00% |
|    Min cumulative indexing throttle time across primary shard |                                                                   |     0           |     0           |     0       |    min |    0.00% |
| Median cumulative indexing throttle time across primary shard |                                                                   |     0           |     0           |     0       |    min |    0.00% |
|    Max cumulative indexing throttle time across primary shard |                                                                   |     0           |     0           |     0       |    min |    0.00% |
|                       Cumulative merge time of primary shards |                                                                   |    21.5731      |    22.4846      |     0.9115  |    min |   +4.23% |
|                      Cumulative merge count of primary shards |                                                                   |    52           |    54           |     2       |        |   +3.85% |
|                Min cumulative merge time across primary shard |                                                                   |     0           |     0           |     0       |    min |    0.00% |
|             Median cumulative merge time across primary shard |                                                                   |     0.416067    |     0.438383    |     0.02232 |    min |   +5.36% |
|                Max cumulative merge time across primary shard |                                                                   |    11.4742      |    11.1862      |    -0.28797 |    min |   -2.51% |
|              Cumulative merge throttle time of primary shards |                                                                   |     3.03107     |     3.66303     |     0.63197 |    min |  +20.85% |
|       Min cumulative merge throttle time across primary shard |                                                                   |     0           |     0           |     0       |    min |    0.00% |
|    Median cumulative merge throttle time across primary shard |                                                                   |     0.0465417   |     0.054275    |     0.00773 |    min |  +16.62% |
|       Max cumulative merge throttle time across primary shard |                                                                   |     1.32507     |     1.43137     |     0.1063  |    min |   +8.02% |
|                     Cumulative refresh time of primary shards |                                                                   |     0.960417    |     0.87825     |    -0.08217 |    min |   -8.56% |
|                    Cumulative refresh count of primary shards |                                                                   |   252           |   257           |     5       |        |   +1.98% |
|              Min cumulative refresh time across primary shard |                                                                   |     0           |     0           |     0       |    min |    0.00% |
|           Median cumulative refresh time across primary shard |                                                                   |     0.037325    |     0.0415917   |     0.00427 |    min |  +11.43% |
|              Max cumulative refresh time across primary shard |                                                                   |     0.251233    |     0.268983    |     0.01775 |    min |   +7.07% |
|                       Cumulative flush time of primary shards |                                                                   |     5.09515     |     5.62357     |     0.52842 |    min |  +10.37% |
|                      Cumulative flush count of primary shards |                                                                   |   152           |   152           |     0       |        |    0.00% |
|                Min cumulative flush time across primary shard |                                                                   |     3.33333e-05 |     3.33333e-05 |     0       |    min |    0.00% |
|             Median cumulative flush time across primary shard |                                                                   |     0.14775     |     0.16505     |     0.0173  |    min |  +11.71% |
|                Max cumulative flush time across primary shard |                                                                   |     2.2023      |     2.50935     |     0.30705 |    min |  +13.94% |
|                                       Total Young Gen GC time |                                                                   |    11.127       |    11.295       |     0.168   |      s |   +1.51% |
|                                      Total Young Gen GC count |                                                                   |   700           |   707           |     7       |        |   +1.00% |
|                                         Total Old Gen GC time |                                                                   |     0           |     0           |     0       |      s |    0.00% |
|                                        Total Old Gen GC count |                                                                   |     0           |     0           |     0       |        |    0.00% |
|                                                  Dataset size |                                                                   |     2.64065     |     2.65086     |     0.01021 |     GB |   +0.39% |
|                                                    Store size |                                                                   |     2.64065     |     2.65086     |     0.01021 |     GB |   +0.39% |
|                                                 Translog size |                                                                   |     7.17118e-07 |     7.17118e-07 |     0       |     GB |    0.00% |
|                                        Heap used for segments |                                                                   |     0           |     0           |     0       |     MB |    0.00% |
|                                      Heap used for doc values |                                                                   |     0           |     0           |     0       |     MB |    0.00% |
|                                           Heap used for terms |                                                                   |     0           |     0           |     0       |     MB |    0.00% |
|                                           Heap used for norms |                                                                   |     0           |     0           |     0       |     MB |    0.00% |
|                                          Heap used for points |                                                                   |     0           |     0           |     0       |     MB |    0.00% |
|                                   Heap used for stored fields |                                                                   |     0           |     0           |     0       |     MB |    0.00% |
|                                                 Segment count |                                                                   |    13           |    13           |     0       |        |    0.00% |
|                                   Total Ingest Pipeline count |                                                                   |     4.7056e+07  |     4.7056e+07  |     0       |        |    0.00% |
|                                    Total Ingest Pipeline time |                                                                   |     2.79367e+06 |     2.85853e+06 | 64857       |     ms |   +2.32% |
|                                  Total Ingest Pipeline failed |                                                                   |     0           |     0           |     0       |        |    0.00% |
|                                                Min Throughput |                                                  insert-pipelines |    15.9738      |    15.7164      |    -0.25742 |  ops/s |   -1.61% |
|                                               Mean Throughput |                                                  insert-pipelines |    15.9738      |    15.7164      |    -0.25742 |  ops/s |   -1.61% |
|                                             Median Throughput |                                                  insert-pipelines |    15.9738      |    15.7164      |    -0.25742 |  ops/s |   -1.61% |
|                                                Max Throughput |                                                  insert-pipelines |    15.9738      |    15.7164      |    -0.25742 |  ops/s |   -1.61% |
|                                      100th percentile latency |                                                  insert-pipelines |   909.549       |   924.602       |    15.0529  |     ms |   +1.65% |
|                                 100th percentile service time |                                                  insert-pipelines |   909.549       |   924.602       |    15.0529  |     ms |   +1.65% |
|                                                    error rate |                                                  insert-pipelines |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                                        insert-ilm |    26.251       |    24.108       |    -2.14302 |  ops/s |   -8.16% |
|                                               Mean Throughput |                                                        insert-ilm |    26.251       |    24.108       |    -2.14302 |  ops/s |   -8.16% |
|                                             Median Throughput |                                                        insert-ilm |    26.251       |    24.108       |    -2.14302 |  ops/s |   -8.16% |
|                                                Max Throughput |                                                        insert-ilm |    26.251       |    24.108       |    -2.14302 |  ops/s |   -8.16% |
|                                      100th percentile latency |                                                        insert-ilm |    37.5054      |    40.8983      |     3.39296 |     ms |   +9.05% |
|                                 100th percentile service time |                                                        insert-ilm |    37.5054      |    40.8983      |     3.39296 |     ms |   +9.05% |
|                                                    error rate |                                                        insert-ilm |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                            validate-package-template-installation |    43.4099      |    50.6137      |     7.20381 |  ops/s |  +16.59% |
|                                               Mean Throughput |                            validate-package-template-installation |    43.4099      |    50.6137      |     7.20381 |  ops/s |  +16.59% |
|                                             Median Throughput |                            validate-package-template-installation |    43.4099      |    50.6137      |     7.20381 |  ops/s |  +16.59% |
|                                                Max Throughput |                            validate-package-template-installation |    43.4099      |    50.6137      |     7.20381 |  ops/s |  +16.59% |
|                                      100th percentile latency |                            validate-package-template-installation |    22.6165      |    19.4408      |    -3.17572 |     ms |  -14.04% |
|                                 100th percentile service time |                            validate-package-template-installation |    22.6165      |    19.4408      |    -3.17572 |     ms |  -14.04% |
|                                                    error rate |                            validate-package-template-installation |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                   update-custom-package-templates |    33.9585      |    36.2327      |     2.27419 |  ops/s |   +6.70% |
|                                               Mean Throughput |                                   update-custom-package-templates |    33.9585      |    36.2327      |     2.27419 |  ops/s |   +6.70% |
|                                             Median Throughput |                                   update-custom-package-templates |    33.9585      |    36.2327      |     2.27419 |  ops/s |   +6.70% |
|                                                Max Throughput |                                   update-custom-package-templates |    33.9585      |    36.2327      |     2.27419 |  ops/s |   +6.70% |
|                                      100th percentile latency |                                   update-custom-package-templates |   352.977       |   330.856       |   -22.1207  |     ms |   -6.27% |
|                                 100th percentile service time |                                   update-custom-package-templates |   352.977       |   330.856       |   -22.1207  |     ms |   -6.27% |
|                                                    error rate |                                   update-custom-package-templates |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                                        bulk-index |   831.433       |   889.151       |    57.718   | docs/s |   +6.94% |
|                                               Mean Throughput |                                                        bulk-index | 35191.9         | 35128.9         |   -62.9279  | docs/s |   -0.18% |
|                                             Median Throughput |                                                        bulk-index | 36164.7         | 36159           |    -5.69141 | docs/s |   -0.02% |
|                                                Max Throughput |                                                        bulk-index | 36974.4         | 36618.8         |  -355.516   | docs/s |   -0.96% |
|                                       50th percentile latency |                                                        bulk-index |   151.85        |   148.483       |    -3.36693 |     ms |   -2.22% |
|                                       90th percentile latency |                                                        bulk-index |   360.124       |   358.891       |    -1.23276 |     ms |   -0.34% |
|                                       99th percentile latency |                                                        bulk-index |   746.22        |   763.783       |    17.5632  |     ms |   +2.35% |
|                                     99.9th percentile latency |                                                        bulk-index |  3329.2         |  3797.39        |   468.19    |     ms |  +14.06% |
|                                    99.99th percentile latency |                                                        bulk-index |  7125.05        |  6327.6         |  -797.458   |     ms |  -11.19% |
|                                      100th percentile latency |                                                        bulk-index | 10116.7         | 10428.8         |   312.057   |     ms |   +3.08% |
|                                  50th percentile service time |                                                        bulk-index |   153.774       |   149.141       |    -4.63228 |     ms |   -3.01% |
|                                  90th percentile service time |                                                        bulk-index |   361.25        |   359.55        |    -1.70055 |     ms |   -0.47% |
|                                  99th percentile service time |                                                        bulk-index |   748.85        |   779.083       |    30.2326  |     ms |   +4.04% |
|                                99.9th percentile service time |                                                        bulk-index |  3340.32        |  3747.55        |   407.238   |     ms |  +12.19% |
|                               99.99th percentile service time |                                                        bulk-index |  7125.05        |  6327.6         |  -797.458   |     ms |  -11.19% |
|                                 100th percentile service time |                                                        bulk-index | 10116.7         | 10428.8         |   312.057   |     ms |   +3.08% |
|                                                    error rate |                                                        bulk-index |     0.00212513  |     0.00425026  |     0.00213 |      % | +100.00% |
|                                       50th percentile latency |                                                 compression-stats | 10998.3         | 10999.2         |     0.9082  |     ms |    0.01% |
|                                       90th percentile latency |                                                 compression-stats | 11000.4         | 11000.8         |     0.38945 |     ms |    0.00% |
|                                      100th percentile latency |                                                 compression-stats | 11001.1         | 11001.5         |     0.44238 |     ms |    0.00% |
|                                  50th percentile service time |                                                 compression-stats | 10998.3         | 10999.2         |     0.9082  |     ms |    0.01% |
|                                  90th percentile service time |                                                 compression-stats | 11000.4         | 11000.8         |     0.38945 |     ms |    0.00% |
|                                 100th percentile service time |                                                 compression-stats | 11001.1         | 11001.5         |     0.44238 |     ms |    0.00% |
|                                                    error rate |                                                 compression-stats |   100           |   100           |     0       |      % |    0.00% |
|                                                Min Throughput |                                 discovery-search-request-size-100 |    13.8585      |    12.7616      |    -1.09685 |  ops/s |   -7.91% |
|                                               Mean Throughput |                                 discovery-search-request-size-100 |    17.6243      |    17.2748      |    -0.34945 |  ops/s |   -1.98% |
|                                             Median Throughput |                                 discovery-search-request-size-100 |    17.6243      |    17.2748      |    -0.34945 |  ops/s |   -1.98% |
|                                                Max Throughput |                                 discovery-search-request-size-100 |    21.3901      |    21.7881      |     0.39796 |  ops/s |   +1.86% |
|                                       50th percentile latency |                                 discovery-search-request-size-100 |    32.1414      |    34.429       |     2.28764 |     ms |   +7.12% |
|                                       90th percentile latency |                                 discovery-search-request-size-100 |    52.3955      |    51.1634      |    -1.2321  |     ms |   -2.35% |
|                                      100th percentile latency |                                 discovery-search-request-size-100 |   244.203       |   254.479       |    10.2763  |     ms |   +4.21% |
|                                  50th percentile service time |                                 discovery-search-request-size-100 |    32.1414      |    34.429       |     2.28764 |     ms |   +7.12% |
|                                  90th percentile service time |                                 discovery-search-request-size-100 |    52.3955      |    51.1634      |    -1.2321  |     ms |   -2.35% |
|                                 100th percentile service time |                                 discovery-search-request-size-100 |   244.203       |   254.479       |    10.2763  |     ms |   +4.21% |
|                                                    error rate |                                 discovery-search-request-size-100 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                 discovery-search-request-size-500 |    13.9322      |    12.6327      |    -1.29942 |  ops/s |   -9.33% |
|                                               Mean Throughput |                                 discovery-search-request-size-500 |    14.1231      |    13.0697      |    -1.05347 |  ops/s |   -7.46% |
|                                             Median Throughput |                                 discovery-search-request-size-500 |    14.1337      |    13.0953      |    -1.03844 |  ops/s |   -7.35% |
|                                                Max Throughput |                                 discovery-search-request-size-500 |    14.3035      |    13.481       |    -0.82254 |  ops/s |   -5.75% |
|                                       50th percentile latency |                                 discovery-search-request-size-500 |    72.0447      |    74.9224      |     2.87772 |     ms |   +3.99% |
|                                       90th percentile latency |                                 discovery-search-request-size-500 |    79.0119      |    86.8838      |     7.87192 |     ms |   +9.96% |
|                                      100th percentile latency |                                 discovery-search-request-size-500 |    90.0938      |   103.626       |    13.5325  |     ms |  +15.02% |
|                                  50th percentile service time |                                 discovery-search-request-size-500 |    72.0447      |    74.9224      |     2.87772 |     ms |   +3.99% |
|                                  90th percentile service time |                                 discovery-search-request-size-500 |    79.0119      |    86.8838      |     7.87192 |     ms |   +9.96% |
|                                 100th percentile service time |                                 discovery-search-request-size-500 |    90.0938      |   103.626       |    13.5325  |     ms |  +15.02% |
|                                                    error rate |                                 discovery-search-request-size-500 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                discovery-search-request-size-1000 |     8.61423     |     8.09851     |    -0.51572 |  ops/s |   -5.99% |
|                                               Mean Throughput |                                discovery-search-request-size-1000 |     8.76177     |     8.26092     |    -0.50085 |  ops/s |   -5.72% |
|                                             Median Throughput |                                discovery-search-request-size-1000 |     8.73806     |     8.29349     |    -0.44456 |  ops/s |   -5.09% |
|                                                Max Throughput |                                discovery-search-request-size-1000 |     8.94904     |     8.37667     |    -0.57236 |  ops/s |   -6.40% |
|                                       50th percentile latency |                                discovery-search-request-size-1000 |   105.991       |   119.787       |    13.796   |     ms |  +13.02% |
|                                       90th percentile latency |                                discovery-search-request-size-1000 |   125.113       |   129.013       |     3.89986 |     ms |   +3.12% |
|                                      100th percentile latency |                                discovery-search-request-size-1000 |   129.791       |   138.299       |     8.50832 |     ms |   +6.56% |
|                                  50th percentile service time |                                discovery-search-request-size-1000 |   105.991       |   119.787       |    13.796   |     ms |  +13.02% |
|                                  90th percentile service time |                                discovery-search-request-size-1000 |   125.113       |   129.013       |     3.89986 |     ms |   +3.12% |
|                                 100th percentile service time |                                discovery-search-request-size-1000 |   129.791       |   138.299       |     8.50832 |     ms |   +6.56% |
|                                                    error rate |                                discovery-search-request-size-1000 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                                   discover/search |     0.00343566  |     0.00343565  |    -0       |  ops/s |   -0.00% |
|                                               Mean Throughput |                                                   discover/search |     0.00354769  |     0.00354769  |    -0       |  ops/s |   -0.00% |
|                                             Median Throughput |                                                   discover/search |     0.00354769  |     0.00354769  |    -0       |  ops/s |   -0.00% |
|                                                Max Throughput |                                                   discover/search |     0.00365972  |     0.00365972  |     0       |  ops/s |    0.00% |
|                                       50th percentile latency |                                                   discover/search |   324.934       |   324.551       |    -0.3838  |     ms |   -0.12% |
|                                      100th percentile latency |                                                   discover/search |   606.564       |   607.046       |     0.48138 |     ms |   +0.08% |
|                                  50th percentile service time |                                                   discover/search |   323.045       |   322.975       |    -0.0697  |     ms |   -0.02% |
|                                 100th percentile service time |                                                   discover/search |   323.38        |   323.668       |     0.28827 |     ms |   +0.09% |
|                                                    error rate |                                                   discover/search |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                                discover/visualize |     0.00231602  |     0.00231602  |     0       |  ops/s |    0.00% |
|                                               Mean Throughput |                                                discover/visualize |     0.00486777  |     0.00486777  |     0       |  ops/s |    0.00% |
|                                             Median Throughput |                                                discover/visualize |     0.00518902  |     0.00518902  |     0       |  ops/s |    0.00% |
|                                                Max Throughput |                                                discover/visualize |     0.00686521  |     0.00686522  |     0       |  ops/s |    0.00% |
|                                       50th percentile latency |                                                discover/visualize |   320.881       |   319.88        |    -1.00157 |     ms |   -0.31% |
|                                      100th percentile latency |                                                discover/visualize |   324.78        |   323.557       |    -1.22269 |     ms |   -0.38% |
|                                  50th percentile service time |                                                discover/visualize |   318.746       |   318.045       |    -0.70091 |     ms |   -0.22% |
|                                 100th percentile service time |                                                discover/visualize |   323.088       |   322.48        |    -0.60809 |     ms |   -0.19% |
|                                                    error rate |                                                discover/visualize |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                                             kafka |     0.00502538  |     0.00502542  |     0       |  ops/s |    0.00% |
|                                               Mean Throughput |                                                             kafka |     0.0110764   |     0.0110764   |     0       |  ops/s |    0.00% |
|                                             Median Throughput |                                                             kafka |     0.00971787  |     0.00971792  |     0       |  ops/s |    0.00% |
|                                                Max Throughput |                                                             kafka |     0.0187322   |     0.0187323   |     0       |  ops/s |    0.00% |
|                                       50th percentile latency |                                                             kafka |   318.845       |   318.434       |    -0.41084 |     ms |   -0.13% |
|                                      100th percentile latency |                                                             kafka |   328.276       |   327.753       |    -0.52231 |     ms |   -0.16% |
|                                  50th percentile service time |                                                             kafka |   316.88        |   316.739       |    -0.14082 |     ms |   -0.04% |
|                                 100th percentile service time |                                                             kafka |   327.346       |   325.356       |    -1.98975 |     ms |   -0.61% |
|                                                    error rate |                                                             kafka |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                                             nginx |     0.00645914  |     0.00645919  |     0       |  ops/s |    0.00% |
|                                               Mean Throughput |                                                             nginx |     0.0233976   |     0.0233977   |     0       |  ops/s |    0.00% |
|                                             Median Throughput |                                                             nginx |     0.0241385   |     0.0241386   |     0       |  ops/s |    0.00% |
|                                                Max Throughput |                                                             nginx |     0.0347963   |     0.0347963   |     0       |  ops/s |    0.00% |
|                                       50th percentile latency |                                                             nginx |  1725.99        |  1726.75        |     0.7627  |     ms |   +0.04% |
|                                       90th percentile latency |                                                             nginx |  2644.37        |  2644.94        |     0.57007 |     ms |   +0.02% |
|                                      100th percentile latency |                                                             nginx |  3687.37        |  3685.39        |    -1.97192 |     ms |   -0.05% |
|                                  50th percentile service time |                                                             nginx |  1683.8         |  1683.99        |     0.19617 |     ms |   +0.01% |
|                                  90th percentile service time |                                                             nginx |  1727.58        |  1726.97        |    -0.6052  |     ms |   -0.04% |
|                                 100th percentile service time |                                                             nginx |  1752.47        |  1752.18        |    -0.2915  |     ms |   -0.02% |
|                                                    error rate |                                                             nginx |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                                            apache |     0.0450346   |     0.0450347   |     0       |  ops/s |    0.00% |
|                                               Mean Throughput |                                                            apache |     0.0940603   |     0.0940611   |     0       |  ops/s |    0.00% |
|                                             Median Throughput |                                                            apache |     0.0977364   |     0.0977371   |     0       |  ops/s |    0.00% |
|                                                Max Throughput |                                                            apache |     0.158566    |     0.158568    |     0       |  ops/s |    0.00% |
|                                       50th percentile latency |                                                            apache |   317.747       |   317.359       |    -0.38751 |     ms |   -0.12% |
|                                       90th percentile latency |                                                            apache |   330.485       |   331.477       |     0.99284 |     ms |   +0.30% |
|                                      100th percentile latency |                                                            apache |   373.903       |   374.561       |     0.65762 |     ms |   +0.18% |
|                                  50th percentile service time |                                                            apache |   315.818       |   315.031       |    -0.78735 |     ms |   -0.25% |
|                                  90th percentile service time |                                                            apache |   328.108       |   328.318       |     0.21014 |     ms |   +0.06% |
|                                 100th percentile service time |                                                            apache |   332.342       |   356.564       |    24.2218  |     ms |   +7.29% |
|                                                    error rate |                                                            apache |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                                       system/auth |     0.0655626   |     0.0655625   |    -0       |  ops/s |   -0.00% |
|                                               Mean Throughput |                                                       system/auth |     0.12034     |     0.12034     |    -0       |  ops/s |   -0.00% |
|                                             Median Throughput |                                                       system/auth |     0.118772    |     0.118772    |    -0       |  ops/s |   -0.00% |
|                                                Max Throughput |                                                       system/auth |     0.153319    |     0.153319    |    -0       |  ops/s |   -0.00% |
|                                       50th percentile latency |                                                       system/auth |   324.475       |   324.026       |    -0.44899 |     ms |   -0.14% |
|                                       90th percentile latency |                                                       system/auth |   382.123       |   381.402       |    -0.72031 |     ms |   -0.19% |
|                                      100th percentile latency |                                                       system/auth |   595.688       |   594.004       |    -1.68384 |     ms |   -0.28% |
|                                  50th percentile service time |                                                       system/auth |   321.976       |   321.662       |    -0.31343 |     ms |   -0.10% |
|                                  90th percentile service time |                                                       system/auth |   332.068       |   331.278       |    -0.78958 |     ms |   -0.24% |
|                                 100th percentile service time |                                                       system/auth |   416.279       |   415.819       |    -0.46033 |     ms |   -0.11% |
|                                                    error rate |                                                       system/auth |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                           system/syslog/dashboard |     0.0408357   |     0.0408358   |     0       |  ops/s |    0.00% |
|                                               Mean Throughput |                                           system/syslog/dashboard |     0.0535934   |     0.0535934   |     0       |  ops/s |    0.00% |
|                                             Median Throughput |                                           system/syslog/dashboard |     0.0520764   |     0.0520764   |    -0       |  ops/s |   -0.00% |
|                                                Max Throughput |                                           system/syslog/dashboard |     0.0694827   |     0.0694828   |     0       |  ops/s |    0.00% |
|                                       50th percentile latency |                                           system/syslog/dashboard |   318.109       |   317.791       |    -0.3185  |     ms |   -0.10% |
|                                       90th percentile latency |                                           system/syslog/dashboard |   405.184       |   401.923       |    -3.26123 |     ms |   -0.80% |
|                                      100th percentile latency |                                           system/syslog/dashboard |   594.906       |   593.965       |    -0.94147 |     ms |   -0.16% |
|                                  50th percentile service time |                                           system/syslog/dashboard |   316.321       |   316.192       |    -0.1297  |     ms |   -0.04% |
|                                  90th percentile service time |                                           system/syslog/dashboard |   321.561       |   321.093       |    -0.46835 |     ms |   -0.15% |
|                                 100th percentile service time |                                           system/syslog/dashboard |   348.313       |   322.333       |   -25.9799  |     ms |   -7.46% |
|                                                    error rate |                                           system/syslog/dashboard |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                                system/syslog/lens |     0.0113596   |     0.0113597   |     0       |  ops/s |    0.00% |
|                                               Mean Throughput |                                                system/syslog/lens |     0.01913     |     0.0192306   |     0.0001  |  ops/s |   +0.53% |
|                                             Median Throughput |                                                system/syslog/lens |     0.0163198   |     0.0160602   |    -0.00026 |  ops/s |   -1.59% |
|                                                Max Throughput |                                                system/syslog/lens |     0.0512785   |     0.0512788   |     0       |  ops/s |    0.00% |
|                                       50th percentile latency |                                                system/syslog/lens |   323.717       |   323.749       |     0.03204 |     ms |    0.01% |
|                                       90th percentile latency |                                                system/syslog/lens |   856.808       |   855.837       |    -0.97089 |     ms |   -0.11% |
|                                      100th percentile latency |                                                system/syslog/lens |   877.138       |   875.859       |    -1.27838 |     ms |   -0.15% |
|                                  50th percentile service time |                                                system/syslog/lens |   320.342       |   320.27        |    -0.07159 |     ms |   -0.02% |
|                                  90th percentile service time |                                                system/syslog/lens |   852.124       |   851.742       |    -0.38177 |     ms |   -0.04% |
|                                 100th percentile service time |                                                system/syslog/lens |   854.949       |   854.362       |    -0.58746 |     ms |   -0.07% |
|                                                    error rate |                                                system/syslog/lens |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                                   mysql/dashboard |     0.00336287  |     0.00336287  |     0       |  ops/s |    0.00% |
|                                               Mean Throughput |                                                   mysql/dashboard |     0.00888061  |     0.00888061  |     0       |  ops/s |    0.00% |
|                                             Median Throughput |                                                   mysql/dashboard |     0.00851366  |     0.00851366  |    -0       |  ops/s |   -0.00% |
|                                                Max Throughput |                                                   mysql/dashboard |     0.0150139   |     0.0150139   |    -0       |  ops/s |   -0.00% |
|                                       50th percentile latency |                                                   mysql/dashboard |   312.242       |   311.913       |    -0.32822 |     ms |   -0.11% |
|                                       90th percentile latency |                                                   mysql/dashboard |   330.3         |   329.831       |    -0.46906 |     ms |   -0.14% |
|                                      100th percentile latency |                                                   mysql/dashboard |   548.372       |   548.304       |    -0.06757 |     ms |   -0.01% |
|                                  50th percentile service time |                                                   mysql/dashboard |   309.889       |   309.607       |    -0.28185 |     ms |   -0.09% |
|                                  90th percentile service time |                                                   mysql/dashboard |   318.106       |   319.078       |     0.9723  |     ms |   +0.31% |
|                                 100th percentile service time |                                                   mysql/dashboard |   332.596       |   331.469       |    -1.12759 |     ms |   -0.34% |
|                                                    error rate |                                                   mysql/dashboard |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                                             redis |     0.00958883  |     0.00958889  |     0       |  ops/s |    0.00% |
|                                               Mean Throughput |                                                             redis |     0.0402728   |     0.0402729   |     0       |  ops/s |    0.00% |
|                                             Median Throughput |                                                             redis |     0.0410644   |     0.0410645   |     0       |  ops/s |    0.00% |
|                                                Max Throughput |                                                             redis |     0.0726221   |     0.0726223   |     0       |  ops/s |    0.00% |
|                                       50th percentile latency |                                                             redis |   323.206       |   322.93        |    -0.27551 |     ms |   -0.09% |
|                                       90th percentile latency |                                                             redis |   397.141       |   398.646       |     1.50504 |     ms |   +0.38% |
|                                      100th percentile latency |                                                             redis |   784.863       |   785.242       |     0.37909 |     ms |   +0.05% |
|                                  50th percentile service time |                                                             redis |   322.095       |   321.923       |    -0.17206 |     ms |   -0.05% |
|                                  90th percentile service time |                                                             redis |   332.468       |   332.773       |     0.30527 |     ms |   +0.09% |
|                                 100th percentile service time |                                                             redis |   783.831       |   784.196       |     0.36584 |     ms |   +0.05% |
|                                                    error rate |                                                             redis |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                                        mysql/lens |     0.00680638  |     0.00680638  |     0       |  ops/s |    0.00% |
|                                               Mean Throughput |                                                        mysql/lens |     0.0273108   |     0.0273108   |     0       |  ops/s |    0.00% |
|                                             Median Throughput |                                                        mysql/lens |     0.0281678   |     0.0281678   |     0       |  ops/s |    0.00% |
|                                                Max Throughput |                                                        mysql/lens |     0.0470131   |     0.0470133   |     0       |  ops/s |    0.00% |
|                                       50th percentile latency |                                                        mysql/lens |   318.24        |   317.013       |    -1.22653 |     ms |   -0.39% |
|                                       90th percentile latency |                                                        mysql/lens |   983.03        |   982.722       |    -0.30821 |     ms |   -0.03% |
|                                      100th percentile latency |                                                        mysql/lens |  1000.75        |  1000.24        |    -0.51501 |     ms |   -0.05% |
|                                  50th percentile service time |                                                        mysql/lens |   317.283       |   316.181       |    -1.10213 |     ms |   -0.35% |
|                                  90th percentile service time |                                                        mysql/lens |   536.715       |   536.593       |    -0.12228 |     ms |   -0.02% |
|                                 100th percentile service time |                                                        mysql/lens |   998.833       |   998.689       |    -0.14429 |     ms |   -0.01% |
|                                                    error rate |                                                        mysql/lens |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                               postgresql/overview |     0.00513626  |     0.00513626  |     0       |  ops/s |    0.00% |
|                                               Mean Throughput |                                               postgresql/overview |     0.0581883   |     0.0581881   |    -0       |  ops/s |   -0.00% |
|                                             Median Throughput |                                               postgresql/overview |     0.0620373   |     0.0620372   |    -0       |  ops/s |   -0.00% |
|                                                Max Throughput |                                               postgresql/overview |     0.0894029   |     0.089403    |     0       |  ops/s |    0.00% |
|                                       50th percentile latency |                                               postgresql/overview |  1010.75        |  1011.07        |     0.31607 |     ms |   +0.03% |
|                                       90th percentile latency |                                               postgresql/overview |  1502.06        |  1500.34        |    -1.71851 |     ms |   -0.11% |
|                                      100th percentile latency |                                               postgresql/overview |  2143.01        |  2140.26        |    -2.75562 |     ms |   -0.13% |
|                                  50th percentile service time |                                               postgresql/overview |  1007.16        |  1007.18        |     0.01874 |     ms |    0.00% |
|                                  90th percentile service time |                                               postgresql/overview |  1046.52        |  1047.25        |     0.73531 |     ms |   +0.07% |
|                                 100th percentile service time |                                               postgresql/overview |  1673.02        |  1673.47        |     0.45154 |     ms |   +0.03% |
|                                                    error rate |                                               postgresql/overview |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                               postgresql/duration |     0.0224605   |     0.0224605   |     0       |  ops/s |    0.00% |
|                                               Mean Throughput |                                               postgresql/duration |     0.0643451   |     0.0643452   |     0       |  ops/s |    0.00% |
|                                             Median Throughput |                                               postgresql/duration |     0.0679205   |     0.0679207   |     0       |  ops/s |    0.00% |
|                                                Max Throughput |                                               postgresql/duration |     0.0802622   |     0.0802622   |     0       |  ops/s |    0.00% |
|                                       50th percentile latency |                                               postgresql/duration |   313.585       |   313.38        |    -0.20496 |     ms |   -0.07% |
|                                       90th percentile latency |                                               postgresql/duration |   415.068       |   415.16        |     0.09252 |     ms |   +0.02% |
|                                      100th percentile latency |                                               postgresql/duration |   742.273       |   741.736       |    -0.53699 |     ms |   -0.07% |
|                                  50th percentile service time |                                               postgresql/duration |   312.015       |   311.948       |    -0.06674 |     ms |   -0.02% |
|                                  90th percentile service time |                                               postgresql/duration |   318.132       |   317.945       |    -0.18682 |     ms |   -0.06% |
|                                 100th percentile service time |                                               postgresql/duration |   320.427       |   320.061       |    -0.36636 |     ms |   -0.11% |
|                                                    error rate |                                               postgresql/duration |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                  esql_basic_count_group_0_limit_0 |    63.4296      |    63.7263      |     0.29673 |  ops/s |   +0.47% |
|                                               Mean Throughput |                                  esql_basic_count_group_0_limit_0 |    63.4296      |    63.7263      |     0.29673 |  ops/s |   +0.47% |
|                                             Median Throughput |                                  esql_basic_count_group_0_limit_0 |    63.4296      |    63.7263      |     0.29673 |  ops/s |   +0.47% |
|                                                Max Throughput |                                  esql_basic_count_group_0_limit_0 |    63.4296      |    63.7263      |     0.29673 |  ops/s |   +0.47% |
|                                       50th percentile latency |                                  esql_basic_count_group_0_limit_0 |     4.27489     |     4.56411     |     0.28921 |     ms |   +6.77% |
|                                       90th percentile latency |                                  esql_basic_count_group_0_limit_0 |     5.00097     |     5.31546     |     0.31449 |     ms |   +6.29% |
|                                      100th percentile latency |                                  esql_basic_count_group_0_limit_0 |     6.18407     |     5.97126     |    -0.21281 |     ms |   -3.44% |
|                                  50th percentile service time |                                  esql_basic_count_group_0_limit_0 |     4.27489     |     4.56411     |     0.28921 |     ms |   +6.77% |
|                                  90th percentile service time |                                  esql_basic_count_group_0_limit_0 |     5.00097     |     5.31546     |     0.31449 |     ms |   +6.29% |
|                                 100th percentile service time |                                  esql_basic_count_group_0_limit_0 |     6.18407     |     5.97126     |    -0.21281 |     ms |   -3.44% |
|                                                    error rate |                                  esql_basic_count_group_0_limit_0 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                  esql_basic_count_group_1_limit_0 |   217.637       |   172.719       |   -44.9183  |  ops/s |  -20.64% |
|                                               Mean Throughput |                                  esql_basic_count_group_1_limit_0 |   217.637       |   172.719       |   -44.9183  |  ops/s |  -20.64% |
|                                             Median Throughput |                                  esql_basic_count_group_1_limit_0 |   217.637       |   172.719       |   -44.9183  |  ops/s |  -20.64% |
|                                                Max Throughput |                                  esql_basic_count_group_1_limit_0 |   217.637       |   172.719       |   -44.9183  |  ops/s |  -20.64% |
|                                       50th percentile latency |                                  esql_basic_count_group_1_limit_0 |     3.19018     |     4.62546     |     1.43529 |     ms |  +44.99% |
|                                       90th percentile latency |                                  esql_basic_count_group_1_limit_0 |     4.318       |     5.27956     |     0.96156 |     ms |  +22.27% |
|                                      100th percentile latency |                                  esql_basic_count_group_1_limit_0 |     5.30653     |     6.36287     |     1.05634 |     ms |  +19.91% |
|                                  50th percentile service time |                                  esql_basic_count_group_1_limit_0 |     3.19018     |     4.62546     |     1.43529 |     ms |  +44.99% |
|                                  90th percentile service time |                                  esql_basic_count_group_1_limit_0 |     4.318       |     5.27956     |     0.96156 |     ms |  +22.27% |
|                                 100th percentile service time |                                  esql_basic_count_group_1_limit_0 |     5.30653     |     6.36287     |     1.05634 |     ms |  +19.91% |
|                                                    error rate |                                  esql_basic_count_group_1_limit_0 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                  esql_basic_count_group_2_limit_0 |   236.473       |   257.022       |    20.5494  |  ops/s |   +8.69% |
|                                               Mean Throughput |                                  esql_basic_count_group_2_limit_0 |   236.473       |   257.022       |    20.5494  |  ops/s |   +8.69% |
|                                             Median Throughput |                                  esql_basic_count_group_2_limit_0 |   236.473       |   257.022       |    20.5494  |  ops/s |   +8.69% |
|                                                Max Throughput |                                  esql_basic_count_group_2_limit_0 |   236.473       |   257.022       |    20.5494  |  ops/s |   +8.69% |
|                                       50th percentile latency |                                  esql_basic_count_group_2_limit_0 |     3.30323     |     3.12263     |    -0.18059 |     ms |   -5.47% |
|                                       90th percentile latency |                                  esql_basic_count_group_2_limit_0 |     3.86275     |     3.61243     |    -0.25031 |     ms |   -6.48% |
|                                      100th percentile latency |                                  esql_basic_count_group_2_limit_0 |     4.1875      |     3.81976     |    -0.36774 |     ms |   -8.78% |
|                                  50th percentile service time |                                  esql_basic_count_group_2_limit_0 |     3.30323     |     3.12263     |    -0.18059 |     ms |   -5.47% |
|                                  90th percentile service time |                                  esql_basic_count_group_2_limit_0 |     3.86275     |     3.61243     |    -0.25031 |     ms |   -6.48% |
|                                 100th percentile service time |                                  esql_basic_count_group_2_limit_0 |     4.1875      |     3.81976     |    -0.36774 |     ms |   -8.78% |
|                                                    error rate |                                  esql_basic_count_group_2_limit_0 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                  esql_basic_count_group_3_limit_0 |   266.655       |   292.184       |    25.529   |  ops/s |   +9.57% |
|                                               Mean Throughput |                                  esql_basic_count_group_3_limit_0 |   266.655       |   292.184       |    25.529   |  ops/s |   +9.57% |
|                                             Median Throughput |                                  esql_basic_count_group_3_limit_0 |   266.655       |   292.184       |    25.529   |  ops/s |   +9.57% |
|                                                Max Throughput |                                  esql_basic_count_group_3_limit_0 |   266.655       |   292.184       |    25.529   |  ops/s |   +9.57% |
|                                       50th percentile latency |                                  esql_basic_count_group_3_limit_0 |     3.00677     |     2.82452     |    -0.18225 |     ms |   -6.06% |
|                                       90th percentile latency |                                  esql_basic_count_group_3_limit_0 |     3.49469     |     3.09477     |    -0.39992 |     ms |  -11.44% |
|                                      100th percentile latency |                                  esql_basic_count_group_3_limit_0 |     3.93579     |     3.65171     |    -0.28408 |     ms |   -7.22% |
|                                  50th percentile service time |                                  esql_basic_count_group_3_limit_0 |     3.00677     |     2.82452     |    -0.18225 |     ms |   -6.06% |
|                                  90th percentile service time |                                  esql_basic_count_group_3_limit_0 |     3.49469     |     3.09477     |    -0.39992 |     ms |  -11.44% |
|                                 100th percentile service time |                                  esql_basic_count_group_3_limit_0 |     3.93579     |     3.65171     |    -0.28408 |     ms |   -7.22% |
|                                                    error rate |                                  esql_basic_count_group_3_limit_0 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                  esql_basic_count_group_4_limit_0 |   240.357       |   280.788       |    40.4311  |  ops/s |  +16.82% |
|                                               Mean Throughput |                                  esql_basic_count_group_4_limit_0 |   240.357       |   280.788       |    40.4311  |  ops/s |  +16.82% |
|                                             Median Throughput |                                  esql_basic_count_group_4_limit_0 |   240.357       |   280.788       |    40.4311  |  ops/s |  +16.82% |
|                                                Max Throughput |                                  esql_basic_count_group_4_limit_0 |   240.357       |   280.788       |    40.4311  |  ops/s |  +16.82% |
|                                       50th percentile latency |                                  esql_basic_count_group_4_limit_0 |     2.74543     |     2.66796     |    -0.07748 |     ms |   -2.82% |
|                                       90th percentile latency |                                  esql_basic_count_group_4_limit_0 |     3.25717     |     3.6203      |     0.36312 |     ms |  +11.15% |
|                                      100th percentile latency |                                  esql_basic_count_group_4_limit_0 |     3.98327     |     5.06596     |     1.08268 |     ms |  +27.18% |
|                                  50th percentile service time |                                  esql_basic_count_group_4_limit_0 |     2.74543     |     2.66796     |    -0.07748 |     ms |   -2.82% |
|                                  90th percentile service time |                                  esql_basic_count_group_4_limit_0 |     3.25717     |     3.6203      |     0.36312 |     ms |  +11.15% |
|                                 100th percentile service time |                                  esql_basic_count_group_4_limit_0 |     3.98327     |     5.06596     |     1.08268 |     ms |  +27.18% |
|                                                    error rate |                                  esql_basic_count_group_4_limit_0 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |   111.683       |   113.189       |     1.5052  |  ops/s |   +1.35% |
|                                               Mean Throughput |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |   111.683       |   113.189       |     1.5052  |  ops/s |   +1.35% |
|                                             Median Throughput |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |   111.683       |   113.189       |     1.5052  |  ops/s |   +1.35% |
|                                                Max Throughput |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |   111.683       |   113.189       |     1.5052  |  ops/s |   +1.35% |
|                                       50th percentile latency |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |     6.06106     |     5.27802     |    -0.78304 |     ms |  -12.92% |
|                                       90th percentile latency |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |     7.11306     |     6.94656     |    -0.1665  |     ms |   -2.34% |
|                                      100th percentile latency |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |     7.9558      |     7.60574     |    -0.35005 |     ms |   -4.40% |
|                                  50th percentile service time |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |     6.06106     |     5.27802     |    -0.78304 |     ms |  -12.92% |
|                                  90th percentile service time |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |     7.11306     |     6.94656     |    -0.1665  |     ms |   -2.34% |
|                                 100th percentile service time |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |     7.9558      |     7.60574     |    -0.35005 |     ms |   -4.40% |
|                                                    error rate |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |   202.138       |   178.409       |   -23.7289  |  ops/s |  -11.74% |
|                                               Mean Throughput | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |   202.138       |   178.409       |   -23.7289  |  ops/s |  -11.74% |
|                                             Median Throughput | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |   202.138       |   178.409       |   -23.7289  |  ops/s |  -11.74% |
|                                                Max Throughput | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |   202.138       |   178.409       |   -23.7289  |  ops/s |  -11.74% |
|                                       50th percentile latency | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |     4.11251     |     4.65634     |     0.54383 |     ms |  +13.22% |
|                                       90th percentile latency | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |     4.69181     |     5.20267     |     0.51086 |     ms |  +10.89% |
|                                      100th percentile latency | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |     5.17118     |     6.12466     |     0.95348 |     ms |  +18.44% |
|                                  50th percentile service time | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |     4.11251     |     4.65634     |     0.54383 |     ms |  +13.22% |
|                                  90th percentile service time | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |     4.69181     |     5.20267     |     0.51086 |     ms |  +10.89% |
|                                 100th percentile service time | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |     5.17118     |     6.12466     |     0.95348 |     ms |  +18.44% |
|                                                    error rate | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                           esql_dissect_duration_and_stats_limit_0 |   286.532       |   232.654       |   -53.8785  |  ops/s |  -18.80% |
|                                               Mean Throughput |                           esql_dissect_duration_and_stats_limit_0 |   286.532       |   232.654       |   -53.8785  |  ops/s |  -18.80% |
|                                             Median Throughput |                           esql_dissect_duration_and_stats_limit_0 |   286.532       |   232.654       |   -53.8785  |  ops/s |  -18.80% |
|                                                Max Throughput |                           esql_dissect_duration_and_stats_limit_0 |   286.532       |   232.654       |   -53.8785  |  ops/s |  -18.80% |
|                                       50th percentile latency |                           esql_dissect_duration_and_stats_limit_0 |     2.35508     |     3.21805     |     0.86297 |     ms |  +36.64% |
|                                       90th percentile latency |                           esql_dissect_duration_and_stats_limit_0 |     2.79487     |     3.625       |     0.83014 |     ms |  +29.70% |
|                                      100th percentile latency |                           esql_dissect_duration_and_stats_limit_0 |     3.12785     |     3.92132     |     0.79347 |     ms |  +25.37% |
|                                  50th percentile service time |                           esql_dissect_duration_and_stats_limit_0 |     2.35508     |     3.21805     |     0.86297 |     ms |  +36.64% |
|                                  90th percentile service time |                           esql_dissect_duration_and_stats_limit_0 |     2.79487     |     3.625       |     0.83014 |     ms |  +29.70% |
|                                 100th percentile service time |                           esql_dissect_duration_and_stats_limit_0 |     3.12785     |     3.92132     |     0.79347 |     ms |  +25.37% |
|                                                    error rate |                           esql_dissect_duration_and_stats_limit_0 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                          esql_basic_count_group_0 |   110.104       |   110.286       |     0.18133 |  ops/s |   +0.16% |
|                                               Mean Throughput |                                          esql_basic_count_group_0 |   110.104       |   110.286       |     0.18133 |  ops/s |   +0.16% |
|                                             Median Throughput |                                          esql_basic_count_group_0 |   110.104       |   110.286       |     0.18133 |  ops/s |   +0.16% |
|                                                Max Throughput |                                          esql_basic_count_group_0 |   110.104       |   110.286       |     0.18133 |  ops/s |   +0.16% |
|                                       50th percentile latency |                                          esql_basic_count_group_0 |     5.28082     |     5.63732     |     0.3565  |     ms |   +6.75% |
|                                       90th percentile latency |                                          esql_basic_count_group_0 |     6.27441     |     6.73496     |     0.46055 |     ms |   +7.34% |
|                                      100th percentile latency |                                          esql_basic_count_group_0 |    25.0441      |     7.28785     |   -17.7563  |     ms |  -70.90% |
|                                  50th percentile service time |                                          esql_basic_count_group_0 |     5.28082     |     5.63732     |     0.3565  |     ms |   +6.75% |
|                                  90th percentile service time |                                          esql_basic_count_group_0 |     6.27441     |     6.73496     |     0.46055 |     ms |   +7.34% |
|                                 100th percentile service time |                                          esql_basic_count_group_0 |    25.0441      |     7.28785     |   -17.7563  |     ms |  -70.90% |
|                                                    error rate |                                          esql_basic_count_group_0 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                          esql_basic_count_group_1 |     3.5195      |     3.39353     |    -0.12596 |  ops/s |   -3.58% |
|                                               Mean Throughput |                                          esql_basic_count_group_1 |     3.8613      |     3.5777      |    -0.28361 |  ops/s |   -7.34% |
|                                             Median Throughput |                                          esql_basic_count_group_1 |     3.9149      |     3.60642     |    -0.30847 |  ops/s |   -7.88% |
|                                                Max Throughput |                                          esql_basic_count_group_1 |     4.00332     |     3.65484     |    -0.34848 |  ops/s |   -8.70% |
|                                       50th percentile latency |                                          esql_basic_count_group_1 |   238.446       |   266.225       |    27.7793  |     ms |  +11.65% |
|                                       90th percentile latency |                                          esql_basic_count_group_1 |   251.48        |   278.611       |    27.1314  |     ms |  +10.79% |
|                                      100th percentile latency |                                          esql_basic_count_group_1 |   260.154       |   296.4         |    36.2461  |     ms |  +13.93% |
|                                  50th percentile service time |                                          esql_basic_count_group_1 |   238.446       |   266.225       |    27.7793  |     ms |  +11.65% |
|                                  90th percentile service time |                                          esql_basic_count_group_1 |   251.48        |   278.611       |    27.1314  |     ms |  +10.79% |
|                                 100th percentile service time |                                          esql_basic_count_group_1 |   260.154       |   296.4         |    36.2461  |     ms |  +13.93% |
|                                                    error rate |                                          esql_basic_count_group_1 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                          esql_basic_count_group_2 |     0.97656     |     0.94749     |    -0.02907 |  ops/s |   -2.98% |
|                                               Mean Throughput |                                          esql_basic_count_group_2 |     1.35069     |     1.26107     |    -0.08962 |  ops/s |   -6.63% |
|                                             Median Throughput |                                          esql_basic_count_group_2 |     1.40376     |     1.30541     |    -0.09835 |  ops/s |   -7.01% |
|                                                Max Throughput |                                          esql_basic_count_group_2 |     1.55097     |     1.4528      |    -0.09817 |  ops/s |   -6.33% |
|                                       50th percentile latency |                                          esql_basic_count_group_2 |   524.129       |   540.947       |    16.8181  |     ms |   +3.21% |
|                                       90th percentile latency |                                          esql_basic_count_group_2 |   530.45        |   550.775       |    20.3246  |     ms |   +3.83% |
|                                      100th percentile latency |                                          esql_basic_count_group_2 |   542.765       |   610.147       |    67.3826  |     ms |  +12.41% |
|                                  50th percentile service time |                                          esql_basic_count_group_2 |   524.129       |   540.947       |    16.8181  |     ms |   +3.21% |
|                                  90th percentile service time |                                          esql_basic_count_group_2 |   530.45        |   550.775       |    20.3246  |     ms |   +3.83% |
|                                 100th percentile service time |                                          esql_basic_count_group_2 |   542.765       |   610.147       |    67.3826  |     ms |  +12.41% |
|                                                    error rate |                                          esql_basic_count_group_2 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                          esql_basic_count_group_3 |     0.790792    |     0.760959    |    -0.02983 |  ops/s |   -3.77% |
|                                               Mean Throughput |                                          esql_basic_count_group_3 |     0.858906    |     0.871101    |     0.0122  |  ops/s |   +1.42% |
|                                             Median Throughput |                                          esql_basic_count_group_3 |     0.8666      |     0.879337    |     0.01274 |  ops/s |   +1.47% |
|                                                Max Throughput |                                          esql_basic_count_group_3 |     0.902729    |     0.955301    |     0.05257 |  ops/s |   +5.82% |
|                                       50th percentile latency |                                          esql_basic_count_group_3 |   999.476       |   869.215       |  -130.261   |     ms |  -13.03% |
|                                       90th percentile latency |                                          esql_basic_count_group_3 |  1009.74        |   877.813       |  -131.928   |     ms |  -13.07% |
|                                      100th percentile latency |                                          esql_basic_count_group_3 |  1021.01        |   879.239       |  -141.769   |     ms |  -13.89% |
|                                  50th percentile service time |                                          esql_basic_count_group_3 |   999.476       |   869.215       |  -130.261   |     ms |  -13.03% |
|                                  90th percentile service time |                                          esql_basic_count_group_3 |  1009.74        |   877.813       |  -131.928   |     ms |  -13.07% |
|                                 100th percentile service time |                                          esql_basic_count_group_3 |  1021.01        |   879.239       |  -141.769   |     ms |  -13.89% |
|                                                    error rate |                                          esql_basic_count_group_3 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                          esql_basic_count_group_4 |     0.40064     |     0.383885    |    -0.01676 |  ops/s |   -4.18% |
|                                               Mean Throughput |                                          esql_basic_count_group_4 |     0.406392    |     0.38926     |    -0.01713 |  ops/s |   -4.22% |
|                                             Median Throughput |                                          esql_basic_count_group_4 |     0.407058    |     0.389516    |    -0.01754 |  ops/s |   -4.31% |
|                                                Max Throughput |                                          esql_basic_count_group_4 |     0.409602    |     0.393129    |    -0.01647 |  ops/s |   -4.02% |
|                                       50th percentile latency |                                          esql_basic_count_group_4 |  2404.94        |  2494.62        |    89.6797  |     ms |   +3.73% |
|                                       90th percentile latency |                                          esql_basic_count_group_4 |  2412.86        |  2529.63        |   116.773   |     ms |   +4.84% |
|                                      100th percentile latency |                                          esql_basic_count_group_4 |  2419.72        |  2569.5         |   149.779   |     ms |   +6.19% |
|                                  50th percentile service time |                                          esql_basic_count_group_4 |  2404.94        |  2494.62        |    89.6797  |     ms |   +3.73% |
|                                  90th percentile service time |                                          esql_basic_count_group_4 |  2412.86        |  2529.63        |   116.773   |     ms |   +4.84% |
|                                 100th percentile service time |                                          esql_basic_count_group_4 |  2419.72        |  2569.5         |   149.779   |     ms |   +6.19% |
|                                                    error rate |                                          esql_basic_count_group_4 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |          esql_time_range_and_date_histogram_two_groups_pre_filter |     3.29831     |     2.79072     |    -0.50759 |  ops/s |  -15.39% |
|                                               Mean Throughput |          esql_time_range_and_date_histogram_two_groups_pre_filter |     3.81451     |     3.41828     |    -0.39624 |  ops/s |  -10.39% |
|                                             Median Throughput |          esql_time_range_and_date_histogram_two_groups_pre_filter |     3.88525     |     3.49822     |    -0.38703 |  ops/s |   -9.96% |
|                                                Max Throughput |          esql_time_range_and_date_histogram_two_groups_pre_filter |     4.18924     |     3.86879     |    -0.32044 |  ops/s |   -7.65% |
|                                       50th percentile latency |          esql_time_range_and_date_histogram_two_groups_pre_filter |   204.699       |   220.05        |    15.3508  |     ms |   +7.50% |
|                                       90th percentile latency |          esql_time_range_and_date_histogram_two_groups_pre_filter |   220.723       |   232.863       |    12.14    |     ms |   +5.50% |
|                                      100th percentile latency |          esql_time_range_and_date_histogram_two_groups_pre_filter |   252.53        |   274.924       |    22.3933  |     ms |   +8.87% |
|                                  50th percentile service time |          esql_time_range_and_date_histogram_two_groups_pre_filter |   204.699       |   220.05        |    15.3508  |     ms |   +7.50% |
|                                  90th percentile service time |          esql_time_range_and_date_histogram_two_groups_pre_filter |   220.723       |   232.863       |    12.14    |     ms |   +5.50% |
|                                 100th percentile service time |          esql_time_range_and_date_histogram_two_groups_pre_filter |   252.53        |   274.924       |    22.3933  |     ms |   +8.87% |
|                                                    error rate |          esql_time_range_and_date_histogram_two_groups_pre_filter |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |         esql_time_range_and_date_histogram_two_groups_post_filter |     0.289928    |     0.289373    |    -0.00055 |  ops/s |   -0.19% |
|                                               Mean Throughput |         esql_time_range_and_date_histogram_two_groups_post_filter |     0.294982    |     0.292198    |    -0.00278 |  ops/s |   -0.94% |
|                                             Median Throughput |         esql_time_range_and_date_histogram_two_groups_post_filter |     0.295692    |     0.29254     |    -0.00315 |  ops/s |   -1.07% |
|                                                Max Throughput |         esql_time_range_and_date_histogram_two_groups_post_filter |     0.297137    |     0.293447    |    -0.00369 |  ops/s |   -1.24% |
|                                       50th percentile latency |         esql_time_range_and_date_histogram_two_groups_post_filter |  3340.64        |  3383.48        |    42.8398  |     ms |   +1.28% |
|                                       90th percentile latency |         esql_time_range_and_date_histogram_two_groups_post_filter |  3389.4         |  3415.79        |    26.3935  |     ms |   +0.78% |
|                                      100th percentile latency |         esql_time_range_and_date_histogram_two_groups_post_filter |  3401.58        |  3447.63        |    46.0466  |     ms |   +1.35% |
|                                  50th percentile service time |         esql_time_range_and_date_histogram_two_groups_post_filter |  3340.64        |  3383.48        |    42.8398  |     ms |   +1.28% |
|                                  90th percentile service time |         esql_time_range_and_date_histogram_two_groups_post_filter |  3389.4         |  3415.79        |    26.3935  |     ms |   +0.78% |
|                                 100th percentile service time |         esql_time_range_and_date_histogram_two_groups_post_filter |  3401.58        |  3447.63        |    46.0466  |     ms |   +1.35% |
|                                                    error rate |         esql_time_range_and_date_histogram_two_groups_post_filter |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                   esql_dissect_duration_and_stats |     6.79804     |     5.83474     |    -0.96331 |  ops/s |  -14.17% |
|                                               Mean Throughput |                                   esql_dissect_duration_and_stats |     8.51        |     7.6335      |    -0.87651 |  ops/s |  -10.30% |
|                                             Median Throughput |                                   esql_dissect_duration_and_stats |     8.51        |     7.6335      |    -0.87651 |  ops/s |  -10.30% |
|                                                Max Throughput |                                   esql_dissect_duration_and_stats |    10.222       |     9.43225     |    -0.78971 |  ops/s |   -7.73% |
|                                       50th percentile latency |                                   esql_dissect_duration_and_stats |    71.0209      |    73.3941      |     2.3732  |     ms |   +3.34% |
|                                       90th percentile latency |                                   esql_dissect_duration_and_stats |    76.0064      |    79.172       |     3.16566 |     ms |   +4.16% |
|                                      100th percentile latency |                                   esql_dissect_duration_and_stats |    79.1474      |    85.3554      |     6.20802 |     ms |   +7.84% |
|                                  50th percentile service time |                                   esql_dissect_duration_and_stats |    71.0209      |    73.3941      |     2.3732  |     ms |   +3.34% |
|                                  90th percentile service time |                                   esql_dissect_duration_and_stats |    76.0064      |    79.172       |     3.16566 |     ms |   +4.16% |
|                                 100th percentile service time |                                   esql_dissect_duration_and_stats |    79.1474      |    85.3554      |     6.20802 |     ms |   +7.84% |
|                                                    error rate |                                   esql_dissect_duration_and_stats |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                           term_query_with_matches |    21.9675      |    19.8738      |    -2.0937  |  ops/s |   -9.53% |
|                                               Mean Throughput |                                           term_query_with_matches |    24.4548      |    19.8868      |    -4.56803 |  ops/s |  -18.68% |
|                                             Median Throughput |                                           term_query_with_matches |    24.4548      |    19.8868      |    -4.56803 |  ops/s |  -18.68% |
|                                                Max Throughput |                                           term_query_with_matches |    26.9421      |    19.8998      |    -7.04237 |  ops/s |  -26.14% |
|                                       50th percentile latency |                                           term_query_with_matches |    28.643       |    42.5562      |    13.9132  |     ms |  +48.57% |
|                                       90th percentile latency |                                           term_query_with_matches |    93.4403      |    83.226       |   -10.2143  |     ms |  -10.93% |
|                                      100th percentile latency |                                           term_query_with_matches |    97.247       |    93.7556      |    -3.49134 |     ms |   -3.59% |
|                                  50th percentile service time |                                           term_query_with_matches |    28.643       |    42.5562      |    13.9132  |     ms |  +48.57% |
|                                  90th percentile service time |                                           term_query_with_matches |    93.4403      |    83.226       |   -10.2143  |     ms |  -10.93% |
|                                 100th percentile service time |                                           term_query_with_matches |    97.247       |    93.7556      |    -3.49134 |     ms |   -3.59% |
|                                                    error rate |                                           term_query_with_matches |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                  term_query_with_matches_argument |    16.311       |    61.1265      |    44.8155  |  ops/s | +274.76% |
|                                               Mean Throughput |                                  term_query_with_matches_argument |    18.6564      |    61.1265      |    42.4701  |  ops/s | +227.64% |
|                                             Median Throughput |                                  term_query_with_matches_argument |    18.6564      |    61.1265      |    42.4701  |  ops/s | +227.64% |
|                                                Max Throughput |                                  term_query_with_matches_argument |    21.0018      |    61.1265      |    40.1247  |  ops/s | +191.05% |
|                                       50th percentile latency |                                  term_query_with_matches_argument |    61.1743      |    14.0355      |   -47.1388  |     ms |  -77.06% |
|                                       90th percentile latency |                                  term_query_with_matches_argument |    63.7508      |    16.4382      |   -47.3126  |     ms |  -74.21% |
|                                      100th percentile latency |                                  term_query_with_matches_argument |    70.4032      |    18.5594      |   -51.8438  |     ms |  -73.64% |
|                                  50th percentile service time |                                  term_query_with_matches_argument |    61.1743      |    14.0355      |   -47.1388  |     ms |  -77.06% |
|                                  90th percentile service time |                                  term_query_with_matches_argument |    63.7508      |    16.4382      |   -47.3126  |     ms |  -74.21% |
|                                 100th percentile service time |                                  term_query_with_matches_argument |    70.4032      |    18.5594      |   -51.8438  |     ms |  -73.64% |
|                                                    error rate |                                  term_query_with_matches_argument |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                    term_query_empty_template_term |   161.189       |   171.054       |     9.86516 |  ops/s |   +6.12% |
|                                               Mean Throughput |                                    term_query_empty_template_term |   161.189       |   171.054       |     9.86516 |  ops/s |   +6.12% |
|                                             Median Throughput |                                    term_query_empty_template_term |   161.189       |   171.054       |     9.86516 |  ops/s |   +6.12% |
|                                                Max Throughput |                                    term_query_empty_template_term |   161.189       |   171.054       |     9.86516 |  ops/s |   +6.12% |
|                                       50th percentile latency |                                    term_query_empty_template_term |     4.52279     |     4.40229     |    -0.1205  |     ms |   -2.66% |
|                                       90th percentile latency |                                    term_query_empty_template_term |     4.90681     |     4.86287     |    -0.04394 |     ms |   -0.90% |
|                                      100th percentile latency |                                    term_query_empty_template_term |     5.91162     |     5.2602      |    -0.65142 |     ms |  -11.02% |
|                                  50th percentile service time |                                    term_query_empty_template_term |     4.52279     |     4.40229     |    -0.1205  |     ms |   -2.66% |
|                                  90th percentile service time |                                    term_query_empty_template_term |     4.90681     |     4.86287     |    -0.04394 |     ms |   -0.90% |
|                                 100th percentile service time |                                    term_query_empty_template_term |     5.91162     |     5.2602      |    -0.65142 |     ms |  -11.02% |
|                                                    error rate |                                    term_query_empty_template_term |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                    term_query_empty_argument_term |   165.128       |   164.414       |    -0.71342 |  ops/s |   -0.43% |
|                                               Mean Throughput |                                    term_query_empty_argument_term |   165.128       |   164.414       |    -0.71342 |  ops/s |   -0.43% |
|                                             Median Throughput |                                    term_query_empty_argument_term |   165.128       |   164.414       |    -0.71342 |  ops/s |   -0.43% |
|                                                Max Throughput |                                    term_query_empty_argument_term |   165.128       |   164.414       |    -0.71342 |  ops/s |   -0.43% |
|                                       50th percentile latency |                                    term_query_empty_argument_term |     4.36665     |     4.48343     |     0.11679 |     ms |   +2.67% |
|                                       90th percentile latency |                                    term_query_empty_argument_term |     4.96771     |     4.72357     |    -0.24414 |     ms |   -4.91% |
|                                      100th percentile latency |                                    term_query_empty_argument_term |     5.29912     |     5.05129     |    -0.24783 |     ms |   -4.68% |
|                                  50th percentile service time |                                    term_query_empty_argument_term |     4.36665     |     4.48343     |     0.11679 |     ms |   +2.67% |
|                                  90th percentile service time |                                    term_query_empty_argument_term |     4.96771     |     4.72357     |    -0.24414 |     ms |   -4.91% |
|                                 100th percentile service time |                                    term_query_empty_argument_term |     5.29912     |     5.05129     |    -0.24783 |     ms |   -4.68% |
|                                                    error rate |                                    term_query_empty_argument_term |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |              phrase_query_with_matches_template_many_term_matches |     5.55305     |     5.93544     |     0.38239 |  ops/s |   +6.89% |
|                                               Mean Throughput |              phrase_query_with_matches_template_many_term_matches |     6.47162     |     6.73509     |     0.26347 |  ops/s |   +4.07% |
|                                             Median Throughput |              phrase_query_with_matches_template_many_term_matches |     6.69356     |     6.89278     |     0.19922 |  ops/s |   +2.98% |
|                                                Max Throughput |              phrase_query_with_matches_template_many_term_matches |     7.16826     |     7.37706     |     0.2088  |  ops/s |   +2.91% |
|                                       50th percentile latency |              phrase_query_with_matches_template_many_term_matches |   120.427       |   119.409       |    -1.01778 |     ms |   -0.85% |
|                                       90th percentile latency |              phrase_query_with_matches_template_many_term_matches |   126.291       |   127.707       |     1.41599 |     ms |   +1.12% |
|                                      100th percentile latency |              phrase_query_with_matches_template_many_term_matches |   138.578       |   148.249       |     9.67065 |     ms |   +6.98% |
|                                  50th percentile service time |              phrase_query_with_matches_template_many_term_matches |   120.427       |   119.409       |    -1.01778 |     ms |   -0.85% |
|                                  90th percentile service time |              phrase_query_with_matches_template_many_term_matches |   126.291       |   127.707       |     1.41599 |     ms |   +1.12% |
|                                 100th percentile service time |              phrase_query_with_matches_template_many_term_matches |   138.578       |   148.249       |     9.67065 |     ms |   +6.98% |
|                                                    error rate |              phrase_query_with_matches_template_many_term_matches |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                   phrase_query_with_matches_argument_and_template |     4.74694     |     4.84481     |     0.09787 |  ops/s |   +2.06% |
|                                               Mean Throughput |                   phrase_query_with_matches_argument_and_template |     4.84006     |     4.91868     |     0.07862 |  ops/s |   +1.62% |
|                                             Median Throughput |                   phrase_query_with_matches_argument_and_template |     4.85156     |     4.93158     |     0.08002 |  ops/s |   +1.65% |
|                                                Max Throughput |                   phrase_query_with_matches_argument_and_template |     4.91018     |     4.96674     |     0.05656 |  ops/s |   +1.15% |
|                                       50th percentile latency |                   phrase_query_with_matches_argument_and_template |   197.287       |   196.447       |    -0.84014 |     ms |   -0.43% |
|                                       90th percentile latency |                   phrase_query_with_matches_argument_and_template |   199.064       |   198.077       |    -0.98656 |     ms |   -0.50% |
|                                      100th percentile latency |                   phrase_query_with_matches_argument_and_template |   201.435       |   198.519       |    -2.91624 |     ms |   -1.45% |
|                                  50th percentile service time |                   phrase_query_with_matches_argument_and_template |   197.287       |   196.447       |    -0.84014 |     ms |   -0.43% |
|                                  90th percentile service time |                   phrase_query_with_matches_argument_and_template |   199.064       |   198.077       |    -0.98656 |     ms |   -0.50% |
|                                 100th percentile service time |                   phrase_query_with_matches_argument_and_template |   201.435       |   198.519       |    -2.91624 |     ms |   -1.45% |
|                                                    error rate |                   phrase_query_with_matches_argument_and_template |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                              phrase_query_empty_with_term_matches |    12.4225      |    12.5664      |     0.14392 |  ops/s |   +1.16% |
|                                               Mean Throughput |                              phrase_query_empty_with_term_matches |    12.4225      |    12.5664      |     0.14392 |  ops/s |   +1.16% |
|                                             Median Throughput |                              phrase_query_empty_with_term_matches |    12.4225      |    12.5664      |     0.14392 |  ops/s |   +1.16% |
|                                                Max Throughput |                              phrase_query_empty_with_term_matches |    12.4225      |    12.5664      |     0.14392 |  ops/s |   +1.16% |
|                                       50th percentile latency |                              phrase_query_empty_with_term_matches |    75.1842      |    74.7781      |    -0.40604 |     ms |   -0.54% |
|                                       90th percentile latency |                              phrase_query_empty_with_term_matches |    78.8779      |    75.2186      |    -3.65925 |     ms |   -4.64% |
|                                      100th percentile latency |                              phrase_query_empty_with_term_matches |    83.8075      |    76.1392      |    -7.66836 |     ms |   -9.15% |
|                                  50th percentile service time |                              phrase_query_empty_with_term_matches |    75.1842      |    74.7781      |    -0.40604 |     ms |   -0.54% |
|                                  90th percentile service time |                              phrase_query_empty_with_term_matches |    78.8779      |    75.2186      |    -3.65925 |     ms |   -4.64% |
|                                 100th percentile service time |                              phrase_query_empty_with_term_matches |    83.8075      |    76.1392      |    -7.66836 |     ms |   -9.15% |
|                                                    error rate |                              phrase_query_empty_with_term_matches |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                        search_basic_count_group_0 |     3.05388     |     2.72581     |    -0.32807 |  ops/s |  -10.74% |
|                                               Mean Throughput |                                        search_basic_count_group_0 |     3.0689      |     2.73767     |    -0.33123 |  ops/s |  -10.79% |
|                                             Median Throughput |                                        search_basic_count_group_0 |     3.06744     |     2.73956     |    -0.32788 |  ops/s |  -10.69% |
|                                                Max Throughput |                                        search_basic_count_group_0 |     3.09104     |     2.74701     |    -0.34403 |  ops/s |  -11.13% |
|                                       50th percentile latency |                                        search_basic_count_group_0 |   325.71        |   364.196       |    38.4858  |     ms |  +11.82% |
|                                       90th percentile latency |                                        search_basic_count_group_0 |   339.656       |   380.211       |    40.555   |     ms |  +11.94% |
|                                      100th percentile latency |                                        search_basic_count_group_0 |   395.911       |   392.758       |    -3.1525  |     ms |   -0.80% |
|                                  50th percentile service time |                                        search_basic_count_group_0 |   325.71        |   364.196       |    38.4858  |     ms |  +11.82% |
|                                  90th percentile service time |                                        search_basic_count_group_0 |   339.656       |   380.211       |    40.555   |     ms |  +11.94% |
|                                 100th percentile service time |                                        search_basic_count_group_0 |   395.911       |   392.758       |    -3.1525  |     ms |   -0.80% |
|                                                    error rate |                                        search_basic_count_group_0 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                        search_basic_count_group_1 |   442.68        |   448.989       |     6.30887 |  ops/s |   +1.43% |
|                                               Mean Throughput |                                        search_basic_count_group_1 |   442.68        |   448.989       |     6.30887 |  ops/s |   +1.43% |
|                                             Median Throughput |                                        search_basic_count_group_1 |   442.68        |   448.989       |     6.30887 |  ops/s |   +1.43% |
|                                                Max Throughput |                                        search_basic_count_group_1 |   442.68        |   448.989       |     6.30887 |  ops/s |   +1.43% |
|                                       50th percentile latency |                                        search_basic_count_group_1 |     1.65508     |     1.6106      |    -0.04448 |     ms |   -2.69% |
|                                       90th percentile latency |                                        search_basic_count_group_1 |     1.76939     |     1.81375     |     0.04436 |     ms |   +2.51% |
|                                      100th percentile latency |                                        search_basic_count_group_1 |     2.11814     |     2.03002     |    -0.08812 |     ms |   -4.16% |
|                                  50th percentile service time |                                        search_basic_count_group_1 |     1.65508     |     1.6106      |    -0.04448 |     ms |   -2.69% |
|                                  90th percentile service time |                                        search_basic_count_group_1 |     1.76939     |     1.81375     |     0.04436 |     ms |   +2.51% |
|                                 100th percentile service time |                                        search_basic_count_group_1 |     2.11814     |     2.03002     |    -0.08812 |     ms |   -4.16% |
|                                                    error rate |                                        search_basic_count_group_1 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                        search_basic_count_group_2 |     0.161971    |     0.167209    |     0.00524 |  ops/s |   +3.23% |
|                                               Mean Throughput |                                        search_basic_count_group_2 |     0.164535    |     0.168825    |     0.00429 |  ops/s |   +2.61% |
|                                             Median Throughput |                                        search_basic_count_group_2 |     0.165391    |     0.169145    |     0.00375 |  ops/s |   +2.27% |
|                                                Max Throughput |                                        search_basic_count_group_2 |     0.167222    |     0.170271    |     0.00305 |  ops/s |   +1.82% |
|                                       50th percentile latency |                                        search_basic_count_group_2 |  5841.95        |  5809.09        |   -32.8565  |     ms |   -0.56% |
|                                      100th percentile latency |                                        search_basic_count_group_2 |  6195.63        |  5873.68        |  -321.954   |     ms |   -5.20% |
|                                  50th percentile service time |                                        search_basic_count_group_2 |  5841.95        |  5809.09        |   -32.8565  |     ms |   -0.56% |
|                                 100th percentile service time |                                        search_basic_count_group_2 |  6195.63        |  5873.68        |  -321.954   |     ms |   -5.20% |
|                                                    error rate |                                        search_basic_count_group_2 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                        search_basic_count_group_3 |     0.117976    |     0.122086    |     0.00411 |  ops/s |   +3.48% |
|                                               Mean Throughput |                                        search_basic_count_group_3 |     0.11895     |     0.122684    |     0.00373 |  ops/s |   +3.14% |
|                                             Median Throughput |                                        search_basic_count_group_3 |     0.119244    |     0.12251     |     0.00327 |  ops/s |   +2.74% |
|                                                Max Throughput |                                        search_basic_count_group_3 |     0.11963     |     0.123455    |     0.00382 |  ops/s |   +3.20% |
|                                       50th percentile latency |                                        search_basic_count_group_3 |  8277.35        |  7827.19        |  -450.16    |     ms |   -5.44% |
|                                      100th percentile latency |                                        search_basic_count_group_3 |  8458.78        |  8247.09        |  -211.698   |     ms |   -2.50% |
|                                  50th percentile service time |                                        search_basic_count_group_3 |  8277.35        |  7827.19        |  -450.16    |     ms |   -5.44% |
|                                 100th percentile service time |                                        search_basic_count_group_3 |  8458.78        |  8247.09        |  -211.698   |     ms |   -2.50% |
|                                                    error rate |                                        search_basic_count_group_3 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                        search_basic_count_group_4 |     0.0315652   |     0.0308064   |    -0.00076 |  ops/s |   -2.40% |
|                                               Mean Throughput |                                        search_basic_count_group_4 |     0.042116    |     0.0413954   |    -0.00072 |  ops/s |   -1.71% |
|                                             Median Throughput |                                        search_basic_count_group_4 |     0.0473169   |     0.0463865   |    -0.00093 |  ops/s |   -1.97% |
|                                                Max Throughput |                                        search_basic_count_group_4 |     0.0474658   |     0.0469933   |    -0.00047 |  ops/s |   -1.00% |
|                                       50th percentile latency |                                        search_basic_count_group_4 | 10454.2         | 10901.9         |   447.629   |     ms |   +4.28% |
|                                      100th percentile latency |                                        search_basic_count_group_4 | 10545.3         | 10923           |   377.626   |     ms |   +3.58% |
|                                  50th percentile service time |                                        search_basic_count_group_4 | 10454.2         | 10901.9         |   447.629   |     ms |   +4.28% |
|                                 100th percentile service time |                                        search_basic_count_group_4 | 10545.3         | 10923           |   377.626   |     ms |   +3.58% |
|                                                    error rate |                                        search_basic_count_group_4 |    33.3333      |    33.3333      |     0       |      % |    0.00% |
