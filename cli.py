from app.services.rag_services import RAGServices
import os
import asyncio
import logging
from app.core.reader import TextReader
from app.services.prompter import (
    get_seo_data,
    get_refined_seo_data,
    assess_prompt_gaps,
    analyze_scraped_seo,
    verify_seo_data
)
from app.models.seo import SEOData
from app.core.database import SEODatabaseManager
from app.services.website_analyzer import scrape_website_seo

# ANSI escape codes for beautiful styling
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_RED = "\033[91m"
C_CYAN = "\033[96m"
C_BLUE = "\033[94m"
C_MAGENTA = "\033[95m"
C_BOLD = "\033[1m"
C_UNDERLINE = "\033[4m"
C_RESET = "\033[0m"

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def print_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{C_CYAN}{C_BOLD}" + "=" * 70)
    print("      🌟 INTERAKTYWNY ASYSTENT SEO & AUDYTOR STRON WWW (v2.0) 🌟")
    print("=" * 70 + f"{C_RESET}")
    print(f"  Ten system pomoże Ci zoptymalizować tekst pod SEO w {C_BOLD}3 krokach{C_RESET}.")
    print("  Możesz przeanalizować istniejącą stronę, uzupełnić kluczowe braki")
    print("  (lokalizacja, grupa docelowa, USP) i wygenerować perfekcyjne metadane.")
    print(f"{C_CYAN}" + "=" * 70 + f"{C_RESET}\n")

def print_step(num: int, title: str):
    print(f"\n{C_MAGENTA}{C_BOLD}[KROK {num}] {title.upper()}{C_RESET}")
    print(f"{C_MAGENTA}" + "-" * 50 + f"{C_RESET}")

def print_technical_summary(metrics: dict):
    print(f"\n{C_CYAN}{C_BOLD}📊 TECHNICZNY RAPORT METRYK SEO STRONY{C_RESET}")
    print(f"{C_CYAN}" + "=" * 60 + f"{C_RESET}")
    
    # HTTPS Check (Module A)
    is_https = metrics.get("https_status", False)
    if is_https:
        print(f"🟢 {C_BOLD}Protokół HTTPS:{C_RESET} {C_GREEN}Zabezpieczone szyfrowaniem SSL (HTTPS){C_RESET}")
    else:
        print(f"🔴 {C_BOLD}Protokół HTTPS:{C_RESET} {C_RED}Brak szyfrowania SSL (HTTP)!{C_RESET} (Krytyczny błąd bezpieczeństwa)")

    # Title analysis
    title = metrics.get("title", "")
    title_len = metrics.get("title_len", 0)
    if not title:
        print(f"🔴 {C_BOLD}Tytuł <title>:{C_RESET} {C_RED}BRAK!{C_RESET} (Krytyczny błąd SEO)")
    elif title_len < 30:
        print(f"🟡 {C_BOLD}Tytuł <title>:{C_RESET} '{title}' ({title_len} znaków) - {C_YELLOW}Za krótki{C_RESET} (Sugerowane 50-60)")
    elif title_len > 60:
        print(f"🟡 {C_BOLD}Tytuł <title>:{C_RESET} '{title}' ({title_len} znaków) - {C_YELLOW}Za długi{C_RESET} (Sugerowane 50-60)")
    else:
        print(f"🟢 {C_BOLD}Tytuł <title>:{C_RESET} '{title}' ({title_len} znaków) - {C_GREEN}Optymalny!{C_RESET}")
        
    # Description analysis
    desc = metrics.get("description", "")
    desc_len = metrics.get("description_len", 0)
    if not desc:
        print(f"🔴 {C_BOLD}Meta Description:{C_RESET} {C_RED}BRAK!{C_RESET} (Krytyczny błąd SEO)")
    elif desc_len < 100:
        print(f"🟡 {C_BOLD}Meta Description:{C_RESET} '{desc}' ({desc_len} znaków) - {C_YELLOW}Za krótki{C_RESET} (Sugerowane 120-160)")
    elif desc_len > 160:
        print(f"🟡 {C_BOLD}Meta Description:{C_RESET} '{desc}' ({desc_len} znaków) - {C_YELLOW}Za długi{C_RESET} (Sugerowane 120-160)")
    else:
        print(f"🟢 {C_BOLD}Meta Description:{C_RESET} '{desc}' ({desc_len} znaków) - {C_GREEN}Optymalny!{C_RESET}")

    # Headers H1 analysis
    h1_count = metrics.get("h1_count", 0)
    if h1_count == 0:
        print(f"🔴 {C_BOLD}Nagłówki H1:{C_RESET} {C_RED}Brak nagłówka H1!{C_RESET} Każda podstrona musi mieć dokładnie jeden główny nagłówek.")
    elif h1_count > 1:
        print(f"🔴 {C_BOLD}Nagłówki H1:{C_RESET} {C_RED}Znaleziono aż {h1_count} nagłówków H1!{C_RESET} Powinien być dokładnie jeden.")
        for i, h in enumerate(metrics.get("h1s", [])):
            print(f"   {C_RED}└ H1 #{i+1}:{C_RESET} '{h}'")
    else:
        print(f"🟢 {C_BOLD}Nagłówek H1:{C_RESET} '{metrics.get('h1s', [''])[0]}' - {C_GREEN}Poprawny (dokładnie jeden){C_RESET}")

    # Alt tags on images
    total_imgs = metrics.get("total_images", 0)
    missing_alt = metrics.get("images_missing_alt", 0)
    empty_alt = metrics.get("images_with_empty_alt", 0)
    if total_imgs > 0:
        if missing_alt > 0 or empty_alt > 0:
            print(f"🟡 {C_BOLD}Atrybuty ALT obrazów:{C_RESET} Na {total_imgs} grafik, {C_YELLOW}{missing_alt} nie ma tagu ALT{C_RESET}, a {empty_alt} ma pusty ALT.")
        else:
            print(f"🟢 {C_BOLD}Atrybuty ALT obrazów:{C_RESET} {C_GREEN}Wszystkie {total_imgs} obrazów mają uzupełnione tagi ALT!{C_RESET}")
    else:
        print(f"⚪ {C_BOLD}Obrazy:{C_RESET} Brak obrazów na stronie.")

    # Canonical status
    canonical = metrics.get("canonical", "")
    if canonical:
        print(f"🟢 {C_BOLD}Tag kanoniczny (canonical):{C_RESET} '{canonical}' - {C_GREEN}Obecny{C_RESET}")
    else:
        print(f"🟡 {C_BOLD}Tag kanoniczny (canonical):{C_RESET} {C_YELLOW}Brak linku kanonicznego.{C_RESET}")

    # Robots status
    robots = metrics.get("robots", "")
    rob_file_ok = metrics.get("robots_txt_status", 404) == 200
    if robots:
        print(f"🟢 {C_BOLD}Meta robots:{C_RESET} '{robots}' - {C_GREEN}Obecny{C_RESET}")
    else:
        print(f"🟡 {C_BOLD}Meta robots:{C_RESET} {C_YELLOW}Brak dyrektyw robots w HTML.{C_RESET}")
    if rob_file_ok:
        print(f"🟢 {C_BOLD}Plik robots.txt:{C_RESET} {C_GREEN}Odnaleziono i pobrano poprawnie (200 OK){C_RESET}")
    else:
        print(f"🟡 {C_BOLD}Plik robots.txt:{C_RESET} {C_YELLOW}Brak pliku na serwerze (404 Not Found){C_RESET}")

    # Sitemap status
    site_file_ok = metrics.get("sitemap_xml_status", 404) == 200
    if site_file_ok:
        print(f"🟢 {C_BOLD}Mapa sitemap.xml:{C_RESET} {C_GREEN}Odnaleziono i pobrano poprawnie (200 OK){C_RESET}")
    else:
        print(f"🟡 {C_BOLD}Mapa sitemap.xml:{C_RESET} {C_YELLOW}Brak pliku na serwerze (404 Not Found){C_RESET}")

    # Schema.org Types
    schemas = metrics.get("schema_types", [])
    if schemas:
        print(f"🟢 {C_BOLD}Schema.org JSON-LD:{C_RESET} {C_GREEN}Wykryto następujące schematy:{C_RESET} {', '.join(schemas)}")
    else:
        print(f"🟡 {C_BOLD}Schema.org JSON-LD:{C_RESET} {C_YELLOW}Brak zdefiniowanych danych strukturyzowanych Schema.org.{C_RESET}")

    # OpenGraph status
    og_title = metrics.get("og_title", "")
    og_desc = metrics.get("og_description", "")
    if og_title and og_desc:
        print(f"🟢 {C_BOLD}Social Media (OpenGraph):{C_RESET} {C_GREEN}Tagi og:title i og:description są obecne.{C_RESET}")
    else:
        print(f"🟡 {C_BOLD}Social Media (OpenGraph):{C_RESET} {C_YELLOW}Brak pełnej konfiguracji OpenGraph. Udostępnianie w social media może wyglądać nieatrakcyjnie.{C_RESET}")

    print(f"📝 {C_BOLD}Liczba słów na stronie:{C_RESET} {metrics.get('word_count', 0)}")
    
    # Keyword Density Analysis (Module B)
    top_words = metrics.get("top_words", [])
    top_bigrams = metrics.get("top_bigrams", [])
    
    if top_words:
        print(f"\n{C_CYAN}{C_BOLD}📈 ANALIZA ZAGĘSZCZENIA SŁÓW KLUCZOWYCH (TOP 5):{C_RESET}")
        for idx, item in enumerate(top_words, start=1):
            word = item[0] if isinstance(item, (list, tuple)) else item.get("word") if isinstance(item, dict) else item
            count = item[1] if isinstance(item, (list, tuple)) else item.get("count") if isinstance(item, dict) else 0
            print(f"   {idx}. {C_CYAN}{word:<15}{C_RESET} -> {C_BOLD}{count:<3} wystąpień{C_RESET}")
            
    if top_bigrams:
        print(f"\n{C_CYAN}{C_BOLD}📈 ANALIZA FRAZ DWUWYRAZOWYCH (TOP 5):{C_RESET}")
        for idx, item in enumerate(top_bigrams, start=1):
            phrase = " ".join(item[0]) if isinstance(item, (list, tuple)) and isinstance(item[0], (list, tuple)) else item[0] if isinstance(item, (list, tuple)) else item.get("phrase") if isinstance(item, dict) else item
            count = item[1] if isinstance(item, (list, tuple)) else item.get("count") if isinstance(item, dict) else 0
            print(f"   {idx}. {C_MAGENTA}{phrase:<20}{C_RESET} -> {C_BOLD}{count:<3} wystąpień{C_RESET}")

    print(f"{C_CYAN}" + "=" * 60 + f"{C_RESET}\n")

async def run_app_async():
    print_banner()
    
    db_manager = SEODatabaseManager()
    rag_services = RAGServices()
    
    # Choose input source
    print(f"{C_BOLD}Wybierz źródło tekstu lub prompta początkowego:{C_RESET}")
    print(f"  [{C_GREEN}1{C_RESET}] Wczytaj z pliku '{C_BOLD}sample.txt{C_RESET}'")
    print(f"  [{C_GREEN}2{C_RESET}] Wpisz swój prompt / temat ręcznie w konsoli")
    print(f"  [{C_GREEN}3{C_RESET}] Zobacz dotychczasowe wpisy w bazie danych")
    
    choice = input(f"\n{C_BOLD}Wybór (1/2/3):{C_RESET} ").strip()
    
    target_name = "custom_prompt"
    original_content = ""
    
    if choice == "3":
        print_banner()
        print(f"{C_CYAN}{C_BOLD}📋 ZAPISANE SESJE SEO W BAZIE DANYCH:{C_RESET}")
        print("-" * 60)
        # We can try to query a few default file targets
        targets_to_check = ["sample.txt", "manual_prompt", "custom_prompt"]
        found = False
        for tgt in targets_to_check:
            cached = db_manager.get_from_database(tgt)
            if cached:
                found = True
                print(f"📍 {C_BOLD}ID sesji / target:{C_RESET} {C_GREEN}{cached.file_target}{C_RESET}")
                print(f"   └ Tytuł: {cached.title}")
                print(f"   └ Opis:  {cached.description}")
                print(f"   └ Słowa: {cached.keywords}")
                print("-" * 60)
        if not found:
            print("  Brak zapisanych rekordów w bazie.")
        
        input(f"\nNaciśnij {C_BOLD}[Enter]{C_RESET}, aby powrócić do menu głównego i kontynuować.")
        db_manager.close_connection()
        # Rerun app
        await run_app_async()
        return

    elif choice == "1":
        target_name = "sample.txt"
        reader = TextReader(default_encoding="utf-8")
        print(f"\n🔍 Próba wczytania pliku: {os.path.abspath(target_name)}...")
        file_content = reader.read_file(target_name)
        if file_content is not None:
            print(f"🟢 {C_GREEN}Plik wczytany poprawnie!{C_RESET}")
            original_content = file_content
            # Show a snippet
            print(f"\n{C_BOLD}Tekst wejściowy (fragment):{C_RESET}")
            print(f"---")
            print(original_content[:300] + ("..." if len(original_content) > 300 else ""))
            print(f"---")
        else:
            print(f"🔴 {C_RED}Błąd podczas odczytu pliku.{C_RESET} Przełączam na wprowadzanie ręczne.")
            original_content = input(f"\n{C_BOLD}Wpisz swój temat / prompt SEO:{C_RESET} ").strip()
    else:
        target_name = "custom_prompt"
        original_content = input(f"\n{C_BOLD}Wpisz swój temat / prompt SEO:{C_RESET} ").strip()
        while not original_content:
            original_content = input(f"🔴 {C_RED}Treść nie może być pusta. Wpisz swój temat/prompt SEO:{C_RESET} ").strip()

    # URL Scraping and analysis
    print_step(1, "Opcjonalna analiza istniejącej strony WWW")
    url_input = input(f"Czy posiadasz już działającą stronę internetową?\nJeśli tak, {C_CYAN}{C_BOLD}wklej jej link URL{C_RESET} (lub naciśnij [Enter] aby pominąć): ").strip()
    
    website_metrics = None
    website_analysis_report = ""
    website_context = ""
    
    if url_input:
        print(f"\n🌐 {C_CYAN}Rozpoczynam pobieranie i analizę strony:{C_RESET} {url_input}...")
        website_metrics = scrape_website_seo(url_input)
        
        if "error" in website_metrics:
            print(f"🚨 {C_RED}Błąd analizy strony:{C_RESET} {website_metrics['error']}")
        else:
            print(f"🟢 {C_GREEN}Strona została pobrana pomyślnie!{C_RESET}")
            
            # Print beautiful technical summary of errors and missing elements
            print_technical_summary(website_metrics)
            
            # Generate advanced Gemini SEO analysis report with RAG
            print(f"🔍 {C_CYAN}Pobieranie wytycznych technicznych z bazy wiedzy RAG...{C_RESET}")
            tech_knowledge = rag_services.query_knowledge("technical seo audit canonical robots sitemap headers quality")

            print(f"🤖 {C_CYAN}Generowanie szczegółowego raportu błędów i zalecań przez AI...{C_RESET}")
            website_analysis_report = await analyze_scraped_seo(website_metrics, knowledge_context=tech_knowledge)
            
            print(f"\n{C_MAGENTA}{C_BOLD}📝 RAPORT AUDYTU SEO (OD AI):{C_RESET}")
            print("-" * 60)
            print(website_analysis_report)
            print("-" * 60)
            
            # Prepare context for prompt refinement
            website_context = f"Analiza techniczna strony: Title: {website_metrics.get('title')}, Description: {website_metrics.get('description')}, Nagłówki H1: {website_metrics.get('h1s')}. Fragment tekstu ze strony: {website_metrics.get('clean_text_snippet')}"

    # Prompt clarification
    print_step(2, "3-etapowe doprecyzowanie prompta (Analiza Braków)")
    print(f"🤖 {C_CYAN}Analizowanie Twojego opisu pod kątem kluczowych braków marketingowych i SEO...{C_RESET}")
    
    gaps = await assess_prompt_gaps(original_content, website_context)
    
    answers = {
        "locality": "",
        "target_audience": "",
        "usp": ""
    }
    
    # 3 Steps process
    for i, aspect in enumerate(["locality", "target_audience", "usp"], start=1):
        aspect_name = "Lokalizacja" if aspect == "locality" else "Grupa Docelowa" if aspect == "target_audience" else "USP & Oferta"
        gap_info = gaps.get(aspect, {"present": False, "value": "", "question": ""})
        
        print(f"\n{C_BOLD}Etap 2.{i}: {aspect_name}{C_RESET}")
        
        if gap_info.get("present"):
            val = gap_info.get("value")
            print(f"  {C_GREEN}✓ Wykryto automatycznie:{C_RESET} '{C_BOLD}{val}{C_RESET}'")
            answers[aspect] = val
        else:
            print(f"  {C_YELLOW}⚠ Brak wyraźnych informacji w Twoim opisie.{C_RESET}")
            question = gap_info.get("question", f"Podaj informacje na temat {aspect_name}:")
            print(f"  👉 {C_CYAN}{C_BOLD}{question}{C_RESET}")
            user_ans = input(f"  Twój wybór / odpowiedź (Enter by pominąć): ").strip()
            if user_ans:
                answers[aspect] = user_ans
                print(f"  {C_GREEN}✓ Zapisano:{C_RESET} {user_ans}")
            else:
                answers[aspect] = ""
                print(f"  ⚪ Pominięto.")

    # Optimization and Generation
    print_step(3, "Generowanie zoptymalizowanych materiałów i metadanych SEO")
    print(f"🚀 {C_GREEN}Łączenie zebranych informacji i generowanie ostatecznych materiałów...{C_RESET}\n")
    
    # Get content optimization guidelines from RAG
    print(f"🔍 {C_CYAN}Pobieranie wytycznych optymalizacji treści z bazy wiedzy RAG...{C_RESET}")
    content_knowledge = rag_services.query_knowledge(f"seo optimization for {original_content} {answers['usp']}")

    seo_response = await get_refined_seo_data(
        content=original_content,
        locality=answers["locality"],
        target_audience=answers["target_audience"],
        usp=answers["usp"],
        website_analysis=website_analysis_report if website_analysis_report else "Brak danych dotychczasowej strony.",
        knowledge_context=content_knowledge
    )
    
    if not seo_response:
        print(f"🔴 {C_RED}Wystąpił błąd podczas generowania SEO przez Gemini API.{C_RESET}")
        db_manager.close_connection()
        return

    # Display result
    print("=" * 70)
    print(f"                {C_GREEN}{C_BOLD}✨ EFEKTY OPTYMALIZACJI SEO ✨{C_RESET}                ")
    print("=" * 70)
    print(f"  {C_CYAN}{C_BOLD}1. TYTUŁ (SEO TITLE):{C_RESET}")
    print(f"     {C_BOLD}{seo_response.title}{C_RESET}")
    print(f"     (Długość: {len(seo_response.title)} znaków - zalecane < 60)")
    print("-" * 70)
    print(f"  {C_CYAN}{C_BOLD}2. OPIS (META DESCRIPTION):{C_RESET}")
    print(f"     {seo_response.description}")
    print(f"     (Długość: {len(seo_response.description)} znaków - zalecane < 160)")
    print("-" * 70)
    print(f"  {C_CYAN}{C_BOLD}3. SŁOWA KLUCZOWE (KEYWORDS):{C_RESET}")
    print(f"     {seo_response.keywords}")
    print("-" * 70)
    print(f"  {C_CYAN}{C_BOLD}4. ZOPTYMALIZOWANA TREŚĆ STRONY:{C_RESET}")
    print(seo_response.content)
    print("=" * 70)
    
    # Validation info
    is_valid = verify_seo_data(seo_response)
    if is_valid:
        print(f"💚 {C_GREEN}{C_BOLD}Weryfikacja pomyślna:{C_RESET} Metadane spełniają techniczne limity długości!")
    else:
        print(f"💛 {C_YELLOW}Uwaga:{C_RESET} Niektóre metadane nieznacznie przekraczają standardowe limity (ale wciąż są gotowe do użycia).")

    # Feedback loop and save
    while True:
        print(f"\n{C_BOLD}Wybierz dalsze działanie:{C_RESET}")
        print(f"  [{C_GREEN}ok{C_RESET}] Zatwierdź i zapisz w lokalnej bazie danych")
        print(f"  [{C_GREEN}popraw{C_RESET}] Wprowadź dodatkowe uwagi / poprawki")
        print(f"  [{C_GREEN}wyjdz{C_RESET}] Wyjdź bez zapisywania")
        
        feedback = input(f"\n{C_BOLD}Twoja decyzja:{C_RESET} ").strip().lower()
        
        if feedback == "ok":
            print(f"\n💾 Zapisuję do bazy danych z identyfikatorem '{C_BOLD}{target_name}{C_RESET}'...")
            
            # Check if exists to choose update or save
            existing = db_manager.get_from_database(target_name)
            response_obj = SEOData(
                file_target=target_name,
                title=seo_response.title,
                description=seo_response.description,
                keywords=seo_response.keywords,
                content=seo_response.content
            )
            
            if existing:
                db_manager.update_database(response_obj)
            else:
                db_manager.save_to_database(response_obj)
                
            print(f"🎉 {C_GREEN}{C_BOLD}Pomyślnie zapisano w bazie danych!{C_RESET}")
            break
            
        elif feedback == "popraw":
            corrections = input(f"\n{C_BOLD}Wpisz swoje uwagi / poprawki (np. 'Zmień ton na bardziej humorystyczny'):{C_RESET}\n👉 ")
            print(f"\n🚀 {C_CYAN}Generowanie nowej wersji uwzględniając uwagi...{C_RESET}")
            
            seo_response = await get_refined_seo_data(
                content=original_content + f"\n[UWAGI UŻYTKOWNIKA DO POPRAWY: {corrections}]",
                locality=answers["locality"],
                target_audience=answers["target_audience"],
                usp=answers["usp"],
                website_analysis=website_analysis_report,
                knowledge_context=content_knowledge
            )
            
            # Show updated output
            print("\n" + "=" * 70)
            print(f"              {C_GREEN}{C_BOLD}✨ POPRAWIONA WERSJA SEO ✨{C_RESET}              ")
            print("=" * 70)
            print(f"  {C_CYAN}{C_BOLD}1. TYTUŁ (SEO TITLE):{C_RESET} {C_BOLD}{seo_response.title}{C_RESET}")
            print(f"  {C_CYAN}{C_BOLD}2. OPIS (META DESCRIPTION):{C_RESET} {seo_response.description}")
            print(f"  {C_CYAN}{C_BOLD}3. SŁOWA KLUCZOWE:{C_RESET} {seo_response.keywords}")
            print(f"  {C_CYAN}{C_BOLD}4. TREŚĆ STRONY:{C_RESET}\n{seo_response.content}")
            print("=" * 70)
            continue
            
        elif feedback == "wyjdz" or feedback == "q":
            print(f"\n👋 Dziękujemy za skorzystanie z Asystenta SEO. Do zobaczenia!")
            break
        else:
            print(f"❌ {C_RED}Nieznana komenda.{C_RESET} Wybierz 'ok', 'popraw' lub 'wyjdz'.")

    db_manager.close_connection()

if __name__ == "__main__":
    asyncio.run(run_app_async())
