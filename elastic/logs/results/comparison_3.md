Baseline:
  - Race ID: `755c12c3-cb5b-477c-b3e9-4d684bf8b2e1`
  - Race timestamp: 2025-10-28 09:09:27
  - Challenge: logging-querying
  - Car: external
  - User tags: `created-by=esbench, division=engineering, env-id=2241ac07-93d6-44fc-a1f2-fea5c2074e86, git-username=eyalkoren, 
    host-username=eyalkoren, name=timestamp-date, org=obs, project=logs-plus, setup=esbench, team=obs-experience`

Contender:
  - Race ID: `e118cb4b-6e77-49d8-a157-8f663c2d74f6`
  - Race timestamp: 2025-10-28 07:39:58
  - Challenge: logging-querying
  - Car: external
  - User tags: `created-by=esbench, division=engineering, env-id=2241ac07-93d6-44fc-a1f2-fea5c2074e86, git-username=eyalkoren, 
    host-username=eyalkoren, name=timestamp-date_nanos, org=obs, project=logs-plus, setup=esbench, team=obs-experience`

|                                                        Metric |                                                              Task |        Baseline |       Contender |        Diff |   Unit |   Diff % |
|--------------------------------------------------------------:|------------------------------------------------------------------:|----------------:|----------------:|------------:|-------:|---------:|
|                    Cumulative indexing time of primary shards |                                                                   |    91.5774      |    96.2972      |     4.71978 |    min |   +5.15% |
|             Min cumulative indexing time across primary shard |                                                                   |     0           |     0           |     0       |    min |    0.00% |
|          Median cumulative indexing time across primary shard |                                                                   |     2.40973     |     2.60951     |     0.19977 |    min |   +8.29% |
|             Max cumulative indexing time across primary shard |                                                                   |    41.3325      |    43.4093      |     2.07682 |    min |   +5.02% |
|           Cumulative indexing throttle time of primary shards |                                                                   |     0           |     0           |     0       |    min |    0.00% |
|    Min cumulative indexing throttle time across primary shard |                                                                   |     0           |     0           |     0       |    min |    0.00% |
| Median cumulative indexing throttle time across primary shard |                                                                   |     0           |     0           |     0       |    min |    0.00% |
|    Max cumulative indexing throttle time across primary shard |                                                                   |     0           |     0           |     0       |    min |    0.00% |
|                       Cumulative merge time of primary shards |                                                                   |    21.3133      |    24.777       |     3.46363 |    min |  +16.25% |
|                      Cumulative merge count of primary shards |                                                                   |    50           |    57           |     7       |        |  +14.00% |
|                Min cumulative merge time across primary shard |                                                                   |     0           |     0           |     0       |    min |    0.00% |
|             Median cumulative merge time across primary shard |                                                                   |     0.465508    |     0.5437      |     0.07819 |    min |  +16.80% |
|                Max cumulative merge time across primary shard |                                                                   |    10.863       |    11.9019      |     1.03893 |    min |   +9.56% |
|              Cumulative merge throttle time of primary shards |                                                                   |     2.62397     |     4.23972     |     1.61575 |    min |  +61.58% |
|       Min cumulative merge throttle time across primary shard |                                                                   |     0           |     0           |     0       |    min |    0.00% |
|    Median cumulative merge throttle time across primary shard |                                                                   |     0.03975     |     0.0752      |     0.03545 |    min |  +89.18% |
|       Max cumulative merge throttle time across primary shard |                                                                   |     1.09662     |     1.5093      |     0.41268 |    min |  +37.63% |
|                     Cumulative refresh time of primary shards |                                                                   |     0.904783    |     1.021       |     0.11622 |    min |  +12.84% |
|                    Cumulative refresh count of primary shards |                                                                   |   255           |   262           |     7       |        |   +2.75% |
|              Min cumulative refresh time across primary shard |                                                                   |     0           |     0           |     0       |    min |    0.00% |
|           Median cumulative refresh time across primary shard |                                                                   |     0.0409083   |     0.0561833   |     0.01528 |    min |  +37.34% |
|              Max cumulative refresh time across primary shard |                                                                   |     0.28375     |     0.25805     |    -0.0257  |    min |   -9.06% |
|                       Cumulative flush time of primary shards |                                                                   |     5.4112      |     5.47975     |     0.06855 |    min |   +1.27% |
|                      Cumulative flush count of primary shards |                                                                   |   151           |   154           |     3       |        |   +1.99% |
|                Min cumulative flush time across primary shard |                                                                   |     3.33333e-05 |     3.33333e-05 |     0       |    min |    0.00% |
|             Median cumulative flush time across primary shard |                                                                   |     0.164258    |     0.165367    |     0.00111 |    min |   +0.67% |
|                Max cumulative flush time across primary shard |                                                                   |     2.31548     |     2.2524      |    -0.06308 |    min |   -2.72% |
|                                       Total Young Gen GC time |                                                                   |    11.393       |    11.375       |    -0.018   |      s |   -0.16% |
|                                      Total Young Gen GC count |                                                                   |   707           |   706           |    -1       |        |   -0.14% |
|                                         Total Old Gen GC time |                                                                   |     0           |     0           |     0       |      s |    0.00% |
|                                        Total Old Gen GC count |                                                                   |     0           |     0           |     0       |        |    0.00% |
|                                                  Dataset size |                                                                   |     2.63547     |     2.64884     |     0.01337 |     GB |   +0.51% |
|                                                    Store size |                                                                   |     2.63547     |     2.64884     |     0.01337 |     GB |   +0.51% |
|                                                 Translog size |                                                                   |     7.17118e-07 |     7.17118e-07 |     0       |     GB |    0.00% |
|                                        Heap used for segments |                                                                   |     0           |     0           |     0       |     MB |    0.00% |
|                                      Heap used for doc values |                                                                   |     0           |     0           |     0       |     MB |    0.00% |
|                                           Heap used for terms |                                                                   |     0           |     0           |     0       |     MB |    0.00% |
|                                           Heap used for norms |                                                                   |     0           |     0           |     0       |     MB |    0.00% |
|                                          Heap used for points |                                                                   |     0           |     0           |     0       |     MB |    0.00% |
|                                   Heap used for stored fields |                                                                   |     0           |     0           |     0       |     MB |    0.00% |
|                                                 Segment count |                                                                   |    13           |    13           |     0       |        |    0.00% |
|                                   Total Ingest Pipeline count |                                                                   |     4.7056e+07  |     4.7056e+07  |     0       |        |    0.00% |
|                                    Total Ingest Pipeline time |                                                                   |     2.81267e+06 |     2.81821e+06 |  5532       |     ms |   +0.20% |
|                                  Total Ingest Pipeline failed |                                                                   |     0           |     0           |     0       |        |    0.00% |
|                                                Min Throughput |                                                  insert-pipelines |    16.3593      |    17.2691      |     0.90979 |  ops/s |   +5.56% |
|                                               Mean Throughput |                                                  insert-pipelines |    16.3593      |    17.2691      |     0.90979 |  ops/s |   +5.56% |
|                                             Median Throughput |                                                  insert-pipelines |    16.3593      |    17.2691      |     0.90979 |  ops/s |   +5.56% |
|                                                Max Throughput |                                                  insert-pipelines |    16.3593      |    17.2691      |     0.90979 |  ops/s |   +5.56% |
|                                      100th percentile latency |                                                  insert-pipelines |   887.486       |   839.464       |   -48.0226  |     ms |   -5.41% |
|                                 100th percentile service time |                                                  insert-pipelines |   887.486       |   839.464       |   -48.0226  |     ms |   -5.41% |
|                                                    error rate |                                                  insert-pipelines |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                                        insert-ilm |    25.4328      |    25.7302      |     0.29737 |  ops/s |   +1.17% |
|                                               Mean Throughput |                                                        insert-ilm |    25.4328      |    25.7302      |     0.29737 |  ops/s |   +1.17% |
|                                             Median Throughput |                                                        insert-ilm |    25.4328      |    25.7302      |     0.29737 |  ops/s |   +1.17% |
|                                                Max Throughput |                                                        insert-ilm |    25.4328      |    25.7302      |     0.29737 |  ops/s |   +1.17% |
|                                      100th percentile latency |                                                        insert-ilm |    38.7498      |    38.3196      |    -0.43012 |     ms |   -1.11% |
|                                 100th percentile service time |                                                        insert-ilm |    38.7498      |    38.3196      |    -0.43012 |     ms |   -1.11% |
|                                                    error rate |                                                        insert-ilm |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                            validate-package-template-installation |    41.6325      |    47.8862      |     6.25373 |  ops/s |  +15.02% |
|                                               Mean Throughput |                            validate-package-template-installation |    41.6325      |    47.8862      |     6.25373 |  ops/s |  +15.02% |
|                                             Median Throughput |                            validate-package-template-installation |    41.6325      |    47.8862      |     6.25373 |  ops/s |  +15.02% |
|                                                Max Throughput |                            validate-package-template-installation |    41.6325      |    47.8862      |     6.25373 |  ops/s |  +15.02% |
|                                      100th percentile latency |                            validate-package-template-installation |    23.7183      |    20.5943      |    -3.12394 |     ms |  -13.17% |
|                                 100th percentile service time |                            validate-package-template-installation |    23.7183      |    20.5943      |    -3.12394 |     ms |  -13.17% |
|                                                    error rate |                            validate-package-template-installation |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                   update-custom-package-templates |    33.935       |    36.1163      |     2.18135 |  ops/s |   +6.43% |
|                                               Mean Throughput |                                   update-custom-package-templates |    33.935       |    36.1163      |     2.18135 |  ops/s |   +6.43% |
|                                             Median Throughput |                                   update-custom-package-templates |    33.935       |    36.1163      |     2.18135 |  ops/s |   +6.43% |
|                                                Max Throughput |                                   update-custom-package-templates |    33.935       |    36.1163      |     2.18135 |  ops/s |   +6.43% |
|                                      100th percentile latency |                                   update-custom-package-templates |   353.318       |   331.973       |   -21.3448  |     ms |   -6.04% |
|                                 100th percentile service time |                                   update-custom-package-templates |   353.318       |   331.973       |   -21.3448  |     ms |   -6.04% |
|                                                    error rate |                                   update-custom-package-templates |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                                        bulk-index |   818.105       |   891.529       |    73.4236  | docs/s |   +8.97% |
|                                               Mean Throughput |                                                        bulk-index | 35678.2         | 35034.8         |  -643.395   | docs/s |   -1.80% |
|                                             Median Throughput |                                                        bulk-index | 36724.5         | 36065.9         |  -658.613   | docs/s |   -1.79% |
|                                                Max Throughput |                                                        bulk-index | 37870.4         | 36738.4         | -1131.98    | docs/s |   -2.99% |
|                                       50th percentile latency |                                                        bulk-index |   144.001       |   150.77        |     6.7694  |     ms |   +4.70% |
|                                       90th percentile latency |                                                        bulk-index |   350.546       |   362.587       |    12.0403  |     ms |   +3.43% |
|                                       99th percentile latency |                                                        bulk-index |   804.187       |   816.055       |    11.8681  |     ms |   +1.48% |
|                                     99.9th percentile latency |                                                        bulk-index |  3702.73        |  3683.78        |   -18.9567  |     ms |   -0.51% |
|                                    99.99th percentile latency |                                                        bulk-index |  6162.76        |  6273.08        |   110.321   |     ms |   +1.79% |
|                                      100th percentile latency |                                                        bulk-index |  8060.44        |  9029.5         |   969.063   |     ms |  +12.02% |
|                                  50th percentile service time |                                                        bulk-index |   145.2         |   150.445       |     5.2443  |     ms |   +3.61% |
|                                  90th percentile service time |                                                        bulk-index |   350.792       |   361.794       |    11.0021  |     ms |   +3.14% |
|                                  99th percentile service time |                                                        bulk-index |   808.475       |   813.26        |     4.78462 |     ms |   +0.59% |
|                                99.9th percentile service time |                                                        bulk-index |  3715.57        |  3707.27        |    -8.30313 |     ms |   -0.22% |
|                               99.99th percentile service time |                                                        bulk-index |  6150.52        |  6276.29        |   125.765   |     ms |   +2.04% |
|                                 100th percentile service time |                                                        bulk-index |  8060.44        |  9029.5         |   969.063   |     ms |  +12.02% |
|                                                    error rate |                                                        bulk-index |     0           |     0           |     0       |      % |    0.00% |
|                                       50th percentile latency |                                                 compression-stats | 10999.1         | 10999.5         |     0.37207 |     ms |    0.00% |
|                                       90th percentile latency |                                                 compression-stats | 11000.5         | 11000.4         |    -0.14609 |     ms |   -0.00% |
|                                      100th percentile latency |                                                 compression-stats | 11000.9         | 11000.8         |    -0.11133 |     ms |   -0.00% |
|                                  50th percentile service time |                                                 compression-stats | 10999.1         | 10999.5         |     0.37207 |     ms |    0.00% |
|                                  90th percentile service time |                                                 compression-stats | 11000.5         | 11000.4         |    -0.14609 |     ms |   -0.00% |
|                                 100th percentile service time |                                                 compression-stats | 11000.9         | 11000.8         |    -0.11133 |     ms |   -0.00% |
|                                                    error rate |                                                 compression-stats |   100           |   100           |     0       |      % |    0.00% |
|                                                Min Throughput |                                 discovery-search-request-size-100 |    16.8179      |     9.82804     |    -6.98986 |  ops/s |  -41.56% |
|                                               Mean Throughput |                                 discovery-search-request-size-100 |    19.576       |    14.0099      |    -5.56612 |  ops/s |  -28.43% |
|                                             Median Throughput |                                 discovery-search-request-size-100 |    19.576       |    14.0099      |    -5.56612 |  ops/s |  -28.43% |
|                                                Max Throughput |                                 discovery-search-request-size-100 |    22.3341      |    18.1918      |    -4.14238 |  ops/s |  -18.55% |
|                                       50th percentile latency |                                 discovery-search-request-size-100 |    34.8083      |    36.0157      |     1.20748 |     ms |   +3.47% |
|                                       90th percentile latency |                                 discovery-search-request-size-100 |    54.9231      |    58.9293      |     4.00617 |     ms |   +7.29% |
|                                      100th percentile latency |                                 discovery-search-request-size-100 |   181.298       |   282.818       |   101.521   |     ms |  +56.00% |
|                                  50th percentile service time |                                 discovery-search-request-size-100 |    34.8083      |    36.0157      |     1.20748 |     ms |   +3.47% |
|                                  90th percentile service time |                                 discovery-search-request-size-100 |    54.9231      |    58.9293      |     4.00617 |     ms |   +7.29% |
|                                 100th percentile service time |                                 discovery-search-request-size-100 |   181.298       |   282.818       |   101.521   |     ms |  +56.00% |
|                                                    error rate |                                 discovery-search-request-size-100 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                 discovery-search-request-size-500 |    12.8703      |    13.2816      |     0.41133 |  ops/s |   +3.20% |
|                                               Mean Throughput |                                 discovery-search-request-size-500 |    13.5088      |    13.5783      |     0.06952 |  ops/s |   +0.51% |
|                                             Median Throughput |                                 discovery-search-request-size-500 |    13.7822      |    13.4653      |    -0.3169  |  ops/s |   -2.30% |
|                                                Max Throughput |                                 discovery-search-request-size-500 |    13.8739      |    13.988       |     0.11412 |  ops/s |   +0.82% |
|                                       50th percentile latency |                                 discovery-search-request-size-500 |    72.6632      |    73.4531      |     0.78984 |     ms |   +1.09% |
|                                       90th percentile latency |                                 discovery-search-request-size-500 |    81.6942      |    78.4382      |    -3.25605 |     ms |   -3.99% |
|                                      100th percentile latency |                                 discovery-search-request-size-500 |    97.75        |    90.8715      |    -6.87847 |     ms |   -7.04% |
|                                  50th percentile service time |                                 discovery-search-request-size-500 |    72.6632      |    73.4531      |     0.78984 |     ms |   +1.09% |
|                                  90th percentile service time |                                 discovery-search-request-size-500 |    81.6942      |    78.4382      |    -3.25605 |     ms |   -3.99% |
|                                 100th percentile service time |                                 discovery-search-request-size-500 |    97.75        |    90.8715      |    -6.87847 |     ms |   -7.04% |
|                                                    error rate |                                 discovery-search-request-size-500 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                discovery-search-request-size-1000 |     7.89855     |     8.22789     |     0.32934 |  ops/s |   +4.17% |
|                                               Mean Throughput |                                discovery-search-request-size-1000 |     8.17871     |     8.61797     |     0.43926 |  ops/s |   +5.37% |
|                                             Median Throughput |                                discovery-search-request-size-1000 |     8.25248     |     8.66794     |     0.41546 |  ops/s |   +5.03% |
|                                                Max Throughput |                                discovery-search-request-size-1000 |     8.35334     |     8.79418     |     0.44084 |  ops/s |   +5.28% |
|                                       50th percentile latency |                                discovery-search-request-size-1000 |   111.057       |   107.617       |    -3.43925 |     ms |   -3.10% |
|                                       90th percentile latency |                                discovery-search-request-size-1000 |   129.936       |   128.033       |    -1.90306 |     ms |   -1.46% |
|                                      100th percentile latency |                                discovery-search-request-size-1000 |   139.941       |   132.21        |    -7.73175 |     ms |   -5.52% |
|                                  50th percentile service time |                                discovery-search-request-size-1000 |   111.057       |   107.617       |    -3.43925 |     ms |   -3.10% |
|                                  90th percentile service time |                                discovery-search-request-size-1000 |   129.936       |   128.033       |    -1.90306 |     ms |   -1.46% |
|                                 100th percentile service time |                                discovery-search-request-size-1000 |   139.941       |   132.21        |    -7.73175 |     ms |   -5.52% |
|                                                    error rate |                                discovery-search-request-size-1000 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                                   discover/search |     0.00343566  |     0.00343566  |     0       |  ops/s |    0.00% |
|                                               Mean Throughput |                                                   discover/search |     0.00354769  |     0.00354769  |    -0       |  ops/s |   -0.00% |
|                                             Median Throughput |                                                   discover/search |     0.00354769  |     0.00354769  |    -0       |  ops/s |   -0.00% |
|                                                Max Throughput |                                                   discover/search |     0.00365972  |     0.00365972  |    -0       |  ops/s |   -0.00% |
|                                       50th percentile latency |                                                   discover/search |   325.006       |   326.231       |     1.22459 |     ms |   +0.38% |
|                                      100th percentile latency |                                                   discover/search |   606.608       |   606.607       |    -0.00037 |     ms |   -0.00% |
|                                  50th percentile service time |                                                   discover/search |   322.971       |   323.177       |     0.20573 |     ms |   +0.06% |
|                                 100th percentile service time |                                                   discover/search |   323.726       |   325.905       |     2.17892 |     ms |   +0.67% |
|                                                    error rate |                                                   discover/search |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                                discover/visualize |     0.00231601  |     0.00231602  |     0       |  ops/s |    0.00% |
|                                               Mean Throughput |                                                discover/visualize |     0.00486776  |     0.00486777  |     0       |  ops/s |    0.00% |
|                                             Median Throughput |                                                discover/visualize |     0.00518901  |     0.00518902  |     0       |  ops/s |    0.00% |
|                                                Max Throughput |                                                discover/visualize |     0.0068652   |     0.00686522  |     0       |  ops/s |    0.00% |
|                                       50th percentile latency |                                                discover/visualize |   320.669       |   320.099       |    -0.57036 |     ms |   -0.18% |
|                                      100th percentile latency |                                                discover/visualize |   324.288       |   325.401       |     1.1127  |     ms |   +0.34% |
|                                  50th percentile service time |                                                discover/visualize |   318.753       |   318.353       |    -0.39969 |     ms |   -0.13% |
|                                 100th percentile service time |                                                discover/visualize |   322.821       |   324.313       |     1.49246 |     ms |   +0.46% |
|                                                    error rate |                                                discover/visualize |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                                             kafka |     0.0050254   |     0.00502542  |     0       |  ops/s |    0.00% |
|                                               Mean Throughput |                                                             kafka |     0.0110764   |     0.0110764   |     0       |  ops/s |    0.00% |
|                                             Median Throughput |                                                             kafka |     0.00971789  |     0.00971794  |     0       |  ops/s |    0.00% |
|                                                Max Throughput |                                                             kafka |     0.0187323   |     0.0187324   |     0       |  ops/s |    0.00% |
|                                       50th percentile latency |                                                             kafka |   318.425       |   318.747       |     0.32208 |     ms |   +0.10% |
|                                      100th percentile latency |                                                             kafka |   327.016       |   328.646       |     1.62997 |     ms |   +0.50% |
|                                  50th percentile service time |                                                             kafka |   316.719       |   316.928       |     0.2086  |     ms |   +0.07% |
|                                 100th percentile service time |                                                             kafka |   326.139       |   327.724       |     1.58481 |     ms |   +0.49% |
|                                                    error rate |                                                             kafka |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                                             nginx |     0.00645828  |     0.0064591   |     0       |  ops/s |   +0.01% |
|                                               Mean Throughput |                                                             nginx |     0.0233961   |     0.0233975   |     0       |  ops/s |    0.01% |
|                                             Median Throughput |                                                             nginx |     0.0241355   |     0.0241384   |     0       |  ops/s |   +0.01% |
|                                                Max Throughput |                                                             nginx |     0.0347947   |     0.0347961   |     0       |  ops/s |    0.00% |
|                                       50th percentile latency |                                                             nginx |  1725.87        |  1725.87        |    -0.00012 |     ms |   -0.00% |
|                                       90th percentile latency |                                                             nginx |  2644.29        |  2643.58        |    -0.71353 |     ms |   -0.03% |
|                                      100th percentile latency |                                                             nginx |  3692.63        |  3686.47        |    -6.16504 |     ms |   -0.17% |
|                                  50th percentile service time |                                                             nginx |  1684.17        |  1683.6         |    -0.56226 |     ms |   -0.03% |
|                                  90th percentile service time |                                                             nginx |  1727.28        |  1726.99        |    -0.29241 |     ms |   -0.02% |
|                                 100th percentile service time |                                                             nginx |  1752.34        |  1752.62        |     0.28271 |     ms |   +0.02% |
|                                                    error rate |                                                             nginx |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                                            apache |     0.0450344   |     0.0450344   |    -0       |  ops/s |   -0.00% |
|                                               Mean Throughput |                                                            apache |     0.094059    |     0.0940582   |    -0       |  ops/s |   -0.00% |
|                                             Median Throughput |                                                            apache |     0.0977351   |     0.0977344   |    -0       |  ops/s |   -0.00% |
|                                                Max Throughput |                                                            apache |     0.158561    |     0.158559    |    -0       |  ops/s |   -0.00% |
|                                       50th percentile latency |                                                            apache |   317.692       |   317.157       |    -0.53479 |     ms |   -0.17% |
|                                       90th percentile latency |                                                            apache |   331.13        |   330.659       |    -0.47141 |     ms |   -0.14% |
|                                      100th percentile latency |                                                            apache |   375.094       |   373.302       |    -1.79144 |     ms |   -0.48% |
|                                  50th percentile service time |                                                            apache |   316.196       |   316.049       |    -0.14731 |     ms |   -0.05% |
|                                  90th percentile service time |                                                            apache |   328.211       |   328.072       |    -0.13872 |     ms |   -0.04% |
|                                 100th percentile service time |                                                            apache |   331.415       |   331.037       |    -0.37814 |     ms |   -0.11% |
|                                                    error rate |                                                            apache |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                                       system/auth |     0.0655626   |     0.0655626   |     0       |  ops/s |    0.00% |
|                                               Mean Throughput |                                                       system/auth |     0.12034     |     0.120341    |     0       |  ops/s |    0.00% |
|                                             Median Throughput |                                                       system/auth |     0.118772    |     0.118772    |     0       |  ops/s |    0.00% |
|                                                Max Throughput |                                                       system/auth |     0.153319    |     0.153319    |     0       |  ops/s |    0.00% |
|                                       50th percentile latency |                                                       system/auth |   324.336       |   324.192       |    -0.14363 |     ms |   -0.04% |
|                                       90th percentile latency |                                                       system/auth |   381.412       |   381.972       |     0.56042 |     ms |   +0.15% |
|                                      100th percentile latency |                                                       system/auth |   595.887       |   595.811       |    -0.07532 |     ms |   -0.01% |
|                                  50th percentile service time |                                                       system/auth |   322.008       |   322.07        |     0.06161 |     ms |   +0.02% |
|                                  90th percentile service time |                                                       system/auth |   330.87        |   330.304       |    -0.56606 |     ms |   -0.17% |
|                                 100th percentile service time |                                                       system/auth |   414.624       |   414.8         |     0.17636 |     ms |   +0.04% |
|                                                    error rate |                                                       system/auth |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                           system/syslog/dashboard |     0.0408357   |     0.0408358   |     0       |  ops/s |    0.00% |
|                                               Mean Throughput |                                           system/syslog/dashboard |     0.0535934   |     0.0535934   |     0       |  ops/s |    0.00% |
|                                             Median Throughput |                                           system/syslog/dashboard |     0.0520764   |     0.0520765   |     0       |  ops/s |    0.00% |
|                                                Max Throughput |                                           system/syslog/dashboard |     0.0694828   |     0.0694828   |     0       |  ops/s |    0.00% |
|                                       50th percentile latency |                                           system/syslog/dashboard |   318.237       |   317.887       |    -0.35008 |     ms |   -0.11% |
|                                       90th percentile latency |                                           system/syslog/dashboard |   401.738       |   401.033       |    -0.70489 |     ms |   -0.18% |
|                                      100th percentile latency |                                           system/syslog/dashboard |   593.975       |   594.138       |     0.16327 |     ms |   +0.03% |
|                                  50th percentile service time |                                           system/syslog/dashboard |   316.048       |   315.949       |    -0.09998 |     ms |   -0.03% |
|                                  90th percentile service time |                                           system/syslog/dashboard |   321.155       |   321.039       |    -0.11551 |     ms |   -0.04% |
|                                 100th percentile service time |                                           system/syslog/dashboard |   322.596       |   322.34        |    -0.25577 |     ms |   -0.08% |
|                                                    error rate |                                           system/syslog/dashboard |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                                system/syslog/lens |     0.0113597   |     0.0113597   |    -0       |  ops/s |   -0.00% |
|                                               Mean Throughput |                                                system/syslog/lens |     0.0192306   |     0.0192306   |    -0       |  ops/s |   -0.00% |
|                                             Median Throughput |                                                system/syslog/lens |     0.0160602   |     0.0160602   |     0       |  ops/s |    0.00% |
|                                                Max Throughput |                                                system/syslog/lens |     0.0512792   |     0.0512791   |    -0       |  ops/s |   -0.00% |
|                                       50th percentile latency |                                                system/syslog/lens |   322.35        |   322.254       |    -0.09637 |     ms |   -0.03% |
|                                       90th percentile latency |                                                system/syslog/lens |   856.11        |   855.76        |    -0.34918 |     ms |   -0.04% |
|                                      100th percentile latency |                                                system/syslog/lens |   876.357       |   876.08        |    -0.27655 |     ms |   -0.03% |
|                                  50th percentile service time |                                                system/syslog/lens |   320.052       |   319.376       |    -0.67633 |     ms |   -0.21% |
|                                  90th percentile service time |                                                system/syslog/lens |   853.016       |   852.904       |    -0.11224 |     ms |   -0.01% |
|                                 100th percentile service time |                                                system/syslog/lens |   855.021       |   854.884       |    -0.1369  |     ms |   -0.02% |
|                                                    error rate |                                                system/syslog/lens |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                                   mysql/dashboard |     0.00336287  |     0.00336287  |     0       |  ops/s |    0.00% |
|                                               Mean Throughput |                                                   mysql/dashboard |     0.0088806   |     0.00888061  |     0       |  ops/s |    0.00% |
|                                             Median Throughput |                                                   mysql/dashboard |     0.00851366  |     0.00851366  |     0       |  ops/s |    0.00% |
|                                                Max Throughput |                                                   mysql/dashboard |     0.0150139   |     0.0150139   |     0       |  ops/s |    0.00% |
|                                       50th percentile latency |                                                   mysql/dashboard |   312.049       |   312.093       |     0.04402 |     ms |   +0.01% |
|                                       90th percentile latency |                                                   mysql/dashboard |   328.779       |   329.582       |     0.8032  |     ms |   +0.24% |
|                                      100th percentile latency |                                                   mysql/dashboard |   548.147       |   548.406       |     0.25861 |     ms |   +0.05% |
|                                  50th percentile service time |                                                   mysql/dashboard |   309.711       |   309.706       |    -0.00482 |     ms |   -0.00% |
|                                  90th percentile service time |                                                   mysql/dashboard |   317.567       |   318.65        |     1.08285 |     ms |   +0.34% |
|                                 100th percentile service time |                                                   mysql/dashboard |   331.525       |   331.727       |     0.20175 |     ms |   +0.06% |
|                                                    error rate |                                                   mysql/dashboard |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                                             redis |     0.00958893  |     0.00958888  |    -0       |  ops/s |   -0.00% |
|                                               Mean Throughput |                                                             redis |     0.040273    |     0.0402729   |    -0       |  ops/s |   -0.00% |
|                                             Median Throughput |                                                             redis |     0.0410645   |     0.0410644   |    -0       |  ops/s |   -0.00% |
|                                                Max Throughput |                                                             redis |     0.0726224   |     0.0726223   |    -0       |  ops/s |   -0.00% |
|                                       50th percentile latency |                                                             redis |   322.745       |   323.074       |     0.32892 |     ms |   +0.10% |
|                                       90th percentile latency |                                                             redis |   398.848       |   399.942       |     1.09399 |     ms |   +0.27% |
|                                      100th percentile latency |                                                             redis |   784.991       |   784.49        |    -0.50128 |     ms |   -0.06% |
|                                  50th percentile service time |                                                             redis |   321.631       |   321.74        |     0.10861 |     ms |   +0.03% |
|                                  90th percentile service time |                                                             redis |   332.515       |   332.777       |     0.26215 |     ms |   +0.08% |
|                                 100th percentile service time |                                                             redis |   784.09        |   784.061       |    -0.02917 |     ms |   -0.00% |
|                                                    error rate |                                                             redis |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                                        mysql/lens |     0.00680638  |     0.00680638  |     0       |  ops/s |    0.00% |
|                                               Mean Throughput |                                                        mysql/lens |     0.0273108   |     0.0273108   |    -0       |  ops/s |   -0.00% |
|                                             Median Throughput |                                                        mysql/lens |     0.0281678   |     0.0281678   |    -0       |  ops/s |   -0.00% |
|                                                Max Throughput |                                                        mysql/lens |     0.0470133   |     0.0470132   |    -0       |  ops/s |   -0.00% |
|                                       50th percentile latency |                                                        mysql/lens |   317.626       |   318.552       |     0.92618 |     ms |   +0.29% |
|                                       90th percentile latency |                                                        mysql/lens |   983.396       |   983.798       |     0.40183 |     ms |   +0.04% |
|                                      100th percentile latency |                                                        mysql/lens |  1000.11        |  1000.6         |     0.48126 |     ms |   +0.05% |
|                                  50th percentile service time |                                                        mysql/lens |   316.463       |   316.542       |     0.07857 |     ms |   +0.02% |
|                                  90th percentile service time |                                                        mysql/lens |   536.653       |   571.238       |    34.5856  |     ms |   +6.44% |
|                                 100th percentile service time |                                                        mysql/lens |   998.767       |   998.005       |    -0.76123 |     ms |   -0.08% |
|                                                    error rate |                                                        mysql/lens |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                               postgresql/overview |     0.00513625  |     0.00513625  |     0       |  ops/s |    0.00% |
|                                               Mean Throughput |                                               postgresql/overview |     0.0581882   |     0.0581883   |     0       |  ops/s |    0.00% |
|                                             Median Throughput |                                               postgresql/overview |     0.0620373   |     0.0620372   |    -0       |  ops/s |   -0.00% |
|                                                Max Throughput |                                               postgresql/overview |     0.089403    |     0.089403    |     0       |  ops/s |    0.00% |
|                                       50th percentile latency |                                               postgresql/overview |  1010.85        |  1011.31        |     0.46091 |     ms |   +0.05% |
|                                       90th percentile latency |                                               postgresql/overview |  1500.21        |  1501.94        |     1.73032 |     ms |   +0.12% |
|                                      100th percentile latency |                                               postgresql/overview |  2140.05        |  2142.11        |     2.05566 |     ms |   +0.10% |
|                                  50th percentile service time |                                               postgresql/overview |  1007.36        |  1006.96        |    -0.40143 |     ms |   -0.04% |
|                                  90th percentile service time |                                               postgresql/overview |  1047.5         |  1045.62        |    -1.88519 |     ms |   -0.18% |
|                                 100th percentile service time |                                               postgresql/overview |  1673.03        |  1673.43        |     0.39966 |     ms |   +0.02% |
|                                                    error rate |                                               postgresql/overview |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                               postgresql/duration |     0.0224605   |     0.0224605   |     0       |  ops/s |    0.00% |
|                                               Mean Throughput |                                               postgresql/duration |     0.0643453   |     0.0643453   |    -0       |  ops/s |   -0.00% |
|                                             Median Throughput |                                               postgresql/duration |     0.0679207   |     0.0679207   |     0       |  ops/s |    0.00% |
|                                                Max Throughput |                                               postgresql/duration |     0.0802624   |     0.0802623   |    -0       |  ops/s |   -0.00% |
|                                       50th percentile latency |                                               postgresql/duration |   313.578       |   313.424       |    -0.1539  |     ms |   -0.05% |
|                                       90th percentile latency |                                               postgresql/duration |   415.419       |   414.607       |    -0.81265 |     ms |   -0.20% |
|                                      100th percentile latency |                                               postgresql/duration |   740.305       |   740.556       |     0.25098 |     ms |   +0.03% |
|                                  50th percentile service time |                                               postgresql/duration |   311.702       |   311.717       |     0.01489 |     ms |    0.00% |
|                                  90th percentile service time |                                               postgresql/duration |   317.929       |   317.779       |    -0.15067 |     ms |   -0.05% |
|                                 100th percentile service time |                                               postgresql/duration |   322.045       |   320.594       |    -1.4512  |     ms |   -0.45% |
|                                                    error rate |                                               postgresql/duration |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                  esql_basic_count_group_0_limit_0 |    65.4593      |    60.8747      |    -4.58464 |  ops/s |   -7.00% |
|                                               Mean Throughput |                                  esql_basic_count_group_0_limit_0 |    65.4593      |    60.8747      |    -4.58464 |  ops/s |   -7.00% |
|                                             Median Throughput |                                  esql_basic_count_group_0_limit_0 |    65.4593      |    60.8747      |    -4.58464 |  ops/s |   -7.00% |
|                                                Max Throughput |                                  esql_basic_count_group_0_limit_0 |    65.4593      |    60.8747      |    -4.58464 |  ops/s |   -7.00% |
|                                       50th percentile latency |                                  esql_basic_count_group_0_limit_0 |     3.67796     |     4.25376     |     0.5758  |     ms |  +15.66% |
|                                       90th percentile latency |                                  esql_basic_count_group_0_limit_0 |     5.26253     |     4.87797     |    -0.38456 |     ms |   -7.31% |
|                                      100th percentile latency |                                  esql_basic_count_group_0_limit_0 |     6.66271     |     5.89092     |    -0.77179 |     ms |  -11.58% |
|                                  50th percentile service time |                                  esql_basic_count_group_0_limit_0 |     3.67796     |     4.25376     |     0.5758  |     ms |  +15.66% |
|                                  90th percentile service time |                                  esql_basic_count_group_0_limit_0 |     5.26253     |     4.87797     |    -0.38456 |     ms |   -7.31% |
|                                 100th percentile service time |                                  esql_basic_count_group_0_limit_0 |     6.66271     |     5.89092     |    -0.77179 |     ms |  -11.58% |
|                                                    error rate |                                  esql_basic_count_group_0_limit_0 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                  esql_basic_count_group_1_limit_0 |   214.83        |   187.519       |   -27.311   |  ops/s |  -12.71% |
|                                               Mean Throughput |                                  esql_basic_count_group_1_limit_0 |   214.83        |   187.519       |   -27.311   |  ops/s |  -12.71% |
|                                             Median Throughput |                                  esql_basic_count_group_1_limit_0 |   214.83        |   187.519       |   -27.311   |  ops/s |  -12.71% |
|                                                Max Throughput |                                  esql_basic_count_group_1_limit_0 |   214.83        |   187.519       |   -27.311   |  ops/s |  -12.71% |
|                                       50th percentile latency |                                  esql_basic_count_group_1_limit_0 |     3.53835     |     4.48213     |     0.94378 |     ms |  +26.67% |
|                                       90th percentile latency |                                  esql_basic_count_group_1_limit_0 |     4.56317     |     5.13653     |     0.57336 |     ms |  +12.56% |
|                                      100th percentile latency |                                  esql_basic_count_group_1_limit_0 |     5.12029     |     5.45089     |     0.3306  |     ms |   +6.46% |
|                                  50th percentile service time |                                  esql_basic_count_group_1_limit_0 |     3.53835     |     4.48213     |     0.94378 |     ms |  +26.67% |
|                                  90th percentile service time |                                  esql_basic_count_group_1_limit_0 |     4.56317     |     5.13653     |     0.57336 |     ms |  +12.56% |
|                                 100th percentile service time |                                  esql_basic_count_group_1_limit_0 |     5.12029     |     5.45089     |     0.3306  |     ms |   +6.46% |
|                                                    error rate |                                  esql_basic_count_group_1_limit_0 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                  esql_basic_count_group_2_limit_0 |   264.225       |   256.046       |    -8.1792  |  ops/s |   -3.10% |
|                                               Mean Throughput |                                  esql_basic_count_group_2_limit_0 |   264.225       |   256.046       |    -8.1792  |  ops/s |   -3.10% |
|                                             Median Throughput |                                  esql_basic_count_group_2_limit_0 |   264.225       |   256.046       |    -8.1792  |  ops/s |   -3.10% |
|                                                Max Throughput |                                  esql_basic_count_group_2_limit_0 |   264.225       |   256.046       |    -8.1792  |  ops/s |   -3.10% |
|                                       50th percentile latency |                                  esql_basic_count_group_2_limit_0 |     2.99251     |     3.21813     |     0.22562 |     ms |   +7.54% |
|                                       90th percentile latency |                                  esql_basic_count_group_2_limit_0 |     3.54981     |     3.63333     |     0.08351 |     ms |   +2.35% |
|                                      100th percentile latency |                                  esql_basic_count_group_2_limit_0 |     3.80644     |     4.16255     |     0.35611 |     ms |   +9.36% |
|                                  50th percentile service time |                                  esql_basic_count_group_2_limit_0 |     2.99251     |     3.21813     |     0.22562 |     ms |   +7.54% |
|                                  90th percentile service time |                                  esql_basic_count_group_2_limit_0 |     3.54981     |     3.63333     |     0.08351 |     ms |   +2.35% |
|                                 100th percentile service time |                                  esql_basic_count_group_2_limit_0 |     3.80644     |     4.16255     |     0.35611 |     ms |   +9.36% |
|                                                    error rate |                                  esql_basic_count_group_2_limit_0 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                  esql_basic_count_group_3_limit_0 |   294.467       |   260.412       |   -34.0556  |  ops/s |  -11.57% |
|                                               Mean Throughput |                                  esql_basic_count_group_3_limit_0 |   294.467       |   260.412       |   -34.0556  |  ops/s |  -11.57% |
|                                             Median Throughput |                                  esql_basic_count_group_3_limit_0 |   294.467       |   260.412       |   -34.0556  |  ops/s |  -11.57% |
|                                                Max Throughput |                                  esql_basic_count_group_3_limit_0 |   294.467       |   260.412       |   -34.0556  |  ops/s |  -11.57% |
|                                       50th percentile latency |                                  esql_basic_count_group_3_limit_0 |     2.74417     |     3.22592     |     0.48175 |     ms |  +17.56% |
|                                       90th percentile latency |                                  esql_basic_count_group_3_limit_0 |     3.0827      |     3.80298     |     0.72028 |     ms |  +23.37% |
|                                      100th percentile latency |                                  esql_basic_count_group_3_limit_0 |     3.39262     |     4.06846     |     0.67583 |     ms |  +19.92% |
|                                  50th percentile service time |                                  esql_basic_count_group_3_limit_0 |     2.74417     |     3.22592     |     0.48175 |     ms |  +17.56% |
|                                  90th percentile service time |                                  esql_basic_count_group_3_limit_0 |     3.0827      |     3.80298     |     0.72028 |     ms |  +23.37% |
|                                 100th percentile service time |                                  esql_basic_count_group_3_limit_0 |     3.39262     |     4.06846     |     0.67583 |     ms |  +19.92% |
|                                                    error rate |                                  esql_basic_count_group_3_limit_0 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                  esql_basic_count_group_4_limit_0 |   271.212       |   239.602       |   -31.6096  |  ops/s |  -11.65% |
|                                               Mean Throughput |                                  esql_basic_count_group_4_limit_0 |   271.212       |   239.602       |   -31.6096  |  ops/s |  -11.65% |
|                                             Median Throughput |                                  esql_basic_count_group_4_limit_0 |   271.212       |   239.602       |   -31.6096  |  ops/s |  -11.65% |
|                                                Max Throughput |                                  esql_basic_count_group_4_limit_0 |   271.212       |   239.602       |   -31.6096  |  ops/s |  -11.65% |
|                                       50th percentile latency |                                  esql_basic_count_group_4_limit_0 |     2.99977     |     2.91891     |    -0.08086 |     ms |   -2.70% |
|                                       90th percentile latency |                                  esql_basic_count_group_4_limit_0 |     3.35945     |     3.25801     |    -0.10144 |     ms |   -3.02% |
|                                      100th percentile latency |                                  esql_basic_count_group_4_limit_0 |     3.80834     |     4.76073     |     0.95239 |     ms |  +25.01% |
|                                  50th percentile service time |                                  esql_basic_count_group_4_limit_0 |     2.99977     |     2.91891     |    -0.08086 |     ms |   -2.70% |
|                                  90th percentile service time |                                  esql_basic_count_group_4_limit_0 |     3.35945     |     3.25801     |    -0.10144 |     ms |   -3.02% |
|                                 100th percentile service time |                                  esql_basic_count_group_4_limit_0 |     3.80834     |     4.76073     |     0.95239 |     ms |  +25.01% |
|                                                    error rate |                                  esql_basic_count_group_4_limit_0 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |   122.142       |   100.288       |   -21.8542  |  ops/s |  -17.89% |
|                                               Mean Throughput |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |   122.142       |   100.288       |   -21.8542  |  ops/s |  -17.89% |
|                                             Median Throughput |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |   122.142       |   100.288       |   -21.8542  |  ops/s |  -17.89% |
|                                                Max Throughput |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |   122.142       |   100.288       |   -21.8542  |  ops/s |  -17.89% |
|                                       50th percentile latency |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |     5.18889     |     6.33525     |     1.14636 |     ms |  +22.09% |
|                                       90th percentile latency |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |     6.59799     |     7.37668     |     0.77869 |     ms |  +11.80% |
|                                      100th percentile latency |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |     7.3057      |     7.98604     |     0.68034 |     ms |   +9.31% |
|                                  50th percentile service time |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |     5.18889     |     6.33525     |     1.14636 |     ms |  +22.09% |
|                                  90th percentile service time |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |     6.59799     |     7.37668     |     0.77869 |     ms |  +11.80% |
|                                 100th percentile service time |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |     7.3057      |     7.98604     |     0.68034 |     ms |   +9.31% |
|                                                    error rate |  esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |   196.153       |   190.896       |    -5.25742 |  ops/s |   -2.68% |
|                                               Mean Throughput | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |   196.153       |   190.896       |    -5.25742 |  ops/s |   -2.68% |
|                                             Median Throughput | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |   196.153       |   190.896       |    -5.25742 |  ops/s |   -2.68% |
|                                                Max Throughput | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |   196.153       |   190.896       |    -5.25742 |  ops/s |   -2.68% |
|                                       50th percentile latency | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |     4.44115     |     4.46758     |     0.02643 |     ms |   +0.60% |
|                                       90th percentile latency | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |     5.07334     |     5.12325     |     0.04991 |     ms |   +0.98% |
|                                      100th percentile latency | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |     5.75086     |     6.35572     |     0.60486 |     ms |  +10.52% |
|                                  50th percentile service time | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |     4.44115     |     4.46758     |     0.02643 |     ms |   +0.60% |
|                                  90th percentile service time | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |     5.07334     |     5.12325     |     0.04991 |     ms |   +0.98% |
|                                 100th percentile service time | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |     5.75086     |     6.35572     |     0.60486 |     ms |  +10.52% |
|                                                    error rate | esql_time_range_and_date_histogram_two_groups_post_filter_limit_0 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                           esql_dissect_duration_and_stats_limit_0 |   220.789       |   263.37        |    42.5813  |  ops/s |  +19.29% |
|                                               Mean Throughput |                           esql_dissect_duration_and_stats_limit_0 |   220.789       |   263.37        |    42.5813  |  ops/s |  +19.29% |
|                                             Median Throughput |                           esql_dissect_duration_and_stats_limit_0 |   220.789       |   263.37        |    42.5813  |  ops/s |  +19.29% |
|                                                Max Throughput |                           esql_dissect_duration_and_stats_limit_0 |   220.789       |   263.37        |    42.5813  |  ops/s |  +19.29% |
|                                       50th percentile latency |                           esql_dissect_duration_and_stats_limit_0 |     2.99662     |     2.72904     |    -0.26759 |     ms |   -8.93% |
|                                       90th percentile latency |                           esql_dissect_duration_and_stats_limit_0 |     3.64262     |     2.95774     |    -0.68488 |     ms |  -18.80% |
|                                      100th percentile latency |                           esql_dissect_duration_and_stats_limit_0 |     3.78335     |     3.77839     |    -0.00496 |     ms |   -0.13% |
|                                  50th percentile service time |                           esql_dissect_duration_and_stats_limit_0 |     2.99662     |     2.72904     |    -0.26759 |     ms |   -8.93% |
|                                  90th percentile service time |                           esql_dissect_duration_and_stats_limit_0 |     3.64262     |     2.95774     |    -0.68488 |     ms |  -18.80% |
|                                 100th percentile service time |                           esql_dissect_duration_and_stats_limit_0 |     3.78335     |     3.77839     |    -0.00496 |     ms |   -0.13% |
|                                                    error rate |                           esql_dissect_duration_and_stats_limit_0 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                          esql_basic_count_group_0 |   105.804       |   108.987       |     3.18319 |  ops/s |   +3.01% |
|                                               Mean Throughput |                                          esql_basic_count_group_0 |   105.804       |   108.987       |     3.18319 |  ops/s |   +3.01% |
|                                             Median Throughput |                                          esql_basic_count_group_0 |   105.804       |   108.987       |     3.18319 |  ops/s |   +3.01% |
|                                                Max Throughput |                                          esql_basic_count_group_0 |   105.804       |   108.987       |     3.18319 |  ops/s |   +3.01% |
|                                       50th percentile latency |                                          esql_basic_count_group_0 |     5.9989      |     5.54053     |    -0.45837 |     ms |   -7.64% |
|                                       90th percentile latency |                                          esql_basic_count_group_0 |     7.02563     |     6.50381     |    -0.52182 |     ms |   -7.43% |
|                                      100th percentile latency |                                          esql_basic_count_group_0 |    10.3056      |     8.26158     |    -2.04406 |     ms |  -19.83% |
|                                  50th percentile service time |                                          esql_basic_count_group_0 |     5.9989      |     5.54053     |    -0.45837 |     ms |   -7.64% |
|                                  90th percentile service time |                                          esql_basic_count_group_0 |     7.02563     |     6.50381     |    -0.52182 |     ms |   -7.43% |
|                                 100th percentile service time |                                          esql_basic_count_group_0 |    10.3056      |     8.26158     |    -2.04406 |     ms |  -19.83% |
|                                                    error rate |                                          esql_basic_count_group_0 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                          esql_basic_count_group_1 |     3.50178     |     3.48445     |    -0.01733 |  ops/s |   -0.49% |
|                                               Mean Throughput |                                          esql_basic_count_group_1 |     3.69501     |     3.65574     |    -0.03927 |  ops/s |   -1.06% |
|                                             Median Throughput |                                          esql_basic_count_group_1 |     3.71993     |     3.69355     |    -0.02639 |  ops/s |   -0.71% |
|                                                Max Throughput |                                          esql_basic_count_group_1 |     3.76711     |     3.74183     |    -0.02528 |  ops/s |   -0.67% |
|                                       50th percentile latency |                                          esql_basic_count_group_1 |   256.233       |   255.714       |    -0.51908 |     ms |   -0.20% |
|                                       90th percentile latency |                                          esql_basic_count_group_1 |   275.94        |   267.361       |    -8.57979 |     ms |   -3.11% |
|                                      100th percentile latency |                                          esql_basic_count_group_1 |   325.338       |   330.601       |     5.26318 |     ms |   +1.62% |
|                                  50th percentile service time |                                          esql_basic_count_group_1 |   256.233       |   255.714       |    -0.51908 |     ms |   -0.20% |
|                                  90th percentile service time |                                          esql_basic_count_group_1 |   275.94        |   267.361       |    -8.57979 |     ms |   -3.11% |
|                                 100th percentile service time |                                          esql_basic_count_group_1 |   325.338       |   330.601       |     5.26318 |     ms |   +1.62% |
|                                                    error rate |                                          esql_basic_count_group_1 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                          esql_basic_count_group_2 |     0.717578    |     0.949469    |     0.23189 |  ops/s |  +32.32% |
|                                               Mean Throughput |                                          esql_basic_count_group_2 |     0.929138    |     1.20789     |     0.27875 |  ops/s |  +30.00% |
|                                             Median Throughput |                                          esql_basic_count_group_2 |     0.959897    |     1.24725     |     0.28735 |  ops/s |  +29.94% |
|                                                Max Throughput |                                          esql_basic_count_group_2 |     1.0372      |     1.3677      |     0.33051 |  ops/s |  +31.87% |
|                                       50th percentile latency |                                          esql_basic_count_group_2 |   816.752       |   599.756       |  -216.996   |     ms |  -26.57% |
|                                       90th percentile latency |                                          esql_basic_count_group_2 |   836.76        |   621.913       |  -214.848   |     ms |  -25.68% |
|                                      100th percentile latency |                                          esql_basic_count_group_2 |   856.156       |   652.057       |  -204.099   |     ms |  -23.84% |
|                                  50th percentile service time |                                          esql_basic_count_group_2 |   816.752       |   599.756       |  -216.996   |     ms |  -26.57% |
|                                  90th percentile service time |                                          esql_basic_count_group_2 |   836.76        |   621.913       |  -214.848   |     ms |  -25.68% |
|                                 100th percentile service time |                                          esql_basic_count_group_2 |   856.156       |   652.057       |  -204.099   |     ms |  -23.84% |
|                                                    error rate |                                          esql_basic_count_group_2 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                          esql_basic_count_group_3 |     0.653512    |     0.667198    |     0.01369 |  ops/s |   +2.09% |
|                                               Mean Throughput |                                          esql_basic_count_group_3 |     0.737312    |     0.740916    |     0.0036  |  ops/s |   +0.49% |
|                                             Median Throughput |                                          esql_basic_count_group_3 |     0.74404     |     0.740858    |    -0.00318 |  ops/s |   -0.43% |
|                                                Max Throughput |                                          esql_basic_count_group_3 |     0.794971    |     0.801193    |     0.00622 |  ops/s |   +0.78% |
|                                       50th percentile latency |                                          esql_basic_count_group_3 |  1063.76        |  1060.6         |    -3.1622  |     ms |   -0.30% |
|                                       90th percentile latency |                                          esql_basic_count_group_3 |  1098.4         |  1194.6         |    96.202   |     ms |   +8.76% |
|                                      100th percentile latency |                                          esql_basic_count_group_3 |  1138.82        |  1250.51        |   111.691   |     ms |   +9.81% |
|                                  50th percentile service time |                                          esql_basic_count_group_3 |  1063.76        |  1060.6         |    -3.1622  |     ms |   -0.30% |
|                                  90th percentile service time |                                          esql_basic_count_group_3 |  1098.4         |  1194.6         |    96.202   |     ms |   +8.76% |
|                                 100th percentile service time |                                          esql_basic_count_group_3 |  1138.82        |  1250.51        |   111.691   |     ms |   +9.81% |
|                                                    error rate |                                          esql_basic_count_group_3 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                          esql_basic_count_group_4 |     0.388128    |     0.370504    |    -0.01762 |  ops/s |   -4.54% |
|                                               Mean Throughput |                                          esql_basic_count_group_4 |     0.393843    |     0.37975     |    -0.01409 |  ops/s |   -3.58% |
|                                             Median Throughput |                                          esql_basic_count_group_4 |     0.393977    |     0.380753    |    -0.01322 |  ops/s |   -3.36% |
|                                                Max Throughput |                                          esql_basic_count_group_4 |     0.397817    |     0.385452    |    -0.01237 |  ops/s |   -3.11% |
|                                       50th percentile latency |                                          esql_basic_count_group_4 |  2464.24        |  2525.87        |    61.6293  |     ms |   +2.50% |
|                                       90th percentile latency |                                          esql_basic_count_group_4 |  2512.09        |  2543.4         |    31.3031  |     ms |   +1.25% |
|                                      100th percentile latency |                                          esql_basic_count_group_4 |  2531.24        |  2589.1         |    57.8565  |     ms |   +2.29% |
|                                  50th percentile service time |                                          esql_basic_count_group_4 |  2464.24        |  2525.87        |    61.6293  |     ms |   +2.50% |
|                                  90th percentile service time |                                          esql_basic_count_group_4 |  2512.09        |  2543.4         |    31.3031  |     ms |   +1.25% |
|                                 100th percentile service time |                                          esql_basic_count_group_4 |  2531.24        |  2589.1         |    57.8565  |     ms |   +2.29% |
|                                                    error rate |                                          esql_basic_count_group_4 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |          esql_time_range_and_date_histogram_two_groups_pre_filter |     3.16608     |     2.79952     |    -0.36656 |  ops/s |  -11.58% |
|                                               Mean Throughput |          esql_time_range_and_date_histogram_two_groups_pre_filter |     3.58327     |     3.29433     |    -0.28893 |  ops/s |   -8.06% |
|                                             Median Throughput |          esql_time_range_and_date_histogram_two_groups_pre_filter |     3.62416     |     3.37227     |    -0.25188 |  ops/s |   -6.95% |
|                                                Max Throughput |          esql_time_range_and_date_histogram_two_groups_pre_filter |     3.91867     |     3.63326     |    -0.28541 |  ops/s |   -7.28% |
|                                       50th percentile latency |          esql_time_range_and_date_histogram_two_groups_pre_filter |   211.491       |   211.125       |    -0.36607 |     ms |   -0.17% |
|                                       90th percentile latency |          esql_time_range_and_date_histogram_two_groups_pre_filter |   230.639       |   238.676       |     8.03737 |     ms |   +3.48% |
|                                      100th percentile latency |          esql_time_range_and_date_histogram_two_groups_pre_filter |   230.97        |   279.812       |    48.8424  |     ms |  +21.15% |
|                                  50th percentile service time |          esql_time_range_and_date_histogram_two_groups_pre_filter |   211.491       |   211.125       |    -0.36607 |     ms |   -0.17% |
|                                  90th percentile service time |          esql_time_range_and_date_histogram_two_groups_pre_filter |   230.639       |   238.676       |     8.03737 |     ms |   +3.48% |
|                                 100th percentile service time |          esql_time_range_and_date_histogram_two_groups_pre_filter |   230.97        |   279.812       |    48.8424  |     ms |  +21.15% |
|                                                    error rate |          esql_time_range_and_date_histogram_two_groups_pre_filter |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |         esql_time_range_and_date_histogram_two_groups_post_filter |     0.286551    |     0.2793      |    -0.00725 |  ops/s |   -2.53% |
|                                               Mean Throughput |         esql_time_range_and_date_histogram_two_groups_post_filter |     0.293485    |     0.284697    |    -0.00879 |  ops/s |   -2.99% |
|                                             Median Throughput |         esql_time_range_and_date_histogram_two_groups_post_filter |     0.294446    |     0.285165    |    -0.00928 |  ops/s |   -3.15% |
|                                                Max Throughput |         esql_time_range_and_date_histogram_two_groups_post_filter |     0.296506    |     0.2873      |    -0.00921 |  ops/s |   -3.10% |
|                                       50th percentile latency |         esql_time_range_and_date_histogram_two_groups_post_filter |  3331.45        |  3446.36        |   114.906   |     ms |   +3.45% |
|                                       90th percentile latency |         esql_time_range_and_date_histogram_two_groups_post_filter |  3377.84        |  3485.71        |   107.87    |     ms |   +3.19% |
|                                      100th percentile latency |         esql_time_range_and_date_histogram_two_groups_post_filter |  3389.44        |  3489.41        |    99.9639  |     ms |   +2.95% |
|                                  50th percentile service time |         esql_time_range_and_date_histogram_two_groups_post_filter |  3331.45        |  3446.36        |   114.906   |     ms |   +3.45% |
|                                  90th percentile service time |         esql_time_range_and_date_histogram_two_groups_post_filter |  3377.84        |  3485.71        |   107.87    |     ms |   +3.19% |
|                                 100th percentile service time |         esql_time_range_and_date_histogram_two_groups_post_filter |  3389.44        |  3489.41        |    99.9639  |     ms |   +2.95% |
|                                                    error rate |         esql_time_range_and_date_histogram_two_groups_post_filter |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                   esql_dissect_duration_and_stats |     5.95045     |     6.87019     |     0.91973 |  ops/s |  +15.46% |
|                                               Mean Throughput |                                   esql_dissect_duration_and_stats |     5.95045     |     6.87019     |     0.91973 |  ops/s |  +15.46% |
|                                             Median Throughput |                                   esql_dissect_duration_and_stats |     5.95045     |     6.87019     |     0.91973 |  ops/s |  +15.46% |
|                                                Max Throughput |                                   esql_dissect_duration_and_stats |     5.95045     |     6.87019     |     0.91973 |  ops/s |  +15.46% |
|                                       50th percentile latency |                                   esql_dissect_duration_and_stats |    71.3223      |    69.1641      |    -2.15816 |     ms |   -3.03% |
|                                       90th percentile latency |                                   esql_dissect_duration_and_stats |    83.7442      |    75.0953      |    -8.64889 |     ms |  -10.33% |
|                                      100th percentile latency |                                   esql_dissect_duration_and_stats |   106.985       |    81.6269      |   -25.358   |     ms |  -23.70% |
|                                  50th percentile service time |                                   esql_dissect_duration_and_stats |    71.3223      |    69.1641      |    -2.15816 |     ms |   -3.03% |
|                                  90th percentile service time |                                   esql_dissect_duration_and_stats |    83.7442      |    75.0953      |    -8.64889 |     ms |  -10.33% |
|                                 100th percentile service time |                                   esql_dissect_duration_and_stats |   106.985       |    81.6269      |   -25.358   |     ms |  -23.70% |
|                                                    error rate |                                   esql_dissect_duration_and_stats |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                           term_query_with_matches |    15.6339      |    14.812       |    -0.82194 |  ops/s |   -5.26% |
|                                               Mean Throughput |                                           term_query_with_matches |    15.924       |    16.6524      |     0.72835 |  ops/s |   +4.57% |
|                                             Median Throughput |                                           term_query_with_matches |    15.924       |    17.5243      |     1.60029 |  ops/s |  +10.05% |
|                                                Max Throughput |                                           term_query_with_matches |    16.2142      |    17.6209      |     1.4067  |  ops/s |   +8.68% |
|                                       50th percentile latency |                                           term_query_with_matches |     8.22524     |    53.881       |    45.6557  |     ms | +555.07% |
|                                       90th percentile latency |                                           term_query_with_matches |    86.9916      |    90.1282      |     3.13666 |     ms |   +3.61% |
|                                      100th percentile latency |                                           term_query_with_matches |   130.961       |    91.0887      |   -39.8723  |     ms |  -30.45% |
|                                  50th percentile service time |                                           term_query_with_matches |     8.22524     |    53.881       |    45.6557  |     ms | +555.07% |
|                                  90th percentile service time |                                           term_query_with_matches |    86.9916      |    90.1282      |     3.13666 |     ms |   +3.61% |
|                                 100th percentile service time |                                           term_query_with_matches |   130.961       |    91.0887      |   -39.8723  |     ms |  -30.45% |
|                                                    error rate |                                           term_query_with_matches |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                  term_query_with_matches_argument |    75.3953      |    16.8185      |   -58.5768  |  ops/s |  -77.69% |
|                                               Mean Throughput |                                  term_query_with_matches_argument |    75.3953      |    16.9451      |   -58.4502  |  ops/s |  -77.53% |
|                                             Median Throughput |                                  term_query_with_matches_argument |    75.3953      |    16.9729      |   -58.4224  |  ops/s |  -77.49% |
|                                                Max Throughput |                                  term_query_with_matches_argument |    75.3953      |    17.0438      |   -58.3515  |  ops/s |  -77.39% |
|                                       50th percentile latency |                                  term_query_with_matches_argument |    11.2118      |    58.8198      |    47.608   |     ms | +424.63% |
|                                       90th percentile latency |                                  term_query_with_matches_argument |    11.9074      |    60.827       |    48.9196  |     ms | +410.83% |
|                                      100th percentile latency |                                  term_query_with_matches_argument |    13.7715      |    66.9323      |    53.1608  |     ms | +386.02% |
|                                  50th percentile service time |                                  term_query_with_matches_argument |    11.2118      |    58.8198      |    47.608   |     ms | +424.63% |
|                                  90th percentile service time |                                  term_query_with_matches_argument |    11.9074      |    60.827       |    48.9196  |     ms | +410.83% |
|                                 100th percentile service time |                                  term_query_with_matches_argument |    13.7715      |    66.9323      |    53.1608  |     ms | +386.02% |
|                                                    error rate |                                  term_query_with_matches_argument |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                    term_query_empty_template_term |   169.202       |   177.604       |     8.40207 |  ops/s |   +4.97% |
|                                               Mean Throughput |                                    term_query_empty_template_term |   169.202       |   177.604       |     8.40207 |  ops/s |   +4.97% |
|                                             Median Throughput |                                    term_query_empty_template_term |   169.202       |   177.604       |     8.40207 |  ops/s |   +4.97% |
|                                                Max Throughput |                                    term_query_empty_template_term |   169.202       |   177.604       |     8.40207 |  ops/s |   +4.97% |
|                                       50th percentile latency |                                    term_query_empty_template_term |     4.56075     |     4.22036     |    -0.34039 |     ms |   -7.46% |
|                                       90th percentile latency |                                    term_query_empty_template_term |     4.88518     |     4.67337     |    -0.21181 |     ms |   -4.34% |
|                                      100th percentile latency |                                    term_query_empty_template_term |     5.30121     |     4.99833     |    -0.30288 |     ms |   -5.71% |
|                                  50th percentile service time |                                    term_query_empty_template_term |     4.56075     |     4.22036     |    -0.34039 |     ms |   -7.46% |
|                                  90th percentile service time |                                    term_query_empty_template_term |     4.88518     |     4.67337     |    -0.21181 |     ms |   -4.34% |
|                                 100th percentile service time |                                    term_query_empty_template_term |     5.30121     |     4.99833     |    -0.30288 |     ms |   -5.71% |
|                                                    error rate |                                    term_query_empty_template_term |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                    term_query_empty_argument_term |   169.439       |   169.91        |     0.47064 |  ops/s |   +0.28% |
|                                               Mean Throughput |                                    term_query_empty_argument_term |   169.439       |   169.91        |     0.47064 |  ops/s |   +0.28% |
|                                             Median Throughput |                                    term_query_empty_argument_term |   169.439       |   169.91        |     0.47064 |  ops/s |   +0.28% |
|                                                Max Throughput |                                    term_query_empty_argument_term |   169.439       |   169.91        |     0.47064 |  ops/s |   +0.28% |
|                                       50th percentile latency |                                    term_query_empty_argument_term |     4.26421     |     4.2997      |     0.03549 |     ms |   +0.83% |
|                                       90th percentile latency |                                    term_query_empty_argument_term |     4.79971     |     4.92033     |     0.12062 |     ms |   +2.51% |
|                                      100th percentile latency |                                    term_query_empty_argument_term |     5.32893     |     5.22038     |    -0.10855 |     ms |   -2.04% |
|                                  50th percentile service time |                                    term_query_empty_argument_term |     4.26421     |     4.2997      |     0.03549 |     ms |   +0.83% |
|                                  90th percentile service time |                                    term_query_empty_argument_term |     4.79971     |     4.92033     |     0.12062 |     ms |   +2.51% |
|                                 100th percentile service time |                                    term_query_empty_argument_term |     5.32893     |     5.22038     |    -0.10855 |     ms |   -2.04% |
|                                                    error rate |                                    term_query_empty_argument_term |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |              phrase_query_with_matches_template_many_term_matches |     6.23607     |     5.38137     |    -0.8547  |  ops/s |  -13.71% |
|                                               Mean Throughput |              phrase_query_with_matches_template_many_term_matches |     6.51554     |     6.46038     |    -0.05516 |  ops/s |   -0.85% |
|                                             Median Throughput |              phrase_query_with_matches_template_many_term_matches |     6.51554     |     6.72502     |     0.20947 |  ops/s |   +3.21% |
|                                                Max Throughput |              phrase_query_with_matches_template_many_term_matches |     6.79502     |     7.27476     |     0.47974 |  ops/s |   +7.06% |
|                                       50th percentile latency |              phrase_query_with_matches_template_many_term_matches |   122.431       |   116.244       |    -6.18764 |     ms |   -5.05% |
|                                       90th percentile latency |              phrase_query_with_matches_template_many_term_matches |   136.108       |   120.6         |   -15.5079  |     ms |  -11.39% |
|                                      100th percentile latency |              phrase_query_with_matches_template_many_term_matches |   163.5         |   129.943       |   -33.5574  |     ms |  -20.52% |
|                                  50th percentile service time |              phrase_query_with_matches_template_many_term_matches |   122.431       |   116.244       |    -6.18764 |     ms |   -5.05% |
|                                  90th percentile service time |              phrase_query_with_matches_template_many_term_matches |   136.108       |   120.6         |   -15.5079  |     ms |  -11.39% |
|                                 100th percentile service time |              phrase_query_with_matches_template_many_term_matches |   163.5         |   129.943       |   -33.5574  |     ms |  -20.52% |
|                                                    error rate |              phrase_query_with_matches_template_many_term_matches |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                   phrase_query_with_matches_argument_and_template |     4.8035      |     4.9052      |     0.10171 |  ops/s |   +2.12% |
|                                               Mean Throughput |                   phrase_query_with_matches_argument_and_template |     4.86508     |     4.94914     |     0.08405 |  ops/s |   +1.73% |
|                                             Median Throughput |                   phrase_query_with_matches_argument_and_template |     4.87436     |     4.94876     |     0.0744  |  ops/s |   +1.53% |
|                                                Max Throughput |                   phrase_query_with_matches_argument_and_template |     4.90811     |     4.99382     |     0.08571 |  ops/s |   +1.75% |
|                                       50th percentile latency |                   phrase_query_with_matches_argument_and_template |   199.246       |   194.147       |    -5.09907 |     ms |   -2.56% |
|                                       90th percentile latency |                   phrase_query_with_matches_argument_and_template |   200.605       |   202.279       |     1.67375 |     ms |   +0.83% |
|                                      100th percentile latency |                   phrase_query_with_matches_argument_and_template |   200.935       |   211.341       |    10.4064  |     ms |   +5.18% |
|                                  50th percentile service time |                   phrase_query_with_matches_argument_and_template |   199.246       |   194.147       |    -5.09907 |     ms |   -2.56% |
|                                  90th percentile service time |                   phrase_query_with_matches_argument_and_template |   200.605       |   202.279       |     1.67375 |     ms |   +0.83% |
|                                 100th percentile service time |                   phrase_query_with_matches_argument_and_template |   200.935       |   211.341       |    10.4064  |     ms |   +5.18% |
|                                                    error rate |                   phrase_query_with_matches_argument_and_template |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                              phrase_query_empty_with_term_matches |    12.1875      |    12.8056      |     0.61805 |  ops/s |   +5.07% |
|                                               Mean Throughput |                              phrase_query_empty_with_term_matches |    12.1875      |    12.8056      |     0.61805 |  ops/s |   +5.07% |
|                                             Median Throughput |                              phrase_query_empty_with_term_matches |    12.1875      |    12.8056      |     0.61805 |  ops/s |   +5.07% |
|                                                Max Throughput |                              phrase_query_empty_with_term_matches |    12.1875      |    12.8056      |     0.61805 |  ops/s |   +5.07% |
|                                       50th percentile latency |                              phrase_query_empty_with_term_matches |    75.728       |    74.4698      |    -1.25813 |     ms |   -1.66% |
|                                       90th percentile latency |                              phrase_query_empty_with_term_matches |    77.1289      |    76.7656      |    -0.3633  |     ms |   -0.47% |
|                                      100th percentile latency |                              phrase_query_empty_with_term_matches |    81.1842      |    79.476       |    -1.70816 |     ms |   -2.10% |
|                                  50th percentile service time |                              phrase_query_empty_with_term_matches |    75.728       |    74.4698      |    -1.25813 |     ms |   -1.66% |
|                                  90th percentile service time |                              phrase_query_empty_with_term_matches |    77.1289      |    76.7656      |    -0.3633  |     ms |   -0.47% |
|                                 100th percentile service time |                              phrase_query_empty_with_term_matches |    81.1842      |    79.476       |    -1.70816 |     ms |   -2.10% |
|                                                    error rate |                              phrase_query_empty_with_term_matches |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                        search_basic_count_group_0 |     1.97993     |     3.863       |     1.88306 |  ops/s |  +95.11% |
|                                               Mean Throughput |                                        search_basic_count_group_0 |     2.16393     |     4.01192     |     1.84799 |  ops/s |  +85.40% |
|                                             Median Throughput |                                        search_basic_count_group_0 |     2.19109     |     4.03699     |     1.8459  |  ops/s |  +84.25% |
|                                                Max Throughput |                                        search_basic_count_group_0 |     2.22031     |     4.0627      |     1.84239 |  ops/s |  +82.98% |
|                                       50th percentile latency |                                        search_basic_count_group_0 |   429.25        |   243.543       |  -185.708   |     ms |  -43.26% |
|                                       90th percentile latency |                                        search_basic_count_group_0 |   457.754       |   254.596       |  -203.158   |     ms |  -44.38% |
|                                      100th percentile latency |                                        search_basic_count_group_0 |   497.483       |   384.378       |  -113.105   |     ms |  -22.74% |
|                                  50th percentile service time |                                        search_basic_count_group_0 |   429.25        |   243.543       |  -185.708   |     ms |  -43.26% |
|                                  90th percentile service time |                                        search_basic_count_group_0 |   457.754       |   254.596       |  -203.158   |     ms |  -44.38% |
|                                 100th percentile service time |                                        search_basic_count_group_0 |   497.483       |   384.378       |  -113.105   |     ms |  -22.74% |
|                                                    error rate |                                        search_basic_count_group_0 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                        search_basic_count_group_1 |   358.335       |   354.105       |    -4.2298  |  ops/s |   -1.18% |
|                                               Mean Throughput |                                        search_basic_count_group_1 |   358.335       |   354.105       |    -4.2298  |  ops/s |   -1.18% |
|                                             Median Throughput |                                        search_basic_count_group_1 |   358.335       |   354.105       |    -4.2298  |  ops/s |   -1.18% |
|                                                Max Throughput |                                        search_basic_count_group_1 |   358.335       |   354.105       |    -4.2298  |  ops/s |   -1.18% |
|                                       50th percentile latency |                                        search_basic_count_group_1 |     2.0833      |     2.12248     |     0.03918 |     ms |   +1.88% |
|                                       90th percentile latency |                                        search_basic_count_group_1 |     2.30975     |     2.49982     |     0.19008 |     ms |   +8.23% |
|                                      100th percentile latency |                                        search_basic_count_group_1 |     2.63654     |     2.79004     |     0.1535  |     ms |   +5.82% |
|                                  50th percentile service time |                                        search_basic_count_group_1 |     2.0833      |     2.12248     |     0.03918 |     ms |   +1.88% |
|                                  90th percentile service time |                                        search_basic_count_group_1 |     2.30975     |     2.49982     |     0.19008 |     ms |   +8.23% |
|                                 100th percentile service time |                                        search_basic_count_group_1 |     2.63654     |     2.79004     |     0.1535  |     ms |   +5.82% |
|                                                    error rate |                                        search_basic_count_group_1 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                        search_basic_count_group_2 |     0.139024    |     0.156784    |     0.01776 |  ops/s |  +12.77% |
|                                               Mean Throughput |                                        search_basic_count_group_2 |     0.140024    |     0.158029    |     0.018   |  ops/s |  +12.86% |
|                                             Median Throughput |                                        search_basic_count_group_2 |     0.140054    |     0.158429    |     0.01838 |  ops/s |  +13.12% |
|                                                Max Throughput |                                        search_basic_count_group_2 |     0.141099    |     0.158706    |     0.01761 |  ops/s |  +12.48% |
|                                       50th percentile latency |                                        search_basic_count_group_2 |  6996.69        |  6251.81        |  -744.881   |     ms |  -10.65% |
|                                      100th percentile latency |                                        search_basic_count_group_2 |  7363.4         |  6290.76        | -1072.64    |     ms |  -14.57% |
|                                  50th percentile service time |                                        search_basic_count_group_2 |  6996.69        |  6251.81        |  -744.881   |     ms |  -10.65% |
|                                 100th percentile service time |                                        search_basic_count_group_2 |  7363.4         |  6290.76        | -1072.64    |     ms |  -14.57% |
|                                                    error rate |                                        search_basic_count_group_2 |     0           |     0           |     0       |      % |    0.00% |
|                                                Min Throughput |                                        search_basic_count_group_3 |     0.101608    |     0.116565    |     0.01496 |  ops/s |  +14.72% |
|                                               Mean Throughput |                                        search_basic_count_group_3 |     0.102138    |     0.116779    |     0.01464 |  ops/s |  +14.34% |
|                                             Median Throughput |                                        search_basic_count_group_3 |     0.102392    |     0.116859    |     0.01447 |  ops/s |  +14.13% |
|                                                Max Throughput |                                        search_basic_count_group_3 |     0.102414    |     0.116915    |     0.0145  |  ops/s |  +14.16% |
|                                       50th percentile latency |                                        search_basic_count_group_3 |  9907.14        |  8540.38        | -1366.76    |     ms |  -13.80% |
|                                      100th percentile latency |                                        search_basic_count_group_3 | 10073.7         |  8631.92        | -1441.8     |     ms |  -14.31% |
|                                  50th percentile service time |                                        search_basic_count_group_3 |  9907.14        |  8540.38        | -1366.76    |     ms |  -13.80% |
|                                 100th percentile service time |                                        search_basic_count_group_3 | 10073.7         |  8631.92        | -1441.8     |     ms |  -14.31% |
|                                                    error rate |                                        search_basic_count_group_3 |     0           |     0           |     0       |      % |    0.00% |
|                                       50th percentile latency |                                        search_basic_count_group_4 | 10999.4         | 10999           |    -0.3418  |     ms |   -0.00% |
|                                      100th percentile latency |                                        search_basic_count_group_4 | 11000.4         | 11000.5         |     0.04785 |     ms |    0.00% |
|                                  50th percentile service time |                                        search_basic_count_group_4 | 10999.4         | 10999           |    -0.3418  |     ms |   -0.00% |
|                                 100th percentile service time |                                        search_basic_count_group_4 | 11000.4         | 11000.5         |     0.04785 |     ms |    0.00% |
|                                                    error rate |                                        search_basic_count_group_4 |   100           |   100           |     0       |      % |    0.00% |

