# Pectora Development Failure Log

This document records the actual, technical failures encountered during the development of the Pectora deterministic architecture, how they were resolved, and what vulnerabilities remain in the MVP.

---

## 1. Memory Engine Contradiction Resolution Failure

**What we attempted:**  
We attempted to build a deterministic, keyword-overlap-based contradiction filter for the `MemoryEngine` to prioritize newer, explicit user instructions (e.g., "I don't care about Friday anymore") over older AI inferences (e.g., "User prefers Friday").

**What failed:**  
During automated testing (`test_contradiction_explicit_wins_over_inference`), the engine failed to drop the older inferred memory, returning a `len(results) == 2` instead of the expected `1`.

**Why it failed:**  
The engine used naive Python `.split()` to calculate keyword intersection. Because it retained punctuation, the string `"Friday."` did not match `"Friday"`. Furthermore, the overlap threshold was set to `>= 2` words, which failed when the only intersecting noun was a single keyword.

**How we fixed it:**  
We imported Python's `re` module and used `re.findall(r'\b\w+\b', text)` to strip punctuation and extract clean words. We also adjusted the logic to trigger contradiction resolution if *any* relevant query keywords intersected between the two memories, rather than requiring an arbitrary 2-word overlap.

**What still fails:**  
The keyword matching is strictly lexical, not semantic. 

**What we would improve with another week:**  
If a user says "weekends" and the AI infers "Saturday", the current engine will fail to detect the overlap. With another week, we would implement a lightweight local embedding model (e.g., `all-MiniLM-L6-v2`) to perform cosine-similarity contradiction detection before applying the deterministic source-weighting.

---

## 2. Privacy Firewall "K-Notation" Bypass (Severity: Critical)

**What we attempted:**  
We attempted to build a `PrivacyFirewall` that deterministically blocks the AI from leaking private constraints (e.g., a hidden maximum budget of `42000`) by regex-scanning outgoing dialogue for exact numeric matches.

**What failed:**  
In hostile security testing (`test_privacy_bypass_k_notation`), the firewall failed to block the LLM when it generated: *"I cannot go higher than 42k, that is my max."*

**Why it failed:**  
The regex strictly matched continuous integers and decimals (`\b\d+(?:,\d{3})*(?:\.\d+)?\b`). It correctly extracted the number `42`, but because `42 != 42000`, the firewall assumed the agent was discussing a safe, unrelated number.

**How we fixed it:**  
We rewrote the regex engine to detect trailing multipliers (`k`, `m`, `thousand`, `lakh`, `crore`). When extracted, the engine casts the string to a float and applies the mathematical multiplier (e.g., `42 * 1000 = 42000.0`), successfully matching the private constraint and blocking the leak. We also added a hardcoded linguistic dictionary mapping common English numbers (e.g., "forty two thousand").

**What still fails:**  
Highly obfuscated linguistic numbers (e.g., "four tens and a two followed by three zeroes") or complex spelling errors ("fourty too thosand") will still bypass the firewall.

**What we would improve with another week:**  
We would introduce a secondary, small-scale LLM evaluator (e.g., Llama 3 8B) running in parallel, tasked *exclusively* with acting as a semantic firewall to judge if the private value was leaked, acting as a fallback for the deterministic regex layer.

---

## 3. Mission Validation Schema Mismatch

**What we attempted:**  
During the ultimate end-to-end (E2E) integration test, we attempted to pass a simulated JSON response from the LLM into the `MissionValidator` to verify that constraints were correctly instantiated.

**What failed:**  
The `MissionValidator` threw a `ValueError` during initialization, crashing the pipeline.

**Why it failed:**  
The simulated JSON placed `{"key": "bag_included", "type": "SOFT"}` inside the `hard_constraints` list. The Pydantic model for `MissionValidator` is strictly deterministic and demands that any object inside the `hard_constraints` array possess `type == 'HARD'`.

**How we fixed it:**  
We corrected the mock JSON payload in the test to properly define the constraint as `HARD`. 

**What still fails:**  
If a live LLM makes this exact schema mistake during extraction, the pipeline will currently crash and return a 500 error to the frontend.

**What we would improve with another week:**  
We would implement a robust LLM retry loop. If `MissionValidator` catches a `ValueError`, it should automatically feed the Pydantic error trace back to the LLM and ask it to fix the JSON formatting, rather than failing the negotiation outright.

---

## 4. Architectural Misalignment in Component Wiring

**What we attempted:**  
We attempted to wire the E2E test through the `FakeChannel` (simulating WebRTC) and the `AgreementVerifier`.

**What failed:**  
The test crashed twice sequentially with an `AttributeError` (`FakeChannel has no attribute 'send_message'`) and a `TypeError` (`AgreementVerifier takes no arguments`).

**Why it failed:**  
Rapid development led to API drift. The `NegotiationEngine` expects a channel with a `.send()` method, but the test attempted to call `.send_message()`. Furthermore, `AgreementVerifier` was instantiated as `AgreementVerifier(mission)`, but the class was designed to be stateless, taking `mission` as an argument during the `.verify(agreement, mission)` call.

**How we fixed it:**  
We refactored the test scripts to align perfectly with the backend class signatures.

**What still fails:**  
The `FakeChannel` mock does not accurately simulate WebSocket network latency, packet loss, or out-of-order message delivery.

**What we would improve with another week:**  
We would replace the pure Python `FakeChannel` with an actual local WebSocket integration test using `pytest-asyncio` and `websockets` to accurately simulate client-server network failures and test the engine's disconnect-recovery circuit breakers.
