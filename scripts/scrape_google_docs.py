import asyncio
import os
import httpx
from playwright.async_api import async_playwright

async def scrape_google_search_docs():
    base_url = "https://developers.google.com/search/docs"
    output_file = "google_search_guidelines.md"
    
    async with async_playwright() as p:
        print("🔍 Zbieram listę podstron z nawigacji...")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(base_url, wait_until="networkidle")
            # Pobieramy linki z nawigacji bocznej
            links = await page.eval_on_selector_all(
                "a.devsite-nav-title, a.devsite-nav-link", 
                "nodes => nodes.map(n => n.href)"
            )
        finally:
            await browser.close()
        
        # Filtrowanie i czyszczenie linków
        unique_links = []
        for link in links:
            # Czyścimy link z kotwic i parametrów dla bazy
            clean_base = link.split('#')[0].split('?')[0]
            if "/search/docs/" in clean_base and clean_base not in unique_links:
                link_lower = clean_base.lower()
                # Pomijamy wprowadzenie/overview zgodnie z prośbą
                if any(x in link_lower for x in ["introduction", "overview", "start-here"]):
                    continue
                unique_links.append(clean_base)
        
        # Usuwamy ewentualne duplikaty po czyszczeniu
        unique_links = sorted(list(set(unique_links)))
        print(f"✅ Znaleziono {len(unique_links)} unikalnych podstron.")
        
        full_markdown = []
        
        # Używamy httpx dla wydajnego pobierania surowego tekstu
        async with httpx.AsyncClient(timeout=30.0) as client:
            for i, link in enumerate(unique_links):
                # Konstruujemy link do wersji Markdown zgodnie ze wzorcem .md.txt
                md_url = f"{link}.md.txt?hl=pl"
                
                print(f"[{i+1}/{len(unique_links)}] Pobieram: {md_url}")
                
                try:
                    response = await client.get(md_url, follow_redirects=True)
                    if response.status_code == 200:
                        content = response.text
                        full_markdown.append(f"\n\n<!-- SOURCE: {link} -->\n" + content)
                    else:
                        print(f"   ⚠️ Status {response.status_code} dla: {link}")
                except Exception as e:
                    print(f"   ❌ Błąd przy {link}: {e}")
        
        # Zapis zbiorczy
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# Google Search Documentation (Technical Guidelines)\n")
            f.write("\n".join(full_markdown))
            
        print(f"\n🚀 Zakończono! Wszystkie dane zapisane w: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    asyncio.run(scrape_google_search_docs())
