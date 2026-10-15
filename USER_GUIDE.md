# ResearchMesh — User Guide & Architecture Manual

**ResearchMesh** is an autonomous, evidence-backed research intelligence agent. It replaces manual web searching, copying, pasting, and reconciling disparate sources with an automated, 4-stage cross-examination pipeline.

Powered by:
- **TinyFish Web & Agent Infrastructure** (`tinyfish` SDK)
- **Google Gemini 3.8 Flash** (`google-genai` SDK) with native Structured Outputs
- **Streamlit** modern design-system UI conforming to [DESIGN.md](DESIGN.md)

---

## Table of Contents
1. [Core Features](#1-core-features)
2. [Architecture & The Escalation Ladder](#2-architecture--the-escalation-ladder)
3. [Quickstart & Setup](#3-quickstart--setup)
4. [Step-by-Step Walkthrough](#4-step-by-step-walkthrough)
5. [Understanding Your Report](#5-understanding-your-report)
6. [Best Practices & Query Tips](#6-best-practices--query-tips)
7. [Exporting & Integration](#7-exporting--integration)
8. [Troubleshooting & FAQs](#8-troubleshooting--faqs)

---

## 1. Core Features

- **Multi-Perspective Search**: Gemini analyzes your question and decomposes it into 2 complementary search queries (consensus/data vs. counterarguments/critiques).
- **Parallel Markdown Extraction**: TinyFish Fetch retrieves up to 6 pages simultaneously, stripping HTML bloat, scripts, and trackers into clean Markdown.
- **Autonomous Web Agent Rescue**: When pages are behind cookie banners, interactive single-page apps (SPAs), or anti-bot walls, the pipeline automatically escalates to a live browser agent to recover the evidence.
- **Deterministic Conflict Detection**: Claims are classified strictly into:
  - `Corroborated`: 2+ independent sources agree.
  - `Conflicting`: 2+ sources present opposing assertions, with explicit rationale.
  - `Single-Source`: Reported by a single source only.
- **Automated Chronology**: Datable milestones and events extracted chronologically into a timeline.
- **One-Click Exports**: Publication-ready Markdown (`.md`) with inline citation links, and raw structured JSON (`.json`) bundles.

---

## 2. Architecture & The Escalation Ladder

ResearchMesh uses a deterministic 4-stage pipeline that minimizes cost and latency while maximizing data extraction quality:

```
[ User Question ]
       │
       ▼
[ Stage 0: Query Generation ] ─── Gemini 3.8 Flash generates 2 balanced queries
       │
       ▼
[ Stage 1: Source Discovery ] ─── TinyFish Search (queries deduplicated & ranked)
       │
       ▼
[ Stage 2: Content Retrieval ] ── TinyFish Fetch (parallel Markdown extraction)
       │
       ├─► Clean content (≥ 250 chars) ──────────────────────────┐
       │                                                         │
       └─► Blocked / Thin (< 250 chars)                          │
             │                                                   │
             ▼                                                   ▼
     [ Stage 3: Escalation ]                             [ Unified Corpus ]
     TinyFish Web Agent                                          │
     (Autonomous browser navigation, max 2 URLs)                 │
             │                                                   │
             └───────────────────────────────────────────────────┘
                                       │
                                       ▼
                         [ Stage 4: Cross-Examination ]
                             Gemini 3.8 Flash
                      (Strict Pydantic JSON Schema)
                                       │
                                       ▼
                       [ Interactive Streamlit Dashboard ]
                       Summary · Claims · Timeline · Sources
```

### The Cost-Conscious Escalation Ladder
1. **TinyFish Search (`client.search.query`)**: Fast search querying across general web, news, or academic papers.
2. **TinyFish Fetch (`client.fetch.get_contents`)**: Fast, lightweight Chromium rendering that extracts clean markdown without agent overhead.
3. **TinyFish Web Agent (`client.agent.run`)**: Reserved for hard walls (interactive tabs, paywalls, consent overlays). Only triggered if the user enables the toggle in the sidebar and content fails or is thinner than 250 characters. Capped at 2 URLs to protect your wallet balance.

---

## 3. Quickstart & Setup

### Prerequisites
- Python 3.10 or higher
- A [TinyFish API Key](https://agent.tinyfish.ai/api-keys)
- A [Google Gemini API Key](https://aistudio.google.com/app/apikey)

### Installation

1. **Clone or navigate to the repository directory**:
   ```bash
   cd c:\Users\arpit\Documents\antigravity\adventurous-hypatia
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Keys**:
   Create or edit your `.env` file:
   ```ini
   TINYFISH_API_KEY=your_tinyfish_key_here
   GEMINI_API_KEY=your_gemini_key_here
   ```
   *(Note: You can also enter or override these keys directly in the web UI sidebar at runtime).*

4. **Launch the Application**:
   ```bash
   python -m streamlit run app.py
   ```
   Open your browser at `http://localhost:8501`.

---

## 4. Step-by-Step Walkthrough

### Step 1: Sidebar Configuration
On the left sidebar, configure your run parameters:
- **API Keys**: Ensure both keys are present.
- **Search Domain**:
  - `Web — general`: Best for general knowledge, technical guides, industry trends.
  - `News — recent events`: Ideal for breaking news, policy changes, quarterly earnings.
  - `Papers — academic`: Focuses on scientific literature, clinical trials, peer-reviewed journals.
- **Max Sources Slider**: Choose between 3 and 8 sources (5 is the recommended default for speed and depth).
- **Web Agent Escalation**: Check this box if you expect the topic to hit gated or JavaScript-heavy pages (e.g., Bloomberg, Substack, paywalled publications).

### Step 2: Formulate Your Question
Enter a specific, falsifiable question in the main text area. Examples:
- *"What are the documented cardiovascular risks of ultra-processed foods in long-term cohort studies?"*
- *"How do solid-state battery energy densities compare with current lithium-ion in 2025/2026?"*
- *"What are the primary antitrust arguments for and against major cloud provider bundling practices?"*

### Step 3: Run the Pipeline
Click **Run ResearchMesh** (`Enter` or mouse click). Watch the live status feed expand in real time:
- Query generation progress
- Discovered URLs and deduplication count
- Parallel fetch completions
- Web Agent recovery (if active)
- Gemini cross-examination synthesis

---

## 5. Understanding Your Report

Once complete, the dashboard renders the top metric strip and 4 tabs:

### Metric Strip
- **Sources**: Total verified sources contributing to the report.
- **Claims**: Total discrete factual assertions identified.
- **Corroborated**: Assertions backed by 2 or more distinct sources.
- **Conflicting**: Assertions where sources disagree or report conflicting data.
- **Single-Source**: Points mentioned by only one source.

### Tab 1: Summary
- **Executive Summary**: A cohesive synthesis written with inline bracketed citations (`[1]`, `[2]`).
- **Follow-Up Questions**: 3–4 logical next-step questions identified by the agent. Clicking any follow-up question immediately pre-fills the input box so you can run the next iteration instantly.

### Tab 2: Claims & Conflict Matrix
- Use the **Filter** pill toggle to view `All`, `Corroborated`, `Conflicting`, or `Single-Source` claims.
- **Corroborated Claims**: Highlighted with supporting source IDs.
- **Conflicting Claims**: Automatically expanded in a high-contrast dark callout card detailing the exact nature of the dispute, which source took which position, and verbatim evidence quotes.

### Tab 3: Timeline
- Chronological breakdown of dates and historical milestones extracted from the articles.
- Each event is linked to its originating source domain.

### Tab 4: Sources
- Structured comparison table displaying the Title, Domain, Publication Date, and Retrieval Method (`TinyFish Fetch` vs. `TinyFish Web Agent`).
- Direct, clickable hyperlinks to all original web articles.

---

## 6. Best Practices & Query Tips

| Goal | Recommended Settings | Example Prompt Structure |
|---|---|---|
| **Scientific / Medical** | Domain: `Papers`, Sources: `6-8` | *"What clinical evidence exists regarding [Intervention] for [Condition]?"* |
| **Market / Company Analysis** | Domain: `News`, Web Agent: `ON` | *"What were the stated financial results and subscriber changes for [Company] in Q3/Q4?"* |
| **Tech Architecture / Comparison** | Domain: `Web`, Sources: `5` | *"What are the architectural trade-offs between [Technology A] and [Technology B]?"* |

---

## 7. Exporting & Integration

At the bottom of the page, two export options are available:
- **Download report (`.md`)**: A self-contained Markdown file with headers, tables, callouts, and a complete bibliography. Perfect for pasting into Obsidian, Notion, GitHub PRs, or publishing.
- **Download evidence (`.json`)**: Machine-readable JSON output containing the full Pydantic data bundle (claims, source metadata, timeline events, and execution stats). Ideal for ingestion into vector databases, downstream agents, or automated CI/CD pipelines.

---

## 8. Troubleshooting & FAQs

**Q: The search returns 0 results.**  
A: Check that your TinyFish API key is valid. Try rephrasing your question to use more standard terminology, or switch the domain from `Papers` to `Web`.

**Q: Why didn't the Web Agent fire?**  
A: Web Agent escalation only fires if the toggle is checked in the sidebar AND at least one URL either failed HTTP retrieval or returned under 250 characters of text. If all pages fetched cleanly, Web Agent is skipped to save your credits.

**Q: Can I run ResearchMesh in headless mode?**  
A: Yes! Run:
```bash
python -m streamlit run app.py --server.headless true
```
