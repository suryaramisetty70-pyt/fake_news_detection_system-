function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    })[char]);
}

function safeSourceUrl(value) {
    try {
        const url = new URL(value);
        return ["http:", "https:"].includes(url.protocol) ? escapeHtml(url.href) : "#";
    } catch {
        return "#";
    }
}

/**
 * TruthLens AI — Interactive Client-Side Engine
 * Handles real-time verification, Web Audio API, OCR, Newspaper Reader & Dynamic UI
 */

// Initialize Lucide Icons on load
document.addEventListener("DOMContentLoaded", () => {
    window.lucide?.createIcons();
    initCharCounter();
    loadPublishers();
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

    window.lucide?.createIcons();
}

// ─── Character Counter ───
function initCharCounter() {
    const input = document.getElementById("news-input");
    const count = document.getElementById("char-count");
    if (input && count) {
        input.addEventListener("input", () => {
            resetVerification();
            count.textContent = `${input.value.length} characters`;
        });
    }
}

function resetVerification() {
    activeVerification?.abort();
    activeVerification = undefined;
    document.getElementById("loading-state").classList.add("hidden");
    document.getElementById("result-container").classList.add("hidden");
    document.getElementById("deep-dive-grid").classList.add("hidden");
    document.getElementById("idle-state").classList.remove("hidden");
}

function clearText() {
    resetVerification();
    const input = document.getElementById("news-input");
    if (input) {
        input.value = "";
        document.getElementById("char-count").textContent = "0 characters";
    }
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
let activeVerification;

async function analyzeText(source = "text_input") {
    const input = document.getElementById("news-input");
    const text = input ? input.value.trim() : "";
    if (!text || text.length < 8) {
        alert("Please enter at least 8 characters to analyze.");
        return;
    }

    activeVerification?.abort();
    const verification = new AbortController();
    activeVerification = verification;

    // Toggle loading UI
    document.getElementById("idle-state").classList.add("hidden");
    document.getElementById("result-container").classList.add("hidden");
    document.getElementById("deep-dive-grid").classList.add("hidden");
    document.getElementById("loading-state").classList.remove("hidden");

    try {
        const response = await fetch("/api/verify", {
            method: "POST",
            signal: AbortSignal.any([verification.signal, AbortSignal.timeout(25000)]),
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text, source })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Verification failed");
        }

        const data = await response.json();
        if (activeVerification === verification) {
            renderResults(data);
            renderDeepDive(data);
        }
    } catch (err) {
        if (verification.signal.aborted) return;
        alert(err.name === "TimeoutError" ? "Verification timed out. Please try again." : `Error: ${err.message}`);
        document.getElementById("idle-state").classList.remove("hidden");
    } finally {
        if (activeVerification === verification) {
            activeVerification = undefined;
            document.getElementById("loading-state").classList.add("hidden");
        }
    }
}

// ─── Result Card Renderer ───
function renderResults(data) {
    const container = document.getElementById("result-container");
    container.classList.remove("hidden");

    const label = data.label || "UNABLE TO VERIFY";
    const webCheck = data.web_check || {};

    let verdictColor = "border-amber-500/40 bg-amber-500/10 text-amber-400";
    let badgeText = "⚠️ UNABLE TO VERIFY";
    let descText = data.message || "No verified media or fact-checker corroboration found. Treat with caution.";

    if (label === "REAL") {
        verdictColor = "border-emerald-500/40 bg-emerald-500/10 text-emerald-400";
        badgeText = data.model_type === "official_record"
            ? "✅ CONFIRMED BY AN OFFICIAL RECORD" : "✅ CONFIRMED BY FACT-CHECKER";
    } else if (label === "REPORTED") {
        badgeText = "MATCHING PUBLISHED HEADLINE";
    } else if (label === "FAKE") {
        verdictColor = "border-rose-500/40 bg-rose-500/10 text-rose-400";
        badgeText = "❌ CONTRADICTED BY SOURCE";
        descText = data.message || "This claim has been contradicted or flagged by official fact-checking agencies.";
    }

    let matchesHtml = "";
    if (webCheck.matches && webCheck.matches.length > 0) {
        matchesHtml = `
            <div class="mt-4 pt-4 border-t border-surfaceBorder space-y-2">
                <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Source Evidence</span>
                ${webCheck.matches.map(m => `
                    <div class="p-2.5 rounded-xl bg-darkbg/80 border border-surfaceBorder/80 flex items-start justify-between gap-3 text-xs">
                        <div>
                            <a href="${safeSourceUrl(m.url)}" target="_blank" rel="noopener noreferrer" class="font-semibold text-indigo-400 hover:underline">
                                ${escapeHtml(m.title)}
                            </a>
                            <p class="text-slate-400 text-[11px] mt-0.5">Publisher Domain: <span class="text-slate-300 font-mono">${escapeHtml(m.domain)}</span></p>
                        </div>
                        <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 border border-emerald-500/30 text-emerald-400 shrink-0">
                            ${({ REAL: "SUPPORTS", FAKE: "DEBUNKS", REPORTED: "HEADLINE MATCH" })[m.stance] || "RELATED"}
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
            </div>

            <p class="text-sm text-slate-200 leading-relaxed">${escapeHtml(descText)}</p>

            ${data.cached ? `<div class="text-[11px] text-indigo-400 flex items-center gap-1">⚡ Loaded instantaneously from local SQLite verification cache</div>` : ""}

            ${matchesHtml}
        </div>
    `;

    window.lucide?.createIcons();
}

// ─── Deep Dive Grid Renderer ───
function renderDeepDive(data) {
    const grid = document.getElementById("deep-dive-grid");
    grid.classList.remove("hidden");

    const ling = data.linguistics || {};
    const social = data.social_context || {};
    grid.innerHTML = `
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
                        <span>Writing style score</span>
                        <span class="font-mono">${ling.credibility_index ?? 50}%</span>
                    </div>
                    <div class="w-full bg-darkbg rounded-full h-2">
                        <div class="bg-emerald-500 h-2 rounded-full" style="width: ${ling.credibility_index ?? 50}%"></div>
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

    window.lucide?.createIcons();
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
        btn.disabled = true;
        voiceUpload.disabled = true;
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
            mediaRecorder.onstop = () => {
                stream.getTracks().forEach(track => track.stop());
                sendVoiceData(new Blob(audioChunks, { type: mediaRecorder.mimeType }));
            };

            mediaRecorder.start();
            isRecording = true;
            status.textContent = "Recording... Click again to stop";
            ring.classList.remove("hidden");
        } catch (err) {
            voiceUpload.disabled = false;
            alert(`Microphone access error: ${err.message}. Ensure microphone permission is granted.`);
        } finally {
            btn.disabled = false;
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

const voiceUpload = document.getElementById("voice-file-input");
voiceUpload.addEventListener("change", () => {
    const file = voiceUpload.files[0];
    if (file) sendVoiceData(file);
    voiceUpload.value = "";
});

async function sendVoiceData(audioBlob) {
    const mic = document.getElementById("mic-record-btn");
    mic.disabled = voiceUpload.disabled = true;
    const lang = document.getElementById("voice-lang-select").value;

    const formData = new FormData();
    formData.append("file", audioBlob, "voice_input");
    formData.append("language", lang);

    const status = document.getElementById("record-status");
    status.textContent = "Transcribing & Verifying with AI...";

    try {
        const response = await fetch("/api/voice-verify", {
            method: "POST",
            body: formData
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || "Voice verification failed");

        status.textContent = "Click to Start Recording";
        // Show transcription in text tab and switch
        const textInput = document.getElementById("news-input");
        if (textInput) {
            clearText();
            textInput.value = data.transcription;
            textInput.dispatchEvent(new Event("input"));
            document.getElementById("idle-state").classList.add("hidden");
            switchTab("text-tab");
            renderResults(data.prediction);
            renderDeepDive(data.prediction);
        }
    } catch (err) {
        alert(`Voice Error: ${err.message}`);
        status.textContent = "Click to Start Recording";
    } finally {
        mic.disabled = voiceUpload.disabled = false;
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
        if (!response.ok && /unavailable on this server|not installed on this server/i.test(data.error || "")) {
            btn.textContent = "Reading the image in your browser…";
            if (!window.Tesseract) {
                await new Promise((resolve, reject) => {
                    const script = document.createElement("script");
                    script.src = "https://cdn.jsdelivr.net/npm/tesseract.js@5.1.1/dist/tesseract.min.js";
                    script.onload = resolve;
                    script.onerror = () => reject(new Error("Could not load the browser OCR engine."));
                    document.head.appendChild(script);
                });
            }
            const languages = {English:"eng", Telugu:"tel", Hindi:"hin", Tamil:"tam", Kannada:"kan", Malayalam:"mal", Bengali:"ben", Marathi:"mar"};
            const worker = await Tesseract.createWorker(languages[lang]);
            let extracted;
            try {
                const result = await worker.recognize(file);
                extracted = result.data.text.trim();
            } finally {
                await worker.terminate();
            }
            if (extracted.length < 8) throw new Error("Too little readable text. Try a clearer image.");
            clearText();
            const input = document.getElementById("news-input");
            input.value = extracted;
            input.dispatchEvent(new Event("input"));
            switchTab("text-tab");
            await analyzeText("ocr_image");
            return;
        }
        if (!response.ok) throw new Error(data.error || data.detail || "OCR extraction failed");

        // Send to text tab
        const textInput = document.getElementById("news-input");
        if (textInput) {
            clearText();
            textInput.value = data.extracted_text;
            textInput.dispatchEvent(new Event("input"));
            document.getElementById("idle-state").classList.add("hidden");
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
async function loadPublishers() {
    const select = document.getElementById("paper-select");
    try {
        const response = await fetch("/api/scrapers/sources");
        if (!response.ok) return;
        const data = await response.json();
        const selected = select.value;
        select.replaceChildren(...Object.entries(data.newspapers).map(([key, name]) => new Option(name, key)));
        select.value = selected;
    } catch {
        // The built-in list is available when the source directory is offline.
    }
}

async function fetchPaperHeadlines() {
    const paper = document.getElementById("paper-select").value;
    const grid = document.getElementById("headlines-grid");
    grid.innerHTML = `<div class="col-span-full py-12 text-center text-slate-400">Fetching live front-page headlines...</div>`;

    try {
        const response = await fetch(`/api/scrapers/headlines?newspaper=${paper}&max_count=12`);
        const data = await response.json();

        if (paper !== document.getElementById("paper-select").value) return;
        if (!response.ok) throw new Error(data.error || "Publisher unavailable");
        if (!data.headlines || data.headlines.length === 0) {
            grid.innerHTML = `<div class="col-span-full py-12 text-center text-slate-400">No headlines returned. Please try another publisher.</div>`;
            return;
        }

        grid.innerHTML = data.headlines.map(h => `
            <div class="glass-panel p-5 rounded-2xl flex flex-col justify-between hover:border-primary/50 transition group">
                <div>
                    <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">${escapeHtml(h.newspaper)}</span>
                    <h4 class="text-sm font-semibold text-slate-100 group-hover:text-primary transition mt-1.5 leading-snug">
                        ${escapeHtml(h.title)}
                    </h4>
                </div>
                <div class="mt-4 pt-3 border-t border-surfaceBorder flex items-center justify-between text-xs">
                    <a href="${safeSourceUrl(h.url)}" target="_blank" rel="noopener noreferrer" class="text-indigo-400 hover:underline">Read Source</a>
                    <button data-claim="${escapeHtml(h.title)}" class="px-3 py-1 rounded-lg bg-primary/20 hover:bg-primary text-primary hover:text-white transition font-medium">
                        Fact-Check
                    </button>
                </div>
            </div>
        `).join("");
        const buttons = grid.querySelectorAll("[data-claim]");
        buttons.forEach(button => {
            button.addEventListener("click", () => checkHeadline(button.dataset.claim));
        });
    } catch (err) {
        grid.innerHTML = `<div class="col-span-full py-12 text-center text-rose-400">Failed to fetch newspaper headlines: ${escapeHtml(err.message)}</div>`;
    }
}

function checkHeadline(title) {
    const input = document.getElementById("news-input");
    if (input) {
        input.value = title;
        input.dispatchEvent(new Event("input"));
        switchTab("text-tab");
        analyzeText("newspaper");
    }
}

// ─── Intelligence Analytics & History ───
async function loadAnalytics() {
    try {
        const res = await fetch("/api/analytics");
        if (!res.ok) return;
        const data = await res.json();

        document.getElementById("stat-total").textContent = data.total || 0;
        document.getElementById("stat-real").textContent = data.real || 0;
        document.getElementById("stat-fake").textContent = data.fake || 0;
        document.getElementById("stat-unverified").textContent = (data.total || 0) - ((data.real || 0) + (data.fake || 0));

        const realRate = data.total ? Math.round((data.real / data.total) * 100) : 0;
        const fakeRate = data.total ? Math.round((data.fake / data.total) * 100) : 0;

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
                            ${escapeHtml(row.prediction_label)}
                        </span>
                    </td>
                    <td class="py-3 px-4 max-w-xs truncate text-slate-200">${escapeHtml(row.text_preview)}</td>
                    <td class="py-3 px-4 font-mono">${row.confidence ? Math.round(row.confidence * 100) + "%" : "—"}</td>
                    <td class="py-3 px-4 capitalize text-slate-400">${escapeHtml((row.source || "").replaceAll("_", " "))}</td>
                    <td class="py-3 px-4 text-slate-500 text-xs">${escapeHtml(row.analyzed_at || "Recent")}</td>
                </tr>
            `;
        }).join("");
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="5" class="py-6 text-center text-rose-400">Failed to load history.</td></tr>`;
    }
}
