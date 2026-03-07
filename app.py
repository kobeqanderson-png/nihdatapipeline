"""
Data Processing Pipeline - Interactive Web App

Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import io
import sys

# Add project root to path for imports
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data_load import read_csv, read_excel
from src.cleaning import basic_clean, save_clean
from src.features import add_log_feature
from src.visualize import boxplot_by_category, countplot

import matplotlib.pyplot as plt
import seaborn as sns

# Page configuration
st.set_page_config(
    page_title="Sex Differences Analysis Pipeline",
    page_icon="📊",
    layout="wide"
)

# Title and description
st.title("📊 Sex Differences Analysis Pipeline")
st.markdown("""
Upload CSV or Excel files to analyze sex differences in your data.

**Features:**
- Load CSV and Excel files
- Automatic sex classification (Animal ≤16 = Male, >16 = Female)
- Basic data cleaning (missing values, duplicates, whitespace)
- Sex differences visualization and statistics
- Feature engineering (log transformations)
- Download processed data
""")

st.divider()

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")

    # Sex classification settings
    st.subheader("Sex Classification")
    st.markdown("**Animal # ≤ threshold = Male, > threshold = Female**")
    sex_threshold = st.number_input("Threshold (Animal #)", value=16, min_value=1, step=1)

    st.divider()

    # Sheet selection for Excel files
    sheet_option = st.radio(
        "Excel Sheet Selection",
        ["First sheet (index 0)", "Specify sheet name"],
        index=0
    )

    if sheet_option == "Specify sheet name":
        sheet_name = st.text_input("Sheet name", value="Sheet1")
    else:
        sheet_name = 0

    st.divider()

    # Cleaning options
    st.subheader("Cleaning Options")
    fill_missing_numeric = st.checkbox("Fill missing numeric values with median", value=True)
    remove_duplicates = st.checkbox("Remove duplicate rows", value=True)
    strip_whitespace = st.checkbox("Strip whitespace from strings", value=True)

    st.divider()

    # Feature engineering options
    st.subheader("Feature Engineering")
    add_log_features = st.checkbox("Add log-transformed features", value=True)

# File upload section
st.header("1️⃣ Upload Your Data")

uploaded_file = st.file_uploader(
    "Choose a CSV or Excel file",
    type=["csv", "xlsx", "xls"],
    help="Drag and drop or click to upload"
)

# Initialize session state
if 'df_raw' not in st.session_state:
    st.session_state.df_raw = None
if 'df_processed' not in st.session_state:
    st.session_state.df_processed = None

if uploaded_file is not None:
    # Load the file
    try:
        file_extension = Path(uploaded_file.name).suffix.lower()
        
        if file_extension == '.csv':
            # This calls your custom function in src/data_load.py
            df_raw = read_csv(uploaded_file)
        elif file_extension in ['.xlsx', '.xls']:
            xl = pd.ExcelFile(uploaded_file)
            available_sheets = xl.sheet_names
            st.info(f"📋 Available sheets: {', '.join(available_sheets)}")
            selected_sheet = st.selectbox("Select sheet to load", available_sheets, index=0)
            df_raw = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
        
        st.session_state.df_raw = df_raw
        st.success(f"✅ Loaded **{uploaded_file.name}** - {len(df_raw):,} rows × {len(df_raw.columns)} columns")
        
    except Exception as e:
        st.error(f"❌ Error loading file: {e}")
        st.stop()

# Data exploration section
if st.session_state.df_raw is not None:
    df_raw = st.session_state.df_raw

    st.divider()
    st.header("2️⃣ Explore Raw Data")

    # Data preview tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Preview", "📊 Statistics", "❓ Missing Values", "📈 Columns"])

    with tab1:
        st.subheader("Data Preview")
        n_rows = st.slider("Rows to display", 5, 50, 10)
        st.dataframe(df_raw.head(n_rows), use_container_width=True)

    with tab2:
        st.subheader("Summary Statistics")
        numeric_cols = df_raw.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            st.dataframe(df_raw[numeric_cols].describe(), use_container_width=True)
        else:
            st.warning("No numeric columns found")

    with tab3:
        st.subheader("Missing Values")
        missing = df_raw.isnull().sum()
        missing_pct = (missing / len(df_raw) * 100).round(2)
        missing_df = pd.DataFrame({
            'Column': missing.index,
            'Missing Count': missing.values,
            'Missing %': missing_pct.values
        }).sort_values('Missing Count', ascending=False)

        missing_with_values = missing_df[missing_df['Missing Count'] > 0]
        if len(missing_with_values) > 0:
            st.dataframe(missing_with_values, use_container_width=True)
        else:
            st.success("✅ No missing values found!")

    with tab4:
        st.subheader("Column Information")
        col_info = pd.DataFrame({
            'Column': df_raw.columns,
            'Type': df_raw.dtypes.astype(str).values,
            'Non-Null Count': df_raw.notna().sum().values,
            'Unique Values': df_raw.nunique().values
        })
        st.dataframe(col_info, use_container_width=True)

    # Processing section
    st.divider()
    st.header("3️⃣ Process Data")

    # Animal column selection for sex classification
    st.divider()
st.header("3️⃣ Process Data")

# Dynamic Column Selection
all_cols = df_raw.columns.tolist()

col_a, col_b = st.columns(2)
with col_a:
    # This allows you to pick ANY column from your uploaded file
    sex_col = st.selectbox(
        "Select Column for Sex Classification", 
        options=all_cols,
        help="Select the column containing the numeric values used to determine sex."
    )

with col_b:
    # Users can set the threshold for the specific column chosen above
    threshold = st.number_input(
        f"Threshold for {sex_col}", 
        value=16, 
        step=1
    )

if st.button("🚀 Run Processing Pipeline", type="primary", use_container_width=True):
    with st.spinner("Processing data..."):
        try:
            # Apply basic cleaning
            df_processed = basic_clean(df_raw)
            
   # Processing section
    if st.button("🚀 Run Processing Pipeline", type="primary", use_container_width=True):
        with st.spinner("Processing data..."):
            try:
                # 1. Apply basic cleaning
                df_processed = basic_clean(df_raw)
                
                # 2. Apply sex classification using YOUR chosen column and threshold
                # This uses 'sex_col' and 'threshold' defined right above this button
                df_processed['Sex'] = df_processed[sex_col].apply(
                    lambda x: 'Male' if pd.notna(x) and x <= threshold else 'Female'
                )
                
                # 3. Add log features if enabled in sidebar
                if add_log_features:
                    numeric_cols = df_processed.select_dtypes(include=['number']).columns
                    if len(numeric_cols) > 0:
                        df_processed = add_log_feature(df_processed, col=numeric_cols[0])
                
                # 4. Save results to session state
                st.session_state.df_processed = df_processed
                
                # Show Success Metrics
                st.success("✅ Processing complete!")
                m1, m2, m3 = st.columns(3)
                m1.metric("Original Rows", len(df_raw))
                m2.metric("Processed Rows", len(df_processed))
                m3.metric("Males Identified", (df_processed['Sex'] == 'Male').sum())
                
            except Exception as e:
                st.error(f"❌ Error during processing: {e}")        
    # Columns list
    with st.expander("📋 All Columns"):
        for i, col in enumerate(df_processed.columns, 1):
            st.text(f"{i}. {col}")

    # Visualization section
    st.divider()
    st.header("5️⃣ Sex Differences Analysis")

    numeric_cols = df_processed.select_dtypes(include=['number']).columns.tolist()

    # Check if Sex column exists
    if 'Sex' in df_processed.columns:
        # Sex distribution overview
        st.subheader("📊 Sex Distribution")

        sex_counts = df_processed['Sex'].value_counts()
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Samples", len(df_processed))
        with col2:
            male_count = sex_counts.get('Male', 0)
            st.metric("Males", male_count, f"{male_count/len(df_processed)*100:.1f}%")
        with col3:
            female_count = sex_counts.get('Female', 0)
            st.metric("Females", female_count, f"{female_count/len(df_processed)*100:.1f}%")

        # Sex distribution pie chart
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))

        # Pie chart
        colors = ['#3498db', '#e74c3c']  # Blue for male, red for female
        axes[0].pie(sex_counts.values, labels=sex_counts.index, autopct='%1.1f%%',
                   colors=colors, startangle=90)
        axes[0].set_title('Sex Distribution')

        # Bar chart
        sex_counts.plot(kind='bar', ax=axes[1], color=colors, edgecolor='black')
        axes[1].set_title('Sex Counts')
        axes[1].set_xlabel('Sex')
        axes[1].set_ylabel('Count')
        axes[1].tick_params(axis='x', rotation=0)

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        st.divider()

        # Sex differences comparison
        st.subheader("🔬 Compare Variables by Sex")

        if numeric_cols:
            selected_var = st.selectbox(
                "Select variable to compare between sexes",
                numeric_cols,
                key="sex_compare"
            )

            viz_col1, viz_col2 = st.columns(2)

            with viz_col1:
                # Box plot by sex
                fig, ax = plt.subplots(figsize=(8, 5))
                df_processed.boxplot(column=selected_var, by='Sex', ax=ax)
                ax.set_title(f'{selected_var} by Sex')
                ax.set_xlabel('Sex')
                ax.set_ylabel(selected_var)
                plt.suptitle('')  # Remove automatic title
                st.pyplot(fig)
                plt.close()

            with viz_col2:
                # Violin plot by sex
                fig, ax = plt.subplots(figsize=(8, 5))
                parts = ax.violinplot(
                    [df_processed[df_processed['Sex'] == 'Male'][selected_var].dropna(),
                     df_processed[df_processed['Sex'] == 'Female'][selected_var].dropna()],
                    positions=[1, 2],
                    showmeans=True,
                    showmedians=True
                )
                ax.set_xticks([1, 2])
                ax.set_xticklabels(['Male', 'Female'])
                ax.set_title(f'{selected_var} Distribution by Sex')
                ax.set_xlabel('Sex')
                ax.set_ylabel(selected_var)
                st.pyplot(fig)
                plt.close()

            # Histogram overlay by sex
            st.subheader("📈 Distribution Overlay")
            fig, ax = plt.subplots(figsize=(10, 5))

            male_data = df_processed[df_processed['Sex'] == 'Male'][selected_var].dropna()
            female_data = df_processed[df_processed['Sex'] == 'Female'][selected_var].dropna()

            ax.hist(male_data, bins=20, alpha=0.6, label='Male', color='#3498db', edgecolor='black')
            ax.hist(female_data, bins=20, alpha=0.6, label='Female', color='#e74c3c', edgecolor='black')
            ax.set_title(f'{selected_var} Distribution by Sex')
            ax.set_xlabel(selected_var)
            ax.set_ylabel('Frequency')
            ax.legend()
            st.pyplot(fig)
            plt.close()

            # Summary statistics by sex
            st.subheader("📋 Summary Statistics by Sex")

            stats_by_sex = df_processed.groupby('Sex')[selected_var].agg([
                'count', 'mean', 'std', 'min', 'median', 'max'
            ]).round(4)
            stats_by_sex.columns = ['Count', 'Mean', 'Std Dev', 'Min', 'Median', 'Max']
            st.dataframe(stats_by_sex, use_container_width=True)

            # Statistical test (t-test)
            from scipy import stats as scipy_stats

            if len(male_data) > 1 and len(female_data) > 1:
                t_stat, p_value = scipy_stats.ttest_ind(male_data, female_data)

                st.subheader("📊 Statistical Test (Independent t-test)")
                stat_col1, stat_col2, stat_col3 = st.columns(3)

                with stat_col1:
                    st.metric("t-statistic", f"{t_stat:.4f}")
                with stat_col2:
                    st.metric("p-value", f"{p_value:.4f}")
                with stat_col3:
                    significance = "Significant" if p_value < 0.05 else "Not Significant"
                    st.metric("Result (α=0.05)", significance)

                if p_value < 0.05:
                    st.success(f"✅ Significant difference found (p={p_value:.4f} < 0.05)")
                else:
                    st.info(f"ℹ️ No significant difference (p={p_value:.4f} ≥ 0.05)")

        st.divider()

        # Multi-variable comparison
        st.subheader("📊 Multi-Variable Sex Comparison")

        if len(numeric_cols) > 0:
            selected_vars = st.multiselect(
                "Select variables to compare",
                numeric_cols,
                default=numeric_cols[:min(3, len(numeric_cols))]
            )

            if selected_vars:
                # Mean comparison bar chart
                fig, ax = plt.subplots(figsize=(12, 6))

                male_means = df_processed[df_processed['Sex'] == 'Male'][selected_vars].mean()
                female_means = df_processed[df_processed['Sex'] == 'Female'][selected_vars].mean()

                x = np.arange(len(selected_vars))
                width = 0.35

                bars1 = ax.bar(x - width/2, male_means, width, label='Male', color='#3498db', edgecolor='black')
                bars2 = ax.bar(x + width/2, female_means, width, label='Female', color='#e74c3c', edgecolor='black')

                ax.set_xlabel('Variables')
                ax.set_ylabel('Mean Value')
                ax.set_title('Mean Comparison by Sex')
                ax.set_xticks(x)
                ax.set_xticklabels(selected_vars, rotation=45, ha='right')
                ax.legend()

                plt.tight_layout()
                st.pyplot(fig)
                plt.close()

                # Summary table
                comparison_df = pd.DataFrame({
                    'Variable': selected_vars,
                    'Male Mean': male_means.values,
                    'Female Mean': female_means.values,
                    'Difference': (male_means - female_means).values,
                    'Diff %': ((male_means - female_means) / female_means * 100).values
                }).round(4)
                st.dataframe(comparison_df, use_container_width=True)

    else:
        st.warning("⚠️ No 'Sex' column found. Please run the processing pipeline first with an Animal # column selected.")

    st.divider()
    st.header("6️⃣ General Visualizations")

    viz_col1, viz_col2 = st.columns(2)

    with viz_col1:
        st.subheader("Histogram")
        if numeric_cols:
            hist_col = st.selectbox("Select column for histogram", numeric_cols, key="hist")

            fig, ax = plt.subplots(figsize=(8, 4))
            df_processed[hist_col].dropna().hist(bins=30, ax=ax, edgecolor='black', alpha=0.7)
            ax.set_title(f'Distribution of {hist_col}')
            ax.set_xlabel(hist_col)
            ax.set_ylabel('Frequency')
            st.pyplot(fig)
            plt.close()

    with viz_col2:
        st.subheader("Box Plot")
        if numeric_cols:
            box_col = st.selectbox("Select column for box plot", numeric_cols, key="box")

            fig, ax = plt.subplots(figsize=(8, 4))
            df_processed.boxplot(column=box_col, ax=ax)
            ax.set_title(f'Box Plot of {box_col}')
            st.pyplot(fig)
            plt.close()

    # Correlation heatmap
    st.subheader("Correlation Heatmap")
    numeric_df = df_processed.select_dtypes(include=['number'])
    if len(numeric_df.columns) > 1:
        # Limit columns for readability
        max_cols = st.slider("Max columns to show", 5, 20, 10)
        cols_to_plot = numeric_df.columns[:max_cols]

        fig, ax = plt.subplots(figsize=(12, 8))
        corr_matrix = numeric_df[cols_to_plot].corr()
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, fmt='.2f', ax=ax)
        ax.set_title('Correlation Matrix')
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
    else:
        st.warning("Not enough numeric columns for correlation analysis")

    # Download section
    st.divider()
    st.header("7️⃣ Download Processed Data")

    col1, col2 = st.columns(2)

    with col1:
        # CSV download
        csv_buffer = io.StringIO()
        df_processed.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()

        if uploaded_file:
            csv_filename = Path(uploaded_file.name).stem + "_processed.csv"
        else:
            csv_filename = "processed_data.csv"

        st.download_button(
            label="📥 Download as CSV",
            data=csv_data,
            file_name=csv_filename,
            mime="text/csv",
            use_container_width=True
        )

    with col2:
        # Excel download
        excel_buffer = io.BytesIO()
        df_processed.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_data = excel_buffer.getvalue()

        if uploaded_file:
            excel_filename = Path(uploaded_file.name).stem + "_processed.xlsx"
        else:
            excel_filename = "processed_data.xlsx"

        st.download_button(
            label="📥 Download as Excel",
            data=excel_data,
            file_name=excel_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# Footer
st.divider()
st.markdown("""
---
**Data Processing Pipeline** | Built with Streamlit  
To run from command line: `streamlit run app.py`
""")





