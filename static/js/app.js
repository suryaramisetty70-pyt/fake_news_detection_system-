/**
 * TruthLens AI — Interactive Client-Side Engine
 * Handles real-time verification, Web Audio API, OCR, Newspaper Reader & Dynamic UI
 */

// Initialize Lucide Icons on load
document.addEventListener("DOMContentLoaded", () => {
    lucide.createIcons();
    initCharCounter();
    loadAnalytics();
});

// ─── Tab Switching ───
function switchTab(tabId) {
    document.querySelectorAll(".tab-content").forEach(el => el.classList.add("hidden"));
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.classList.remove("active-tab");
        btn.classList.add("inactive-tab");
    });

    const activeContent = document.getElementById(tabId);
    if (activeContent) activeContent.classList.remove("hidden");

    const activeNav = document.getElementById(`nav-${tabId}`);
    if (activeNav) {
        activeNav.classList.remove("inactive-tab");
        activeNav.classList.add("active-tab");
    }

    if (tabId === "news-tab") {
        fetchPaperHeadlines();
    } else if (tabId === "stats-tab") {
        loadHistory();
        loadAnalytics();
    }

    lucide.createIcons();
}

// ─── Character Counter ───
function initCharCounter() {
    const input = document.getElementById("news-input");
    const count = document.getElementById("char-count");
    if (input && count) {
        input.addEventListener("input", () => {
            count.textContent = `${input.value.length} characters`;
        });
    }
}

function clearText() {
    const input = document.getElementById("news-input");
    if (input) {
        input.value = "";
        document.getElementById("char-count").textContent = "0 characters";
    }
    document.getElementById("result-container").classList.add("hidden");
    document.getElementById("deep-dive-grid").classList.add("hidden");
    document.getElementById("idle-state").classList.remove("hidden");
}

// ─── Sample Prompts ───
const SAMPLES = {
    1: "SHOCKING CONSPIRACY EXPOSED!!! The government is secretly using alien technology to control human minds through 5G towers! SHARE before it gets deleted! URGENT!",
    2: "Federal Reserve officials held interest rates steady on Wednesday and signaled that borrowing costs may still be lowered later this year according to reports from Reuters.",
    3: "చంద్రబాబు నాయుడు ఆంధ్రప్రదేశ్ ముఖ్యమంత్రిగా ప్రమాణ స్వీకారం చేశారు.",
    4: "[10/08, 12:45 pm] Forwarded many times\nBreaking News: Government announced all bank loans will be waived off tomorrow. Check website urgently."
};

function loadSample(id) {
    const input = document.getElementById("news-input");
    if (input && SAMPLES[id]) {
        input.value = SAMPLES[id];
        document.getElementById("char-count").textContent = `${input.value.length} characters`;
        analyzeText();
    }
}

// ─── Main Verification Call ───
async function analyzeText() {
    const input = document.getElementById("news-input");
    const text = input ? input.value.trim() : "";
    if (!text || text.length < 5) {
        alert("Please enter at least 5 characters to analyze.");
        return;
    }

    // Toggle loading UI
    document.getElementById("idle-state").classList.add("hidden");
    document.getElementById("result-container").classList.add("hidden");
    document.getElementById("deep-dive-grid").classList.add("hidden");
    document.getElementById("loading-state").classList.remove("hidden");

    try {
        const response = await fetch("/api/verify", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text, source: "text_input" })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Verification failed");
        }

        const data = await response.json();
        renderResults(data);
        renderDeepDive(data);
    } catch (err) {
        alert(`Error: ${err.message}`);
        document.getElementById("idle-state").classList.remove("hidden");
    } finally {
        document.getElementById("loading-state").classList.add("hidden");
    }
}

// ─── Result Card Renderer ───
function renderResults(data) {
    const container = document.getElementById("result-container");
    container.classList.remove("hidden");

    const label = data.label || "UNABLE TO VERIFY";
    const confidence = Math.round((data.confidence || 0) * 100);
    const webCheck = data.web_check || {};
    const sourcesCount = webCheck.trusted_sources_count || 0;

    let verdictColor = "border-amber-500/40 bg-amber-500/10 text-amber-400";
    let badgeText = "⚠️ UNABLE TO VERIFY";
    let descText = data.message || "No verified media or fact-checker corroboration found. Treat with caution.";

    if (label === "REAL") {
        verdictColor = "border-emerald-500/40 bg-emerald-500/10 text-emerald-400";
        badgeText = "✅ VERIFIED REAL NEWS";
        descText = `Corroborated by ${sourcesCount} trusted media agencies across India.`;
        // Confetti celebration
        confetti({ particleCount: 70, spread: 60, origin: { y: 0.7 } });
    } else if (label === "FAKE") {
        verdictColor = "border-rose-500/40 bg-rose-500/10 text-rose-400";
        badgeText = "❌ OFFICIALLY DEBUNKED / FAKE";
        descText = data.message || "This claim has been contradicted or flagged by official fact-checking agencies.";
    }

    let matchesHtml = "";
    if (webCheck.matches && webCheck.matches.length > 0) {
        matchesHtml = `
            <div class="mt-4 pt-4 border-t border-surfaceBorder space-y-2">
                <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Trusted Publisher Matches:</span>
                ${webCheck.matches.map(m => `
                    <div class="p-2.5 rounded-xl bg-darkbg/80 border border-surfaceBorder/80 flex items-start justify-between gap-3 text-xs">
                        <div>
                            <a href="${m.url}" target="_blank" class="font-semibold text-indigo-400 hover:underline">
                                ${m.title}
                            </a>
                            <p class="text-slate-400 text-[11px] mt-0.5">Publisher Domain: <span class="text-slate-300 font-mono">${m.domain}</span></p>
                        </div>
                        <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 border border-emerald-500/30 text-emerald-400 shrink-0">
                            VERIFIED
                        </span>
                    </div>
                `).join("")}
            </div>
        `;
    }

    container.innerHTML = `
        <div class="glass-panel p-6 rounded-2xl border-2 ${verdictColor} space-y-4 shadow-2xl transition">
            <div class="flex items-center justify-between">
                <span class="px-3 py-1 rounded-full text-xs font-bold tracking-wide uppercase ${verdictColor}">
                    ${badgeText}
                </span>
                <span class="text-xs font-semibold text-slate-400 font-mono">
                    Confidence: <strong class="text-white">${confidence}%</strong>
                </span>
            </div>

            <p class="text-sm text-slate-200 leading-relaxed">${descText}</p>

            ${data.cached ? `<div class="text-[11px] text-indigo-400 flex items-center gap-1">⚡ Loaded instantaneously from local SQLite verification cache</div>` : ""}

            ${matchesHtml}
        </div>
    `;

    lucide.createIcons();
}

// ─── Deep Dive Grid Renderer ───
function renderDeepDive(data) {
    const grid = document.getElementById("deep-dive-grid");
    grid.classList.remove("hidden");

    const ling = data.linguistics || {};
    const ensemble = data.ensemble || {};
    const social = data.social_context || {};
    const votes = ensemble.votes || {};

    grid.innerHTML = `
        <!-- Card 1: Multi-Model Voting Ensemble (sneyhaa / vijaisuria inspired) -->
        <div class="glass-panel p-6 rounded-2xl space-y-4">
            <div class="flex items-center justify-between">
                <h4 class="text-sm font-bold text-white flex items-center gap-2">
                    <i data-lucide="layers" class="w-4 h-4 text-primary"></i>
                    4-Model Voting Ensemble
                </h4>
                <span class="text-xs font-semibold px-2 py-0.5 rounded bg-surface border border-surfaceBorder text-slate-300">
                    Ensemble: ${ensemble.ensemble_label || "N/A"}
                </span>
            </div>

            <div class="space-y-2.5 text-xs">
                ${Object.entries(votes).map(([model, v]) => `
                    <div class="p-2.5 rounded-xl bg-darkbg border border-surfaceBorder flex items-center justify-between">
                        <div>
                            <span class="font-medium text-slate-200 capitalize">${model.replace(/_/g, " ")}</span>
                            <span class="text-[10px] text-slate-400 block">Vote: ${v.label}</span>
                        </div>
                        <span class="font-mono font-bold ${v.label === 'REAL' ? 'text-emerald-400' : 'text-rose-400'}">
                            ${Math.round((v.prob_real || v.confidence || 0) * 100)}% Real
                        </span>
                    </div>
                `).join("")}
            </div>
        </div>

        <!-- Card 2: Linguistic & Dual-Emotion (aryashah2k & WWW Dual-Emotion inspired) -->
        <div class="glass-panel p-6 rounded-2xl space-y-4">
            <h4 class="text-sm font-bold text-white flex items-center gap-2">
                <i data-lucide="activity" class="w-4 h-4 text-accent"></i>
                Linguistic Polarity & Emotion
            </h4>

            <div class="space-y-3 text-xs">
                <div>
                    <div class="flex justify-between text-slate-300 mb-1">
                        <span>Sensationalism / Alarmism</span>
                        <span class="font-mono">${ling.sensationalism || 0}%</span>
                    </div>
                    <div class="w-full bg-darkbg rounded-full h-2">
                        <div class="bg-rose-500 h-2 rounded-full" style="width: ${ling.sensationalism || 0}%"></div>
                    </div>
                </div>

                <div>
                    <div class="flex justify-between text-slate-300 mb-1">
                        <span>Subjectivity Index (Opinion vs Fact)</span>
                        <span class="font-mono">${ling.subjectivity || 0}%</span>
                    </div>
                    <div class="w-full bg-darkbg rounded-full h-2">
                        <div class="bg-amber-500 h-2 rounded-full" style="width: ${ling.subjectivity || 0}%"></div>
                    </div>
                </div>

                <div>
                    <div class="flex justify-between text-slate-300 mb-1">
                        <span>Credibility Index</span>
                        <span class="font-mono">${ling.credibility_index || 50}%</span>
                    </div>
                    <div class="w-full bg-darkbg rounded-full h-2">
                        <div class="bg-emerald-500 h-2 rounded-full" style="width: ${ling.credibility_index || 50}%"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Card 3: Social Media Context (Sohamcoder1 inspired) -->
        <div class="glass-panel p-6 rounded-2xl space-y-4">
            <h4 class="text-sm font-bold text-white flex items-center gap-2">
                <i data-lucide="share-2" class="w-4 h-4 text-emerald-400"></i>
                Social Media Origin Vector
            </h4>

            <div class="space-y-2.5 text-xs">
                <div class="p-3 rounded-xl bg-darkbg border border-surfaceBorder">
                    <span class="text-slate-400">Detected Origin:</span>
                    <p class="font-semibold text-slate-200 text-sm mt-0.5">${social.platform || "Web Article"}</p>
                </div>

                <div class="p-3 rounded-xl bg-darkbg border border-surfaceBorder flex items-center justify-between">
                    <span class="text-slate-400">Viral Forwarding Risk:</span>
                    <span class="font-mono font-bold text-sm ${social.risk_score > 40 ? 'text-rose-400' : 'text-emerald-400'}">
                        ${social.risk_score || 0}%
                    </span>
                </div>

                ${social.viral_signals && social.viral_signals.length > 0 ? `
                    <div class="text-[11px] text-amber-300/90 bg-amber-950/40 border border-amber-500/20 p-2 rounded-lg">
                        ⚠️ ${social.viral_signals.join(", ")}
                    </div>
                ` : ""}
            </div>
        </div>
    `;

    lucide.createIcons();
}

// ─── Live Audio Recording (Web Audio API) ───
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

async function toggleRecording() {
    const btn = document.getElementById("mic-record-btn");
    const status = document.getElementById("record-status");
    const ring = document.getElementById("record-ring");

    if (!isRecording) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
            mediaRecorder.onstop = sendVoiceData;

            mediaRecorder.start();
            isRecording = true;
            status.textContent = "Recording... Click again to stop";
            ring.classList.remove("hidden");
        } catch (err) {
            alert(`Microphone access error: ${err.message}. Ensure microphone permission is granted.`);
        }
    } else {
        if (mediaRecorder && mediaRecorder.state !== "inactive") {
            mediaRecorder.stop();
        }
        isRecording = false;
        status.textContent = "Processing speech...";
        ring.classList.add("hidden");
    }
}

async function sendVoiceData() {
    const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
    const lang = document.getElementById("voice-lang-select").value;

    const formData = new FormData();
    formData.append("file", audioBlob, "voice_input.wav");
    formData.append("language", lang);

    const status = document.getElementById("record-status");
    status.textContent = "Transcribing & Verifying with AI...";

    try {
        const response = await fetch("/api/voice-verify", {
            method: "POST",
            body: formData
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Voice verification failed");

        status.textContent = "Click to Start Recording";
        // Show transcription in text tab and switch
        const textInput = document.getElementById("news-input");
        if (textInput) {
            textInput.value = data.transcription;
            switchTab("text-tab");
            renderResults(data.prediction);
            renderDeepDive(data.prediction);
        }
    } catch (err) {
        alert(`Voice Error: ${err.message}`);
        status.textContent = "Click to Start Recording";
    }
}

// ─── Image OCR Handling ───
const dropZone = document.getElementById("drop-zone");
const ocrFileInput = document.getElementById("ocr-file-input");

if (dropZone && ocrFileInput) {
    dropZone.addEventListener("click", () => ocrFileInput.click());
    dropZone.addEventListener("dragover", e => { e.preventDefault(); dropZone.classList.add("border-primary"); });
    dropZone.addEventListener("dragleave", () => dropZone.classList.remove("border-primary"));
    dropZone.addEventListener("drop", e => {
        e.preventDefault();
        dropZone.classList.remove("border-primary");
        if (e.dataTransfer.files.length) {
            ocrFileInput.files = e.dataTransfer.files;
            previewImage(e.dataTransfer.files[0]);
        }
    });

    ocrFileInput.addEventListener("change", () => {
        if (ocrFileInput.files.length) previewImage(ocrFileInput.files[0]);
    });
}

function previewImage(file) {
    const reader = new FileReader();
    reader.onload = e => {
        document.getElementById("image-preview").src = e.target.result;
        document.getElementById("drop-zone").classList.add("hidden");
        document.getElementById("image-preview-wrapper").classList.remove("hidden");
    };
    reader.readAsDataURL(file);
}

async function processImageOCR() {
    const file = ocrFileInput.files[0];
    if (!file) return;

    const lang = document.getElementById("ocr-lang-select").value;
    const btn = document.getElementById("ocr-run-btn");
    btn.textContent = "Extracting text with Tesseract...";
    btn.disabled = true;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("language", lang);

    try {
        const response = await fetch("/api/ocr-verify", {
            method: "POST",
            body: formData
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "OCR extraction failed");

        // Send to text tab
        const textInput = document.getElementById("news-input");
        if (textInput) {
            textInput.value = data.extracted_text;
            switchTab("text-tab");
            renderResults(data.prediction);
            renderDeepDive(data.prediction);
        }
    } catch (err) {
        alert(`OCR Error: ${err.message}`);
    } finally {
        btn.textContent = "Extract & Verify News";
        btn.disabled = false;
    }
}

// ─── Live Newspaper Headlines Reader ───
async function fetchPaperHeadlines() {
    const paper = document.getElementById("paper-select").value;
    const grid = document.getElementById("headlines-grid");
    grid.innerHTML = `<div class="col-span-full py-12 text-center text-slate-400">Fetching live front-page headlines...</div>`;

    try {
        const response = await fetch(`/api/scrapers/headlines?newspaper=${paper}&max_count=12`);
        const data = await response.json();

        if (!data.headlines || data.headlines.length === 0) {
            grid.innerHTML = `<div class="col-span-full py-12 text-center text-slate-400">No headlines returned. Please try another publisher.</div>`;
            return;
        }

        grid.innerHTML = data.headlines.map(h => `
            <div class="glass-panel p-5 rounded-2xl flex flex-col justify-between hover:border-primary/50 transition group">
                <div>
                    <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">${h.newspaper}</span>
                    <h4 class="text-sm font-semibold text-slate-100 group-hover:text-primary transition mt-1.5 leading-snug">
                        ${h.title}
                    </h4>
                </div>
                <div class="mt-4 pt-3 border-t border-surfaceBorder flex items-center justify-between text-xs">
                    <a href="${h.url}" target="_blank" class="text-indigo-400 hover:underline">Read Source</a>
                    <button onclick="checkHeadline('${encodeURIComponent(h.title)}')" class="px-3 py-1 rounded-lg bg-primary/20 hover:bg-primary text-primary hover:text-white transition font-medium">
                        Fact-Check
                    </button>
                </div>
            </div>
        `).join("");
    } catch (err) {
        grid.innerHTML = `<div class="col-span-full py-12 text-center text-rose-400">Failed to fetch newspaper headlines: ${err.message}</div>`;
    }
}

function checkHeadline(encodedTitle) {
    const title = decodeURIComponent(encodedTitle);
    const input = document.getElementById("news-input");
    if (input) {
        input.value = title;
        switchTab("text-tab");
        analyzeText();
    }
}

// ─── Intelligence Analytics & History ───
async function loadAnalytics() {
    try {
        const res = await fetch("/api/analytics");
        if (!res.ok) return;
        const data = await res.json();

        document.getElementById("stat-total").textContent = data.total_predictions || 0;
        document.getElementById("stat-real").textContent = data.real_count || 0;
        document.getElementById("stat-fake").textContent = data.fake_count || 0;
        document.getElementById("stat-unverified").textContent = (data.total_predictions || 0) - ((data.real_count || 0) + (data.fake_count || 0));

        const realRate = data.total_predictions ? Math.round((data.real_count / data.total_predictions) * 100) : 0;
        const fakeRate = data.total_predictions ? Math.round((data.fake_count / data.total_predictions) * 100) : 0;

        document.getElementById("stat-real-rate").textContent = `${realRate}% rate`;
        document.getElementById("stat-fake-rate").textContent = `${fakeRate}% rate`;
    } catch (e) {
        console.error("Analytics fetch failed:", e);
    }
}

async function loadHistory() {
    const tbody = document.getElementById("history-table-body");
    try {
        const res = await fetch("/api/history?limit=15");
        const data = await res.json();
        const history = data.history || [];

        if (history.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="py-6 text-center text-slate-500">No past scans recorded yet.</td></tr>`;
            return;
        }

        tbody.innerHTML = history.map(row => {
            let badge = "bg-amber-950 border border-amber-500/30 text-amber-400";
            if (row.prediction_label === "REAL") badge = "bg-emerald-950 border border-emerald-500/30 text-emerald-400";
            else if (row.prediction_label === "FAKE") badge = "bg-rose-950 border border-rose-500/30 text-rose-400";

            return `
                <tr class="hover:bg-surface/60 transition">
                    <td class="py-3 px-4">
                        <span class="px-2 py-0.5 rounded text-[11px] font-bold ${badge}">
                            ${row.prediction_label}
                        </span>
                    </td>
                    <td class="py-3 px-4 max-w-xs truncate text-slate-200">${row.text_preview}</td>
                    <td class="py-3 px-4 font-mono">${Math.round(row.confidence * 100)}%</td>
                    <td class="py-3 px-4 capitalize text-slate-400">${row.source.replace("_", " ")}</td>
                    <td class="py-3 px-4 text-slate-500 text-xs">${row.analyzed_at || "Recent"}</td>
                </tr>
            `;
        }).join("");
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="5" class="py-6 text-center text-rose-400">Failed to load history.</td></tr>`;
    }
}
