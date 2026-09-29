# 📖 All-India Fake News Detection & Verification System
## 📑 Complete System Documentation & Technical Reference Manual

---

## 1. 📌 Project Overview & Abstract

In the modern digital information ecosystem, social media platforms and messaging applications (such as WhatsApp, Telegram, and Facebook) are heavily exploited to distribute unverified claims, doctored screenshots, and fabricated news. Traditional Machine Learning (ML) classification systems rely on static datasets (such as LIAR or ISOT), which quickly become obsolete and suffer from topic bias (e.g., falsely classifying genuine sports, entertainment, or government announcements as fake due to sensational phrasing).

The **All-India Fake News Detection & Verification System** is a real-time, multi-modal verification platform that solves this limitation by implementing **Live Web Search Cross-Referencing**. Instead of relying solely on static model weights, the system queries live Google News RSS feeds across **60+ trusted national, state-level, and regional Indian news publishers** and official fact-checking agencies in real time.

### Key Capabilities
* **Multi-Modal Input:** Accepts News Text, WhatsApp forwards, Voice recordings (.wav), and Newspaper screenshots (OCR).
* **Indian Regional Language Support:** Native language detection and search routing for Telugu, Hindi, Tamil, Kannada, Malayalam, Bengali, Marathi, Gujarati, Punjabi, Urdu, and English.
* **Smart Stemmed Overlap Matching:** Robust keyword extraction and English suffix stripping (`_stem_word`) to overcome headline wording differences.
* **3-State Verdict Architecture:** Produces unambiguous results: **`VERIFIED REAL`**, **`OFFICIALLY DEBUNKED / FAKE`**, or **`UNABLE TO VERIFY`**.
* **Zero Cost Infrastructure:** Built on 100% free community APIs and open-source libraries (₹0 API key costs).

---

## 2. 🗂️ Project Directory Structure

```
fake-news-detector/
├── .streamlit/
│   └── config.toml           # Dark theme UI styling & server configurations
├── data/
│   ├── fake_news_detector.db # SQLite database storing scan logs, analytics & cache
│   ├── Fake.csv              # Reference Kaggle dataset (Fake news)
│   └── True.csv              # Reference Kaggle dataset (Real news)
├── database/
│   ├── __init__.py
│   └── db_handler.py         # SQLite CRUD operations, analytics engine & selective cache
├── models/
│   ├── __init__.py
│   ├── model_utils.py        # Central decision tree & prediction routing interface
│   ├── test_prediction.py    # Automated test suite covering 5 verification scenarios
│   ├── debug_verifier.py     # Search diagnostic and domain tracing utility
│   ├── fallback_model.pkl    # Pre-trained fallback classifier
│   └── tfidf_vectorizer.pkl  # Pre-trained TF-IDF vectorizer
├── scrapers/
│   ├── __init__.py
│   ├── scraper_config.py     # XPath/CSS selectors & metadata for Indian regional papers
│   └── newspaper_scraper.py  # Live scraper for front-page headlines
├── utils/
│   ├── __init__.py
│   ├── text_processor.py     # WhatsApp forward cleaner, language detection & diacritics
│   ├── search_verifier.py    # Google News RSS search client, stemmer & overlap matcher
│   ├── speech_to_text.py     # Speech recognition using Google Web Speech API
│   ├── image_to_text.py      # Tesseract OCR engine & image preprocessor
│   └── explainability.py     # Text highlighting, keyword breakdown & metrics
├── app.py                    # Main Streamlit web application frontend
├── requirements.txt          # Python dependencies
└── PROJECT_DOCUMENTATION.md  # Complete Technical Documentation
```

---

## 3. 🔄 System Workflow & Architecture

```
[User Input] (Text / Voice / Image / Newspaper Scraper)
      │
      ▼
[Text Cleaning] (Strip WhatsApp timestamps, forward headers, sender names, emojis)
      │
      ▼
[Language Detection] (langdetect: 'te', 'hi', 'ta', 'en', etc.)
      │
      ▼
[Query Extraction] (Extract 6 high-information words; preserve Unicode marks)
      │
      ▼
[Cache Lookup] (SQLite database: Return immediately if previously verified as REAL)
      │ (Cache Miss)
      ▼
[Rate-Limit Protection] (1.5s delay + 3-retry exponential backoff: 1s, 3s, 5s)
      │
      ▼
[Google News RSS Query] (Language edition: hl=te&gl=IN&ceid=IN:te for Telugu, etc.)
      │
      ▼
[XML Parsing & Domain Extraction] (xml.etree.ElementTree)
      │
      ▼
[Keyword Stemming & Overlap Check] (Suffix stripping: 'launch' == 'launches')
      │
      ▼
[3-State Verdict Evaluation]
      ├─► Matched Fact-Checker (PIB/AltNews)? ──► Verdict: FAKE
      ├─► Matched Trusted News (Eenadu/BBC)? ────► Verdict: REAL
      └─► No Match / Low Overlap (<35%)? ────────► Verdict: UNABLE TO VERIFY
      │
      ▼
[Database Persistence] (Save prediction, timestamp, confidence & language)
      │
      ▼
[Streamlit UI Output] (Color-coded verdict card, trusted publisher links, word cloud)
```

---

## 4. 📦 Module Specifications & Code Details

### 4.1. `app.py` — Web User Interface
* **Framework:** Streamlit (Python).
* **Tabs:**
  1. **📝 Text Input:** Headline and long-text text area with instant pre-loaded sample buttons.
  2. **🎤 Voice Input:** Audio file upload (.wav) and in-browser microphone recording for 9 Indian languages.
  3. **🖼️ Image Upload:** Static OCR image upload (camera capture removed to prevent permission prompts).
  4. **📰 Newspaper Scanner:** Scrapes real-time headlines from Indian news portals.
  5. **📜 History & Stats:** Real-time analytics charts and SQLite history tables.

---

### 4.2. `utils/search_verifier.py` — Search Verifier Engine
* **Key Functions:**
  * `_clean_punctuation(text: str) -> str`: Removes punctuation while preserving Unicode diacritics and combining marks (like Telugu `ీ`, `్` or Hindi `ा`).
  * `_stem_word(word: str) -> str`: Recursively strips English suffixes (`tional`, `tion`, `ment`, `ing`, `ed`, `es`, `ly`, `al`, `s`, `y`) to equate word forms (e.g. `launches` and `launched` $\to$ `launch`).
  * `_extract_search_query(text: str) -> str`: Filters out stopwords and extracts the first 6 key words.
  * `verify_claim_on_web(text: str, lang_code: str = 'en') -> dict`: Queries Google News RSS and calculates keyword overlap.
* **Overlap Threshold:** `OVERLAP_THRESHOLD = 0.35` (35%).

---

### 4.3. `models/model_utils.py` — Decision Logic & Routing
* **Key Functions:**
  * `predict(text: str) -> dict`: Central prediction coordinator.
* **3-State Decision Logic:**
  ```python
  if web_check.get('search_failed') or web_check.get('total_results_count', 0) == 0:
      return {'label': 'UNABLE TO VERIFY', 'confidence': 0.0}

  if web_check.get('verified'):
      if is_fact_checker_domain:
          return {'label': 'FAKE', 'confidence': 0.85}
      return {'label': 'REAL', 'confidence': web_check['confidence']}
  
  return {'label': 'UNABLE TO VERIFY', 'confidence': 0.0}
  ```

---

### 4.4. `utils/text_processor.py` — Text Processing & Cleaning
* **Key Functions:**
  * `clean_forwarded_text(text: str) -> str`: Strips WhatsApp metadata:
    * Timestamps: `[10/08, 12:45 pm]`, `10/08/2026, 12:45 - `
    * Headers: `Forwarded`, `Forwarded many times`
    * Sender prefixes: `John: `, `+91 98765 43210: `
    * Emojis and trailing symbols.
  * `detect_language(text: str) -> dict`: Returns language ISO code and confidence score.
  * `get_text_stats(text: str) -> dict`: Calculates word count, character count, caps ratio, and exclamation marks.

---

### 4.5. `database/db_handler.py` — SQLite Database & Caching
* **Database File:** `data/fake_news_detector.db`
* **Schema:**
  ```sql
  CREATE TABLE IF NOT EXISTS predictions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      text_hash TEXT NOT NULL,
      text_preview TEXT NOT NULL,
      prediction_label TEXT NOT NULL,
      confidence REAL NOT NULL,
      source TEXT NOT NULL,
      language TEXT NOT NULL,
      model_type TEXT NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
  ```
* **Selective Caching:** `get_cached_prediction(text)` only returns cached entries if `prediction_label == 'REAL'`. Failed queries and unverified claims are never cached.

---

### 4.6. `utils/speech_to_text.py` — Voice Recognition
* **Engine:** Google Web Speech Recognition (`SpeechRecognition`).
* **Languages Supported:**
  * English (`en-IN`), Hindi (`hi-IN`), Telugu (`te-IN`), Tamil (`ta-IN`), Malayalam (`ml-IN`), Kannada (`kn-IN`), Bengali (`bn-IN`), Marathi (`mr-IN`), Gujarati (`gu-IN`).

---

### 4.7. `utils/image_to_text.py` — OCR Engine
* **Engine:** Tesseract OCR via `pytesseract`.
* **Preprocessing:** PIL-based grayscale conversion, contrast enhancement (`ImageEnhance.Contrast(image).enhance(1.8)`), and sharpening filter.

---

### 4.8. `scrapers/newspaper_scraper.py` — Newspaper Scraper
* **Supported Newspapers:**
  * **Telugu:** Eenadu (`eenadu.net`), Sakshi (`sakshi.com`)
  * **Hindi:** Dainik Jagran (`jagran.com`), Amar Ujala (`amarujala.com`)
  * **Tamil:** Dinamalar (`dinamalar.com`), Daily Thanthi (`dailythanthi.com`)
  * **English:** The Hindu (`thehindu.com`), NDTV (`ndtv.com`), Times of India (`timesofindia.indiatimes.com`), Indian Express (`indianexpress.com`)

---

## 5. 🛡️ Whitelist of 60+ Trusted Domains

```python
TRUSTED_DOMAINS = {
    # Fact Checkers & Government
    'pib.gov.in', 'factcheck.pib.gov.in', 'gov.in', 'nic.in', 
    'altnews.in', 'boomlive.in', 'factcrescendo.com', 'vishvasnews.com',
    
    # National & International Media
    'reuters.com', 'apnews.com', 'bbc.com', 'bbc.co.uk', 'nytimes.com', 
    'washingtonpost.com', 'bloomberg.com', 'cnn.com', 'theguardian.com',
    'ndtv.com', 'thehindu.com', 'timesofindia.indiatimes.com', 
    'indianexpress.com', 'hindustantimes.com', 'news18.com', 'indiatoday.in', 
    'livemint.com', 'moneycontrol.com', 'firstpost.com', 'oneindia.com',
    
    # Regional Publications
    # Telugu:
    'eenadu.net', 'sakshi.com', 'andhrabhoomi.net', 'andhrajyothy.com',
    'namasthetelangaana.com', 'telugu.samayam.com', 'telugu.oneindia.com',
    # Tamil:
    'dailythanthi.com', 'dinamalar.com', 'dinakaran.com', 'vikatan.com', 
    'tamil.thehindu.com', 'tamil.samayam.com', 'puthiyathalaimurai.com',
    # Kannada:
    'prajavani.net', 'kannadaprabha.com', 'vijaykarnataka.com', 'udayavani.com',
    # Malayalam:
    'mathrubhumi.com', 'manoramaonline.com', 'deshabhimani.com', 'asianetnews.com',
    # Marathi:
    'lokmat.com', 'esakal.com', 'maharashtratimes.com', 'loksatta.com', 'marathi.abplive.com',
    # Gujarati:
    'divyabhaskar.co.in', 'sandesh.com', 'gujaratsamachar.com', 'gujarati.abplive.com',
    # Bengali & Northeast:
    'anandabazar.com', 'bartamanpatrika.com', 'sangbadpratidin.in', 'assamtribune.com',
    # Hindi (North India):
    'jagran.com', 'amarujala.com', 'bhaskar.com', 'jansatta.com', 'livehindustan.com'
}
```

---

## 6. 🧮 Mathematical Matching Algorithm

$$\text{Query Stems} = \{\text{stem}(w) \mid w \in \text{Query Words} \setminus \text{Stopwords}\}$$
$$\text{Title Stems} = \{\text{stem}(w) \mid w \in \text{Title Words} \setminus \text{Stopwords}\}$$

$$\text{Overlap Ratio} = \frac{|\text{Query Stems} \cap \text{Title Stems}|}{\max(|\text{Query Stems}|, 1)}$$

* **Match Criterion:**
  $$\text{Verified} = (\text{Domain} \in \text{TRUSTED\_DOMAINS}) \land (\text{Overlap Ratio} \ge 0.35)$$

---

## 7. 🧪 Test Suite & Validation Evidence

Running `models/test_prediction.py` executes 5 automated end-to-end tests:

| Test # | Test Scenario | Input Sample | Expected Verdict | Actual Verdict | Status |
| :---: | :--- | :--- | :---: | :---: | :---: |
| **1** | Viral Conspiracy Rumor | *"SHOCKING CONSPIRACY EXPOSED!!! The government is secretly using alien technology..."* | `UNABLE TO VERIFY` | `UNABLE TO VERIFY` | 🟢 PASS |
| **2** | Real News + WhatsApp Junk | *"[10/08, 3:22 pm] John: Forwarded many times. According to reports from Reuters, the Federal Reserve..."* | `REAL` | `REAL` (50% Overlap) | 🟢 PASS |
| **3** | Obscure Event | *"An obscure local event happened at some random location where no news agency has written anything."* | `UNABLE TO VERIFY` | `UNABLE TO VERIFY` | 🟢 PASS |
| **4** | Caching Consistency | *"ISRO successfully launches second development flight of SSLV"* (Run 1 vs Run 2) | `REAL` (Both) | `REAL` (Cached: True) | 🟢 PASS |
| **5** | Regional Telugu Headline | *"చంద్రబాబు నాయుడు ప్రమాణ స్వీకారం"* | `REAL` | `REAL` (75% Overlap) | 🟢 PASS |

---

## 8. 💻 Installation, Setup & Execution Manual

### Prerequisites
* Python 3.10 to 3.14
* Tesseract OCR Engine (optional for image scanning, defaults to `C:\Program Files\Tesseract-OCR\tesseract.exe`)

### Step 1: Create Virtual Environment
```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Step 2: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Run Validation Tests
```powershell
.venv\Scripts\python.exe models/test_prediction.py
```

### Step 4: Launch Web Dashboard
```powershell
.venv\Scripts\streamlit.exe run app.py
```

* **Local Browser Access:** **[http://localhost:8501](http://localhost:8501)**
