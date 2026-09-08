# Baseline Benchmark Results

## Test Configuration

- Endpoint: `/hello`
- HTTP method: GET
- Duration: 20 seconds
- Load generator: Autocannon
- Application: FastAPI
- Server: Uvicorn
- Workers: 1

---

## 1. Localhost Baseline

| Concurrency | Avg RPS | Avg Latency | P50 | P97.5 | P99 | Max |
|---:|---:|---:|---:|---:|---:|---:|
| 10 | 1467.35 | 6.32 ms | 6 ms | 12 ms | 17 ms | 60 ms |
| 25 | 1624.10 | 14.90 ms | 14 ms | 28 ms | 32 ms | 73 ms |
| 50 | 1491.70 | 32.99 ms | 31 ms | 53 ms | 58 ms | 132 ms |
| 100 | 1566.85 | 63.23 ms | 60 ms | 96 ms | 115 ms | 140 ms |
| 200 | 1285.80 | 154.74 ms | 154 ms | 219 ms | 239 ms | 728 ms |

---

## 2. AWS EC2 Baseline

### Environment

- Instance: `t3.micro`
- vCPU: 2
- RAM: ~913 MiB
- OS: Amazon Linux 2023
- Python: 3.9.25
- Uvicorn workers: 1

| Concurrency | Avg RPS | Avg Latency | P50 | P97.5 | P99 | Max |
|---:|---:|---:|---:|---:|---:|---:|
| 10 | 240.35 | 41.11 ms | 39 ms | 69 ms | 87 ms | 311 ms |
| 25 | 596.15 | 41.46 ms | 39 ms | 61 ms | 71 ms | 306 ms |
| 50 | 953.55 | 51.96 ms | 46 ms | 105 ms | 128 ms | 387 ms |
| 100 | — | — | — | — | — | — |
| 200 | 1366.50 | 146.17 ms | 108 ms | 475 ms | 958 ms | 2138 ms |

### CPU observations

| Concurrency | Uvicorn CPU observed |
|---:|---:|
| 10 | ~19% |
| 50 | ~61–62% |
| 100 | ~78–97% |
| 200 | ~96% |

> CPU values are observed samples from `pidstat`, not averages over the complete benchmark.

---

## Observations

### Localhost

Throughput remained around 1.3–1.6K RPS, while latency increased substantially as concurrency increased.

### EC2

Throughput increased as concurrency increased, reaching 1366.5 RPS at 200 concurrent connections. However, tail latency increased sharply.

At 200 concurrency:

- P99 latency: 958 ms
- Maximum latency: 2138 ms
- Uvicorn CPU: observed up to ~96%

This indicates that the single-worker configuration was entering a highly stressed region.

## Important limitation

The localhost and EC2 results are not directly equivalent.

The EC2 test includes network communication between the load generator and the cloud instance, while the localhost test does not.

Therefore, these results should be used to understand system behavior rather than as a direct hardware-for-hardware comparison.