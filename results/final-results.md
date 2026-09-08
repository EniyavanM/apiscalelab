# APIScaleLab — Final Benchmark Results

## 1. Objective

APIScaleLab investigates how a small AWS EC2 instance behaves as API traffic increases and how architectural optimizations affect throughput, latency, and bottlenecks.

The experiments focus on:

- API throughput
- Latency under concurrency
- PostgreSQL access
- PostgreSQL connection pooling
- Redis caching
- CPU saturation
- Architectural scaling strategies

The experiments are intended to understand scalability principles rather than reproduce a large-scale production system.

---

## 2. Experimental Environment

| Component | Configuration |
|---|---|
| API | FastAPI |
| Application server | Uvicorn |
| Compute | AWS EC2 t3.micro |
| Database | Amazon RDS PostgreSQL |
| Cache | Amazon ElastiCache Serverless Redis |
| Load generator | autocannon |
| Load source | Windows development machine |
| API server | EC2 |
| Database access | psycopg |
| Connection pooling | psycopg-pool |

The client machine generated the traffic while EC2 acted as the system under test.

---

# 3. Experiment 1 — Baseline API

Endpoint:

```text
GET /hello
