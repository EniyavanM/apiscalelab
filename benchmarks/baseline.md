# Experiment 1 — Baseline API Performance

## Objective

Measure how the baseline FastAPI `/hello` endpoint behaves as concurrent
request load increases.

## Environment

- Application: FastAPI
- Server: Uvicorn
- Endpoint: `GET /hello`
- Workers: 1
- Database: None
- Cache: None
- Load testing tool: Autocannon
- Test duration: 20 seconds
- Test environment: Local Windows machine

## Results

| Concurrency | Avg RPS | Avg Latency | P50 | P97.5 | P99 | Max |
|---:|---:|---:|---:|---:|---:|---:|
| 10 | 1467.35 | 6.32 ms | 6 ms | 12 ms | 17 ms | 60 ms |
| 25 | 1624.10 | 14.90 ms | 14 ms | 28 ms | 32 ms | 73 ms |
| 50 | 1491.70 | 32.99 ms | 31 ms | 53 ms | 58 ms | 132 ms |
| 100 | 1566.85 | 63.23 ms | 60 ms | 96 ms | 115 ms | 140 ms |
| 200 | 1285.80 | 154.74 ms | 154 ms | 219 ms | 239 ms | 728 ms |

## Initial Observations

- Throughput increased from 10 to 25 concurrent connections.
- Increasing concurrency beyond 25 did not produce proportional throughput gains.
- At 200 concurrent connections, throughput decreased to approximately 1,286 RPS.
- Average latency increased from 6.32 ms at 10 concurrency to 154.74 ms at 200.
- P99 latency increased from 17 ms to 239 ms.
- The 728 ms maximum latency at 200 concurrency indicates significant outliers.

## Conclusion

The baseline API shows signs of approaching a throughput limit as concurrency
increases. Additional concurrency primarily increases latency rather than
increasing throughput.

The limiting resource has not yet been identified. Further experiments will
measure CPU, memory, and other system resources.