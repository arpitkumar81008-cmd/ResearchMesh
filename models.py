"""
models.py — Pydantic schemas for ResearchMesh structured LLM outputs.

These schemas are passed directly to Gemini's `response_schema` parameter,
enforcing deterministic, typed JSON extraction on every synthesis call.
"""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class SourceReference(BaseModel):
    """Citation metadata for a single retrieved source."""

    source_id: int = Field(
        description="1-indexed citation number used as [1], [2], etc. throughout the report."
    )
    title: str = Field(description="Page or article title.")
    url: str = Field(description="Canonical URL of the source.")
    domain: str = Field(description="Hostname/domain of the source (e.g. 'nature.com').")
    published_date: Optional[str] = Field(
        default=None,
        description="ISO date string or human-readable date when available.",
    )
    retrieval_method: Literal["TinyFish Fetch", "TinyFish Web Agent"] = Field(
        description="Which TinyFish primitive retrieved this page's content."
    )


class ClaimItem(BaseModel):
    """A single extracted factual claim, cross-examined across sources."""

    topic: str = Field(
        description="Sub-theme or category grouping this claim (e.g. 'Health Outcomes', 'Economic Impact')."
    )
    claim: str = Field(
        description="The core assertion or finding, stated as a complete declarative sentence."
    )
    status: Literal["Corroborated", "Conflicting", "Single-Source"] = Field(
        description=(
            "Corroborated: 2+ sources agree. "
            "Conflicting: 2+ sources make contradictory factual claims. "
            "Single-Source: only one source mentions this."
        )
    )
    supporting_sources: List[int] = Field(
        description="List of source_id values whose content supports this claim."
    )
    contradicting_sources: List[int] = Field(
        default_factory=list,
        description="List of source_id values that dispute or contradict this claim.",
    )
    evidence_quotes: List[str] = Field(
        description=(
            "Short verbatim excerpts or key data points from the sources. "
            "Each quote must end with a [source_id] tag, e.g. '...mortality rose 12%% [3]'."
        )
    )
    conflict_explanation: Optional[str] = Field(
        default=None,
        description=(
            "Required when status is 'Conflicting'. "
            "Explains specifically HOW the sources disagree and which side each takes."
        ),
    )


class TimelineEvent(BaseModel):
    """A single datable event extracted from the source corpus."""

    date: str = Field(
        description="Date in YYYY, YYYY-MM, or YYYY-MM-DD format. Do not fabricate dates."
    )
    event: str = Field(
        description="What happened at this date. May include a [source_id] inline citation."
    )
    source_id: int = Field(description="The source_id from which this event was extracted.")


class ResearchReport(BaseModel):
    """
    Full structured research report produced by Gemini from the source corpus.
    All claims and summary text must cite sources using [source_id] notation.
    """

    question: str = Field(description="The original research question, verbatim.")
    executive_summary: str = Field(
        description=(
            "A 3-4 paragraph synthesis of the key findings. "
            "Must use inline [source_id] citations throughout. "
            "Should cover the main consensus, key conflicts, and overall state of evidence."
        )
    )
    claims: List[ClaimItem] = Field(
        description="Exhaustive list of distinct factual claims extracted and cross-examined."
    )
    timeline: List[TimelineEvent] = Field(
        description="Chronological list of datable events, sorted oldest to newest."
    )
    follow_up_questions: List[str] = Field(
        description=(
            "3-4 deeper research questions that the evidence raises but does not fully answer. "
            "Should guide the next research iteration."
        )
    )
