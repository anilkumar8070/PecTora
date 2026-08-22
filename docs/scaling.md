# Pectora Scaling Analysis: Path to 10,000 Concurrent Users

This document outlines the architectural bottlenecks of the Phase 1 Pectora MVP and the specific modifications required to support 10,000 simultaneous active negotiations.

## 1. WebSocket Connections & Concurrent Negotiations
**Current Architecture**: Single-node FastAPI instance maintaining stateful WebSocket connections in memory.
**Current Bottleneck**: Memory exhaustion and event-loop blocking. A single Python process handling thousands of I/O bound WebSockets will drop frames or crash.
**Expected Failure Point**: ~1,000-2,000 connections (depending on instance size).
**How it would be scaled**:
- Deploy multiple stateless FastAPI instances behind an API Gateway/Load Balancer.
- Introduce **Redis Pub/Sub** or an **AWS API Gateway WebSocket** managed layer to handle the connection persistence, routing events to stateless worker nodes.

## 2. WebRTC Signaling
**Current Architecture**: WebRTC peer connections are negotiated via the central FastAPI WebSocket router. Audio flows peer-to-peer (Browser A ↔ Browser B).
**Current Bottleneck**: STUN/TURN server bandwidth (if P2P fails due to strict NATs) and backend signaling burst traffic during connection initiation.
**Expected Failure Point**: Signaling server overload during mass reconnects or high traffic spikes. Heavy TURN usage will drain bandwidth costs rapidly.
**How it would be scaled**:
- Separate WebRTC signaling to a lightweight, dedicated microservice (e.g., written in Go or Node.js) specifically optimized for high-concurrency ephemeral state.
- Deploy a geographically distributed cluster of TURN servers (e.g., Coturn) for robust fallback.

## 3. AI Inference & Model Rate Limits
**Current Architecture**: Synchronous or simple async calls to an LLM provider (Ollama or API).
**Current Bottleneck**: Inference time (1-3 seconds per turn). Holding the WebSocket open while waiting for inference blocks the server.
**Expected Failure Point**: 10,000 requests to an LLM simultaneously will result in severe rate-limiting (429 errors), timeouts, or complete hardware failure if running locally.
**How it would be scaled**:
- Implement an **Async Worker Pool** (e.g., Celery, RabbitMQ, Kafka) where negotiations are placed in a queue.
- Use a distributed cluster of vLLM / TensorRT-LLM inference servers to batch process requests.
- Implement robust circuit breakers and fallback models (e.g., if Llama 3.1 70B times out, fall back to Llama 3 8B).

## 4. Voice Processing (STT / TTS)
**Current Architecture**: Basic chunk decoding and local processing/API forwarding.
**Current Bottleneck**: Audio transcription and generation are highly compute-intensive.
**Expected Failure Point**: Latency spikes during STT processing causing awkward 5+ second silences in the voice conversation.
**How it would be scaled**:
- Shift TTS/STT to edge streaming architectures.
- Use a dedicated fleet of Whisper (STT) and FastPitch/ElevenLabs (TTS) microservices via gRPC streams to ensure sub-200ms latency independent of the core negotiation engine.

## 5. Database & Storage
**Current Architecture**: Local SQLite database for users, missions, and memory logging.
**Current Bottleneck**: SQLite enforces file-level locks on writes.
**Expected Failure Point**: ~100 concurrent writes will lead to `database is locked` OperationalErrors.
**How it would be scaled**:
- Migrate from SQLite to **PostgreSQL** with connection pooling (PgBouncer).
- Separate read replicas from the primary write node.

## 6. Personal Memory System
**Current Architecture**: Deterministic SQL queries iterating over all memories and running regex keyword comparisons in Python memory.
**Current Bottleneck**: O(N) regex scanning in Python for every negotiation turn.
**Expected Failure Point**: As users accumulate thousands of memories, the CPU overhead of iterating string arrays will block the async event loop.
**How it would be scaled**:
- Implement a distributed caching layer (Redis) for hot memory retrieval.
- Shift keyword comparison from Python memory to indexed PostgreSQL Full-Text Search (TSVECTOR), or introduce a dedicated vector database (Pinecone/Milvus) solely for similarity scoring before passing the results to the deterministic contradiction engine.

## Summary Architecture for 10k Users

```text
10,000 Users
     ↓
[ AWS API Gateway (WebSocket Mgmt) ]
     ↓
[ Redis Pub/Sub Backplane ]
     ↓
[ FastAPI Negotiation Workers (Stateless) ] → [ PostgreSQL (Missions/State) ]
     ↓
[ Message Queue (RabbitMQ) ]
     ↓
[ Distributed AI Inference Cluster (vLLM) ]
```
