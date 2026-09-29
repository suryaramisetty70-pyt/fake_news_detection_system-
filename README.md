# 🔍 All-India Fake News Detection & Real-Time Verification System

AI-powered real-time multi-modal fake news detection and fact-checking web application built with **Streamlit** and Python. Cross-references breaking news and social media rumors against **60+ trusted national and regional Indian news publishers** and official fact-checking agencies in real time.

---

## 🌟 Key Features

- **🌐 Real-Time Web Cross-Referencing:** Verifies claims against live Google News RSS feeds instead of relying solely on static, biased ML models.
- **🧹 WhatsApp Junk & Forward Cleaner:** Automatically strips forwarded headers, timestamps ([10/08, 12:45 pm]), sender prefixes, and emojis from viral messages.
- **🗣️ Multilingual Voice Input:** Transcribes audio files (.wav) and live voice recordings in 9 Indian languages using Google Speech Recognition.
- **🖼️ Image OCR Scanner:** Extracts and verifies text from newspaper clippings and screenshots using Tesseract OCR.
- **📰 Live Newspaper Scanner:** Scrapes breaking front-page headlines in one click from major Indian outlets (*Eenadu, Sakshi, Dainik Jagran, Amar Ujala, Dinamalar, The Hindu, NDTV, Times of India*).
- **🌾 Stemmed Keyword Matching:** Robust keyword overlap checking with English suffix stripping (_stem_word) to equate word tenses (e.g. *launches* vs. *launched*).
- **🌳 3-State Verdict System:** Unambiguous results (**VERIFIED REAL**, **OFFICIALLY DEBUNKED / FAKE**, or **UNABLE TO VERIFY**) preventing false alarms on unreferenced stories.
- **⚡ SQLite Selective Caching:** High-speed local caching that safely reuses confirmed real news checks while bypassing failed searches.
- **💰 100% Free & Open-Source:** Operates at ₹0 API cost with zero required paid API keys.

---

## 🛠️ Tech Stack

| Layer | Technologies Used |
| :--- | :--- |
| **Frontend UI** | Streamlit, Streamlit Option Menu, Audio Recorder |
| **Search & Verification** | Google News RSS Feed, Requests, ElementTree XML |
| **NLP & Language** | Langdetect, Lightweight Suffix Stemming, Scikit-Learn |
| **Voice & Audio** | SpeechRecognition (Google Web Speech API) |
| **Vision / OCR** | Pytesseract (Tesseract OCR), Pillow (PIL) |
| **Scraping** | BeautifulSoup4, Newspaper3k, lxml |
| **Database & Cache** | SQLite3 (Built-in WAL mode) |
| **Visualizations** | Plotly, Matplotlib, WordCloud |

---

## 📁 Project Structure

`
fake-news-detector/
├── .streamlit/
│   └── config.toml           # Dark theme UI styling & server configuration
├── data/
│   ├── fake_news_detector.db # SQLite database for scan logs, history & cache
│   ├── Fake.csv / True.csv   # Reference dataset files
├── database/
│   └── db_handler.py         # SQLite CRUD operations, analytics & selective caching
├── models/
│   ├── model_utils.py        # Central decision tree & prediction routing
│   ├── test_prediction.py    # Automated test suite (5 verification scenarios)
│   └── debug_verifier.py     # Search diagnostic tracing script
├── scrapers/
│   ├── scraper_config.py     # XPath/CSS selectors for Indian regional papers
│   └── newspaper_scraper.py  # Live scraper for front-page headlines
├── utils/
│   ├── text_processor.py     # WhatsApp cleaner, language detection & diacritics
│   ├── search_verifier.py    # Google News RSS client, stemmer & overlap matcher
│   ├── speech_to_text.py     # Voice note transcriber (9 Indian languages)
│   ├── image_to_text.py      # Tesseract OCR image preprocessor
│   └── explainability.py     # Text highlighting, keyword metrics & word clouds
├── app.py                    # Main Streamlit web application
├── requirements.txt          # Python dependencies
└── PROJECT_DOCUMENTATION.md  # Detailed Technical Manual
`

---

## 🚀 Quick Start & Installation

### 1. Clone the Repository
`ash
git clone https://github.com/suryaramisetty70-pyt/fake_news_detection_system-.git
cd fake_news_detection_system-
`

### 2. Create and Activate Virtual Environment
`ash
python -m venv .venv
# On Windows:
.venv\\Scripts\\activate
# On Linux / macOS:
source .venv/bin/activate
`

### 3. Install Dependencies
`ash
pip install -r requirements.txt
`

### 4. Run the Validation Test Suite
`ash
python models/test_prediction.py
`

### 5. Launch the Web Application
`ash
streamlit run app.py
`

Open your browser and navigate to **http://localhost:8501** 🎉

---

## 📄 License

This project is open-source under the MIT License.
