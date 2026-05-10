// Interactive SEO Agent & Website Auditor API Frontend Core

document.addEventListener("DOMContentLoaded", () => {
    // Current application state
    const state = {
        currentStep: 1,
        url: "",
        initialContent: "",
        technicalMetrics: null,
        websiteAnalysis: "",
        gaps: null,
        answers: {
            locality: "",
            target_audience: "",
            usp: ""
        },
        refinedResult: null
    };

    // DOM Elements Cache
    const el = {
        // Nav items
        nav1: document.getElementById("nav-step-1"),
        nav2: document.getElementById("nav-step-2"),
        nav3: document.getElementById("nav-step-3"),
        
        // Panels
        panel1: document.getElementById("panel-step-1"),
        panel2: document.getElementById("panel-step-2"),
        panel3: document.getElementById("panel-step-3"),
        
        // Forms & inputs
        inputUrl: document.getElementById("input-url"),
        inputPrompt: document.getElementById("input-prompt"),
        btnStartAudit: document.getElementById("btn-start-audit"),
        
        // Loader
        loader: document.getElementById("loader-box"),
        loaderText: document.getElementById("loader-text"),
        
        // Step 2 elements
        metricsGrid: document.getElementById("metrics-grid"),
        reportBox: document.getElementById("ai-report-box"),
        gapsForm: document.getElementById("gaps-form"),
        btnGenerateSEO: document.getElementById("btn-generate-seo"),
        
        // Step 3 elements
        resultTitle: document.getElementById("result-title"),
        resultDescription: document.getElementById("result-description"),
        resultKeywords: document.getElementById("result-keywords"),
        resultContent: document.getElementById("result-content"),
        inputId: document.getElementById("save-id"),
        btnSaveDb: document.getElementById("btn-save-db"),
        btnRegenerate: document.getElementById("btn-regenerate"),
        inputCorrection: document.getElementById("input-correction"),
        
        // History Sidebar
        historyList: document.getElementById("history-list")
    };

    // Initialize application
    init();

    function init() {
        loadHistory();
        
        // Event Listeners
        el.btnStartAudit.addEventListener("click", handleStartAudit);
        el.btnGenerateSEO.addEventListener("click", handleGenerateSEO);
        el.btnSaveDb.addEventListener("click", handleSaveToDb);
        el.btnRegenerate.addEventListener("click", handleRegenerate);
        
        // Allow loading default file sample via clicking helper
        document.getElementById("btn-load-sample")?.addEventListener("click", () => {
            el.inputPrompt.value = "I want to create seo on my webpage. Webpage is about clan of star wars battlefront 2 game and comunity. We are playing on pc. clan name is 501st legion pl. what should I add to increase seo?";
        });
    }

    // Load History list in sidebar
    async function loadHistory() {
        try {
            const response = await fetch("/api/v1/audit/history");
            if (!response.ok) throw new Error("Failed to load history.");
            const data = await response.json();
            
            el.historyList.innerHTML = "";
            if (data.length === 0) {
                el.historyList.innerHTML = `<div style="text-align:center; padding: 20px; color: var(--text-muted); font-size:0.9rem;">Brak zapisanych audytów.</div>`;
                return;
            }
            
            data.forEach(item => {
                const row = document.createElement("div");
                row.className = "history-item";
                row.innerHTML = `
                    <div class="history-item-info">
                        <div class="history-item-name">${escapeHtml(item.file_target)}</div>
                        <div class="history-item-title">${escapeHtml(item.title)}</div>
                    </div>
                    <button class="history-delete-btn" title="Usuń z bazy" data-id="${escapeHtml(item.file_target)}">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                `;
                
                row.addEventListener("click", (e) => {
                    if (e.target.closest(".history-delete-btn")) return;
                    loadHistoryItemToOutput(item);
                });
                
                row.querySelector(".history-delete-btn").addEventListener("click", async (e) => {
                    e.stopPropagation();
                    if (confirm(`Czy na pewno chcesz usunąć audyt '${item.file_target}' z bazy?`)) {
                        await deleteHistoryItem(item.file_target);
                    }
                });
                
                el.historyList.appendChild(row);
            });
        } catch (err) {
            console.error("Error loading history:", err);
        }
    }

    // Delete a saved history item
    async function deleteHistoryItem(id) {
        try {
            const response = await fetch(`/api/v1/audit/${encodeURIComponent(id)}`, { method: "DELETE" });
            if (response.ok) {
                loadHistory();
            } else {
                alert("Nie udało się usunąć wpisu.");
            }
        } catch (err) {
            console.error("Error deleting item:", err);
        }
    }

    // Render a loaded history item to Step 3 output immediately
    function loadHistoryItemToOutput(item) {
        state.refinedResult = item;
        
        showPanel(3);
        
        el.resultTitle.innerText = item.title;
        el.resultDescription.innerText = item.description;
        el.resultKeywords.innerText = item.keywords;
        el.resultContent.innerHTML = parseMarkdown(item.content);
        el.inputId.value = item.file_target;
    }

    // Step 1 Click Handler: Technical Audit
    async function handleStartAudit() {
        const url = el.inputUrl.value.trim();
        const prompt = el.inputPrompt.value.trim();
        
        if (!prompt && !url) {
            alert("Podaj adres URL lub wpisz temat / opis początkowy SEO!");
            return;
        }
        
        state.url = url;
        state.initialContent = prompt || (url ? `Audyt i optymalizacja strony: ${url}` : "Brak opisu");
        
        showLoader("🔍 Pobieranie strony i wykonywanie audytu technicznego SEO...");
        
        try {
            let websiteContext = "";
            
            if (url) {
                const response = await fetch("/api/v1/audit/technical", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ url, content: prompt })
                });
                
                if (!response.ok) {
                    const err = await response.json();
                    throw new Error(err.detail || "Error during website audit.");
                }
                
                const data = await response.json();
                state.technicalMetrics = data.metrics;
                state.websiteAnalysis = data.audit_report;
                
                renderTechnicalSummary(data.metrics);
                renderAuditReport(data.audit_report);
                
                websiteContext = `Technical audit title: ${data.metrics.title}, Description: ${data.metrics.description}. Text snippets: ${data.metrics.clean_text_snippet}`;
                
                document.getElementById("audit-results-card").style.display = "block";
            } else {
                document.getElementById("audit-results-card").style.display = "none";
                state.websiteAnalysis = "Brak dotychczasowej strony www.";
            }
            
            showLoader("🤖 Analizowanie luk i braków w Twoim opisie przez AI...");
            
            const gapResponse = await fetch("/api/v1/audit/gaps", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    content: state.initialContent,
                    website_context: websiteContext
                })
            });
            
            if (!gapResponse.ok) throw new Error("Failed to assess prompt gaps.");
            
            const gapsData = await gapResponse.json();
            state.gaps = gapsData;
            
            renderGapsForm(gapsData);
            
            hideLoader();
            showPanel(2);
            
        } catch (err) {
            hideLoader();
            alert(`Wystąpił błąd: ${err.message}`);
        }
    }

    // Step 2 Click Handler: Final Generation
    async function handleGenerateSEO() {
        // Collect answers from generated questions
        state.answers.locality = document.getElementById("input-gap-locality")?.value.trim() || "";
        state.answers.target_audience = document.getElementById("input-gap-target_audience")?.value.trim() || "";
        state.answers.usp = document.getElementById("input-gap-usp")?.value.trim() || "";
        
        showLoader("🚀 Generowanie ostatecznych, zoptymalizowanych pod SEO metadanych i treści...");
        
        try {
            const response = await fetch("/api/v1/audit/refine", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    content: state.initialContent,
                    locality: state.answers.locality,
                    target_audience: state.answers.target_audience,
                    usp: state.answers.usp,
                    website_analysis: state.websiteAnalysis
                })
            });
            
            if (!response.ok) throw new Error("Failed to generate final SEO materials.");
            
            const data = await response.json();
            state.refinedResult = data;
            
            // Populate step 3 UI
            el.resultTitle.innerText = data.title;
            el.resultDescription.innerText = data.description;
            el.resultKeywords.innerText = data.keywords;
            el.resultContent.innerHTML = parseMarkdown(data.content);
            
            // Formulate target ID name
            if (state.url) {
                try {
                    const parsed = new URL(state.url.startsWith("http") ? state.url : "https://" + state.url);
                    el.inputId.value = parsed.hostname;
                } catch {
                    el.inputId.value = "api_refined";
                }
            } else {
                el.inputId.value = "api_refined";
            }
            
            hideLoader();
            showPanel(3);
        } catch (err) {
            hideLoader();
            alert(`Błąd generowania SEO: ${err.message}`);
        }
    }

    // Step 3 Click Handler: Save results to SQLite
    async function handleSaveToDb() {
        const targetId = el.inputId.value.trim();
        if (!targetId) {
            alert("Wpisz unikalną nazwę identyfikatora przed zapisem!");
            return;
        }
        
        try {
            const response = await fetch("/api/v1/audit/save", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    file_target: targetId,
                    title: state.refinedResult.title,
                    description: state.refinedResult.description,
                    keywords: state.refinedResult.keywords,
                    content: state.refinedResult.content
                })
            });
            
            if (!response.ok) throw new Error("Failed to save to db.");
            
            alert("💾 Pomyślnie zapisano w lokalnej bazie danych!");
            loadHistory();
        } catch (err) {
            alert(`Błąd zapisu: ${err.message}`);
        }
    }

    // Step 3 Click Handler: Regenerate with corrections
    async function handleRegenerate() {
        const correction = el.inputCorrection.value.trim();
        if (!correction) {
            alert("Wpisz uwagi lub poprawki do wprowadzenia!");
            return;
        }
        
        showLoader("🔄 Regenerowanie i wprowadzanie poprawek...");
        
        try {
            const response = await fetch("/api/v1/audit/refine", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    content: `${state.initialContent}\n\n[POPRAWKI UŻYTKOWNIKA DO UWZGLĘDNIENIA: ${correction}]`,
                    locality: state.answers.locality,
                    target_audience: state.answers.target_audience,
                    usp: state.answers.usp,
                    website_analysis: state.websiteAnalysis
                })
            });
            
            if (!response.ok) throw new Error("Failed to regenerate.");
            
            const data = await response.json();
            state.refinedResult = data;
            
            // Update fields
            el.resultTitle.innerText = data.title;
            el.resultDescription.innerText = data.description;
            el.resultKeywords.innerText = data.keywords;
            el.resultContent.innerHTML = parseMarkdown(data.content);
            
            el.inputCorrection.value = ""; // reset correction
            hideLoader();
        } catch (err) {
            hideLoader();
            alert(`Błąd regeneracji: ${err.message}`);
        }
    }

    // Render HTML Technical Checklist Cards
    function renderTechnicalSummary(metrics) {
        el.metricsGrid.innerHTML = "";
        
        let titleClass = "success", titleIcon = '<i class="fas fa-check"></i>', titleComment = "Prawidłowa długość.";
        if (!metrics.title) {
            titleClass = "error"; titleIcon = '<i class="fas fa-times"></i>'; titleComment = "Brak tagu <title>!";
        } else if (metrics.title_len < 30 || metrics.title_len > 60) {
            titleClass = "warning"; titleIcon = '<i class="fas fa-exclamation"></i>'; titleComment = `Za krótki lub za długi (${metrics.title_len} znaków). Zalecane 50-60.`;
        }
        addMetricCard("Tytuł <title>", metrics.title || "[BRAK]", titleClass, titleIcon, titleComment);
        
        let descClass = "success", descIcon = '<i class="fas fa-check"></i>', descComment = "Prawidłowa długość.";
        if (!metrics.description) {
            descClass = "error"; descIcon = '<i class="fas fa-times"></i>'; descComment = "Brak meta description!";
        } else if (metrics.description_len < 100 || metrics.description_len > 160) {
            descClass = "warning"; descIcon = '<i class="fas fa-exclamation"></i>'; descComment = `Sugerowana długość 120-160 (${metrics.description_len} zn.).`;
        }
        addMetricCard("Opis (Meta Description)", metrics.description || "[BRAK]", descClass, descIcon, descComment);
        
        let h1Class = "success", h1Icon = '<i class="fas fa-check"></i>', h1Comment = "Dokładnie jeden nagłówek H1.";
        if (metrics.h1_count === 0) {
            h1Class = "error"; h1Icon = '<i class="fas fa-times"></i>'; h1Comment = "Brak nagłówka H1 na stronie!";
        } else if (metrics.h1_count > 1) {
            h1Class = "error"; h1Icon = '<i class="fas fa-exclamation"></i>'; h1Comment = `Za dużo nagłówków H1 (${metrics.h1_count}). Powinien być 1.`;
        }
        addMetricCard("Nagłówki H1", `${metrics.h1_count} nagłówek(ów)`, h1Class, h1Icon, h1Comment);
        
        let imgClass = "success", imgIcon = '<i class="fas fa-check"></i>', imgComment = "Wszystkie grafiki posiadają tag ALT.";
        if (metrics.total_images > 0 && (metrics.images_missing_alt > 0 || metrics.images_with_empty_alt > 0)) {
            imgClass = "warning"; imgIcon = '<i class="fas fa-exclamation"></i>'; imgComment = `Brak ALT na ${metrics.images_missing_alt} z ${metrics.total_images} obrazów.`;
        } else if (metrics.total_images === 0) {
            imgClass = "success"; imgIcon = '<i class="fas fa-image"></i>'; imgComment = "Brak grafik na stronie.";
        }
        addMetricCard("Alternatywne opisy ALT", `${metrics.total_images} grafik`, imgClass, imgIcon, imgComment);

        const canClass = metrics.canonical ? "success" : "warning";
        const canIcon = metrics.canonical ? '<i class="fas fa-link"></i>' : '<i class="fas fa-exclamation"></i>';
        const canComment = metrics.canonical ? "Link kanoniczny zdefiniowany." : "Brak canonical linku.";
        addMetricCard("Tag kanoniczny (canonical)", metrics.canonical ? "Obecny" : "Brak", canClass, canIcon, canComment);
        
        let wcClass = metrics.word_count > 250 ? "success" : "warning";
        let wcComment = metrics.word_count > 250 ? "Wystarczająca ilość treści." : "Za mało tekstu na stronie.";
        addMetricCard("Liczba słów", `${metrics.word_count} słów`, wcClass, '<i class="fas fa-file-alt"></i>', wcComment);

        const httpsClass = metrics.https_status ? "success" : "error";
        const httpsIcon = metrics.https_status ? '<i class="fas fa-shield-alt"></i>' : '<i class="fas fa-unlock-alt"></i>';
        const httpsComment = metrics.https_status ? "Połączenie szyfrowane SSL." : "Niezabezpieczone połączenie HTTP!";
        addMetricCard("Certyfikat SSL (HTTPS)", metrics.https_status ? "Bezpieczny" : "Brak SSL", httpsClass, httpsIcon, httpsComment);

        const robOk = metrics.robots_txt_status === 200;
        const robClass = robOk ? "success" : "warning";
        const robIcon = robOk ? '<i class="fas fa-robot"></i>' : '<i class="fas fa-user-slash"></i>';
        const robComment = robOk ? "Plik robots.txt jest dostępny." : "Nie znaleziono pliku robots.txt.";
        addMetricCard("Plik robots.txt", robOk ? "Dostępny (200)" : "Brak (404)", robClass, robIcon, robComment);

        const siteOk = metrics.sitemap_xml_status === 200;
        const siteClass = siteOk ? "success" : "warning";
        const siteIcon = siteOk ? '<i class="fas fa-sitemap"></i>' : '<i class="fas fa-exclamation-triangle"></i>';
        const siteComment = siteOk ? "Mapa witryny sitemap.xml została wykryta." : "Nie wykryto mapy witryny.";
        addMetricCard("Mapa sitemap.xml", siteOk ? "Dostępna (200)" : "Brak (404)", siteClass, siteIcon, siteComment);

        const advDiv = document.createElement("div");
        advDiv.className = "advanced-analysis-card";
        
        let schemaBadges = "";
        if (metrics.schema_types && metrics.schema_types.length > 0) {
            metrics.schema_types.forEach(t => {
                schemaBadges += `<span class="schema-tag">${escapeHtml(t)}</span>`;
            });
        } else {
            schemaBadges = `<span style="font-size:0.85rem; color: var(--text-muted);">Brak wykrytych struktur Schema.org (JSON-LD)</span>`;
        }

        let wordsRows = "";
        if (metrics.top_words && metrics.top_words.length > 0) {
            metrics.top_words.forEach(item => {
                const word = Array.isArray(item) ? item[0] : item.word || item;
                const count = Array.isArray(item) ? item[1] : item.count || 0;
                wordsRows += `<tr>
                    <td style="color: var(--accent); font-weight:700;">${escapeHtml(word)}</td>
                    <td style="text-align:right; font-weight:700;">${count} x</td>
                </tr>`;
            });
        } else {
            wordsRows = `<tr><td colspan="2" style="text-align:center; color: var(--text-muted); padding: 12px;">Brak danych</td></tr>`;
        }

        let bigramsRows = "";
        if (metrics.top_bigrams && metrics.top_bigrams.length > 0) {
            metrics.top_bigrams.forEach(item => {
                const phrase = Array.isArray(item) ? (Array.isArray(item[0]) ? item[0].join(" ") : item[0]) : (item.phrase || item);
                const count = Array.isArray(item) ? item[1] : item.count || 0;
                bigramsRows += `<tr>
                    <td style="color: var(--secondary); font-weight:700;">${escapeHtml(phrase)}</td>
                    <td style="text-align:right; font-weight:700;">${count} x</td>
                </tr>`;
            });
        } else {
            bigramsRows = `<tr><td colspan="2" style="text-align:center; color: var(--text-muted); padding: 12px;">Brak danych</td></tr>`;
        }

        advDiv.innerHTML = `
            <!-- Schema.org Section (Takes Full Width) -->
            <div style="margin-bottom: 30px;">
                <div style="font-weight:700; font-size:1rem; margin-bottom:15px; color:var(--text-light); display:flex; align-items:center; gap:8px;">
                    <i class="fas fa-code" style="color:var(--secondary);"></i> Dane Strukturyzowane (Schema.org):
                </div>
                <div class="schema-box">${schemaBadges}</div>
            </div>
            
            <!-- Keywords and Phrases Section (Takes Full Width, Tables are Side-by-Side) -->
            <div>
                <div style="font-weight:700; font-size:1rem; margin-bottom:15px; color:var(--text-light); display:flex; align-items:center; gap:8px;">
                    <i class="fas fa-chart-line" style="color:var(--accent);"></i> Najczęstsze Słowa i Frazy (Gęstość):
                </div>
                <div class="keyword-density-tables">
                    <table class="density-table">
                        <thead>
                            <tr>
                                <th style="color: var(--text-muted);">Słowo</th>
                                <th style="text-align:right; color: var(--text-muted);">Wystąpienia</th>
                            </tr>
                        </thead>
                        <tbody>${wordsRows}</tbody>
                    </table>
                    <table class="density-table">
                        <thead>
                            <tr>
                                <th style="color: var(--text-muted);">Fraza</th>
                                <th style="text-align:right; color: var(--text-muted);">Wystąpienia</th>
                            </tr>
                        </thead>
                        <tbody>${bigramsRows}</tbody>
                    </table>
                </div>
            </div>
        `;
        el.metricsGrid.appendChild(advDiv);
    }

    function addMetricCard(name, val, typeClass, iconHtml, comment) {
        const div = document.createElement("div");
        div.className = "metric-card";
        div.innerHTML = `
            <div class="metric-icon ${typeClass}">${iconHtml}</div>
            <div class="metric-details">
                <div class="metric-name">${escapeHtml(name)}</div>
                <div class="metric-value">${escapeHtml(val)}</div>
                <div class="metric-comment">${escapeHtml(comment)}</div>
            </div>
        `;
        el.metricsGrid.appendChild(div);
    }

    // Render Gemini technical recommendations in report box
    function renderAuditReport(markdown) {
        el.reportBox.innerHTML = parseMarkdown(markdown);
    }

    // Render Dynamic Gaps Form with 3 Steps questions from AI
    function renderGapsForm(gaps) {
        el.gapsForm.innerHTML = "";
        
        const aspects = [
            { id: "locality", label: "Lokalizacja / Obszar działania" },
            { id: "target_audience", label: "Grupa docelowa" },
            { id: "usp", label: "USP / Wyróżniki i usługi" }
        ];
        
        aspects.forEach((asp, idx) => {
            const info = gaps[asp.id];
            const fg = document.createElement("div");
            fg.className = "form-group";
            
            if (info.present) {
                fg.innerHTML = `
                    <label>${asp.label} <span style="color:var(--success); font-weight:700;">[Wykryto automatycznie]</span></label>
                    <input type="text" id="input-gap-${asp.id}" value="${escapeHtml(info.value)}" class="input-success" placeholder="Np. cała Polska, lokalnie, gracze">
                    <p style="font-size:0.8rem; color:var(--text-muted); margin-top:4px;">Wykryto z Twojego promptu/strony. Możesz zmienić lub pozostawić bez zmian.</p>
                `;
            } else {
                fg.innerHTML = `
                    <label>${asp.label} <span style="color:var(--warning); font-weight:700;">[Brakujące dane]</span></label>
                    <p style="font-size:0.85rem; color: #a5b4fc; font-weight: 600; margin-bottom: 6px;">👉 ${escapeHtml(info.question)}</p>
                    <input type="text" id="input-gap-${asp.id}" placeholder="Twoja odpowiedź (np. fani gier, cała Polska, najniższe ceny)">
                `;
            }
            el.gapsForm.appendChild(fg);
        });
    }

    // Wizard panel switcher
    function showPanel(stepNum) {
        state.currentStep = stepNum;
        
        // Reset nav highlights
        el.nav1.className = "step-nav-item" + (stepNum === 1 ? " active" : stepNum > 1 ? " completed" : "");
        el.nav2.className = "step-nav-item" + (stepNum === 2 ? " active" : stepNum > 2 ? " completed" : "");
        el.nav3.className = "step-nav-item" + (stepNum === 3 ? " active" : "");
        
        // Toggle visibility
        el.panel1.style.display = stepNum === 1 ? "block" : "none";
        el.panel2.style.display = stepNum === 2 ? "block" : "none";
        el.panel3.style.display = stepNum === 3 ? "block" : "none";
    }

    // Loading overlay
    function showLoader(txt) {
        el.loaderText.innerText = txt;
        el.loader.style.display = "flex";
    }

    function hideLoader() {
        el.loader.style.display = "none";
    }

    // Global Clipboard Copies
    window.copyText = function(elementId, btn) {
        const text = document.getElementById(elementId).innerText;
        navigator.clipboard.writeText(text).then(() => {
            const orig = btn.innerText;
            btn.innerText = "Skopiowano!";
            btn.style.background = "var(--success)";
            setTimeout(() => {
                btn.innerText = orig;
                btn.style.background = "";
            }, 1500);
        });
    };

    // Helper functions
    function escapeHtml(text) {
        if (!text) return "";
        return text
            .toString()
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Lightweight clean markdown parser
    function parseMarkdown(md) {
        if (!md) return "";
        let html = md;
        
        // Headers
        html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
        html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
        html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
        
        // Bold
        html = html.replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>');
        
        // Icons/Emojis inside list bullets
        html = html.replace(/^\s*-\s*(.*$)/gim, '<li>$1</li>');
        html = html.replace(/^\s*\*\s*(.*$)/gim, '<li>$1</li>');
        
        // Wrappers for lists
        html = html.replace(/(<li>.*<\/li>)/gim, '<ul>$1</ul>');
        // Clean multiple adjacent ul tags
        html = html.replace(/<\/ul>\s*<ul>/gim, '');
        
        // New lines
        html = html.replace(/\n$/gim, '<br />');
        
        return html;
    }
});
