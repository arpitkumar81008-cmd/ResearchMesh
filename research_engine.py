"""
research_engine.py — Core evidence pipeline for ResearchMesh.

Pipeline stages:
  0. generate_search_queries  — Gemini expands the question into 2 targeted queries.
  1. _discover_urls           — TinyFish Search (multi-query, deduplicated).
  2. _fetch_urls              — TinyFish Fetch (batch markdown extraction, up to 6 URLs).
  3. _escalate                — TinyFish Web Agent (optional, max 2 blocked/thin URLs).
  4. synthesize_report        — Gemini 2.5 Flash with Pydantic response_schema.

Public API
----------
  set_api_keys(tinyfish_key, gemini_key)   — Inject keys from Streamlit sidebar.
  generate_search_queries(question)        — Returns List[str] of queries.
  gather_evidence(...)                     — Returns (sources_data, source_refs).
  synthesize_report(question, sources_data)— Returns ResearchReport.
"""
from __future__ import annotations

import os
from typing import Callable, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from tinyfish import TinyFish

from models import ResearchReport, SourceReference

load_dotenv()

# ---------------------------------------------------------------------------
# Client singletons — lazily initialised; replaced by set_api_keys() at runtime
# ---------------------------------------------------------------------------
_tf_client: Optional[TinyFish] = None
_gemini_client: Optional[genai.Client] = None


def _get_tf() -> TinyFish:
    global _tf_client
    if _tf_client is None:
        key = os.getenv("TINYFISH_API_KEY", "").strip()
        if not key:
            raise ValueError(
                "TINYFISH_API_KEY is not set. Add it to .env or the sidebar."
            )
        _tf_client = TinyFish(api_key=key)
    return _tf_client


def _get_gc() -> genai.Client:
    global _gemini_client
    if _gemini_client is None:
        key = os.getenv("GEMINI_API_KEY", "").strip()
        if not key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Add it to .env or the sidebar."
            )
        _gemini_client = genai.Client(api_key=key)
    return _gemini_client


def set_api_keys(tinyfish_key: str, gemini_key: str) -> None:
    """Inject API keys at runtime (called from the Streamlit sidebar)."""
    global _tf_client, _gemini_client
    _tf_client = TinyFish(api_key=tinyfish_key.strip())
    _gemini_client = genai.Client(api_key=gemini_key.strip())


# ---------------------------------------------------------------------------
# Internal schema: query generation output
# ---------------------------------------------------------------------------
class _SearchQueriesOutput(BaseModel):
    queries: List[str] = Field(
        description="Exactly 2 distinct, complementary web search queries."
    )


_MODEL_CANDIDATES = [
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3.8-flash",
    "models/gemini-3.1-flash-lite",
    "models/gemini-3.5-flash-lite",
    "models/gemini-3.5-flash",
]


def _generate_with_fallback(
    contents,
    config,
    status_callback: Optional[Callable[[str], None]] = None,
):
    """
    Execute generation across tiered candidate models.
    Seamlessly falls back if a model encounters 429 RESOURCE_EXHAUSTED (free tier quota limit),
    503 UNAVAILABLE (high demand), 404 NOT_FOUND (model migration), or rate limiting.
    """
    last_err = None
    for model_name in _MODEL_CANDIDATES:
        try:
            return _get_gc().models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
        except Exception as exc:
            last_err = exc
            err_str = str(exc)
            # Inspect for recoverable errors: quota limits (429), high demand (503), model retirement (404), etc.
            is_recoverable = any(
                token in err_str
                for token in [
                    "429",
                    "RESOURCE_EXHAUSTED",
                    "quota",
                    "Quota",
                    "rate limit",
                    "503",
                    "UNAVAILABLE",
                    "high demand",
                    "404",
                    "NOT_FOUND",
                    "500",
                    "INTERNAL",
                ]
            )
            clean_model = model_name.replace("models/", "")
            if is_recoverable:
                notice = f"⚡ Gemini `{clean_model}` quota/capacity busy. Auto-falling back to next model..."
                if status_callback:
                    try:
                        status_callback(notice)
                    except Exception:
                        pass
                print(f"[Gemini Fallback] {clean_model} -> {type(exc).__name__}: {err_str[:80]}... Trying next.")
                continue
            else:
                print(f"[Gemini Fallback] Non-standard exception on {clean_model}: {exc}. Trying next candidate...")
                continue

    if last_err:
        raise last_err


# ---------------------------------------------------------------------------
# Stage 0: Query generation
# ---------------------------------------------------------------------------
def generate_search_queries(
    question: str,
    status_callback: Optional[Callable[[str], None]] = None,
    *args,
    **kwargs,
) -> List[str]:
    """
    Use Gemini to expand the research question into 2 complementary search queries.

    Query 1 targets primary claims and statistics.
    Query 2 targets counterarguments, critiques, or alternative viewpoints.

    Falls back to [question] if Gemini fails.
    """
    prompt = (
        f"Research question: {question}\n\n"
        "Generate exactly 2 distinct, complementary web search queries that together "
        "maximise coverage of factual evidence and different perspectives.\n"
        "- Query 1: target primary claims, recent findings, and key statistics.\n"
        "- Query 2: target counterarguments, limitations, critiques, or alternative views.\n"
        "Return JSON only."
    )
    try:
        response = _generate_with_fallback(
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=_SearchQueriesOutput,
                temperature=0.3,
            ),
            status_callback=status_callback,
        )
        parsed: _SearchQueriesOutput = response.parsed
        queries = [q.strip() for q in parsed.queries if q.strip()]
        return queries[:2] if queries else [question]
    except Exception:
        # Graceful fallback — use the original question verbatim
        return [question]


# ---------------------------------------------------------------------------
# Stage 1: Source discovery
# ---------------------------------------------------------------------------
def _discover_urls(
    queries: List[str],
    domain_type: str,
    question: str,
    max_sources: int,
    status_cb: Callable[[str], None],
) -> Dict[str, dict]:
    """
    Run each search query and collect deduplicated URL → metadata mapping.
    Results are ordered by discovery rank (TinyFish returns ranked results).
    """
    seen: Dict[str, dict] = {}  # url → {title, snippet, site_name}

    for i, query in enumerate(queries, 1):
        status_cb(f"🔍 **Search {i}/{len(queries)}:** `{query}`")
        try:
            res = _get_tf().search.query(
                query=query,
                purpose=f"Researching evidence and claims for: {question}",
                domain_type=domain_type,
            )
            added = 0
            for item in res.results:
                if item.url not in seen:
                    seen[item.url] = {
                        "title": getattr(item, "title", None) or item.url,
                        "snippet": getattr(item, "snippet", "") or "",
                        "site_name": getattr(item, "site_name", None)
                        or urlparse(item.url).netloc,
                    }
                    added += 1
            status_cb(f"   ↳ Found {len(res.results)} results, {added} new unique URLs.")
        except Exception as exc:
            status_cb(f"   ↳ ⚠️ Search query {i} failed: {exc}")

    # Trim to max_sources (preserve discovery rank)
    top = dict(list(seen.items())[:max_sources])
    status_cb(
        f"📋 **{len(top)} unique sources** selected from {len(seen)} discovered URLs."
    )
    return top


# ---------------------------------------------------------------------------
# Stage 2: Batch content retrieval
# ---------------------------------------------------------------------------
def _fetch_urls(
    urls: List[str],
    question: str,
    status_cb: Callable[[str], None],
) -> Tuple[List, List]:
    """
    Batch-fetch up to 6 URLs via TinyFish Fetch.
    Returns (results_list, errors_list) from the fetch response.
    """
    batch = urls[:6]  # API guidance: keep to 5-6 for speed
    status_cb(f"📥 **TinyFish Fetch:** retrieving {len(batch)} URLs in parallel…")
    try:
        res = _get_tf().fetch.get_contents(
            urls=batch,
            format="markdown",
            purpose=f"Extract factual claims, dates, and evidence regarding: {question}",
            per_url_timeout_ms=30000,
        )
        success_count = len(res.results)
        error_count = len(res.errors)
        status_cb(
            f"   ↳ ✅ {success_count} succeeded · ❌ {error_count} failed/blocked."
        )
        return res.results, res.errors
    except Exception as exc:
        status_cb(f"   ↳ ❌ Fetch stage error: {exc}")
        return [], []


# ---------------------------------------------------------------------------
# Stage 3: Web Agent escalation
# ---------------------------------------------------------------------------
_THIN_CONTENT_THRESHOLD = 250  # characters — below this we consider a page "thin"
_MAX_AGENT_ESCALATIONS = 2     # wallet-safe ceiling


def _escalate(
    candidates: List[str],
    question: str,
    status_cb: Callable[[str], None],
) -> Dict[str, str]:
    """
    Escalate up to _MAX_AGENT_ESCALATIONS blocked/thin URLs to TinyFish Web Agent.
    Returns url → extracted_text for successfully recovered pages.
    """
    recovered: Dict[str, str] = {}
    limit = min(len(candidates), _MAX_AGENT_ESCALATIONS)

    for url in candidates[:limit]:
        status_cb(f"🤖 **TinyFish Web Agent** escalating: `{url}`")
        try:
            agent_res = _get_tf().agent.run(
                url=url,
                goal=(
                    "Navigate past any cookie banners, login walls, paywalls, "
                    "or JavaScript-rendered interactive tabs and extract the main "
                    "factual claims, statistics, and dates that answer: "
                    f"{question}"
                ),
            )
            text = (agent_res.result or "").strip()
            if text:
                recovered[url] = text
                status_cb(
                    f"   ↳ ✅ Recovered **{len(text):,} chars** via Web Agent."
                )
            else:
                status_cb(f"   ↳ ⚠️ Web Agent returned empty result for `{url}`.")
        except Exception as exc:
            status_cb(f"   ↳ ❌ Web Agent failed for `{url}`: {exc}")

    return recovered


# ---------------------------------------------------------------------------
# Public: gather_evidence
# ---------------------------------------------------------------------------
def gather_evidence(
    question: str,
    queries: List[str],
    max_sources: int = 5,
    use_web_agent: bool = False,
    domain_type: str = "web",
    status_callback: Callable[[str], None] = print,
) -> Tuple[List[dict], List[SourceReference]]:
    """
    Full three-stage evidence pipeline:
      1. Search (multi-query, deduplication, rank-order selection).
      2. Fetch (batch markdown retrieval).
      3. Agent escalation for errors + thin content (optional, capped at 2).

    Parameters
    ----------
    question       : The user's research question (forwarded as `purpose`).
    queries        : Search queries from generate_search_queries().
    max_sources    : Maximum number of sources to process (3–8).
    use_web_agent  : Whether to escalate blocked/thin pages to agent.run().
    domain_type    : TinyFish domain filter — "web", "news", "research_paper".
    status_callback: Callable that receives human-readable progress strings.

    Returns
    -------
    sources_data   : List[dict] — rich content dicts passed to synthesize_report().
    source_refs    : List[SourceReference] — citation metadata for the UI.
    """
    # ── Stage 1: Discovery ──────────────────────────────────────────────────
    url_meta = _discover_urls(queries, domain_type, question, max_sources, status_callback)
    if not url_meta:
        status_callback("❌ No URLs discovered. Check your API key and try a broader query.")
        return [], []

    ordered_urls = list(url_meta.keys())

    # ── Stage 2: Fetch ──────────────────────────────────────────────────────
    fetch_results, fetch_errors = _fetch_urls(ordered_urls, question, status_callback)

    # Index successes by URL for fast lookup
    fetched: Dict[str, object] = {page.url: page for page in fetch_results}

    # ── Identify escalation candidates ──────────────────────────────────────
    # Priority: hard errors first, then thin content (< threshold chars)
    error_urls: List[str] = [err.url for err in fetch_errors]
    thin_urls: List[str] = [
        page.url
        for page in fetch_results
        if len(getattr(page, "text", "") or "") < _THIN_CONTENT_THRESHOLD
    ]
    # Deduplicate while preserving order
    seen_cands: set = set()
    escalation_candidates: List[str] = []
    for u in error_urls + thin_urls:
        if u not in seen_cands:
            seen_cands.add(u)
            escalation_candidates.append(u)

    # ── Stage 3: Agent escalation (optional) ────────────────────────────────
    agent_texts: Dict[str, str] = {}
    if escalation_candidates:
        if use_web_agent:
            status_callback(
                f"🚦 {len(escalation_candidates)} URL(s) need escalation "
                f"(errors: {len(error_urls)}, thin: {len(thin_urls)}). "
                f"Escalating up to {_MAX_AGENT_ESCALATIONS} via TinyFish Web Agent…"
            )
            agent_texts = _escalate(escalation_candidates, question, status_callback)
        else:
            status_callback(
                f"ℹ️  {len(escalation_candidates)} URL(s) failed or returned thin content. "
                f"Enable **Web Agent Escalation** in the sidebar to recover them."
            )

    # ── Build sources_data + source_refs ────────────────────────────────────
    sources_data: List[dict] = []
    source_refs: List[SourceReference] = []
    source_id = 1

    for url in ordered_urls:
        meta = url_meta[url]
        domain = urlparse(url).netloc

        page = fetched.get(url)
        page_text = (getattr(page, "text", "") or "") if page else ""
        page_title = (getattr(page, "title", "") or "") if page else ""
        published_date = getattr(page, "published_date", None) if page else None
        author = getattr(page, "author", None) if page else None

        # Determine final text and retrieval method
        if page and len(page_text) >= _THIN_CONTENT_THRESHOLD:
            # ✅ Clean fetch
            text = page_text
            retrieval_method: str = "TinyFish Fetch"
            title = page_title or meta["title"]
        elif url in agent_texts:
            # ✅ Recovered by Web Agent
            text = agent_texts[url]
            retrieval_method = "TinyFish Web Agent"
            title = meta["title"]
            published_date = None
            author = None
        elif page and page_text:
            # ⚠️  Thin fetch — use what was returned
            text = page_text
            retrieval_method = "TinyFish Fetch"
            title = page_title or meta["title"]
        elif meta.get("snippet"):
            # ⚠️  Complete failure — fall back to search snippet
            text = meta["snippet"]
            retrieval_method = "TinyFish Fetch"
            title = meta["title"]
            published_date = None
            author = None
        else:
            # ❌ No content at all — skip this URL
            status_callback(f"   ↳ Skipping `{url}` — no content available.")
            continue

        sources_data.append(
            {
                "source_id": source_id,
                "url": url,
                "title": title,
                "domain": domain,
                "published_date": str(published_date) if published_date else None,
                "author": author,
                "text": text,
                "char_count": len(text),
                "retrieval_method": retrieval_method,
            }
        )
        source_refs.append(
            SourceReference(
                source_id=source_id,
                title=title,
                url=url,
                domain=domain,
                published_date=str(published_date) if published_date else None,
                retrieval_method=retrieval_method,  # type: ignore[arg-type]
            )
        )
        source_id += 1

    status_callback(
        f"📚 **{len(sources_data)} sources** ready for synthesis "
        f"(total content: {sum(s['char_count'] for s in sources_data):,} chars)."
    )
    return sources_data, source_refs


# ---------------------------------------------------------------------------
# Stage 4: LLM synthesis
# ---------------------------------------------------------------------------
_SYNTHESIS_SYSTEM_PROMPT = """\
You are a rigorous, impartial research analyst. You will receive a research \
question and a numbered list of source excerpts tagged [1], [2], etc.

Your task is to produce a structured ResearchReport JSON by following these \
rules exactly:

CROSS-EXAMINATION RULES
  • "Corroborated" — At least 2 sources independently confirm the same factual \
point. List all supporting source_ids.
  • "Conflicting" — At least 2 sources make contradictory factual claims about \
the same point. You MUST populate conflict_explanation with: which sources say \
what, and why they disagree. List supporting_sources and contradicting_sources \
on opposite sides.
  • "Single-Source" — Only one source mentions this claim.

CITATION RULES
  • Every claim sentence in executive_summary must end with [source_id].
  • Every evidence_quote must end with [source_id].
  • Timeline event strings may embed [source_id] inline.
  • Never cite a source_id that was not provided to you.

TIMELINE RULES
  • Extract only events that have an explicit date in the source text.
  • Format dates as YYYY, YYYY-MM, or YYYY-MM-DD.
  • Do NOT fabricate or infer dates.
  • Sort chronologically oldest → newest.

EXECUTIVE SUMMARY RULES
  • Write 3-4 dense, connected paragraphs.
  • Open with the overall state of evidence.
  • Address the main consensus and its strength.
  • Describe the most important conflict(s) if any.
  • Close with what the evidence does NOT yet resolve.

FOLLOW-UP QUESTIONS
  • Propose 3-4 questions that the evidence raises but does not answer.
  • They should guide the next research iteration, not restate the original.

OUTPUT
  • Return only a single JSON object conforming to the ResearchReport schema.
  • No markdown fences, no prose outside the JSON.
"""


def synthesize_report(
    question: str,
    sources_data: List[dict],
    status_callback: Optional[Callable[[str], None]] = None,
    *args,
    **kwargs,
) -> ResearchReport:
    """
    Pass the collected source corpus to Gemini and extract a
    validated ResearchReport using Pydantic structured output.

    Each source is truncated to 8,000 chars to stay within token budget.
    Falls back to manual JSON parsing if response.parsed is None.

    Raises
    ------
    ValueError   if sources_data is empty.
    Exception    propagated from Gemini if the API call fails entirely.
    """
    if not sources_data:
        raise ValueError("No sources available — cannot synthesize a report.")

    # Build the numbered source corpus
    corpus_blocks: List[str] = []
    for s in sources_data:
        text_excerpt = (s.get("text") or "")[:8000]
        corpus_blocks.append(
            f"--- SOURCE [{s['source_id']}] ---\n"
            f"Title: {s['title']}\n"
            f"URL: {s['url']}\n"
            f"Published: {s.get('published_date') or 'Unknown'}\n"
            f"Author: {s.get('author') or 'Unknown'}\n"
            f"Domain: {s['domain']}\n\n"
            f"{text_excerpt}\n"
        )

    corpus = "\n".join(corpus_blocks)
    user_prompt = (
        f"RESEARCH QUESTION:\n{question}\n\n"
        f"SOURCE CORPUS ({len(sources_data)} sources):\n"
        f"{corpus}\n\n"
        "Produce the ResearchReport JSON now."
    )

    response = _generate_with_fallback(
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=_SYNTHESIS_SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=ResearchReport,
            temperature=0.1,
        ),
        status_callback=status_callback,
    )

    # Primary path: typed .parsed attribute
    if getattr(response, "parsed", None) is not None:
        return response.parsed  # type: ignore[return-value]

    # Fallback: validate raw JSON text
    return ResearchReport.model_validate_json(response.text)
