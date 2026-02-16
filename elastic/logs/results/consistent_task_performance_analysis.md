# Consistent Task Performance Analysis Across Three Comparisons

This document identifies tasks that show **consistently different behavior** (either degraded or improved) across all three benchmark comparisons, excluding 90th percentile or higher metrics and Min/Max values.

## Comparison Overview
- **Comparison 1**: baseline vs date_nanos (Oct 27)
- **Comparison 2**: baseline vs date_nanos (Oct 27, different times)
- **Comparison 3**: baseline vs date_nanos (Oct 28)

---

## 🔴 TASKS WITH CONSISTENT PERFORMANCE DEGRADATION (Contender Worse)

### 1. **esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0**
**Consistently shows throughput decrease and latency increase across all comparisons**

| Metric | Comp 1 | Comp 2 | Comp 3 |
|--------|--------|--------|--------|
| **Mean Throughput** (ops/s) | **-7.47%** | **-9.20%** | **-17.89%** |
| **50th percentile latency** (ms) | **+8.43%** | **+10.64%** | **+22.09%** |

**Baseline Throughput**: ~105-122 ops/s  
**Contender Throughput**: ~97-100 ops/s  
**Conclusion**: The contender consistently reduces throughput by 7-18% and increases latency by 8-22%.

---

### 2. **esql_basic_count_group_0_limit_0**
**Consistently shows throughput decrease**

| Metric | Comp 1 | Comp 2 | Comp 3 |
|--------|--------|--------|--------|
| **Mean Throughput** (ops/s) | **-9.24%** | **+36.61%** | **-7.00%** |
| **50th percentile latency** (ms) | **+5.19%** | **-10.12%** | **+15.66%** |

**Note**: Comparison 2 shows opposite behavior - this task is NOT consistently degraded.

---

### 3. **esql_basic_count_group_1_limit_0**
**Consistently shows throughput decrease and latency increase across all comparisons**

| Metric | Comp 1 | Comp 2 | Comp 3 |
|--------|--------|--------|--------|
| **Mean Throughput** (ops/s) | **-7.10%** | **-12.11%** | **-12.71%** |
| **50th percentile latency** (ms) | **+7.04%** | **+17.37%** | **+26.67%** |

**Baseline Throughput**: ~208-216 ops/s  
**Contender Throughput**: ~187-194 ops/s  
**Conclusion**: The contender consistently reduces throughput by 7-13% and increases latency by 7-27%.

---

### 4. **esql_basic_count_group_2_limit_0**
**Consistently shows throughput decrease and latency increase across all comparisons**

| Metric | Comp 1 | Comp 2 | Comp 3 |
|--------|--------|--------|--------|
| **Mean Throughput** (ops/s) | **-15.76%** | **-4.59%** | **-3.10%** |
| **50th percentile latency** (ms) | **+19.61%** | **+3.53%** | **+7.54%** |

**Baseline Throughput**: ~250-264 ops/s  
**Contender Throughput**: ~211-256 ops/s  
**Conclusion**: The contender consistently reduces throughput by 3-16% and increases latency by 4-20%.

---

### 5. **esql_basic_count_group_3_limit_0**
**Consistently shows throughput decrease and latency increase across all comparisons**

| Metric | Comp 1 | Comp 2 | Comp 3 |
|--------|--------|--------|--------|
| **Mean Throughput** (ops/s) | **-14.95%** | **-3.88%** | **-11.57%** |
| **50th percentile latency** (ms) | **+18.40%** | **+4.76%** | **+17.56%** |

**Baseline Throughput**: ~231-294 ops/s  
**Contender Throughput**: ~222-260 ops/s  
**Conclusion**: The contender consistently reduces throughput by 4-15% and increases latency by 5-18%.

---

### 6. **esql_basic_count_group_4_limit_0**
**Shows mixed results - NOT consistently degraded**

| Metric | Comp 1 | Comp 2 | Comp 3 |
|--------|--------|--------|--------|
| **Mean Throughput** (ops/s) | **-12.95%** | **+21.38%** | **-11.65%** |
| **50th percentile latency** (ms) | **+20.50%** | **-10.02%** | **-2.70%** |

**Note**: Comparison 2 shows significant improvement - this task is NOT consistently degraded.

---

### 7. **esql_basic_count_group_1** (without limit_0)
**Consistently shows throughput decrease across all comparisons**

| Metric | Comp 1 | Comp 2 | Comp 3 |
|--------|--------|--------|--------|
| **Mean Throughput** (ops/s) | **-4.63%** | **-3.51%** | **-1.06%** |
| **50th percentile latency** (ms) | **+10.85%** | **+1.82%** | **-0.20%** |

**Baseline Throughput**: ~3.5-3.7 ops/s  
**Contender Throughput**: ~3.4-3.7 ops/s  
**Conclusion**: The contender consistently reduces throughput by 1-5%.

---

### 8. **term_query_with_matches_argument**
**Shows extremely inconsistent behavior - NOT reliably degraded**

| Metric | Comp 1 | Comp 2 | Comp 3 |
|--------|--------|--------|--------|
| **Mean Throughput** (ops/s) | **+314.94%** | **-14.59%** | **-77.53%** |
| **50th percentile latency** (ms) | **-80.72%** | **+24.08%** | **+424.63%** |

**Note**: Wildly inconsistent results - NOT a consistent pattern.

---

### 9. **esql_time_range_and_date_histogram_two_groups_pre_filter** (without limit_0)
**Consistently shows throughput decrease**

| Metric | Comp 1 | Comp 2 | Comp 3 |
|--------|--------|--------|--------|
| **Mean Throughput** (ops/s) | **-1.98%** | **+6.37%** | **-8.06%** |
| **50th percentile latency** (ms) | **+6.98%** | **+1.13%** | **-0.17%** |

**Note**: Mixed results - NOT consistently degraded.

---

### 10. **esql_time_range_and_date_histogram_two_groups_post_filter** (without limit_0)
**Consistently shows throughput decrease and latency increase**

| Metric | Comp 1 | Comp 2 | Comp 3 |
|--------|--------|--------|--------|
| **Mean Throughput** (ops/s) | **-4.86%** | **-3.87%** | **-2.99%** |
| **50th percentile latency** (ms) | **+3.91%** | **+6.11%** | **+3.45%** |

**Baseline Throughput**: ~0.29-0.32 ops/s  
**Contender Throughput**: ~0.28-0.29 ops/s  
**Conclusion**: The contender consistently reduces throughput by 3-5% and increases latency by 3-6%.

---

## 🟢 TASKS WITH CONSISTENT PERFORMANCE IMPROVEMENT (Contender Better)

### 1. **esql_time_range_and_date_histogram_two_groups_post_filter_limit_0**
**Consistently shows throughput increase and latency decrease (or near-zero) across all comparisons**

| Metric | Comp 1 | Comp 2 | Comp 3 |
|--------|--------|--------|--------|
| **Mean Throughput** (ops/s) | **+0.90%** | **+12.10%** | **-2.68%** |
| **50th percentile latency** (ms) | **-1.18%** | **-15.53%** | **+0.60%** |

**Note**: Mixed results - NOT consistently improved.

---

### 2. **esql_dissect_duration_and_stats_limit_0**
**Shows very mixed results - NOT consistently improved**

| Metric | Comp 1 | Comp 2 | Comp 3 |
|--------|--------|--------|--------|
| **Mean Throughput** (ops/s) | **+3.37%** | **+2.35%** | **+19.29%** |
| **50th percentile latency** (ms) | **-0.43%** | **-5.34%** | **-8.93%** |

**Note**: Comparison 3 shows very large improvement - inconsistent.

---

### 3. **esql_basic_count_group_0** (without limit_0)
**Consistently shows small throughput increase**

| Metric | Comp 1 | Comp 2 | Comp 3 |
|--------|--------|--------|--------|
| **Mean Throughput** (ops/s) | **+0.75%** | **+3.72%** | **+3.01%** |
| **50th percentile latency** (ms) | **-5.78%** | **-13.33%** | **-7.64%** |

**Baseline Throughput**: ~100-107 ops/s  
**Contender Throughput**: ~101-111 ops/s  
**Conclusion**: The contender consistently increases throughput by 1-4% and reduces latency by 6-13%.

---

### 4. **esql_basic_count_group_2** (without limit_0)
**Consistently shows throughput increase**

| Metric | Comp 1 | Comp 2 | Comp 3 |
|--------|--------|--------|--------|
| **Mean Throughput** (ops/s) | **-3.71%** | **+6.01%** | **+30.00%** |
| **50th percentile latency** (ms) | **+0.11%** | **+3.28%** | **-26.57%** |

**Note**: Mixed results with Comparison 3 showing very large improvement - NOT consistently improved.

---

### 5. **esql_dissect_duration_and_stats** (without limit_0)
**Shows very mixed results**

| Metric | Comp 1 | Comp 2 | Comp 3 |
|--------|--------|--------|--------|
| **Mean Throughput** (ops/s) | **+1.79%** | **+69.77%** | **+15.46%** |
| **50th percentile latency** (ms) | **-0.22%** | **-0.90%** | **-3.03%** |

**Note**: Comparison 2 shows massive improvement - inconsistent pattern.

---

### 6. **search_basic_count_group_0**
**Shows very mixed results**

| Metric | Comp 1 | Comp 2 | Comp 3 |
|--------|--------|--------|--------|
| **Mean Throughput** (ops/s) | **+1.05%** | **-29.29%** | **+85.40%** |
| **50th percentile latency** (ms) | **-0.38%** | **+46.76%** | **-43.26%** |

**Note**: Wildly inconsistent - NOT a consistent pattern.

---

## ⚠️ SUMMARY: CONSISTENTLY DEGRADED TASKS

Based on the analysis, the following tasks show **consistent performance degradation** across all three comparisons:

### Tier 1: Most Consistent Degradation
1. **esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0**
   - Throughput: -7% to -18%
   - Latency: +8% to +22%

2. **esql_basic_count_group_1_limit_0**
   - Throughput: -7% to -13%
   - Latency: +7% to +27%

3. **esql_basic_count_group_2_limit_0**
   - Throughput: -3% to -16%
   - Latency: +4% to +20%

4. **esql_basic_count_group_3_limit_0**
   - Throughput: -4% to -15%
   - Latency: +5% to +18%

### Tier 2: Moderate Consistent Degradation
5. **esql_time_range_and_date_histogram_two_groups_post_filter** (without limit_0)
   - Throughput: -3% to -5%
   - Latency: +3% to +6%

6. **esql_basic_count_group_1** (without limit_0)
   - Throughput: -1% to -5%
   - Latency: mixed

## ✅ CONSISTENTLY IMPROVED TASK

Only one task shows consistent improvement:

1. **esql_basic_count_group_0** (without limit_0)
   - Throughput: +1% to +4%
   - Latency: -6% to -13%

---

## 🎯 KEY FINDING

**The contender (`date_nanos`) shows consistent performance overhead for ES|QL queries with date histogram and grouping operations, particularly those with limit=0.** 

The pattern is clear: ES|QL queries that perform:
- Time range filters + date histograms with grouping (`esql_time_range_and_date_histogram_two_groups_pre_filter_limit_0`)
- Basic count operations with 1-3 groups and limit=0 (`esql_basic_count_group_1/2/3_limit_0`)

These queries consistently show 3-18% throughput reduction and 4-27% latency increase when using `date_nanos` compared to `date`.

