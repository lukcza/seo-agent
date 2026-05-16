from typing import Counter
from pydantic import json_schema
from pydantic import json_schema
from pydantic import json_schema
from pydantic import json_schema
from pydantic import json_schema
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

def scrape_website_seo(url: str) -> dict:
    """
    Pobiera i analizuje podstawowe elementy SEO ze wskazanej strony internetowej.
    """
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=12)
        response.raise_for_status()
    except Exception as e:
        return {"error": f"Nie udało się pobrać strony: {e}"}

    soup = BeautifulSoup(response.text, "html.parser")

    # Ekstrakcja podstawowych metatagów SEO
    title_tag = soup.find("title")
    title = title_tag.get_text().strip() if title_tag else ""

    desc_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)}) or \
               soup.find("meta", attrs={"property": re.compile(r"^og:description$", re.I)})
    description = desc_tag.get("content", "").strip() if desc_tag else ""

    keywords_tag = soup.find("meta", attrs={"name": re.compile(r"^keywords$", re.I)})
    keywords = keywords_tag.get("content", "").strip() if keywords_tag else ""
    viewport_tag = soup.find("meta", attrs={"name": re.compile(r"^viewport$", re.I)})
    viewport = viewport_tag.get("content", "").strip() if viewport_tag else ""
    
    # Analiza struktury nagłówków
    h1s = [h.get_text().strip() for h in soup.find_all("h1") if h.get_text().strip()]
    h2s = [h.get_text().strip() for h in soup.find_all("h2") if h.get_text().strip()]
    h3s = [h.get_text().strip() for h in soup.find_all("h3") if h.get_text().strip()]

    # Analiza obrazków pod kątem atrybutów ALT
    images = soup.find_all("img")
    total_images = len(images)
    images_missing_alt = 0
    images_with_empty_alt = 0
    
    for img in images:
        alt = img.get("alt")
        if alt is None:
            images_missing_alt += 1
        elif alt.strip() == "":
            images_with_empty_alt += 1

    # Weryfikacja tagów canonical oraz robots
    canonical_tag = soup.find("link", rel="canonical")
    canonical = canonical_tag.get("href", "").strip() if canonical_tag else ""

    robots_tag = soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
    robots = robots_tag.get("content", "").strip() if robots_tag else ""

    # Tagi protokołu Open Graph (Social Media)
    og_title_tag = soup.find("meta", property="og:title")
    og_title = og_title_tag.get("content", "").strip() if og_title_tag else ""
    
    og_desc_tag = soup.find("meta", property="og:description")
    og_desc = og_desc_tag.get("content", "").strip() if og_desc_tag else ""

    og_image_tag = soup.find("meta", property="og:image")
    og_image = og_image_tag.get("content", "").strip() if og_image_tag else ""

    # Detekcja języka witryny
    html_tag = soup.find("html")
    lang = html_tag.get("lang", "").strip() if html_tag else ""

    # Oczyszczanie treści tekstowej z kodu i znaczników formatujących
    for script_or_style in soup(["script", "style", "noscript", "svg", "iframe", "header", "footer"]):
        script_or_style.decompose()
    
    text_content = soup.get_text()
    lines = (line.strip() for line in text_content.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    clean_text = " ".join(chunk for chunk in chunks if chunk)
    word_count = len(clean_text.split())
    # Analiza danych strukturalnych JSON-LD (Schema.org)
    scripts = soup.find_all("script", type="application/ld+json")
    script_json = [json.loads(script.string) for script in scripts]
    schema_types = [script["@type"] for script in script_json if isinstance(script, dict) and "@type" in script]
    # Pobieranie linków i ich atrybutów
    links = soup.find_all("a")
    links_href = [link.get("href", "").strip() for link in links]
    links_title = [link.get("title", "").strip() for link in links]
    # Oczyszczanie tekstu do analizy gęstości słów kluczowych
    clean_text = re.sub(r'<.*?>', '', clean_text)

    clean_text = re.sub(r'[^a-zA-Z0-9\s]', '', clean_text)
    clean_text = ' '.join(clean_text.split()).lower()
    
    # Eliminacja stop words 
    stop_words = ["a", "i", "w", "z", "na", "do", "od", "za", "przez", "dla", "po", "pod", "nad", "obok", "przed", "za", "pod", "nad", "obok", "przed", "za", "pod", "nad", "obok", "przed"]
    words = clean_text.split()
    filtered_words = [word for word in words if word not in stop_words]
    
    # Analiza częstotliwości unigramów i bigramów
    word_counts = Counter(filtered_words)
    top_words = word_counts.most_common(5)
    # Obliczanie częstości występowania fraz dwuwyrazowych
    bigram_counts = Counter(zip(filtered_words, filtered_words[1:]))
    top_bigrams = bigram_counts.most_common(5)
    # Wyodrębnienie domeny głównej strony
    domain = urllib.parse.urlparse(url).netloc
    
    # Weryfikacja dostępności plików robots.txt oraz sitemap.xml
    try:
        robots_txt_status = requests.head(f"https://{domain}/robots.txt", headers={"User-Agent": "Mozilla/5.0"}, timeout=5).status_code
    except Exception:
        robots_txt_status = 404
        
    try:
        sitemap_xml_status = requests.head(f"https://{domain}/sitemap.xml", headers={"User-Agent": "Mozilla/5.0"}, timeout=5).status_code
    except Exception:
        sitemap_xml_status = 404
        
    # Badanie szyfrowania HTTPS
    https_status = url.startswith("https://")
    return {
        "url": url,
        "title": title,
        "title_len": len(title),
        "description": description,
        "description_len": len(description),
        "keywords": keywords,
        "h1s": h1s,
        "h1_count": len(h1s),
        "h2_count": len(h2s),
        "h3_count": len(h3s),
        "h2s_sample": h2s[:5],
        "h3s_sample": h3s[:5],
        "total_images": total_images,
        "images_missing_alt": images_missing_alt,
        "images_with_empty_alt": images_with_empty_alt,
        "canonical": canonical,
        "robots": robots,
        "og_title": og_title,
        "og_description": og_desc,
        "og_image": og_image,
        "lang": lang,
        "word_count": word_count,
        "clean_text_snippet": clean_text[:1200],
        "schema_types": schema_types,
        "robots_txt_status": robots_txt_status,
        "sitemap_xml_status": sitemap_xml_status,
        "top_words": top_words,
        "top_bigrams": top_bigrams,
        "domain": domain,
        "https_status": https_status
    }
