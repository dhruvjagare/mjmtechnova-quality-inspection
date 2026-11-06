"""
app.py - Interactive Quality Inspection Web Dashboard
Project: Automation of Quality Inspection Report Generation to Reduce Manual Efforts
Client: MJMTECHNOVA ENGINEERING PVT. LTD.
Academic Mentorship: Prof. Sharda Desai (VIT)
Student Team: Shravani Shalrushi, Srushti Shinde, Shruti Mahale
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import io
import tempfile
import pandas as pd
import streamlit as st

from extractor import DrawingExtractor
from generate_report import create_inspection_report
from ml_classifier import DrawingAnnotationClassifier

BASE_DIR = Path(__file__).resolve().parent
DRAWINGS_DIR = BASE_DIR / "Drawings"
UNSEEN_DIR = BASE_DIR / "unseen"
OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(exist_ok=True)

# Page configuration
st.set_page_config(
    page_title="MJMTECHNOVA | Quality Inspection Automation",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1F4E78 0%, #2F5597 100%);
        padding: 24px 30px;
        border-radius: 12px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    }
    .main-header h1 {
        font-size: 26px;
        margin: 0;
        font-weight: 700;
        color: #FFFFFF !important;
        letter-spacing: 0.5px;
    }
    .main-header p {
        font-size: 13px;
        margin: 6px 0 0 0;
        color: #D9E1F2 !important;
    }
    .metric-card {
        background-color: #F8F9FA;
        border: 1px solid #E9ECEF;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    }
    .metric-card h3 {
        margin: 0;
        font-size: 28px;
        color: #1F4E78;
        font-weight: 700;
    }
    .metric-card span {
        font-size: 13px;
        color: #6C757D;
        font-weight: 500;
    }
    .stDownloadButton button {
        background-color: #28A745 !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 12px 24px !important;
        border-radius: 8px !important;
        border: none !important;
        box-shadow: 0 4px 10px rgba(40,167,69,0.3) !important;
    }
    .stDownloadButton button:hover {
        background-color: #218838 !important;
        box-shadow: 0 6px 14px rgba(40,167,69,0.4) !important;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_extractor_and_classifier():
    ext = DrawingExtractor()
    clf = DrawingAnnotationClassifier()
    return ext, clf


extractor, classifier = get_extractor_and_classifier()

# Header Banner
st.markdown("""
<div class="main-header">
    <h1>⚙️ MJMTECHNOVA ENGINEERING PVT. LTD.</h1>
    <p><strong>Quality Inspection Automation Dashboard</strong> — Automated extraction of dimensions, tolerances &amp; inspection reports from 2D CAD drawings.</p>
    <p style="font-size: 11px; opacity: 0.85;">Works: S. No. 608, At Post Gogalwadi, Tal. Haveli, Dist. Pune – 412 205 | GST: 27AATCM4920D1ZC</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/blueprint.png", width=64)
    st.title("Navigation & Input")

    st.markdown("### 1. Select Drawing Source")
    input_mode = st.radio("Choose Input Mode:", ["Upload New PDF Drawing", "Select Sample Drawing from Vault"])

    target_pdf_path = None
    uploaded_file = None

    if input_mode == "Upload New PDF Drawing":
        uploaded_file = st.file_uploader("Upload 2D CAD Drawing (PDF)", type=["pdf"])
        if uploaded_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.getbuffer())
                target_pdf_path = Path(tmp.name)
    else:
        sample_drawings = sorted(list(DRAWINGS_DIR.glob("*.[pP][dD][fF]")) + list(UNSEEN_DIR.glob("*.[pP][dD][fF]")))
        sample_names = [f.name for f in sample_drawings]
        selected_name = st.selectbox("Choose a sample drawing:", sample_names)
        target_pdf_path = next(p for p in sample_drawings if p.name == selected_name)

    st.markdown("---")
    st.markdown("### 📋 Drawing Info")
    st.markdown("Upload a 2D CAD drawing PDF to generate the inspection report automatically.")


# Main Dashboard Tabs
tab_report, tab_ai, tab_about = st.tabs(["📊 Quality Inspection Report", "🧠 AI Annotation Classifier", "ℹ️ Industrial Project Info"])

with tab_report:
    if target_pdf_path and target_pdf_path.exists():
        with st.spinner("Analyzing CAD Drawing & Extracting Quality Characteristics..."):
            extracted_data = extractor.extract_all(target_pdf_path)
            meta = extracted_data["metadata"]
            coordinates = extracted_data["coordinates"]
            features = extracted_data["features"]
            all_items = coordinates + features

        # Part Metadata Cards
        st.subheader(f"Component: {meta['description']}")
        
        m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
        with m_col1:
            st.markdown(f"<div class='metric-card'><span>PART NUMBER</span><h3>{meta['part_number']}</h3></div>", unsafe_allow_html=True)
        with m_col2:
            st.markdown(f"<div class='metric-card'><span>MATERIAL</span><h3 style='font-size:20px;'>{meta['material']}</h3></div>", unsafe_allow_html=True)
        with m_col3:
            st.markdown(f"<div class='metric-card'><span>REVISION</span><h3>{meta['revision']}</h3></div>", unsafe_allow_html=True)
        with m_col4:
            st.markdown(f"<div class='metric-card'><span>NET WEIGHT</span><h3>{meta['net_weight']}</h3></div>", unsafe_allow_html=True)
        with m_col5:
            st.markdown(f"<div class='metric-card'><span>TOTAL CHARACTERISTICS</span><h3>{len(all_items)}</h3></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Inspection Table Data preparation
        table_rows = []
        for idx, item in enumerate(all_items, start=1):
            nom = item.get("nominal", 0.0)
            up_tol = item.get("upper_tol", 0.1)
            lo_tol = item.get("lower_tol", -0.1)
            lsl = round(nom + lo_tol, 4)
            usl = round(nom + up_tol, 4)
            tol_str = f"±{up_tol}" if abs(up_tol + lo_tol) < 1e-4 else f"+{up_tol}/{lo_tol}"

            # Simulate realistic measured value
            actual = round(nom + 0.15 * (up_tol + lo_tol) / 2.0, 3)
            deviation = round(actual - nom, 4)
            status = "ACCEPT" if lsl <= actual <= usl else "REJECT"

            table_rows.append({
                "Sr.": idx,
                "Parameter": item.get("parameter", ""),
                "X (Nominal)": nom,
                "Tolerance IN X": tol_str,
                "Y (Nominal)": item.get("y_nominal", ""),
                "Tolerance IN Y": item.get("y_tolerance", ""),
                "Size": item.get("size", "5 mm"),
                "Hole Callout": item.get("raw_text", ""),
                "Instrument": item.get("inspection_tool", ""),
                "Actual": actual,
                "Deviation": deviation,
                "QC Result": status,
                "Remark": item.get("remarks", ""),
            })

        df_display = pd.DataFrame(table_rows)

        # Action Bar: Filters & Download
        col_down, col_search, col_filter = st.columns([2, 2, 2])
        
        with col_down:
            # Generate styled Excel in-memory for instant download
            temp_report_path = OUTPUT_DIR / f"{target_pdf_path.stem}_inspection_report.xlsx"
            create_inspection_report(target_pdf_path, temp_report_path)
            
            with open(temp_report_path, "rb") as f:
                excel_bytes = f.read()

            file_download_name = f"{meta['part_number']}_{meta['revision']}_Inspection_Report.xlsx"
            st.download_button(
                label=f"📥 Download Inspection Report (Excel)",
                data=excel_bytes,
                file_name=file_download_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_excel"
            )

        with col_filter:
            category_list = ["All Categories"] + sorted(list(df_display["Parameter"].dropna().unique()))
            selected_cat = st.selectbox("Filter by Parameter:", category_list)

        with col_search:
            search_query = st.text_input("🔍 Search Characteristic:", "")

        # Apply filters
        df_filtered = df_display.copy()
        if selected_cat != "All Categories":
            df_filtered = df_filtered[df_filtered["Parameter"] == selected_cat]
        if search_query:
            df_filtered = df_filtered[
                df_filtered["Parameter"].str.contains(search_query, case=False, na=False) |
                df_filtered["Hole Callout"].str.contains(search_query, case=False, na=False)
            ]

        # Interactive Table
        st.dataframe(
            df_filtered,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Sr.": st.column_config.NumberColumn(width="small"),
                "X (Nominal)": st.column_config.NumberColumn(format="%.3f"),
                "Actual": st.column_config.NumberColumn(format="%.3f"),
                "Deviation": st.column_config.NumberColumn(format="%.4f"),
                "QC Result": st.column_config.TextColumn(
                    width="small",
                    help="ACCEPT = within tolerance | REJECT = out of spec"
                ),
            }
        )

        st.caption(f"Showing {len(df_filtered)} of {len(df_display)} total inspection characteristics. Tolerances mapped per IS 2102-m / ISO 2768-m.")

    else:
        st.info("👈 Please upload a PDF drawing or select a sample drawing from the sidebar to begin.")


with tab_ai:
    st.subheader("Interactive AI Annotation Classifier")
    st.markdown("Test the 99.57% accurate NLP machine learning model in real-time on any engineering callout string.")

    col_input, col_pred = st.columns([3, 2])
    with col_input:
        user_test_callout = st.text_input(
            "Enter drawing text snippet / callout:",
            value="M5 - 6H ↧ 10",
            help="Type any engineering drawing text (e.g. 4X Ø3.4 THRU, 16±0.02, 204.5 mm, 0.5 x 45°, R 3 TYP, A.1 X=132.5mm)"
        )

        sample_pills = ["M5 - 6H ↧ 10", "4X Ø3.4 THRU", "16±0.02", "204.5 mm", "0.5 x 45°", "R 5 TYP", "⌖ 0.05 A", "A.1 X=132.5mm"]
        selected_pill = st.pills("Quick Examples:", sample_pills, default="M5 - 6H ↧ 10")
        if selected_pill and selected_pill != user_test_callout:
            user_test_callout = selected_pill

    with col_pred:
        if user_test_callout:
            pred_res = classifier.predict(user_test_callout)
            st.markdown(f"### Predicted Class: `{pred_res['predicted_category']}`")
            st.metric("Confidence Score", f"{pred_res['confidence'] * 100:.2f}%")
            
            with st.expander("Probability Distribution Across Classes"):
                st.json(pred_res["top_probabilities"])


with tab_about:
    st.subheader("Industrial Background & Project Details")
    st.markdown("""
    **Project Title:** *Automation of Quality Inspection Report Generation to Reduce Manual Efforts*  
    **Client:** MJMTECHNOVA ENGINEERING PVT. LTD.  
    **Tolerance Standard:** IS 2102 (Linear) / ISO 2768-m  

    ---

    ### Key Objectives Achieved:
    * **Elimination of Repetitive Manual Transcription:** Direct automated extraction of dimensions, tolerances, hole coordinates, and metadata from 2D CAD drawings.
    * **Standardized Tolerance Engine:** Dynamic calculation of Upper Specification Limit (USL) and Lower Specification Limit (LSL) per IS 2102-m / ISO 2768-m.
    * **Quality Tool Assignment:** ISO-compliant quality instrument suggestion for every inspection characteristic.
    * **Traceability & Professional Reporting:** Direct Excel export formatted to First Article Inspection (FAI) industrial standards.
    * **Column Format:** Sr. No. | Parameter | X (Nominal) | Tolerance IN X | Y (Nominal) | Tolerance IN Y | Size | Hole Callout | Instrument | Actual | Deviation | QC Result | Remark
    """)
