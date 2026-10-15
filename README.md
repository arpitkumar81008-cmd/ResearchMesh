# ResearchMesh ⬡
### Evidence-Backed Autonomous Research Agent

> Discovers web sources with **TinyFish Search**, extracts clean markdown via **TinyFish Fetch**, rescues blocked pages via **TinyFish Web Agent**, and synthesizes cross-examined, conflict-aware evidence reports using **Google Gemini** (`gemini-3.5-flash`, `gemini-3.1-flash-lite`, `gemini-3.6-flash`) with dynamic 429/503 quota & rate fallback and Pydantic Structured Outputs.

---

## ⚡ Quickstart

```bash
# 1. Install requirements
pip install -r requirements.txt

# 2. Configure keys (or input in UI)
copy .env.example .env

# 3. Launch UI
python -m streamlit run app.py
```

Then visit [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🛠️ Tech Stack & Architecture

- **Web Discovery & Fetch**: [TinyFish](https://tinyfish.ai) SDK (`tinyfish`)
  - `client.search.query`: Multi-query search across `web`, `news`, and `research_paper`
  - `client.fetch.get_contents`: Parallel Chromium-rendered Markdown extraction
  - `client.agent.run`: Autonomous Web Agent escalation for login/paywalls and JS-rendered pages
- **Reasoning & Synthesis**: Google GenAI SDK (`google-genai`)
  - Models: Tiered fallback (`gemini-3.5-flash`, `gemini-3.1-flash-lite`, `gemini-3.6-flash`, `gemini-3.8-flash`)
  - Resilient to 429 RESOURCE_EXHAUSTED free-tier daily limits and 503 capacity spikes
  - Strict JSON enforcement with `response_schema=ResearchReport` via Pydantic
- **UI & Export**: Streamlit (`streamlit`) styled with an editorial, minimalist design system (see [DESIGN.md](DESIGN.md))
- **Documentation**: Detailed instructions in [USER_GUIDE.md](USER_GUIDE.md)

---

## 📁 Repository Structure

```text
├── app.py              # Streamlit dashboard & Ollama-inspired design system UI
├── research_engine.py  # 4-stage pipeline (query expansion, search, fetch, escalation, synthesis)
├── models.py           # Pydantic schemas (ResearchReport, ClaimItem, TimelineEvent, SourceReference)
├── exporter.py         # Markdown (.md) and JSON (.json) report generators
├── DESIGN.md           # Product design tokens & visual system reference
├── USER_GUIDE.md       # Full user manual and query best practices
├── requirements.txt    # Production dependencies
└── .env.example        # Environment variable template
```

---

## 🤝 Community & Acknowledgements

This project was built by **Arpit Kumar** as part of a hands-on learning initiative exploring autonomous AI agents, in collaboration with the **TechnoJam Club** at **Galgotias University** during an interactive workshop on Agentic AI and multi-modal reasoning.

Special thanks to the TechnoJam student community and mentors for fostering an environment of hands-on experimentation and collaborative learning!

---

## 📄 License
MIT
