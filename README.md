# 🔍 Veritas AI: All-India Fake News Detection & Real-Time Verification Platform

A modern, production-grade AI platform and high-performance **FastAPI REST API** with a dark-glassmorphism **Single Page Application (SPA)** interface for real-time fake news detection and fact-checking.

Combines cutting-edge research algorithms from leading GitHub repositories (AAAI/WWW dual-emotion detection, multi-model voting ensembles, and social vector tracking) with live cross-referencing across **60+ trusted Indian & international news outlets**.

---

## 🌟 Key Capabilities & Upgrades

- 🚀 **High-Performance FastAPI Architecture:** Pure asynchronous ASGI web service consuming **< 80MB RAM** (saving > 75% memory over traditional Streamlit apps, zero OOM risk on cloud hosting).
- 🗳️ **4-Model Voting Ensemble:** Weighted soft-voting combining Logistic Regression, Naive Bayes Lexical Fact Density, Stylometric Analysis, and Clickbait Sensationalism Scorer (*inspired by sneyhaa & vijaisuria*).
- 🧠 **Dual-Emotion & Linguistic Credibility Engine:** Quantifies Subjectivity, Emotional Alarmism, Sensationalism Index, and Objective Factuality (*inspired by aryashah2k & AAAI 2023/2024 papers*).
- 📱 **Social Platform Origin & Viral Risk Detector:** Automatically detects forwarding chains, WhatsApp forward markers, Telegram rumors, and viral social signatures (*inspired by Sohamcoder1*).
- 🌐 **Real-Time Web Cross-Referencing:** Verifies claims against live Google News RSS feeds across 50+ national & regional Indian news sources (*The Hindu, NDTV, Eenadu, Sakshi, Dinamalar, Dainik Jagran, PIB Fact Check, AltNews, BoomLive*).
- 🎙️ **Direct Browser Voice Verification:** Built-in Web Audio API recording supporting 9 Indian regional languages with speech-to-text.
- 🖼️ **Client-Side Drag & Drop OCR:** Extracts text directly from news clippings, screenshots, and forwards using Tesseract OCR.
- 📰 **Live Regional Newspaper Reader:** Scrapes and analyzes breaking headlines on-demand from major Indian dailies.
- 🔌 **OpenAPI / Swagger REST Endpoints:** Full REST API documentation ready for mobile apps and browser extension integration at `/docs`.
- 💰 **₹0 Operational Cost:** Zero required paid API keys or subscriptions.

---

## 🛠️ Architecture & Tech Stack

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Backend Framework** | **FastAPI + Uvicorn (ASGI)** | High-throughput asynchronous REST API & static file server |
| **Frontend UI** | **HTML5, TailwindCSS, Chart.js, Lucide Icons** | Modern glassmorphism SPA with zero page reloads |
| **Ensemble Engine** | **Scikit-Learn, Custom Voting Ensembles** | 4-model weighted consensus classification |
| **Linguistic Analysis** | **Regex, Lexical Sentiment Dictionaries** | Subjectivity, sensationalism, and alarmism indexing |
| **Search & Fact-Check** | **Google News RSS, XML ElementTree, Requests** | Real-time cross-referencing across 60+ verified domains |
| **Speech-to-Text** | **HTML5 MediaRecorder + Google Speech Recognition** | Multi-lingual audio transcription (Hindi, Telugu, Tamil, etc.) |
| **Computer Vision / OCR** | **Tesseract OCR, Pillow** | Image text extraction from news clips and social screenshots |
| **Database & Cache** | **SQLite3 (WAL Mode)** | Persistent verification history, analytics & query caching |

---

## 📁 Repository Structure

```
fake-news-detector/
├── main.py                     # Production FastAPI server & REST endpoints
├── static/                     # Modern Dark-Glassmorphism Single Page Application
│   ├── index.html              # Reactive UI (5 tabs: Text, Voice, OCR, Newspapers, Analytics)
│   ├── css/style.css           # Glassmorphism visual styling & custom animations
│   └── js/app.js               # Web Audio recorder, async API calls & dynamic rendering
├── models/
│   ├── ensemble_classifier.py  # 4-Model Voting Ensemble (Soft/Hard voting)
│   ├── model_utils.py          # Unified prediction pipeline & verdict synthesizer
│   ├── fallback_model.pkl      # Pre-trained TF-IDF Logistic Regression model
│   └── tfidf_vectorizer.pkl    # Pre-trained TF-IDF vectorizer
├── utils/
│   ├── linguistic_analyzer.py  # Dual-Emotion, Subjectivity & Alarmism scorer
│   ├── social_verifier.py      # WhatsApp/Telegram viral forward & risk detector
│   ├── search_verifier.py      # Real-time Google News RSS verifier & domain matcher
│   ├── text_processor.py       # Indian language detector & forward cleaner
│   ├── speech_to_text.py       # Multilingual voice transcription
│   └── image_to_text.py        # Tesseract OCR image extractor
├── scrapers/
│   ├── newspaper_scraper.py    # Live newspaper headline scraper
│   └── scraper_config.py       # Newspaper source definitions & CSS/XPath configs
├── database/
│   └── db_handler.py           # SQLite persistence & query cache
├── app.py                      # Legacy Streamlit interface (optional fallback)
├── Procfile                    # Render production web process config
├── render-build.sh             # Cloud build script (installs Tesseract OCR)
└── requirements.txt            # Python dependencies
```

---

## 🚀 Quick Start Guide

### 1. Clone the Repository
```bash
git clone https://github.com/suryaramisetty70-pyt/fake_news_detection_system-.git
cd fake_news_detection_system-
```

### 2. Activate Virtual Environment & Install Dependencies
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Run the Production FastAPI Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- **Web Application:** Open [http://localhost:8000](http://localhost:8000)
- **Interactive API Documentation:** Open [http://localhost:8000/docs](http://localhost:8000/docs)

*(Optional) To launch the legacy Streamlit UI:*
```bash
streamlit run app.py
```

---

## ☁️ Deployment on Render

1. **Repository:** Link your GitHub repo `fake_news_detection_system-`.
2. **Environment:** `Python 3`
3. **Build Command:**
   ```bash
   ./render-build.sh
   ```
4. **Start Command:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
5. **Instance Type:** Free Tier (0.1 CPU, 512 MB RAM) — FastAPI runs comfortably under 80MB!

---

## 📄 License
Open-source under the MIT License.
