from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class AuditRequest(BaseModel):
    url: str = Field(..., description="Adres URL strony internetowej do audytu SEO")
    content: Optional[str] = Field(None, description="Opcjonalny początkowy tekst lub prompt użytkownika")

class TechnicalMetrics(BaseModel):
    url: str
    title: str
    title_len: int
    description: str
    description_len: int
    keywords: str
    h1s: List[str]
    h1_count: int
    h2_count: int
    h3_count: int
    h2s_sample: List[str]
    h3s_sample: List[str]
    total_images: int
    images_missing_alt: int
    images_with_empty_alt: int
    canonical: str
    robots: str
    og_title: str
    og_description: str
    og_image: str
    lang: str
    word_count: int
    robots_txt_status: int
    sitemap_xml_status: int
    top_words: List[str]
    top_bigrams: List[str]
    domain: str
    schema_types: List[str]
    https_status: bool

class AuditResponse(BaseModel):
    metrics: TechnicalMetrics
    audit_report: str = Field(..., description="Szczegółowy raport audytu SEO wygenerowany przez Gemini")

class GapItem(BaseModel):
    present: bool
    value: str
    question: str

class GapAnalysisResponse(BaseModel):
    locality: GapItem
    target_audience: GapItem
    usp: GapItem

class RefineSEORequest(BaseModel):
    content: str = Field(..., description="Pierwotny opis lub prompt użytkownika")
    locality: Optional[str] = Field("", description="Wybrana lokalizacja / zasięg działania")
    target_audience: Optional[str] = Field("", description="Zdefiniowana grupa docelowa")
    usp: Optional[str] = Field("", description="Wyróżniki oferty (USP) / Główne usługi")
    website_analysis: Optional[str] = Field("", description="Kontekst / raport techniczny dotychczasowej strony")

class SEODataResponse(BaseModel):
    file_target: str
    title: str
    description: str
    keywords: str
    content: str
    is_valid: bool
