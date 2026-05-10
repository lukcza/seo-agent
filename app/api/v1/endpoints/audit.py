from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from typing import List, Dict, Any, Optional
from app.schemas.seo import (
    AuditRequest,
    AuditResponse,
    GapAnalysisResponse,
    RefineSEORequest,
    SEODataResponse
)
from app.services.website_analyzer import scrape_website_seo
from app.services.prompter import (
    get_refined_seo_data,
    assess_prompt_gaps,
    analyze_scraped_seo,
    verify_seo_data
)
from app.models.seo import SEOData
from app.core.database import SEODatabaseManager

router = APIRouter()

@router.post("/technical", response_model=AuditResponse)
async def analyze_website_technical(request: AuditRequest):
    """
    Pobiera i analizuje strukturę SEO wskazanego adresu URL oraz generuje merytoryczny raport AI.
    """
    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Adres URL nie może być pusty.")
    
    # Pobranie danych technicznych i struktury SEO witryny
    scraped_data = scrape_website_seo(url)
    if "error" in scraped_data:
        raise HTTPException(status_code=400, detail=scraped_data["error"])
        
    # Generowanie merytorycznego raportu z audytu przy użyciu LLM
    audit_report = await analyze_scraped_seo(scraped_data)
    
    return {
        "metrics": scraped_data,
        "audit_report": audit_report
    }

@router.post("/gaps", response_model=GapAnalysisResponse)
async def analyze_prompt_gaps(request_data: Dict[str, Any]):
    """
    Analizuje opis użytkownika i kontekst strony, aby wykryć braki w 3 kluczowych aspektach:
    Lokalizacja, Grupa docelowa, USP. Zwraca spersonalizowane pytania.
    """
    content = request_data.get("content", "")
    website_context = request_data.get("website_context", "")
    
    if not content and not website_context:
        raise HTTPException(status_code=400, detail="Musisz podać początkowy tekst lub kontekst strony do analizy.")
        
    gaps = await assess_prompt_gaps(content, website_context)
    return gaps

@router.post("/refine", response_model=SEODataResponse)
async def generate_refined_seo(request: RefineSEORequest):
    """
    Generuje ostateczny zestaw zoptymalizowanych pod kątem SEO danych wejściowych (Title, Description, Keywords, Content)
    na podstawie zebranych uszczegółowień.
    """
    if not request.content.strip():
        raise HTTPException(status_code=400, detail="Treść początkowa nie może być pusta.")
        
    seo_data = await get_refined_seo_data(
        content=request.content,
        locality=request.locality,
        target_audience=request.target_audience,
        usp=request.usp,
        website_analysis=request.website_analysis
    )
    
    if not seo_data:
        raise HTTPException(status_code=500, detail="Nie udało się wygenerować danych SEO przy użyciu Gemini API.")
        
    is_valid = verify_seo_data(seo_data)
    
    return {
        "file_target": "api_refined",
        "title": seo_data.title,
        "description": seo_data.description,
        "keywords": seo_data.keywords,
        "content": seo_data.content,
        "is_valid": is_valid
    }

@router.post("/save", status_code=status.HTTP_201_CREATED)
async def save_audit_result(data: Dict[str, Any]):
    """
    Zapisuje wygenerowane dane SEO do lokalnej bazy danych SQLite.
    """
    target = data.get("file_target", "api_refined").strip()
    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    keywords = data.get("keywords", "").strip()
    content = data.get("content", "").strip()
    
    if not target or not title:
        raise HTTPException(status_code=400, detail="Identyfikator docelowy i tytuł są wymagane do zapisu.")
        
    db_manager = SEODatabaseManager()
    
    seo_obj = SEOData(
        file_target=target,
        title=title,
        description=description,
        keywords=keywords,
        content=content
    )
    
    try:
        existing = db_manager.get_from_database(target)
        if existing:
            db_manager.update_database(seo_obj)
        else:
            db_manager.save_to_database(seo_obj)
        return {"status": "success", "message": f"Zapisano pomyślnie pod identyfikatorem '{target}'."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd zapisu w bazie danych: {e}")

@router.get("/history", response_model=List[Dict[str, Any]])
async def get_audit_history():
    """
    Zwraca listę wszystkich zapisanych audytów z bazy danych.
    """
    db_manager = SEODatabaseManager()
    db_manager._init_db()
    
    try:
        db_manager.cursor.execute("SELECT file_target, seo_title, seo_description, seo_keywords, seo_content FROM seo_cache ORDER BY id DESC")
        rows = db_manager.cursor.fetchall()
        db_manager.close_connection()
        
        history = []
        for row in rows:
            history.append({
                "file_target": row[0],
                "title": row[1],
                "description": row[2],
                "keywords": row[3],
                "content": row[4]
            })
        return history
    except Exception as e:
        db_manager.close_connection()
        raise HTTPException(status_code=500, detail=f"Błąd odczytu z bazy danych: {e}")

@router.delete("/{file_target}")
async def delete_audit_history(file_target: str):
    """
    Usuwa wpis o danym identyfikatorze z bazy danych.
    """
    db_manager = SEODatabaseManager()
    try:
        existing = db_manager.get_from_database(file_target)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Nie znaleziono audytu o identyfikatorze '{file_target}'.")
            
        db_manager.delete_from_database(file_target)
        return {"status": "success", "message": f"Pomyślnie usunięto '{file_target}' z bazy danych."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd usuwania z bazy danych: {e}")
