from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class VisibilityResult(BaseModel):
    brand_name: str
    visibility_score: float
    mentions: int
    samples: int
    raw_responses: list[str] = Field(default_factory=list)


class CitationResult(BaseModel):
    top_domains: list[str] = Field(default_factory=list)
    domain_counts: dict[str, int] = Field(default_factory=dict)
    citation_share: float = 0.0
    brand_domain_mentions: int = 0
    total_citation_mentions: int = 0


class GroundingResult(BaseModel):
    static_mentions: int = 0
    web_mentions: int = 0


class EvidenceGap(BaseModel):
    gap_type: str
    confidence: str
    evidence: list[str] = Field(default_factory=list)


class AuditReport(BaseModel):
    brand_name: str
    brand_website: str
    prompts_used: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    visibility: Optional[VisibilityResult] = None
    competitors: dict[str, int] = Field(default_factory=dict)
    citations: Optional[CitationResult] = None
    grounding: Optional[GroundingResult] = None
    evidence_gaps: list[EvidenceGap] = Field(default_factory=list)
    quick_wins: list[str] = Field(default_factory=list)
    status: str = "complete"
