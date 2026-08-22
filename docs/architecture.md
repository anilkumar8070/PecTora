# Pectora: Technical Architecture

This document presents the high-level architecture of Pectora, designed for hackathon judges to understand the flow of data, state protection, and our novel deterministic-AI hybrid approach in under 30 seconds.

## Core Philosophy
We isolate the unpredictable **LLM Intelligence** from the critical **Private State**. The LLM never holds the user's private constraints in its context indefinitely; instead, our custom Python **Deterministic Engineering** layer intercepts, validates, and filters every single token before it leaves the system.

---

## Architecture Diagram

```mermaid
graph TD
    %% Styling Classes
    classDef user fill:#2d3748,stroke:#4a5568,stroke-width:2px,color:#fff
    classDef llm fill:#4c51bf,stroke:#434190,stroke-width:2px,color:#fff
    classDef deterministic fill:#2b6cb0,stroke:#2c5282,stroke-width:2px,color:#fff
    classDef db fill:#276749,stroke:#22543d,stroke-width:2px,color:#fff
    classDef comms fill:#c05621,stroke:#9c4221,stroke-width:2px,color:#fff
    classDef counterparty fill:#702459,stroke:#521b41,stroke-width:2px,color:#fff

    %% 1. Input & Mission Phase
    USER((User Owner)):::user
    VOICE_TEXT[Voice / Text Input\n(Hinglish/English)]:::user
    MISSION_ENGINE[Mission Engine\n(Parser & Validator)]:::deterministic
    DB[(SQLite Database\nState & Constraints)]:::db

    USER -- "Speaks instructions" --> VOICE_TEXT
    VOICE_TEXT -- "Raw text" --> MISSION_ENGINE
    MISSION_ENGINE -- "Extracts JSON\n(LLM CALL)" --> MISSION_ENGINE
    MISSION_ENGINE -- "Saves hard constraints" --> DB

    %% 2. Negotiation Phase
    PERSONAL_AGENT[Personal Agent\n(Negotiation State Machine)]:::deterministic
    PRIVATE_STATE[(Private State\nMemory & Limits)]:::db
    MEMORY_ENGINE[Memory Engine\n(Contradiction Resolver)]:::deterministic
    LLM_ENGINE((LLM Intelligence\nAction Generator)):::llm
    PERMISSION_ENGINE[Permission Engine\n& Privacy Firewall]:::deterministic
    
    DB -. "Loads constraints" .-> PERSONAL_AGENT
    MEMORY_ENGINE -- "Injects historical context" --> PERSONAL_AGENT
    PERSONAL_AGENT -- "Reads private rules" --> PRIVATE_STATE
    
    PERSONAL_AGENT -- "Requests Next Action\n(LLM CALL)" --> LLM_ENGINE
    LLM_ENGINE -- "Returns {Intent, Offer, Dialogue}" --> PERMISSION_ENGINE
    PERMISSION_ENGINE -- "Regex Scans & Blocks Leaks\n(Deterministic Check)" --> PERSONAL_AGENT

    %% 3. Communication & Verification Phase
    WEBSOCKET_GATEWAY[WebSocket/WebRTC\nSignaling Gateway]:::comms
    VERIFIER[Agreement Verifier\n(Final Rules Check)]:::deterministic
    HUMAN_APPROVAL[Human Approval\nEngine]:::deterministic
    
    PERSONAL_AGENT -- "Sends safe public message" --> WEBSOCKET_GATEWAY
    WEBSOCKET_GATEWAY -- "Receives counter-offer" --> PERSONAL_AGENT
    
    PERSONAL_AGENT -- "Ambiguous condition detected" --> HUMAN_APPROVAL
    HUMAN_APPROVAL -- "Requests human override" --> USER
    USER -- "Modifies constraints" --> HUMAN_APPROVAL
    HUMAN_APPROVAL -- "Updates state" --> PRIVATE_STATE

    %% 4. Counterparty
    COUNTER_HUMAN((Human Counterparty)):::counterparty
    COUNTER_AI((AI Counterparty)):::counterparty
    
    WEBSOCKET_GATEWAY <== "P2P WebRTC Audio / JSON" ==> COUNTER_HUMAN
    WEBSOCKET_GATEWAY <== "P2P WebRTC Audio / JSON" ==> COUNTER_AI

    %% 5. Completion
    PERSONAL_AGENT -- "Proposes Final Agreement" --> VERIFIER
    VERIFIER -- "Validates constraints 100%" --> DB
    VERIFIER -- "Logs success" --> EVAL_DASH[Evaluation Dashboard]:::deterministic

```

### Legend
* **Purple (LLM Intelligence)**: Non-deterministic generation nodes (Ollama/Llama 3.1).
* **Blue (Deterministic Engineering)**: 100% predictable Python logic containing our proprietary Safety Firewalls, State Machines, and Verification Engines.
* **Green (Data Stores)**: SQLite persistence and Private Memory isolation.
* **Orange (Communication)**: High-speed WebSocket and P2P WebRTC signaling.

### How to Read the Flow (30 Seconds)
1. **Setup**: The User speaks. The Mission Engine extracts hard numeric constraints using an LLM, but *deterministically validates* them before locking them into the Database.
2. **Execution**: The Personal Agent orchestrates the negotiation. It asks the LLM for a recommended move.
3. **Protection**: Before the LLM's move is executed, the **Permission Engine & Privacy Firewall** strictly scan the output to ensure private maximums (e.g., ₹42,000) are not leaked into the dialogue.
4. **Escalation**: If the counterparty introduces an un-delegated term (e.g., "15 day delivery"), the Agent halts and the **Human Approval Engine** kicks in.
5. **Closure**: Once an agreement is reached, the **Agreement Verifier** mathematically proves the deal did not violate any constraints before committing it to Memory.
