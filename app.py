"""
🔍 Fake News Detection System
================================
AI-powered multilingual fake news detection with:
- Text input
- Voice input (Speech-to-Text)
- Camera / Image input (OCR)
- Live Newspaper Scanner
- Explainability (highlighted suspicious words)

All tools are 100% FREE | Built with Streamlit + DistilBERT
"""
import streamlit as st
import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.text_processor import clean_text, detect_language, get_text_stats, truncate_text
from utils.image_to_text import extract_text_from_image, get_supported_ocr_languages
from utils.speech_to_text import get_supported_languages as get_speech_languages
from utils.explainability import (
    generate_word_importance,
    generate_highlighted_html,
    generate_confidence_chart,
    generate_wordcloud_image,
    get_text_analysis_summary,
)
from models.model_utils import predict, predict_batch
from scrapers.newspaper_scraper import scrape_headlines, scrape_article
from scrapers.scraper_config import (
    NEWSPAPER_SOURCES,
    get_newspapers_by_language,
    get_available_languages,
    get_newspaper_names,
)
from database.db_handler import (
    save_prediction,
    get_cached_prediction,
    get_analysis_history,
    get_statistics,
    get_db_info,
    save_scraped_headlines,
)


# ─── PAGE CONFIG ───
st.set_page_config(
    page_title="🔍 Fake News Detector",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─── CUSTOM CSS ───
st.markdown("""
<style>
    /* Main background and fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
    }
    .main-header h1 {
        color: white;
        font-size: 2.4rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: rgba(255, 255, 255, 0.85);
        font-size: 1.05rem;
        margin: 0.5rem 0 0 0;
        font-weight: 400;
    }
    
    /* Result cards */
    .result-card {
        padding: 1.8rem;
        border-radius: 16px;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .result-fake {
        background: linear-gradient(135deg, #1a0000 0%, #2d0a0a 100%);
        border-left: 5px solid #FF4B4B;
    }
    .result-real {
        background: linear-gradient(135deg, #001a00 0%, #0a2d0a 100%);
        border-left: 5px solid #00CC66;
    }
    .result-unknown {
        background: linear-gradient(135deg, #1f1a00 0%, #2b250a 100%);
        border-left: 5px solid #FFA500;
    }
    
    /* Verdict badge */
    .verdict-fake {
        background: linear-gradient(135deg, #FF4B4B, #CC0000);
        color: white;
        padding: 0.6rem 1.8rem;
        border-radius: 50px;
        font-size: 1.5rem;
        font-weight: 800;
        display: inline-block;
        letter-spacing: 2px;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.4);
    }
    .verdict-real {
        background: linear-gradient(135deg, #00CC66, #009944);
        color: white;
        padding: 0.6rem 1.8rem;
        border-radius: 50px;
        font-size: 1.5rem;
        font-weight: 800;
        display: inline-block;
        letter-spacing: 2px;
        box-shadow: 0 4px 15px rgba(0, 204, 102, 0.4);
    }
    .verdict-unknown {
        background: linear-gradient(135deg, #FFA500, #CC7A00);
        color: white;
        padding: 0.6rem 1.8rem;
        border-radius: 50px;
        font-size: 1.5rem;
        font-weight: 800;
        display: inline-block;
        letter-spacing: 2px;
        box-shadow: 0 4px 15px rgba(255, 165, 0, 0.4);
    }
    
    /* Stats cards */
    .stat-card {
        background: linear-gradient(135deg, #1A1F2E 0%, #252B3B 100%);
        padding: 1.2rem;
        border-radius: 12px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .stat-number {
        font-size: 2rem;
        font-weight: 800;
        color: #667eea;
    }
    .stat-label {
        font-size: 0.85rem;
        color: rgba(255, 255, 255, 0.6);
        margin-top: 0.2rem;
    }
    
    /* Newspaper headline cards */
    .headline-card {
        background: #1A1F2E;
        padding: 1rem 1.2rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .headline-card:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 12px 24px;
        border-radius: 10px;
        font-weight: 600;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Word highlight box */
    .highlight-box {
        background: #1A1F2E;
        padding: 1.5rem;
        border-radius: 12px;
        line-height: 2;
        font-size: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Sidebar styling */
    .sidebar-info {
        background: linear-gradient(135deg, #1A1F2E, #252B3B);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)


# ─── HEADER ───
st.markdown("""
<div class="main-header">
    <h1>🔍 Fake News Detection System</h1>
    <p>AI-Powered Multilingual Fake News Detector — Text • Voice • Camera • Newspapers</p>
</div>
""", unsafe_allow_html=True)


# ─── SIDEBAR ───
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    
    # Language selector
    selected_language = st.selectbox(
        "🌐 Preferred Language",
        ["English", "Hindi", "Telugu", "Tamil", "Malayalam", "Kannada", "Bengali", "Marathi"],
        index=0,
        help="Select your preferred language for voice input and OCR"
    )
    
    st.markdown("---")
    
    # Database stats
    st.markdown("## 📊 Statistics")
    stats = get_statistics()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{stats['total']}</div>
            <div class="stat-label">Total Analyzed</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{stats['today']}</div>
            <div class="stat-label">Today</div>
        </div>
        """, unsafe_allow_html=True)
    
    col3, col4 = st.columns(2)
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number" style="color: #FF4B4B;">{stats['fake']}</div>
            <div class="stat-label">Fake Detected</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number" style="color: #00CC66;">{stats['real']}</div>
            <div class="stat-label">Real News</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # DB Info
    db_info = get_db_info()
    st.markdown(f"""
    <div class="sidebar-info">
        <strong>💾 Database:</strong> {db_info['engine']}<br>
        <strong>📦 Size:</strong> {db_info['size']}<br>
        <strong>💰 Cost:</strong> {db_info['cost']}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # About section
    with st.expander("ℹ️ About This Project"):
        st.markdown("""
        **Fake News Detection System** uses AI to analyze news articles 
        and classify them as Real or Fake.
        
        **Features:**
        - 📝 Text analysis
        - 🎤 Voice input (Speech-to-Text)
        - 📷 Camera / Image OCR
        - 📰 Live newspaper scanning
        - 🌐 Multilingual support (104+ languages)
        - 🔬 Explainable AI (word highlighting)
        
        **Tech:** DistilBERT + Streamlit + SQLite
        
        **Cost:** ₹0 (Everything is FREE)
        """)
    
    # History
    with st.expander("📜 Recent History"):
        history = get_analysis_history(limit=10)
        if history:
            for item in history:
                label = item['prediction_label']
                emoji = "❌" if label == "FAKE" else "✅"
                conf = item.get('confidence', 0)
                preview = item.get('text_preview', '')[:80]
                st.markdown(f"{emoji} **{label}** ({conf:.0%}) — {preview}...")
        else:
            st.caption("No analysis history yet. Start analyzing news!")


# ─── HELPER FUNCTIONS ───

def display_results(text: str, prediction: dict, source: str = "text_input"):
    """Display prediction results with visualizations."""
    label = prediction.get('label', 'UNKNOWN')
    confidence = prediction.get('confidence', 0)
    model_type = prediction.get('model_type', 'unknown')
    web_check = prediction.get('web_check', {})
    
    # Detect language
    lang_info = detect_language(text)
    
    # Save to database
    save_prediction(text, prediction, source=source, language=lang_info['name'])
    
    # Verdict card
    if label == 'FAKE':
        card_class = 'result-fake'
        verdict_class = 'verdict-fake'
        verdict_emoji = '❌'
        verdict_title = 'UNVERIFIED / SUSPICIOUS'
    elif label == 'UNABLE TO VERIFY':
        card_class = 'result-unknown'
        verdict_class = 'verdict-unknown'
        verdict_emoji = '⚠️'
        verdict_title = 'UNABLE TO VERIFY'
    else:
        card_class = 'result-real'
        verdict_class = 'verdict-real'
        verdict_emoji = '✅'
        verdict_title = 'VERIFIED REAL NEWS'
    
    st.markdown(f"""
    <div class="result-card {card_class}">
        <div style="text-align: center; margin-bottom: 1rem;">
            <span class="{verdict_class}">{verdict_emoji} {verdict_title}</span>
        </div>
        <div style="text-align: center;">
            <span style="font-size: 1.2rem; color: rgba(255,255,255,0.8);">
                Verification Confidence: <strong>{confidence:.1%}</strong>
            </span>
            <span style="font-size: 0.85rem; color: rgba(255,255,255,0.5); margin-left: 1rem;">
                Method: {model_type} | Language: {lang_info['name']}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Detailed analysis in columns
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Show Web Search verification widget
        st.markdown("#### 🌐 Google / MSN Web Search Verification")
        if web_check.get('matches'):
            st.success(
                f"Found this story reported by **{web_check['trusted_sources_count']}** trusted news agencies!"
            )
            for match in web_check['matches']:
                st.markdown(f"""
                <div style="background: #1A1F2E; padding: 0.8rem; border-radius: 8px; margin: 0.4rem 0; border-left: 3px solid #00CC66;">
                    <strong><a href="{match['url']}" target="_blank" style="color: #667eea; text-decoration: none;">{match['title']}</a></strong>
                    <br><span style="font-size: 0.8rem; color: #888;">Domain: {match['domain']}</span>
                    <br><span style="font-size: 0.85rem;">{match['snippet']}</span>
                </div>
                """, unsafe_allow_html=True)
        elif label == 'UNABLE TO VERIFY':
            st.warning(prediction.get('message', "We couldn't find matching sources. This doesn't confirm the news is fake — try rephrasing or check manually."))
            st.info(
                "💡 **How is this decided?** Google News RSS returned zero matches for this query. "
                "This does NOT mean the story is fake. The search query might be too specific or obscure. "
                "Try rephrasing or check major news outlets manually."
            )
        else:
            st.warning("Could not find this story reported on trusted news sites across India.")
            st.info(
                "💡 **Why Unverified?** The system checks major newspapers covering all states in India. "
                "If it cannot find any credible news sources reporting this event, it is flagged as suspicious."
            )
    
    with col2:
        # Text stats
        st.markdown("#### 📋 Text Analysis Summary")
        summary = get_text_analysis_summary(text, prediction)
        
        st.metric("📝 Word Count", summary['word_count'])
        st.metric("⬆️ Caps Ratio", f"{summary['caps_ratio']}%")
        st.metric("❗ Exclamation Marks", summary['exclamation_count'])
        
        # Word cloud
        st.markdown("#### ☁️ Word Cloud")
        wc_buf = generate_wordcloud_image(text, label)
        if wc_buf:
            st.image(wc_buf, use_container_width=True)
    
    if prediction.get('cached'):
        st.caption("⚡ This result was loaded from cache (previously analyzed).")


# ─── MAIN TABS ───

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 Text Input",
    "🎤 Voice Input", 
    "🖼️ Image Upload",
    "📰 Newspaper Scanner",
    "📜 History & Stats",
])


# ━━━ TAB 1: TEXT INPUT ━━━
with tab1:
    st.markdown("### 📝 Paste News Article or Headline")
    st.caption("Paste any news article, headline, or social media post to check if it's fake.")
    
    text_input = st.text_area(
        "Enter news text here:",
        height=200,
        placeholder="Paste the news article or headline you want to verify...\n\nSupports: English, Hindi, Telugu, Tamil, and 100+ other languages.",
        key="text_input_area"
    )
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        check_btn = st.button("🔍 Check News", type="primary", use_container_width=True, key="check_text")
    with col2:
        clear_btn = st.button("🗑️ Clear", use_container_width=True, key="clear_text")
    
    if check_btn and text_input:
        cleaned = clean_text(text_input)
        
        if len(cleaned.split()) < 5:
            st.warning("⚠️ Please enter at least 5 words for accurate analysis.")
        else:
            with st.spinner("🧠 Analyzing with AI... Please wait..."):
                # Check cache first
                cached = get_cached_prediction(cleaned)
                if cached:
                    prediction = cached
                else:
                    prediction = predict(cleaned)
                
                display_results(cleaned, prediction, source="text_input")
    
    elif check_btn and not text_input:
        st.warning("⚠️ Please enter some text to analyze.")
    
    # Example texts for quick testing
    with st.expander("💡 Try Example Texts"):
        st.markdown("**Example 1 (Likely Fake):**")
        fake_example = (
            "SHOCKING!!! Scientists EXPOSED government CONSPIRACY to hide the TRUTH "
            "about miracle cure!!! SHARE before they DELETE this!!! You WON'T BELIEVE "
            "what they found!!! URGENT!!!"
        )
        if st.button("Try this fake example", key="try_fake"):
            st.session_state['text_input_area'] = fake_example
            st.rerun()
        st.code(fake_example, language=None)
        
        st.markdown("**Example 2 (Likely Real):**")
        real_example = (
            "According to a study published in the journal Nature, researchers at "
            "the University of Oxford have confirmed that the new climate model "
            "accurately predicts temperature changes. The peer-reviewed analysis "
            "was based on data collected over 30 years from multiple sources."
        )
        if st.button("Try this real example", key="try_real"):
            st.session_state['text_input_area'] = real_example
            st.rerun()
        st.code(real_example, language=None)


# ━━━ TAB 2: VOICE INPUT ━━━
with tab2:
    st.markdown("### 🎤 Voice Input — Speak the News")
    st.caption("Record your voice or upload an audio file. Works with English, Hindi, Telugu, Tamil, and more.")
    
    voice_language = st.selectbox(
        "Select speech language:",
        get_speech_languages(),
        index=0,
        key="voice_lang"
    )
    
    st.markdown("---")
    
    # Audio upload option (works on deployed version)
    st.markdown("#### 📁 Upload Audio File")
    st.caption("Upload a WAV audio file to convert to text and analyze.")
    
    audio_file = st.file_uploader(
        "Upload audio file (WAV format)",
        type=['wav'],
        key="audio_upload",
        help="Record audio on your phone/PC and upload the WAV file here."
    )
    
    if audio_file:
        st.audio(audio_file, format='audio/wav')
        
        if st.button("🔍 Analyze Voice Input", type="primary", key="analyze_voice"):
            with st.spinner("🎤 Converting speech to text..."):
                from utils.speech_to_text import convert_audio_to_text
                
                audio_bytes = audio_file.read()
                result = convert_audio_to_text(audio_bytes, language=voice_language)
                
                if result['success']:
                    st.success(f"✅ Transcribed text ({voice_language}):")
                    st.markdown(f"> {result['text']}")
                    
                    cleaned = clean_text(result['text'])
                    with st.spinner("🧠 Analyzing with AI..."):
                        prediction = predict(cleaned)
                        display_results(cleaned, prediction, source="voice")
                else:
                    st.error(f"❌ {result['error']}")
    
    st.markdown("---")
    
    # Manual mic fallback
    st.markdown("#### ⌨️ Or Type What You Heard")
    st.caption("If voice recording doesn't work, you can type what you heard:")
    
    voice_text = st.text_input(
        "Type the news you heard:",
        placeholder="Type what you heard in the news...",
        key="voice_text_input"
    )
    
    if st.button("🔍 Check Heard News", key="check_voice_text") and voice_text:
        cleaned = clean_text(voice_text)
        with st.spinner("🧠 Analyzing..."):
            prediction = predict(cleaned)
            display_results(cleaned, prediction, source="voice")


# ━━━ TAB 3: IMAGE UPLOAD ━━━
with tab3:
    st.markdown("### 🖼️ Image Upload — Scan News")
    st.caption("Upload a screenshot or photo of a news article. OCR extracts the text automatically.")
    
    ocr_language = st.selectbox(
        "Select text language in image:",
        get_supported_ocr_languages(),
        index=0,
        key="ocr_lang"
    )
    
    st.markdown("#### 📁 Upload Image")
    uploaded_image = st.file_uploader(
        "Upload newspaper photo or screenshot",
        type=['png', 'jpg', 'jpeg', 'bmp', 'tiff'],
        key="image_upload"
    )
    
    if uploaded_image:
        from PIL import Image
        image = Image.open(uploaded_image)
        st.image(image, caption="Uploaded Image", use_container_width=True)
        
        if st.button("🔍 Analyze Uploaded Image", type="primary", key="analyze_image"):
            with st.spinner("🖼️ Extracting text from image (OCR)..."):
                result = extract_text_from_image(image, language=ocr_language)
                
                if result['success']:
                    st.success("✅ Text extracted successfully!")
                    st.markdown("**Extracted Text:**")
                    st.text_area("OCR Result:", value=result['text'], height=150, key="ocr_image_result")
                    
                    cleaned = clean_text(result['text'])
                    with st.spinner("🧠 Analyzing with AI..."):
                        prediction = predict(cleaned)
                        display_results(cleaned, prediction, source="camera")
                else:
                    st.error(f"❌ {result['error']}")
    
    st.markdown("---")
    st.info(
        "💡 **Tip:** For best OCR results, ensure the text in the image is clear and well-lit. "
        "Works with printed newspapers, screenshots, and photos of news articles."
    )


# ━━━ TAB 4: NEWSPAPER SCANNER ━━━
with tab4:
    st.markdown("### 📰 Live Newspaper Scanner")
    st.caption("Scan headlines from Indian newspapers in Telugu, Hindi, Tamil, and English.")
    
    # Language filter
    available_langs = get_available_languages()
    selected_news_lang = st.selectbox(
        "🌐 Filter by Language:",
        ["All Languages"] + available_langs,
        index=0,
        key="news_lang_filter"
    )
    
    # Newspaper selector
    if selected_news_lang == "All Languages":
        papers = get_newspaper_names()
    else:
        filtered = get_newspapers_by_language(selected_news_lang)
        papers = {k: v['name'] for k, v in filtered.items()}
    
    selected_paper_key = st.selectbox(
        "📰 Select Newspaper:",
        list(papers.keys()),
        format_func=lambda x: f"{papers[x]} ({NEWSPAPER_SOURCES[x]['language']})",
        key="newspaper_select"
    )
    
    col1, col2 = st.columns([1, 3])
    with col1:
        scan_btn = st.button("🔍 Scan Headlines", type="primary", use_container_width=True, key="scan_news")
    
    if scan_btn:
        with st.spinner(f"📡 Fetching headlines from {papers[selected_paper_key]}..."):
            result = scrape_headlines(selected_paper_key, max_headlines=15)
            
            if result['success'] and result['headlines']:
                st.success(f"✅ Found {result['count']} headlines from **{result['newspaper']}** ({result['language']})")
                
                headlines = result['headlines']
                
                # Analyze all headlines
                with st.spinner("🧠 Analyzing headlines with AI..."):
                    predictions = predict_batch([h['title'] for h in headlines])
                    
                    # Save to database
                    save_scraped_headlines(
                        result['newspaper'],
                        result['language'],
                        headlines,
                        predictions
                    )
                
                # Display headlines with verdicts
                st.markdown("---")
                
                for i, (headline, pred) in enumerate(zip(headlines, predictions)):
                    label = pred.get('label', 'UNKNOWN')
                    confidence = pred.get('confidence', 0)
                    
                    if label == 'FAKE':
                        badge = "🔴"
                        badge_color = "#FF4B4B"
                    else:
                        badge = "🟢"
                        badge_color = "#00CC66"
                    
                    st.markdown(f"""
                    <div class="headline-card">
                        <span style="color: {badge_color}; font-weight: 700;">
                            {badge} {label} ({confidence:.0%})
                        </span>
                        <br>
                        <span style="font-size: 1rem;">{headline['title']}</span>
                        <br>
                        <a href="{headline.get('url', '#')}" target="_blank" 
                           style="font-size: 0.8rem; color: #667eea;">
                            🔗 Read Full Article
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Expandable detailed analysis
                    with st.expander(f"📊 Detailed Analysis — Headline {i+1}"):
                        display_results(headline['title'], pred, source="newspaper")
            
            elif result['success'] and not result['headlines']:
                st.warning(f"⚠️ No headlines found from {papers[selected_paper_key]}. The website structure may have changed.")
            else:
                st.error(f"❌ {result.get('error', 'Failed to fetch headlines.')}")
    
    st.markdown("---")
    
    # Manual URL check
    st.markdown("#### 🔗 Check a News URL")
    news_url = st.text_input(
        "Paste a news article URL:",
        placeholder="https://www.thehindu.com/news/...",
        key="news_url_input"
    )
    
    if st.button("🔍 Check URL", key="check_url") and news_url:
        with st.spinner("📡 Fetching article..."):
            article = scrape_article(news_url)
            
            if article['success']:
                st.success(f"✅ Article fetched: **{article.get('title', 'Untitled')}**")
                
                with st.expander("📄 View Full Article Text"):
                    st.text_area("Article:", value=article['text'], height=200, key="article_text")
                
                cleaned = clean_text(article['text'])
                with st.spinner("🧠 Analyzing..."):
                    prediction = predict(cleaned)
                    display_results(cleaned, prediction, source="newspaper")
            else:
                st.error(f"❌ {article.get('error', 'Failed to fetch article.')}")


# ━━━ TAB 5: HISTORY & STATS ━━━
with tab5:
    st.markdown("### 📜 Analysis History & Statistics")
    
    # Stats overview
    stats = get_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{stats['total']}</div>
            <div class="stat-label">Total Analyses</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number" style="color: #FF4B4B;">{stats['fake']}</div>
            <div class="stat-label">Fake Detected</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number" style="color: #00CC66;">{stats['real']}</div>
            <div class="stat-label">Real News</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        fake_rate = (stats['fake'] / max(stats['total'], 1)) * 100
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number" style="color: #FFD700;">{fake_rate:.1f}%</div>
            <div class="stat-label">Fake Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Charts
    if stats['total'] > 0:
        import plotly.graph_objects as go
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Pie chart
            fig = go.Figure(data=[go.Pie(
                labels=['Fake', 'Real'],
                values=[stats['fake'], stats['real']],
                hole=0.5,
                marker_colors=['#FF4B4B', '#00CC66'],
                textinfo='label+percent',
                textfont_size=14,
            )])
            fig.update_layout(
                title="Fake vs Real Distribution",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                height=350,
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Source breakdown
            by_source = stats.get('by_source', {})
            if by_source:
                source_labels = {
                    'text_input': '📝 Text',
                    'voice': '🎤 Voice',
                    'camera': '📷 Camera',
                    'newspaper': '📰 Newspaper',
                }
                fig = go.Figure(data=[go.Bar(
                    x=[source_labels.get(k, k) for k in by_source.keys()],
                    y=list(by_source.values()),
                    marker_color='#667eea',
                    text=list(by_source.values()),
                    textposition='auto',
                )])
                fig.update_layout(
                    title="Analysis by Input Source",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='white',
                    height=350,
                    xaxis_title="Source",
                    yaxis_title="Count",
                )
                st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # History table
    st.markdown("#### 📋 Recent Analyses")
    history = get_analysis_history(limit=30)
    
    if history:
        import pandas as pd
        
        df = pd.DataFrame(history)
        df['Verdict'] = df['prediction_label'].apply(
            lambda x: f"❌ {x}" if x == 'FAKE' else f"✅ {x}"
        )
        df['Confidence'] = df['confidence'].apply(lambda x: f"{x:.1%}")
        df['Preview'] = df['text_preview'].apply(lambda x: x[:100] + '...' if len(x) > 100 else x)
        
        display_df = df[['Verdict', 'Confidence', 'source', 'language', 'Preview', 'analyzed_at']]
        display_df.columns = ['Verdict', 'Confidence', 'Source', 'Language', 'Text Preview', 'Date']
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("📭 No analysis history yet. Start analyzing news to see results here!")
    
    st.markdown("---")
    
    # Clear history button
    if st.button("🗑️ Clear All History", type="secondary", key="clear_history"):
        from database.db_handler import clear_history
        if clear_history():
            st.success("✅ History cleared successfully!")
            st.rerun()


# ─── FOOTER ───
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: rgba(255,255,255,0.4); font-size: 0.8rem; padding: 1rem;">
    🔍 Fake News Detection System | Built with ❤️ using Streamlit + DistilBERT | 
    💰 100% FREE & Open Source | 🌐 Supports 104+ Languages
</div>
""", unsafe_allow_html=True)
