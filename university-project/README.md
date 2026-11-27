# 🌾 PaddyGuard MAS

### A Personalized, Multilingual, Weather-Aware Multi-Agent AI Advisory Platform for Climate-Resilient Paddy Cultivation in Sri Lanka

---

> **Innodata AI Catalyst '26 — External University Track**
> Challenge: Multi-Agent AI for Global Problems | Domain: Agriculture

| Field | Details |
|---|---|
| **University** | Sabaragamuwa University of Sri Lanka (SUSL) |
| **Team Name** | Enigma |
| **Team Members** | Kathuskan · AmalAnojan · Abilas · Thushan |
| **GitHub** | [github.com/Kathuskan/Team_Enigma_SUSL](https://github.com/Kathuskan/Team_Enigma_SUSL) |

---

## Current implementation

PaddyGuard is a local paddy advisory app for six Sri Lankan field areas. Farmers can confirm a field, update crop details in chat, attach a leaf or pest photo, dictate a question and review the transcript before sending. Replies combine available field evidence, a weather window and safety checks.

## Run on Windows

From the repository root, run these commands in PowerShell.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m project.rag.ingest
.\.venv\Scripts\python -m project.rag.hybrid
.\.venv\Scripts\python -m uvicorn project.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. The two index commands are needed on a fresh installation or after changing source material. The first dense build downloads an embedding model. Search then runs locally. Current crop data and history live under project/data.

## Enable cloud transcription and vision

Create a file named `.env` beside this README. Start with the values in `.env.example`. Add a Gemini API key from a project with access to the chosen models. Keys stay on the server. Refresh the app after changing these settings.

- `GEMINI_API_KEY` enables cloud dictation, image analysis, multilingual crop detail extraction and model-based advice.
- `GEMINI_MODEL` selects the multimodal model for the five-agent workflow and transcription.
- `GEMINI_TTS_MODEL` selects the audio generation model for reply playback when the browser lacks a matching voice.

Use localhost or HTTPS and allow microphone access. Tap Dictate, speak, then stop. The server sends a short WAV clip to Gemini for transcription. The app does not save audio. Only pressing Send adds the edited transcript to the conversation. Without a server key, dictation uses the browser's speech service if available. Language support varies by browser.

Choose a crop image to preview it. The browser resizes it to JPEG under 1 MB. Sending submits it to the server for Gemini vision. A referral photo stays with the anonymous farm session so the farmer can share it later. With no model access, the app reports that image analysis is unavailable.

## Decisions and evidence

The orchestrator reads current season data and pending questions. Weather, vision and agronomy run in parallel. The independent critic can ask for missing information, request a clearer photo, block unsafe field work, approve a supported observation, request up to two revisions or refer to an Agricultural Instructor. The decision panel receives progress during a turn.

Retrieval combines BM25 keyword ranking, local ChromaDB embeddings and multilingual crop concepts using reciprocal rank fusion. Returned passages retain the publisher, page or section. The initial corpus includes IRRI plant health guidance and RRDI symptom and crop-management references. The 2013 Sinhala PDF contains legacy-font text. Unreadable pages are excluded from search pending checked Unicode extraction. Automated chemical rates and pre-harvest clearance require reviewed tables and are withheld.

## Verification and proposal coverage

```powershell
.\.venv\Scripts\python -m pip install pytest
.\.venv\Scripts\python -m pytest project/eval -q
.\.venv\Scripts\python -m project.eval.benchmark --output project/data/benchmark.csv
```

The tests cover routing, revisions, weather thresholds, memory, referrals, multilingual retrieval and the cloud transcription API using controlled inputs. The benchmark compares 30 fixed cases with the same model, evidence and recorded weather or image findings. It requires live Gemini access and consumes quota. It measures the advisory decision; image classifier calibration and recorded native-speaker transcription tests require separate real examples. Human baseline measurements must be collected from knowledgeable reviewers.

See plan.md for the full field-release criteria. Outstanding validation includes agronomist review, field-photo calibration, speech testing on target phones, human comparisons, latency and cost measurements. The current frontend uses native browser modules and CSS.


---

## Executive Summary

Smallholder paddy farmers in Sri Lanka face recurring crop losses and severe input waste when erratic monsoon rainfall, pest and disease outbreaks, stage-specific fertilizer rules, and tight budgets collide. Existing weather apps deliver raw forecasts without agronomic meaning, while single-agent chatbots retrieve generic textbook dosages without checking live rainfall wash-off risks, verified field locations, crop growth stages, or safety ceilings.

**PaddyGuard MAS** resolves this gap as a **mobile-first Progressive Web App (PWA)** backed by a **5-agent LangGraph system**:

- 🧠 **Orchestrator & Memory Agent**
- ⛅ **Weather & Microclimate Agent**
- 👁️ **Vision Diagnostic Agent**
- 📚 **Agronomy & Pest RAG Agent** *(grounded strictly in Sri Lanka RRDI, Department of Agriculture, and IRRI manuals)*
- 🛡️ **Safety & Feasibility Critic Agent**

Designed for real field deployment, PaddyGuard MAS verifies the farmer's actual paddy field location at onboarding, builds a structured Farm Profile automatically from natural conversation in **Sinhala, Tamil, or English**, supports **voice-to-text preview** and **Text-to-Speech (TTS)** audio replies, compresses leaf/pest photos with strict anti-hallucination guardrails, and escalates uncertain or high-risk cases to human Agricultural Instructors.

---

## 1. Problem

Rice (paddy) is the staple food for over half of humanity and the primary livelihood for hundreds of thousands of smallholder farming families across Sri Lanka (Polonnaruwa, Anuradhapura, Kurunegala, Ampara, Batticaloa, and Hambantota). Yet smallholder paddy farmers routinely suffer **preventable yield losses** and **wasted agrochemical expenditure** because field decisions require reconciling four rapidly changing variables at once: local weather, crop growth stage, verified agronomic rules, and input cost.

### 1.1 The Real-World Decision Problem

During a 3–3.5-month paddy cultivation cycle (Yala and Maha seasons), farmers must decide precisely when to apply basal/top-dressing fertilizers and when to spray pesticides or fungicides. Acting without cross-checking live short-window weather causes:
- Unexpected monsoon rain **washes freshly sprayed agrochemicals** off the field within hours
- Excessive nitrogen fertilizer at the wrong stage **worsens pest outbreaks** (e.g., Rice Leaffolders)
- Prolonged high humidity accelerates **fungal outbreaks** like Rice Blast and Brown Spot

### 1.2 Affected Stakeholders

- **Smallholder Paddy Farmers:** 140M+ rice-farming households globally (1.8M+ in Sri Lanka) absorbing direct financial shocks from rain wash-off, misdiagnosed pests, and rising agrochemical prices.
- **Agricultural Instructors (AIs) & Extension Officers:** Heavily overstretched — often covering thousands of farmers per division — making timely one-on-one field visits impossible during peak monsoon seasons.
- **Rural Ecosystems & Consumers:** Repeated mis-timed spraying contaminates local groundwater and tanks while reducing domestic rice output and inflating staple food prices.

### 1.3 Why Existing Solutions Fall Short

| Gap | Problem |
|---|---|
| Raw Weather Apps | Display temperature or rainfall percentages without translating into spray wash-off thresholds, wind spray-drift limits, or fungal humidity risks |
| Single-Agent Chatbots | Dump a pesticide dosage and weather summary side-by-side without catching that heavy rain in 6 hours invalidates the spray |
| Accessibility & Context | Assume desktop English typing, force tedious forms, rely on phone GPS (fails when farmer installs the app in town), forget crop age day-to-day |

---

## 2. Research Findings & Global Impact

According to FAO, global milled rice production exceeds **520 million tonnes annually**, supplying over 20% of human caloric intake worldwide. IRRI estimates that pests, diseases, and weeds destroy **25–37% of global rice yields** each year, while IPCC AR6 warns that shifting monsoon patterns are intensifying pest lifecycles and shrinking safe field-operation windows.

| Impact Dimension | Global & Sri Lankan Significance |
|---|---|
| **Economic** | Preventing rain wash-off of fertilizers and pesticides directly protects smallholder household income and reduces avoidable crop yield losses across Yala and Maha seasons |
| **Social & Food Security** | Stabilizing paddy yields strengthens national rice self-sufficiency and protects low-income families from staple food price volatility |
| **Environmental Protection** | Blocking unsafe pre-rain spraying and prioritizing IPM curbs chemical leaching into Sri Lankan irrigation tanks, streams, and wetlands |
| **Extension Scalability** | Automating routine triage and escalating only ambiguous or high-toxicity cases multiplies the effective reach of scarce Agricultural Instructors |

Real-world deployments like **Digital Green's FarmerChat** (1M+ farmers) and **Sri Lanka's Govi Mithuru** (1.1M+ users) confirm that voice-enabled, local-language, personalized mobile guidance achieves dramatically higher smallholder adoption than static portals.

---

## 3. Proposed Solution & Product Design

PaddyGuard MAS is a **Mobile-First Progressive Web App (PWA)** combining a familiar WhatsApp + ChatGPT hybrid interface with a 5-agent LangGraph backend. Farmers open a single link on their smartphone and tap **"Add to Home Screen"** for an app-like experience, while desktop users automatically see a split-screen with the live **Multi-Agent Reasoning Trace** alongside the farmer conversation.

### 3.1 Core User-Centered Capabilities

- ✅ **Verified Field Location at Onboarding** — Explicitly asks *"Is your paddy field here, or in another area?"* to save the verified field district for accurate weather lookups
- 🗂️ **Auto-Built Structured Farm Profile + "My Farm" Top Bar** — Silently extracts key attributes (District, Variety, Planting Date, Irrigated vs. Rainfed, Last Fertilizer Date, Season) from natural conversation and displays a compact pinned bar (e.g., *Polonnaruwa • 3.5m paddy • Day 40 • Maha Season*)
- 🔄 **Verified Season Reset (Yala / Maha)** — A "New Season" button requires explicit confirmation before resetting the crop day counter; accidental taps never wipe active data
- ❓ **"Think Before Answering" Active Questioning Loop** — Before answering any query, the agent checks the Farm Profile and past chat memory first, asking only 1–2 short focused questions if critical information is missing
- 🎙️ **Multilingual Voice Input (With Verification Preview) & TTS Audio Output** — Speech-to-Text places the transcribed prompt in the chat box in the same language so farmers can verify before sending; every reply includes a one-tap "Play Audio" (TTS) button
- 📸 **Auto-Compressed Photos & Strict Anti-Hallucination** — Leaf/pest photos compressed client-side (<1 MB) for rural networks; Vision Agent asks for a clearer photo if blurry, and honestly states *"I do not have enough knowledge to safely assist"* if still uncertain
- 🚫 **Zero Open Web Search for Agrochemicals** — Relies exclusively on verified Sri Lanka RRDI/DOA and IRRI manuals (RAG) plus live meteorological data

---

## 4. Multi-Agent Architecture

PaddyGuard MAS uses **LangGraph** to orchestrate five specialized agents over a strongly typed shared state.

```
                          ┌─────────────────────────┐
                          │  Orchestrator & Memory   │
                          │        Agent             │
                          └────────────┬────────────┘
                   ┌──────────────────┼──────────────────┐
                   ▼                  ▼                  ▼
         ┌─────────────┐   ┌─────────────────┐   ┌─────────────┐
         │  Weather &  │   │    Vision       │   │  Agronomy & │
         │ Microclimate│   │  Diagnostic     │   │  Pest RAG   │
         │    Agent    │   │    Agent        │   │    Agent    │
         └─────────────┘   └─────────────────┘   └──────┬──────┘
                                                        │
                                              ┌─────────▼─────────┐
                                              │  Safety &         │
                                              │  Feasibility      │
                                              │  Critic Agent     │
                                              │  (max 2 loops)    │
                                              └─────────┬─────────┘
                                                        │
                                              APPROVE / REVISE / ESCALATE_HUMAN
```

### 4.1 Agent Roles & Responsibilities

| Agent | Responsibilities & Capabilities | Tools / Interfaces |
|---|---|---|
| **1. Orchestrator & Memory Agent** | Determines required slots for the query; reads/updates the auto-built Farm Profile & past conversation memory; asks 1–2 short clarifying questions in Sinhala/Tamil/English if critical info is missing; routes to parallel specialists; compiles final action-first response | Structured State Manager (Pydantic), Farm Profile Store |
| **2. Weather & Microclimate Agent** | Queries 48-hour forecasts for the verified field location and translates raw metrics into agronomic risk tiers: rain wash-off (>40% rain or >2mm in 12h), wind spray-drift (>15 km/h), and fungal humidity (>85% RH) | Open-Meteo REST API, Agronomic Risk Rule Engine |
| **3. Vision Diagnostic Agent** | Inspects client-compressed leaf/pest photos; outputs candidate disorder + confidence score; requests a clearer photo if blurry/low-confidence; strictly refuses to guess when uncertain | Multimodal Vision LLM, Confidence Threshold Gate |
| **4. Agronomy & Pest RAG Agent** | Retrieves verified Sri Lanka RRDI, DOA, and IRRI guidelines matching crop variety, growth stage, and water regime (irrigated/rainfed); drafts IPM-first treatment/fertilizer plans with manual citations; revises upon Critic rejection | Local ChromaDB Vector Store (RRDI/DOA/IRRI PDFs) |
| **5. Safety & Feasibility Critic Agent** | Independently audits the Agronomy draft against Weather risk flags, Vision confidence, growth-stage rules, dosage ceilings, and Pre-Harvest Intervals (PHI). Issues APPROVE, REVISE (max 2 loops), or ESCALATE_HUMAN | Constraint Verification Matrix, Anti-Hallucination Guardrails |

### 4.2 End-to-End Walkthrough (Polonnaruwa Field Scenario)

> **Context:** Farm Profile stores `{District: Polonnaruwa (verified), Variety: 3.5-month, Day: 40 (Tillering), Season: Maha}`. Farmer speaks in Tamil and attaches a compressed leaf photo: *"I see brown spots on the leaves. Can I spray fungicide tomorrow morning?"*

1. **Orchestrator & Memory** — Confirms all required slots are present; dispatches Weather, Vision, and Agronomy RAG agents in parallel
2. **Parallel Specialists** — Weather flags `HIGH_WASH_OFF_RISK` (85% rain, 14mm tomorrow at 11:00 AM; 89% humidity); Vision identifies oval brown leaf lesions consistent with *Brown Spot* (high confidence); Agronomy RAG retrieves RRDI Brown Spot guidance and drafts a standard fungicide spray
3. **Safety Critic Rejection** — Critic detects a clash between the morning spray draft and imminent heavy rain. Rejects with feedback: *"Heavy rain causes wash-off and waterway runoff; reschedule spray to next 24h dry window and advise immediate drainage/potassium check."*
4. **Revision, Delivery & TTS** — Agronomy Agent revises the plan (delay spray until Thursday dry window; inspect drainage today). Critic approves. Farmer receives a clear action-first Tamil reply with a **Play Audio** button; desktop panel logs the full 5-agent trace.

**Human-in-the-Loop (HITL) Escalation** triggers when:
- Vision Agent remains uncertain after requesting a clearer photo
- Symptoms are ambiguous across incompatible disorders
- Query involves restricted/high-toxicity WHO Class Ib/II chemicals
- Critic loop does not converge within two revisions

In any HITL scenario, PaddyGuard MAS withholds chemical dosage advice and generates a **one-tap shareable case summary** (photo + profile + chat) for a local Agricultural Instructor.

---

## 5. Tech Stack

| Technology | Role in PaddyGuard MAS | Selection Justification |
|---|---|---|
| **LangGraph (Python)** | Stateful 5-agent orchestration, parallel branching, bounded Critic loops (max 2 retries) | Chosen over free-form conversational frameworks (e.g., AutoGen) for deterministic state routing, lower token cost, and predictable latency |
| **Gemini 2.5 Flash (Multimodal)** | Core LLM for multilingual reasoning (Sinhala/Tamil/EN), Vision photo analysis, and critique | Native multimodal + strong Sinhala/Tamil support at low latency/cost; abstracted via LangChain for modular model swapping |
| **ChromaDB + PyPDF** | Local vector database indexed strictly with Sri Lanka RRDI, DOA, and IRRI manuals | Eliminates cloud vector DB credentials and guarantees 100% reproducible local execution for evaluators |
| **Open-Meteo API** | Keyless 48-hour hyperlocal rainfall, humidity, and wind forecast telemetry | Reliable, free meteorological API supporting exact Sri Lankan district coordinates with deterministic JSON outputs |
| **Speech-to-Text & Neural TTS** | Multilingual voice input (with same-language chat preview) and Play Audio replies | Supports Sri Lankan Sinhala (si-LK), Tamil, and English audio so non-typing farmers can interact effortlessly |
| **FastAPI + SQLite** | Async REST backend (`project/main.py`), persistent Farm Profile memory & JSONL traces | Async concurrency supports parallel agent execution; lightweight SQLite stores structured Farm Profiles with zero external DB setup |
| **React + Tailwind PWA** | Mobile-first sunlight-readable UI, browser-image-compression, desktop Agent Trace panel | Single codebase delivering an installable smartphone experience plus a live technical trace view for judges |
| **Pydantic + Tenacity** | Strict inter-agent schemas, API retries, timeouts, and graceful fallback handling | Prevents malformed state handoffs and ensures safe fallback advice if external weather APIs time out |

---

## 6. Repository Structure

```
university-project/
├── project/
│   ├── main.py              # FastAPI + LangGraph entry point
│   ├── agents/              # Modular agent files
│   │   ├── orchestrator.py
│   │   ├── weather.py
│   │   ├── vision.py
│   │   ├── agronomy_rag.py
│   │   └── critic.py
│   ├── rag/                 # ChromaDB ingestion scripts
│   ├── eval/                # Benchmarking suite (N=30 scenarios)
│   ├── frontend/            # React PWA
│   └── logs/                # JSONL execution traces
└── docs/
    ├── Proposal.docx
    ├── Workflow.md
    └── PROJECT_DETAILS.md
```

> **Secret Hygiene:** All API keys are loaded strictly from `.env` (gitignored). Zero committed credentials.

---

## 7. Benchmarking Plan

To rigorously prove that our multi-agent design outperforms simpler alternatives, we run an **automated benchmarking script across 30 standardized Sri Lankan paddy scenarios** comparing three baselines:

| Baseline | Description |
|---|---|
| **Multi-Agent System (PaddyGuard MAS)** | Full 5-agent LangGraph workflow with Farm Profile memory, parallel specialists, and Safety Critic revision loop |
| **Single-Agent Baseline** | Same LLM backbone, same RRDI RAG retriever, and same Open-Meteo tool inside a single monolithic agent prompt without an independent Critic loop |
| **Human Baseline** | Timed manual consultation of RRDI/DOA manuals and district weather tables by knowledgeable reviewers to establish human-level accuracy and completion speed |

### Evaluation Metrics

| Metric Category | Test Suite Coverage (N = 30) | Evaluation Purpose |
|---|---|---|
| **Safety Conflict Catch Rate (%)** | 12 "trap" scenarios (imminent rain wash-off, high wind drift, wrong growth-stage fertilizer, PHI violations) | Measures the primary safety advantage of the independent Critic agent |
| **Agronomic & Memory Accuracy** | 0–5 rubric score on RRDI manual fidelity, correct crop-day calculation, and active questioning efficiency | Verifies factual grounding and multi-turn personalization quality |
| **Anti-Hallucination & HITL Precision** | 8 edge scenarios (blurry/unrelated photos, ambiguous symptoms, restricted chemicals, Weather API timeouts) | Confirms the system refuses to guess and escalates responsibly |
| **Latency & Operating Cost** | Mean/P95 end-to-end response time (seconds), total tokens, and estimated USD cost per 1,000 queries | Quantifies speed gain over humans and real-world deployment affordability |

---

## 8. Limitations & Ethical Considerations

- **Weather Uncertainty:** Tropical convective showers in Sri Lanka cannot be predicted with 100% precision. PaddyGuard MAS models weather as probabilistic risk tiers (Low/Moderate/High) and advises farmers to check local sky/wind conditions before spraying.
- **Safety & Anti-Hallucination:** Open web search is disabled for all chemical advice. The system prioritizes IPM and cultural controls, enforces RRDI dosage caps, refuses to guess on unclear photos, and clearly states it *complements — not replaces — certified Agricultural Instructors*.
- **Inclusivity & Anti-Bias:** Full Sinhala, Tamil, and English support with voice preview and TTS audio ensures accessibility regardless of literacy level. Manuals use generic active-ingredient names from public institutions rather than promoting commercial brands.
- **Privacy & Data Minimization:** No personally identifiable information (names, phone numbers, or exact home GPS coordinates) is required; farm profiles store only verified district/area tags and agronomic crop metadata.

---

## 9. References

1. Food and Agriculture Organization of the United Nations (FAO), *World Food and Agriculture – Statistical Yearbook*, Rome: FAO. https://www.fao.org/statistics
2. Department of Agriculture, Sri Lanka — Rice Research and Development Institute (RRDI), *Paddy Cultivation, Variety, Fertilizer, and Pest Management Recommendations*, Bathalagoda, Sri Lanka. https://doa.gov.lk
3. International Rice Research Institute (IRRI), *Rice Knowledge Bank: Pests, Diseases, and Crop Management Guidelines*, Los Banos, Philippines. http://www.knowledgebank.irri.org
4. Intergovernmental Panel on Climate Change (IPCC), *Climate Change 2022: Impacts, Adaptation and Vulnerability* (AR6 WG II, Chapter 5), Cambridge University Press.
5. Savary, S. et al. (2019). The global burden of pathogens and pests on major food crops. *Nature Ecology & Evolution*, 3(3), 430–439.
6. Open-Meteo, *Open-Source Weather Forecast API Documentation*. https://open-meteo.com/en/docs
7. LangChain / LangGraph Documentation, *Stateful Multi-Agent Workflows and Persistence*. https://langchain-ai.github.io/langgraph/
