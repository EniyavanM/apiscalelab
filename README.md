# APIScaleLab

## API Performance & Scalability Experimental Lab

> **How much API traffic can a small AWS instance actually handle?**

APIScaleLab is a hands-on experiment to understand how API architecture affects **throughput, latency, resource utilization, and system bottlenecks**.

Instead of trying to reproduce a large-scale production system, this project takes a small AWS EC2 instance and tests the same user-lookup workload under **three different architectural designs**.

The goal is simple:

> **Measure → Identify the bottleneck → Optimize → Measure again.**

---

# Project Objective

The project investigates how an API behaves when subjected to **500 concurrent requests** and how different architectural decisions affect performance.

Three architectures were evaluated:

1. **PostgreSQL — Connection Per Request**
2. **PostgreSQL — Connection Pooling**
3. **Redis — Cache Hit**

The experiments demonstrate how scalability improvements can move the bottleneck from one layer of the system to another.

---

# Architecture Overview

## Architecture 1 — PostgreSQL Connection Per Request

Every API request creates a new PostgreSQL connection, executes the query, and closes the connection.

```text
Client
   |
   v
EC2
FastAPI
   |
   v
Create PostgreSQL Connection
   |
   v
RDS PostgreSQL
   |
   v
Response
```

## Architecture 2 — PostgreSQL Connection Pool

Instead of creating a new connection for every request, the application reuses connections from a PostgreSQL connection pool.

```text
Client
   |
   v
EC2
FastAPI
   |
   v
Connection Pool
   |
   v
RDS PostgreSQL
   |
   v
Response
```

Connection pool configuration:

```text
Minimum connections: 1
Maximum connections: 5
```

## Architecture 3 — Redis Cache

The API checks Redis before querying PostgreSQL.

```text
Client
   |
   v
EC2
FastAPI
   |
   v
Redis
   |
   +---- Cache HIT ----> Response
   |
   +---- Cache MISS
              |
              v
        RDS PostgreSQL
              |
              v
           Redis
```

For a cache hit, PostgreSQL is completely removed from the request path.

---

# Experimental Environment

| Component | Configuration |
|---|---|
| Cloud | AWS |
| Compute | EC2 t3.micro |
| Operating System | Amazon Linux 2023 |
| API Framework | FastAPI |
| Application Server | Uvicorn |
| Database | Amazon RDS PostgreSQL |
| Cache | Amazon ElastiCache Serverless Redis |
| PostgreSQL Driver | psycopg |
| Connection Pool | psycopg-pool |
| Cache Client | redis-py |
| Load Generator | autocannon |
| Concurrency | **500** |
| Test Duration | **20 seconds** |

The **Windows laptop** was used as the load generator.

The **EC2 instance** was the system under test.

---

# Benchmark Methodology

Each architecture was tested using:

```bash
autocannon -c 500 -d 20 <EC2_PUBLIC_IP>:8000/<endpoint>
```

Where `-c 500` represents 500 concurrent connections and `-d 20` represents a 20-second test duration.

During the benchmarks, EC2 CPU utilization was observed using:

```bash
pidstat -u 1
```

Metrics collected:

- Requests per second (RPS)
- Average latency
- P50 latency
- P99 latency
- Maximum latency
- CPU utilization

---

# Final Benchmark Results

## 500 Concurrent Requests

| Architecture | Avg RPS | Avg Latency | P50 | P99 | Max |
|---|---:|---:|---:|---:|---:|
| PostgreSQL — Connection Per Request | **~111** | **~4.39 s** | ~4.39 s | **~7.95 s** | ~8.38 s |
| PostgreSQL — Connection Pool | **716.35** | **687 ms** | 683 ms | **1.08 s** | 1.38 s |
| Redis — Cache Hit | **1,081.16** | **459 ms** | 431 ms | **2.93 s** | 5.51 s |

---

# Performance Progression

```text
PostgreSQL
Connection Per Request
        |
        | ~111 RPS
        v
PostgreSQL
Connection Pool
        |
        | 716 RPS
        v
Redis
Cache Hit
        |
        | 1,081 RPS
        v
Higher Measured Throughput
```

### Connection Pooling Improvement

At the same 500-concurrency workload:

```text
~111 RPS
    ↓
716 RPS
```

This represents approximately a **6.4× increase in measured throughput** after introducing PostgreSQL connection pooling.

---

# Experiment 1 — PostgreSQL Connection Per Request

### Endpoint

```text
GET /users/1
```

The initial implementation created a PostgreSQL connection for every request.

```text
Request
   |
   v
Create Connection
   |
   v
Execute Query
   |
   v
Close Connection
```

### Result at 500 concurrency

```text
Average RPS       ~111
Average Latency   ~4.39 seconds
P99 Latency       ~7.95 seconds
Maximum Latency   ~8.38 seconds
```

### Observation

The application experienced severe performance degradation under high concurrency.

Repeated database connection creation introduced significant overhead.

This result represents the performance of the **application architecture and test environment**, not the maximum capability of PostgreSQL or Amazon RDS.

---

# Experiment 2 — PostgreSQL Connection Pool

The application was changed to use a reusable PostgreSQL connection pool.

```text
FastAPI
   |
   v
Connection Pool
   |
   +---- Reusable DB Connections
   |
   v
RDS PostgreSQL
```

### Result at 500 concurrency

```text
Average RPS       716.35
Average Latency   687 ms
P50 Latency       683 ms
P99 Latency       1.08 seconds
Maximum Latency   1.38 seconds
```

### Observation

Connection pooling significantly reduced the overhead associated with creating database connections.

At high concurrency, EC2 CPU utilization approached approximately **110–117%**, indicating that the small application server was becoming an important bottleneck.

---

# Experiment 3 — Redis Cache Hit

The API was modified to check Redis before accessing PostgreSQL.

```text
Request
   |
   v
Redis
   |
   +---- HIT ----> Return Response
   |
   +---- MISS
           |
           v
       PostgreSQL
           |
           v
       Store in Redis
```

Cache TTL:

```text
60 seconds
```

### Result at 500 concurrency

```text
Average RPS       1,081.16
Average Latency   459 ms
P50 Latency       431 ms
P99 Latency       2.93 seconds
Maximum Latency   5.51 seconds
```

### Observation

The cache-hit workload achieved approximately **1,081 RPS**.

The important architectural benefit is that a cache hit completely bypasses PostgreSQL.

---

# Bottleneck Progression

One of the most important findings was that **the bottleneck moved as the architecture improved**.

```text
Database Connection Overhead
            ↓
      Connection Pooling
            ↓
      Higher Throughput
            ↓
       EC2 CPU Limit
            ↓
          Caching
            ↓
      Higher Throughput
            ↓
 Horizontal Scaling Required
```

The core engineering loop is:

```text
Measure
   ↓
Find Bottleneck
   ↓
Optimize
   ↓
Measure Again
   ↓
Find Next Bottleneck
   ↓
Scale
```

---

# How This Architecture Can Scale Further

The current experiment uses a single EC2 instance.

A larger production architecture could evolve toward:

```text
                       Load Balancer
                      /      |      \
                     /       |       \
                   EC2      EC2      EC2
                    |        |        |
                 FastAPI  FastAPI  FastAPI
                    \        |        /
                     \       |       /
                         Redis
                           |
                           v
                    PostgreSQL
```

Further strategies include:

### Application Layer
- Multiple EC2 instances
- Load balancing
- Multiple Uvicorn workers
- Auto scaling

### Database Layer
- Connection pooling
- Query optimization
- Database indexes
- Read replicas
- Partitioning

### Caching Layer
- Redis caching
- Appropriate TTLs
- Cache invalidation
- Cache hit-ratio monitoring

### Reliability
- Timeouts
- Rate limiting
- Backpressure
- Retry policies
- Circuit breakers

### Observability
- Request rate
- P50/P95/P99 latency
- Error rate
- CPU utilization
- Memory utilization
- Database connections
- Query latency
- Redis hit ratio

---

# Important Benchmark Caveat

All three final architectures were tested with:

```text
Concurrency: 500
Duration:    20 seconds
```

However, the internal workload differs.

The PostgreSQL connection-pool test forces a database lookup for every request:

```text
GET /users-db/1
```

The Redis test represents a cache-hit workload:

```text
GET /users/1
```

Therefore, these results should be interpreted as:

> **Measured performance of three different request-processing architectures under a 500-concurrency workload.**

They should not be interpreted as universal capacity limits for EC2, FastAPI, PostgreSQL, or Redis.

---

# Screenshots

Place benchmark screenshots in a `screenshots/` directory.

## PostgreSQL — Connection Per Request

![PostgreSQL Connection Per Request](screenshots/postgres-connection-per-request.png)

## PostgreSQL — Connection Pool

![PostgreSQL Connection Pool](screenshots/postgres-connection-pool.png)

## Redis — Cache Hit

![Redis Cache Hit](screenshots/redis-cache-hit.png)

## EC2 CPU During Benchmark

![EC2 CPU Utilization](screenshots/ec2-cpu-utilization.png)

> Do not upload screenshots containing passwords, private keys, authentication tokens, or other secrets.

---

# Project Structure

```text
APIScaleLab/
│
├── app/
│   ├── main.py
│   └── database.py
│
├── benchmarks/
├── docs/
├── experiments/
├── results/
├── scripts/
├── screenshots/
│   ├── postgres-connection-per-request.png
│   ├── postgres-connection-pool.png
│   ├── redis-cache-hit.png
│   └── ec2-cpu-utilization.png
│
├── .gitignore
├── requirements.txt
└── README.md
```

---

# Key Takeaways

### 1. Concurrency does not equal throughput

Increasing concurrency eventually caused latency to increase significantly without proportional throughput gains.

### 2. Database connections should be reused

Connection pooling significantly improved the database workload.

### 3. Caching can remove database work

Redis cache hits bypass PostgreSQL completely.

### 4. Bottlenecks move

Optimizing one layer exposes limitations in another layer.

### 5. Scalability is iterative

The correct architecture depends on identifying the current bottleneck.

---

# Final Conclusion

APIScaleLab started with a simple question:

> **How much API traffic can a small AWS instance actually handle?**

Under a controlled **500-concurrency workload**, three different architectures produced significantly different results:

```text
~111 RPS
PostgreSQL Connection Per Request

        ↓

716 RPS
PostgreSQL Connection Pool

        ↓

1,081 RPS
Redis Cache Hit
```

The most important result is not the final RPS number.

The important lesson is the relationship between **architecture and bottlenecks**.

By measuring the system, identifying the limiting resource, changing the architecture, and measuring again, we can understand how a simple API can progressively evolve toward a scalable distributed system.

> **Measure → Find the Bottleneck → Optimize → Measure Again → Scale**

---

# Author

Built as a hands-on project covering:

- Backend API development
- AWS
- PostgreSQL
- Redis
- Performance testing
- Connection pooling
- Caching
- System design
- Scalability engineering
