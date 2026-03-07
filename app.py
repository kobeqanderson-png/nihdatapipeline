import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import io
import sys
import matplotlib.pyplot as plt
import seaborn as sns

# Add project root to path for imports
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data_load import read_csv, read_excel
from src.cleaning import basic_clean
from src.features import add_log_feature

# --- Page Config ---
st.set_page_config(page_title="Sex Differences Pipeline", page_icon="🧬", layout="wide")


# --- Custom Styling ---
st.markdown("""
    <style>
    .main { 
        background-color: #f9f9f9; 
    }
    /* Style the Metric Cards */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #eee;
    }
    /* Force all text inside metrics to be black for visibility */
    [data-testid="stMetricLabel"] > div {
        color: #000000 !important;
        font-weight: bold !important;
    }
    [data-testid="stMetricValue"] > div {
        color: #000000 !important;
    }
    /* Style the primary button */
    div.stButton > button:first-child {
        background-color: #007bff;
        color: white;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)
# --- Sidebar ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=80)
    st.header("⚙️ Configuration")
    add_log_features = st.checkbox("Enable Log Transformation", value=True)
    st.divider()
    st.info("This pipeline automates sex classification and statistical analysis for research datasets.")

# --- Header ---
st.title("🧬 Sex Differences Analysis Pipeline")
st.caption("Upload, clean, and visualize sexual dimorphism in your research data.")

# --- 1️⃣ Upload Section ---
with st.container():
    uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"], help="Drag and drop your dataset here")

if uploaded_file:
    if 'df_raw' not in st.session_state or st.session_state.get('last_uploaded') != uploaded_file.name:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            st.session_state.df_raw = df
            st.session_state.last_uploaded = uploaded_file.name
        except Exception as e:
            st.error(f"Error loading: {e}")
            st.stop()

    df_raw = st.session_state.df_raw

    # --- 2️⃣ Explore ---
    with st.expander("🔍 Quick Data Preview", expanded=False):
        st.dataframe(df_raw.head(10), use_container_width=True)

    # --- 3️⃣ Process ---
    st.subheader("🛠️ Data Processing")
    c1, c2 = st.columns([2, 1])
    with c1:
        sex_col = st.selectbox("Classification Column", options=df_raw.columns.tolist(), index=0)
    with c2:
        threshold = st.number_input(f"Threshold for {sex_col}", value=16)

    if st.button("🚀 Run Analysis Pipeline", use_container_width=True):
        with st.spinner("Analyzing..."):
            df_proc = basic_clean(df_raw)
            df_proc['Sex'] = df_proc[sex_col].apply(lambda x: 'Male' if pd.notna(x) and x <= threshold else 'Female')
            if add_log_features:
                num_cols = df_proc.select_dtypes(include=[np.number]).columns
                if len(num_cols) > 0: df_proc = add_log_feature(df_proc, col=num_cols[0])
            st.session_state.df_processed = df_proc
            st.toast("Analysis Complete!", icon="✅")

# --- 4️⃣ Visualization ---
if st.session_state.get('df_processed') is not None:
    df_proc = st.session_state.df_processed
    st.divider()
    
    # Metrics Bar
    m1, m2, m3 = st.columns(3)
    male_n = len(df_proc[df_proc['Sex'] == 'Male'])
    female_n = len(df_proc[df_proc['Sex'] == 'Female'])
    m1.metric("Total N", len(df_proc))
    m2.metric("Males (♂️)", male_n, f"{male_n/len(df_proc)*100:.1f}%")
    m3.metric("Females (♀️)", female_n, f"{female_n/len(df_proc)*100:.1f}%")

    # Deep Dive Charts
    st.subheader("🔬 Comparison Deep-Dive")
    num_cols = df_proc.select_dtypes(include=[np.number]).columns.tolist()
    target_var = st.selectbox("Select Variable to Compare", num_cols)

    v1, v2 = st.columns([2, 1])
    with v1:
        sns.set_style("whitegrid")
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.violinplot(data=df_proc, x='Sex', y=target_var, palette=['#3498db', '#e74c3c'], inner="quart")
        sns.stripplot(data=df_proc, x='Sex', y=target_var, color="black", alpha=0.3, size=4)
        st.pyplot(fig)
    
    with v2:
        st.write("**Summary Stats**")
        stats = df_proc.groupby('Sex')[target_var].describe().T
        st.dataframe(stats, use_container_width=True)

    # Download
    st.divider()
    st.download_button("📥 Download Processed Results", 
                       df_proc.to_csv(index=False).encode('utf-8'), 
                       "processed_data.csv", "text/csv")

