import json
import os
import asyncio 
# pyrefly: ignore [missing-import]
import google.generativeai as genai
from dotenv import load_dotenv
from app.models.seo import SEOData

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

async def get_seo_data(content: str) -> SEOData:
    """
    Pobiera dane SEO dla prostego tekstu bez dodatkowych filtrów i kroków (zgodność wsteczna).
    """
    if not content or len(content.strip()) == 0:
        raise ValueError("Content cannot be empty")
    try:
        model = genai.GenerativeModel(
            'gemini-2.5-flash',
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.5,
            )
        )
        prompt = f"""You are a SEO expert. Analyze the following content and generate SEO metadata in JSON format. The JSON object should have the following keys:
        - "title": Title of the content (strictly maximum 50 characters)
        - "description": Description of the content (strictly maximum 130 characters)
        - "keywords": Comma-separated keywords (strictly maximum 40 characters in total)
        - "content": SEO-optimized version of the content
        Return only the JSON object, without any additional text.
        
        Content to analyze:
        {content}
        """
        response = await model.generate_content_async(prompt.format(content=content))
        
        data_dict = json.loads(response.text)
        return SEOData.from_dict(data_dict)
    except Exception as e:
        print(f"Error: {e}")
        return None

async def get_refined_seo_data(
    content: str,
    locality: str = "",
    target_audience: str = "",
    usp: str = "",
    website_analysis: str = ""
) -> SEOData:
    """
    Generuje w pełni zoptymalizowane pod SEO metadane i treść, uwzględniając
    lokalizację, grupę docelową, USP oraz analizę dotychczasowych błędów strony.
    """
    if not content or len(content.strip()) == 0:
        raise ValueError("Content cannot be empty")
    try:
        model = genai.GenerativeModel(
            'gemini-2.5-flash',
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.5,
            )
        )
        
        refinement_context = ""
        if locality:
            refinement_context += f"- Lokalizacja / Obszar działania: {locality}\n"
        if target_audience:
            refinement_context += f"- Grupa docelowa: {target_audience}\n"
        if usp:
            refinement_context += f"- Wyróżniki oferty (USP) / Główne usługi: {usp}\n"
        if website_analysis:
            refinement_context += f"- Wykryte błędy/braki istniejącej strony (napraw je i uwzględnij w optymalizacji):\n{website_analysis}\n"

        prompt = f"""You are an elite SEO expert. Analyze the following content and business context, then generate highly-optimized Polish SEO metadata in JSON format.
        
        The JSON object must have the following keys:
        - "title": Highly optimized SEO Title in Polish (strictly maximum 50 characters, highly clickable, targeting key terms)
        - "description": Compelling meta description in Polish (strictly maximum 130 characters, with a clear call to action)
        - "keywords": Comma-separated keywords in Polish (strictly maximum 40 characters in total)
        - "content": An engaging, professional, fully SEO-optimized content in Polish, structured with clear HTML/Markdown headings, targeting the correct audience, locality, and emphasizing the USP.
        
        Return ONLY the raw JSON object, without any Markdown code blocks or wrapping.
        
        Original Content:
        \"\"\"{content}\"\"\"
        
        Business Context and Constraints:
        {refinement_context}
        """
        response = await model.generate_content_async(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        data_dict = json.loads(text)
        return SEOData.from_dict(data_dict)
    except Exception as e:
        print(f"Error in get_refined_seo_data: {e}")
        return None

async def assess_prompt_gaps(initial_prompt: str, website_context: str = "") -> dict:
    """
    Analizuje prompt wejściowy użytkownika i kontekst strony internetowej pod kątem braków w 3 wymiarach SEO.
    Zwraca ustrukturyzowany słownik z informacją o brakach i wygenerowanymi pytaniami.
    """
    try:
        model = genai.GenerativeModel(
            'gemini-2.5-flash',
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.2,
            )
        )
        prompt = f"""Jesteś doradcą SEO. Przeanalizuj poniższy opis/prompt użytkownika i opcjonalny kontekst strony internetowej pod kątem 3 kluczowych aspektów:
        1. **locality**: Lokalizacja/Miejscowość/Obszar (np. miasto, region, cała Polska, globalnie)
        2. **target_audience**: Grupa docelowa / Idealny klient (np. gracze, młodzież, firmy budowlane)
        3. **usp**: Wyróżniki oferty / USP / Główne usługi (co czyni ich wyjątkowymi, najważniejsze słowa kluczowe)
        
        Zwróć obiekt JSON z analizą, czy te aspekty są jasno określone (present: true/false), oraz spersonalizowanym pytaniem po polsku, jeśli dany aspekt jest nieobecny lub niejasny.
        
        Struktura JSON:
        {{
            "locality": {{
                "present": true/false,
                "value": "znaleziona wartość lub pusta",
                "question": "Zwięzłe, spersonalizowane pytanie o miejscowość/zasięg działania (np. 'W jaką miejscowość lub region celujesz ze swoimi usługami? Jeśli działasz w całej Polsce, wpisz \"cała Polska\".')"
            }},
            "target_audience": {{
                "present": true/false,
                "value": "znaleziona wartość lub pusta",
                "question": "Zwięzłe, spersonalizowane pytanie o grupę docelową (np. 'Do kogo dokładnie kierujesz swoją ofertę? Kto jest Twoim idealnym odbiorcą?')"
            }},
            "usp": {{
                "present": true/false,
                "value": "znaleziona wartość lub pusta",
                "question": "Zwięzłe, spersonalizowane pytanie o unikalne wyróżniki oferty i słowa kluczowe (np. 'Co wyróżnia Twój salon na tle konkurencji i na jakich konkretnych usługach najbardziej Ci zależy?')"
            }}
        }}

        Tekst wejściowy użytkownika:
        {initial_prompt}

        Kontekst ze strony www:
        {website_context}
        """
        response = await model.generate_content_async(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        return json.loads(text)
    except Exception as e:
        print(f"Błąd podczas oceny braków promptu: {e}")
        return {
            "locality": {"present": False, "value": "", "question": "Podaj lokalizację / miasto pozycjonowania (np. Warszawa, cała Polska):"},
            "target_audience": {"present": False, "value": "", "question": "Kto jest głównym odbiorcą / grupą docelową Twojej oferty?:"},
            "usp": {"present": False, "value": "", "question": "Jakie są główne usługi lub wyróżniki Twojej firmy (USP)?:"}
        }

async def analyze_scraped_seo(seo_metadata: dict) -> str:
    """
    Tworzy kompleksowy raport audytu SEO w języku polskim za pomocą Gemini 2.5 Flash,
    analizując dane techniczne i potencjalne błędy pobranej strony.
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""Jesteś wybitnym specjalistą ds. audytów SEO. Przeanalizuj poniższe dane techniczne ze skanowania strony internetowej i stwórz profesjonalny, szczegółowy oraz czytelny raport audytu SEO w języku polskim.
        
        Raport musi w jasny sposób:
        1. Wskazać mocne strony (jeśli występują).
        2. Wypisać konkretne **BRAKI** (np. brak opisu, brak nagłówka H1, brak Open Graph).
        3. Wskazać **MOŻLIWE BŁĘDY** techniczne (np. za długi tytuł/opis, wiele nagłówków H1, brak atrybutów ALT w obrazkach).
        4. Sformułować konkretne **REKOMENDACJE** i kroki naprawcze dla optymalizacji SEO strony.

        Używaj ikon (emoji) i struktury markdown, aby raport wyglądał spektakularnie i czytelnie dla klienta.
        
        Dane techniczne strony:
        {json.dumps(seo_metadata, indent=2, ensure_ascii=False)}
        """
        response = await model.generate_content_async(prompt)
        return response.text.strip()
    except Exception as e:
        return f"🚨 Wystąpił błąd podczas generowania raportu SEO przez Gemini: {e}"

def verify_seo_data(seo_data: SEOData) -> bool:
    if seo_data is None:
        return False
    
    if (
        not seo_data.title or 
        not seo_data.description or 
        not seo_data.keywords or 
        not seo_data.content
    ):
        return False
        
    if len(seo_data.title) > 60:
        return False
    if len(seo_data.description) > 160:
        return False
    if len(seo_data.keywords) > 50:
        return False
        
    return True
