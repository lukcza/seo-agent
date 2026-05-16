# 🌟 Interactive SEO Agent & Website Auditor (v2.0)

[![CI/CD Pipeline](https://github.com/lukcza/seo-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/lukcza/seo-agent/actions)
[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-FastAPI-green)](https://fastapi.tiangolo.com/)
[![AI Engine](https://img.shields.io/badge/AI--Engine-Gemini%202.5%20Flash-purple)](https://deepmind.google/technologies/gemini/)

**Asystent SEO & Audytor Stron** to kompleksowy system wspierania procesów pozycjonowania w wyszukiwarkach, oparty na sztucznej inteligencji (Google Gemini API), który analizuje istniejące witryny internetowe pod kątem technicznym i merytorycznym, przeprowadza 3-etapową interaktywną konwersację w celu doprecyzowania intencji marketingowych oraz generuje zoptymalizowane metadane i bogatą semantycznie treść SEO.

Projekt posiada **dwukierunkowy interfejs**: interaktywny panel webowy w trybie ciemnym (FastAPI + Glassmorphism Dashboard) oraz interaktywny klient konsoli (Interactive CLI client).

---

## 🛠️ Funkcje Systemu (Moduły ABCD)

System realizuje zaawansowany audyt witryn w oparciu o cztery moduły analityczne:

*   **Moduł A (Technical & Structured Audit):** 
    *   Weryfikacja certyfikatu SSL (protokół HTTPS).
    *   Skanowanie i automatyczne parsowanie struktury danych **Schema.org (JSON-LD)** w poszukiwaniu danych ustrukturyzowanych (`Organization`, `LocalBusiness`, itp.).
*   **Moduł B (Content & Keyword Density):**
    *   Obliczanie gęstości słów kluczowych i eliminacja spójników (stop words).
    *   Generowanie statystyk **Top 5 najczęstszych słów** oraz **Top 5 dwuwyrazowych fraz (Bigrams)** w celu wykrycia kanibalizacji lub braków fraz kluczowych.
*   **Moduł C (Interactive Prompt Refinement - 3 Kroki):**
    *   Analiza opisu biznesu pod kątem braków merytorycznych.
    *   3-etapowe dopytywanie użytkownika o kluczowe dane marketingowe: **Lokalizacja**, **Grupa Docelowa** oraz **USP (Unique Selling Proposition)**.
*   **Moduł D (Crawling & Indexing Diagnostics):**
    *   Bezpieczna diagnostyka dostępności mapy witryny (`sitemap.xml`) oraz pliku instrukcji dla robotów (`robots.txt`).

---

## 📂 Struktura Projektu

```text
seo-agent/
│
├── .github/workflows/       # Automatyzacja CI/CD (GitHub Actions)
│   └── ci.yml
│
├── app/                     # Główny kod aplikacji FastAPI
│   ├── api/v1/              # Endpointy API (audyt, doprecyzowanie, bazy danych)
│   ├── core/                # Połączenie z bazą SQLite, wczytywanie plików
│   ├── models/              # Modele danych Pydantic i definicje obiektów
│   ├── schemas/             # Schematy walidacji wejścia/wyjścia API
│   ├── services/            # Logika biznesowa (scraper BeautifulSoup, integracja z Gemini)
│   └── static/              # Panel Frontend (HTML, CSS, JS z obsługą responsywności)
│
├── tests/                   # Kompletna suita testów jednostkowych (13 testów)
│
├── cli.py                   # Konsolowy interfejs klienta (CLI)
├── main.py                  # Główny Launcher (Wybór między CLI a Web Serverem)
├── Dockerfile               # Konfiguracja obrazu kontenera Docker
├── requirements.txt         # Zależności projektu
└── .gitignore               # Ignorowane pliki (bazy danych, venv, secrets)
```

---

## 🚀 Szybki Start

### 1. Wymagania wstępne
*   Python 3.11 lub nowszy
*   Klucz API do platformy **Google Gemini** ([pobierz klucz tutaj](https://aistudio.google.com/))

### 2. Instalacja lokalna

1.  **Sklonuj repozytorium:**
    ```bash
    git clone https://github.com/lukcza/seo-agent.git
    cd seo-agent
    ```

2.  **Stwórz i aktywuj środowisko wirtualne:**
    ```bash
    python -m venv .venv
    # Windows:
    .venv\Scripts\activate
    # macOS/Linux:
    source .venv/bin/activate
    ```

3.  **Zainstaluj wymagane pakiety:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Skonfiguruj zmienne środowiskowe:**
    Skopiuj szablon `.env.template` jako plik `.env` i uzupełnij swój klucz API:
    ```bash
    cp .env.template .env
    ```
    W pliku `.env` ustaw:
    ```env
    GEMINI_API_KEY=twoj_klucz_api_gemini_tutaj
    ```

### 3. Uruchamianie aplikacji

Uruchom główny launcher, który pozwoli Ci wygodnie wybrać metodę pracy za pomocą interaktywnego menu ASCII:
```bash
python main.py
```

Możesz również uruchomić każdy moduł bezpośrednio:
*   **Serwer Web & Pulpit Nawigacyjny (FastAPI):**
    ```bash
    python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
    ```
    Następnie wejdź w przeglądarce pod adres: `http://127.0.0.1:8000/`

*   **Konsola Terminala (CLI):**
    ```bash
    python cli.py
    ```

---

## 🐳 Konteneryzacja (Docker)

Projekt jest w pełni skonteneryzowany. Aby zbudować i uruchomić aplikację w Dockerze:

1.  **Zbuduj obraz:**
    ```bash
    docker build -t seo-agent .
    ```

2.  **Uruchom kontener (przekazując klucz API jako zmienną):**
    ```bash
    docker run -p 8000:8000 -e GEMINI_API_KEY="TwójKluczAPI" seo-agent
    ```

---

## 🧪 Testy Jednostkowe

Aplikacja posiada 13 pokrywających testów jednostkowych badających poprawność parsowania plików oraz integracji schematów API. Aby uruchomić testy lokalnie:
```bash
python -m unittest discover -s tests -v
```

---

## 🤖 Integracja CI/CD (GitHub Actions)

W repozytorium skonfigurowany jest automatyczny rurociąg CI/CD (`.github/workflows/ci.yml`), który przy każdym `push` i `pull_request` na gałęzie `main`/`master`/`develop` wykonuje:
1.  **Kompilację składniową**
2.  **Uruchomienie wszystkich 13 testów jednostkowych** 
3.  **Weryfikację budowania obrazu Docker** 

---
