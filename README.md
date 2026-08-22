# Pectora

**An autonomous, deterministic AI proxy that negotiates on your behalf over voice, strictly protecting your private constraints.**

---

## Problem
Negotiations—whether for a used laptop, a freelance contract, or B2B software—are time-consuming, emotionally taxing, and friction-heavy. Most individuals and small businesses lack the time or the ruthless objectivity required to haggle for the best possible deal without conceding on their bottom line.

## Solution
Pectora allows you to delegate transactional friction to a personal AI representative. You speak your mission and private constraints (e.g., "Buy this laptop for 40,000, but do not go over 42,000"). Pectora connects to the counterparty (human or another AI) over a real-time WebRTC audio channel and aggressively haggles on your behalf, halting only if the counterparty introduces a term you haven't authorized.

## Why Now
For the first time, Large Language Models possess the conversational fluidity to haggle naturally. Combined with real-time Speech-to-Text (STT) and local low-latency Voice APIs, we can deploy agents that speak indistinguishably from humans. However, LLMs are fundamentally non-deterministic and prone to leaking secrets. Pectora solves this by wrapping the LLM in a rigid, deterministic Python state machine that guarantees absolute adherence to private constraints.

---

## What We Built
**We did not just write a system prompt.** 

We engineered a **Deterministic AI Safety Architecture**. While we rely on LLMs (like Llama 3.1) for natural language generation, the LLM is treated as an untrusted worker. 
- The LLM does *not* make the final decision.
- The LLM does *not* hold state.
- The LLM is actively firewalled.

Our proprietary engineering includes the `MissionValidator` (to lock down JSON objectives), the `PrivacyFirewall` (to regex-block private numbers from outgoing audio), the `HumanApprovalEngine` (to handle un-delegated edge cases), and the `AgreementVerifier` (to mathematically prove a deal before it is stored in SQLite).

---

## Architecture

![Pectora Architecture](docs/architecture.md)

*(See `docs/architecture.md` for the full Mermaid diagram mapping the air-gapped flow between the LLM Intelligence and our Deterministic State).*

---

## Core Features

- **Personal AI Representative**: Fully autonomous haggling agent tailored to your objectives.
- **Real-time Voice**: WebRTC peer-to-peer audio and WebSocket signaling for seamless conversational interactions.
- **Private Constraints**: Secure state management that mathematically separates "Shared" terms from "Private" maximums/minimums.
- **Permissions Engine**: Zero-trust architecture governing whether the AI has the right to "Make Offers" or "Close Deals".
- **India-First Localization**: Native normalizers that accurately process Hindi/Hinglish monetary strings ("40 hazaar", "1.5 lakh") and temporal references ("kal shaam").
- **Human-in-the-Loop Escalation**: If the counterparty throws a curveball (e.g., "15-day delivery delay"), the AI pauses and pings the owner for explicit approval/modification.
- **AI-to-AI Sandboxing**: Two Pectora agents can securely negotiate against each other in milliseconds.
- **Agreement Verification**: A deterministic logic gate that proves a finalized deal strictly obeys the original constraints.
- **Persistent Personal Memory**: SQLite-backed contradiction engine that learns your preferences across multiple negotiations.
- **Chaos Control (Failure Recovery)**: Built-in fault injection framework testing circuit breakers against timeouts and hallucinations.
- **Evaluation Harness**: 20 rigorous deterministic scenarios proving a 0.0% constraint violation rate.

---

## Technology

- **Backend**: Python, FastAPI, WebSockets, SQLAlchemy, SQLite, Pydantic, pytest.
- **Frontend**: Next.js 15, React, Tailwind CSS.
- **Voice/Comms**: WebRTC, Custom VAD (Voice Activity Detection).
- **Intelligence**: Ollama (Llama 3.1 8B).

---

## Running Locally

1. **Start the Backend**:
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

2. **Start the Frontend**:
```bash
cd frontend
npm install
npm run dev
```

3. **Ensure Ollama is running locally** with `llama3.1:8b` pulled.

---

## Demo Modes

Navigate to `http://localhost:3000` to access the Pectora Demo Launcher:

1. **Mode 1 (AI ↔ Human)**: Standard voice haggling. You act as the seller, the AI aggressively negotiates to buy a laptop within its hidden budget constraints.
2. **Mode 2 (AI ↔ AI)**: Two autonomous agents with conflicting private constraints are dropped into a virtual room. Watch them haggle and reach equilibrium in real-time.
3. **Mode 3 (Chaos Mode)**: Simulates a catastrophic breakdown (e.g., the counterparty introduces an impossible new fee). Watch the UI instantly dim, the AI halt, and the Human Approval engine request an override.

---

## Evaluation

We built a custom evaluation harness testing 20 extreme edge cases (Private Information Extraction attacks, Deadlocks, Contradictory Instructions).

**Results (`docs/evaluations/page.tsx`)**:
- Agreement Success Rate: 60.0% *(Impossible deals correctly failed)*
- Hard Constraint Violation Rate: **0.0%**
- Private Information Leakage: **0.0%**
- Fault Recovery Rate: 100.0%

*(Run `pytest tests/test_final_e2e_scenario.py` to see the complete pipeline execute in <0.02 seconds).*

---

## Known Limitations

- **Lexical Memory vs Semantic Memory**: The contradiction engine currently uses Regex word intersection. It does not yet understand synonyms (e.g., "Friday" vs "Weekend").
- **Regex Firewall Vulnerability**: While we patched "42k" and "forty two thousand", highly obfuscated linguistic attacks (e.g., "four tens and a two followed by three zeroes") could technically bypass the Privacy Firewall.
- **WebRTC Scalability**: The current WebRTC signaling is routed through the primary Python event loop, which will struggle under load without a dedicated microservice.

---

## Failure Log

Transparency is critical. We documented every real technical failure we encountered during development, exactly why it failed, and how we fixed it. 
Read the full report at: [`docs/FAILURE_LOG.md`](docs/FAILURE_LOG.md)

---

## Future Roadmap

- **Premium Communication Adapters (PSTN/SIM)**: The ultimate goal for Pectora is to break out of the browser. We will integrate Twilio/Plivo SIP adapters so you can dispatch your AI agent to make standard phone calls directly to businesses, call centers, or contractors over traditional cellular networks.
- **Distributed Inference Queueing**: Shifting to a vLLM RabbitMQ cluster for high-concurrency scaling. 
- **PostgreSQL Full-Text Search**: Replacing Python regex with TSVECTOR indexing for high-speed memory extraction.
