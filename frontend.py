import streamlit as st
import os
import tempfile
from backend import job_agent
from database import search_history, get_history, clear_history, delete_history

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Career Coach",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state tracking for active report view
if "active_report" not in st.session_state:
    st.session_state.active_report = None

# ── Global CSS ─────────────────────────────────────────────────────────────────
# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, .stApp {
    background: #F7F5F0;
    font-family: 'DM Sans', sans-serif;
    color: #1C1C1E;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #1C1C1E !important;
    border-right: none;
}
/* Style text elements specifically, avoiding structural overrides on buttons */
[data-testid="stSidebar"] .stMarkdown p, 
[data-testid="stSidebar"] span, 
[data-testid="stSidebar"] label {
    color: #F7F5F0 !important;
}
[data-testid="stSidebar"] .stMarkdown h2 {
    font-family: 'DM Serif Display', serif !important;
    font-size: 1.4rem !important;
    letter-spacing: -0.02em;
    color: #E8C547 !important;
}
[data-testid="stSidebar"] .stMarkdown p {
    font-size: 0.82rem;
    opacity: 0.65;
    line-height: 1.6;
}
[data-testid="stSidebar"] hr {
    border-color: #333 !important;
    margin: 1rem 0;
}

/* Sidebar history cards block styling */
div.history-block {
    margin-bottom: 14px;
    background: #2A2A2C;
    border-radius: 10px;
    border-left: 3px solid #E8C547;
    padding: 8px;
}

/* Clickable Main Session Card Button */
div.history-block .stButton > button[kind="secondary"]:not([key*="del_"]) {
    text-align: left !important;
    background: transparent !important;
    border: none !important;
    color: #F7F5F0 !important;
    padding: 6px 10px !important;
    width: 100% !important;
    white-space: normal !important;
    display: block !important;
}
div.history-block .stButton > button:hover {
    background: #333335 !important;
}

/* Explicit Fix for 'Delete entry' and 'Clear All History' Buttons */
[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
    background: #222224 !important;
    border: 1px solid #444 !important;
    color: #E8C547 !important;  /* High contrast gold text */
    border-radius: 8px !important;
    font-size: 0.8rem !important;
    padding: 6px 14px !important;
    width: 100% !important;
    margin-top: 5px;
    transition: all 0.2s ease;
}

[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
    border-color: #E8C547 !important;
    background: #E8C547 !important;
    color: #1C1C1E !important; /* Invert colors beautifully on hover */
}

.hc-name {
    font-size: 0.9rem;
    font-weight: 600;
    color: #F7F5F0;
}
.hc-meta {
    font-size: 0.72rem;
    color: #888;
    margin-top: 4px;
    line-height: 1.4;
}
.hist-empty {
    font-size: 0.8rem;
    color: #888 !important;
    text-align: center;
    padding: 20px 0;
    font-style: italic;
}

/* ── Main header ── */
.main-header {
    background: linear-gradient(135deg, #1C1C1E 0%, #2D2D30 100%);
    border-radius: 20px;
    padding: 48px 52px;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
}
.main-header h1 {
    font-family: 'DM Serif Display', serif !important;
    font-size: 2.8rem !important;
    color: #F7F5F0 !important;
    letter-spacing: -0.03em;
    line-height: 1.15;
    margin-bottom: 10px;
}
.main-header h1 span { color: #E8C547; }
.main-header p {
    color: rgba(247,245,240,0.65) !important;
    font-size: 1rem;
    font-weight: 300;
    max-width: 480px;
    line-height: 1.65;
}

/* ── Upload zone ── */
.upload-section {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 32px 36px;
    border: 1px solid #E5E2DA;
    box-shadow: 0 2px 12px rgba(0,0,0,0.04);
    margin-bottom: 24px;
}
.upload-section h3 {
    font-family: 'DM Serif Display', serif !important;
    font-size: 1.25rem !important;
    color: #1C1C1E !important;
    margin-bottom: 6px;
}
.upload-section p.sub {
    font-size: 0.85rem;
    color: #888;
    margin-bottom: 20px;
}

/* ── Primary button ── */
.stButton > button[kind="primary"] {
    background: #E8C547 !important;
    color: #1C1C1E !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 14px 36px !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    width: 100%;
    margin-top: 16px;
    box-shadow: 0 4px 14px rgba(232,197,71,0.30) !important;
}

/* ── Result card ── */
.result-wrapper {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 36px 40px;
    border: 1px solid #E5E2DA;
    box-shadow: 0 2px 16px rgba(0,0,0,0.05);
    margin-top: 24px;
}
.result-wrapper .result-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.5rem;
    color: #1C1C1E;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.result-wrapper .result-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #E5E2DA;
}

.badge-success {
    display: inline-block;
    background: #D4EDDA;
    color: #1A5C30;
    font-size: 0.78rem;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 20px;
    margin-bottom: 20px;
}

.stats-row {
    display: flex;
    gap: 16px;
    margin-bottom: 28px;
}
.stat-pill {
    background: #F7F5F0;
    border-radius: 10px;
    padding: 14px 20px;
    flex: 1;
    text-align: center;
    border: 1px solid #E5E2DA;
}
.stat-pill .sp-label {
    font-size: 0.72rem;
    color: #888;
    text-transform: uppercase;
    margin-bottom: 4px;
}
.stat-pill .sp-value {
    font-size: 1rem;
    font-weight: 600;
    color: #1C1C1E;
}

.footer {
    text-align: center;
    color: #BBB;
    font-size: 0.78rem;
    padding: 32px 0 8px;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar: Search History ─────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📋 Search History")
    st.markdown("Your past career report sessions.")
    st.markdown("---")

    history_data = get_history()

    if not history_data:
        st.markdown('<div class="hist-empty">No sessions yet.<br>Upload a résumé to get started.</div>',
                    unsafe_allow_html=True)
    else:
        for item in history_data[:10]:  # show latest 10
            name = item.get("name", "Unknown")
            email = item.get("email", "—")
            location = item.get("location", "—")
            ts = item.get("timestamp")
            ts_str = ts.strftime("%b %d, %Y · %H:%M") if ts else "—"
            doc_id = str(item.get("_id"))

            # Render entry blocks containing active action items
            st.markdown('<div class="history-block">', unsafe_allow_html=True)

            # Clicking this button will pull the history item content into main view
            if st.button(f"👤 {name}\n{email} · {location}\n{ts_str}", key=f"view_{doc_id}"):
                st.session_state.active_report = {
                    "name": name,
                    "email": email,
                    "location": location,
                    "itinerary": item.get("itinerary")
                }

            # Delete button layout
            if st.button(f"🗑 Delete entry", key=f"del_{doc_id}", type="secondary"):
                delete_history(doc_id)
                # Clear active report view if the current view was deleted
                st.session_state.active_report = None
                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")
        if st.button("🗑 Clear All History", type="secondary", key="clear_all_btn"):
            clear_history()
            st.session_state.active_report = None
            st.success("History cleared.")
            st.rerun()

# ── Main Layout ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>AI Career <span>Coach</span><br>&amp; Resume Optimizer</h1>
    <p>Upload your résumé to unlock tailored job matches, deep company insights,
       and a fully optimized career report — powered by a multi-agent AI pipeline.</p>
</div>
""", unsafe_allow_html=True)

# ── Upload Card ────────────────────────────────────────────────────────────────
st.markdown('<div class="upload-section">', unsafe_allow_html=True)
st.markdown("### 📄 Upload Your Résumé")
st.markdown('<p class="sub">Accepted format: PDF · Max 10 MB</p>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    label="Drop your PDF here or click to browse",
    type=["pdf"],
    label_visibility="collapsed",
)

generate = st.button("✨ Generate Career Report", type="primary")
st.markdown('</div>', unsafe_allow_html=True)

# ── Processing New Submissions ──────────────────────────────────────────────────
if generate:
    if not uploaded_file:
        st.error("⚠️ Please upload your résumé (PDF) before generating the report.")
    else:
        with st.spinner("🔍  Analysing your résumé through our AI agent network…"):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name

                result = job_agent(tmp_path)
                os.remove(tmp_path)

                if result.get("errors"):
                    st.error(f"🚨 Agent Error: {result['errors']}")
                elif result.get("itinerary"):
                    # One clean save to MongoDB here on the frontend level
                    search_history(
                        user_query=uploaded_file.name,
                        result=result,
                    )

                    # Store output into state context immediately
                    st.session_state.active_report = {
                        "name": result.get("name", "—"),
                        "email": result.get("email", "—"),
                        "location": result.get("location", "—"),
                        "itinerary": result.get("itinerary")
                    }
                    st.rerun()
                else:
                    st.warning("⚠️ The AI pipeline completed but returned no report. Please try again.")

            except Exception as exc:
                st.error(f"❌ Unexpected error: {exc}")

# ── Render Dynamic Active Report (Fresh Runs or Loaded History) ──────────────────
if st.session_state.active_report:
    report = st.session_state.active_report

    st.markdown(f"""
    <div class="stats-row">
        <div class="stat-pill">
            <div class="sp-label">Candidate</div>
            <div class="sp-value">{report['name']}</div>
        </div>
        <div class="stat-pill">
            <div class="sp-label">Email</div>
            <div class="sp-value">{report['email']}</div>
        </div>
        <div class="stat-pill">
            <div class="sp-label">Location</div>
            <div class="sp-value">{report['location']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="result-wrapper">', unsafe_allow_html=True)
    st.markdown('<span class="badge-success">✓ Session Loaded</span>', unsafe_allow_html=True)
    st.markdown('<div class="result-title">Career Report</div>', unsafe_allow_html=True)
    st.markdown(report["itinerary"])
    st.markdown('</div>', unsafe_allow_html=True)

# ── Footer ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="footer">AI Career Coach · Powered by a multi-agent AI pipeline</div>', unsafe_allow_html=True)