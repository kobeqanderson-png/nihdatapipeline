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
from scipy import stats as scipy_stats
from openpyxl.styles import Font, PatternFill

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


def safe_percent_diff(male_mean: float, female_mean: float) -> float:
    """Return percent difference relative to female mean; NaN if denominator is zero."""
    if pd.isna(female_mean) or female_mean == 0:
        return np.nan
    return (male_mean - female_mean) / female_mean * 100


def ttest_for_groups(df: pd.DataFrame, value_col: str, group_col: str = "Sex"):
    """Compute Welch's t-test between Male and Female groups for a variable."""
    male_data = df[df[group_col] == 'Male'][value_col].dropna()
    female_data = df[df[group_col] == 'Female'][value_col].dropna()

    if len(male_data) > 1 and len(female_data) > 1:
        t_stat, p_value = scipy_stats.ttest_ind(male_data, female_data, equal_var=False)
        return t_stat, p_value, len(male_data), len(female_data)
    return np.nan, np.nan, len(male_data), len(female_data)


def pvalue_to_label(p_value: float) -> str:
    """Convert p-value to a readable significance label."""
    if pd.isna(p_value):
        return "Insufficient data"
    return "Significant" if p_value < 0.05 else "Not Significant"


def sem(series: pd.Series) -> float:
    """Calculate SEM = std(N) / sqrt(N) using sample std (ddof=1)."""
    values = series.dropna()
    n = len(values)
    if n < 2:
        return np.nan
    return values.std(ddof=1) / np.sqrt(n)


def build_excel_export(df_processed: pd.DataFrame) -> bytes:
    """Build formatted Excel output with sex-separated layout and t-test results."""
    excel_buffer = io.BytesIO()

    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df_processed.to_excel(writer, index=False, sheet_name='Processed_Data')

        if 'Sex' in df_processed.columns:
            male_df = df_processed[df_processed['Sex'] == 'Male'].reset_index(drop=True)
            female_df = df_processed[df_processed['Sex'] == 'Female'].reset_index(drop=True)

            gap_cols = 4
            total_cols = len(df_processed.columns)
            female_start_col = total_cols + gap_cols + 1  # 1-based column index

            male_df.to_excel(writer, index=False, sheet_name='Sex_Classified', startrow=1, startcol=0)
            female_df.to_excel(
                writer,
                index=False,
                sheet_name='Sex_Classified',
                startrow=1,
                startcol=female_start_col - 1
            )

            ws = writer.sheets['Sex_Classified']
            header_font = Font(bold=True)
            highlight_fill = PatternFill(start_color='FFF59D', end_color='FFF59D', fill_type='solid')

            ws.cell(row=1, column=1, value='Male Animals').font = header_font
            ws.cell(row=1, column=female_start_col, value='Female Animals').font = header_font

            numeric_cols = df_processed.select_dtypes(include=['number']).columns.tolist()
            max_data_len = max(len(male_df), len(female_df))

            avg_row = max_data_len + 5
            sem_row = avg_row + 1
            ttest_title_row = sem_row + 3
            ttest_header_row = ttest_title_row + 1
            ttest_data_start = ttest_header_row + 1

            ws.cell(row=avg_row, column=1, value='Average (N)').font = header_font
            ws.cell(row=sem_row, column=1, value='SEM = stdev(N)/sqrt(N)').font = header_font
            ws.cell(row=avg_row, column=female_start_col, value='Average (N)').font = header_font
            ws.cell(row=sem_row, column=female_start_col, value='SEM = stdev(N)/sqrt(N)').font = header_font

            for col_name in numeric_cols:
                col_idx = df_processed.columns.get_loc(col_name) + 1
                female_col_idx = female_start_col + col_idx - 1

                male_vals = male_df[col_name].dropna()
                female_vals = female_df[col_name].dropna()

                male_mean = male_vals.mean() if len(male_vals) > 0 else np.nan
                female_mean = female_vals.mean() if len(female_vals) > 0 else np.nan

                if len(male_vals) > 0:
                    ws.cell(row=avg_row, column=col_idx, value=f"{male_mean:.4f} (N={len(male_vals)})")
                else:
                    ws.cell(row=avg_row, column=col_idx, value='N=0')

                if len(female_vals) > 0:
                    ws.cell(row=avg_row, column=female_col_idx, value=f"{female_mean:.4f} (N={len(female_vals)})")
                else:
                    ws.cell(row=avg_row, column=female_col_idx, value='N=0')

                male_sem = sem(male_vals)
                female_sem = sem(female_vals)

                ws.cell(
                    row=sem_row,
                    column=col_idx,
                    value=round(float(male_sem), 6) if not pd.isna(male_sem) else 'N<2'
                )
                ws.cell(
                    row=sem_row,
                    column=female_col_idx,
                    value=round(float(female_sem), 6) if not pd.isna(female_sem) else 'N<2'
                )

            ws.cell(row=ttest_title_row, column=1, value='Welch t-test Results').font = header_font

            ttest_headers = ['Variable', 'Male N', 'Female N', 't-stat', 'p-value', 'p<0.005']
            for i, col_title in enumerate(ttest_headers, start=1):
                ws.cell(row=ttest_header_row, column=i, value=col_title).font = header_font

            for i, col_name in enumerate(numeric_cols):
                row = ttest_data_start + i
                t_stat, p_value, n_male, n_female = ttest_for_groups(df_processed, col_name)
                is_highlight = not pd.isna(p_value) and p_value < 0.005

                ws.cell(row=row, column=1, value=col_name)
                ws.cell(row=row, column=2, value=n_male)
                ws.cell(row=row, column=3, value=n_female)
                ws.cell(row=row, column=4, value=round(float(t_stat), 6) if not pd.isna(t_stat) else np.nan)
                ws.cell(row=row, column=5, value=round(float(p_value), 6) if not pd.isna(p_value) else np.nan)
                ws.cell(row=row, column=6, value='YES' if is_highlight else 'NO')

                if is_highlight:
                    for col_num in range(1, 7):
                        ws.cell(row=row, column=col_num).fill = highlight_fill

            # Publication-style summary table for reporting
            publication_rows = []
            for col_name in numeric_cols:
                male_vals = male_df[col_name].dropna()
                female_vals = female_df[col_name].dropna()
                t_stat, p_value, n_male, n_female = ttest_for_groups(df_processed, col_name)

                male_mean = male_vals.mean() if len(male_vals) > 0 else np.nan
                female_mean = female_vals.mean() if len(female_vals) > 0 else np.nan
                male_sem = sem(male_vals)
                female_sem = sem(female_vals)

                publication_rows.append({
                    'Variable': col_name,
                    'Male Mean': round(float(male_mean), 6) if not pd.isna(male_mean) else np.nan,
                    'Male SEM': round(float(male_sem), 6) if not pd.isna(male_sem) else np.nan,
                    'Male N': int(n_male),
                    'Female Mean': round(float(female_mean), 6) if not pd.isna(female_mean) else np.nan,
                    'Female SEM': round(float(female_sem), 6) if not pd.isna(female_sem) else np.nan,
                    'Female N': int(n_female),
                    't-stat (Welch)': round(float(t_stat), 6) if not pd.isna(t_stat) else np.nan,
                    'p-value': round(float(p_value), 6) if not pd.isna(p_value) else np.nan,
                    'p<0.005': 'YES' if (not pd.isna(p_value) and p_value < 0.005) else 'NO'
                })

            publication_df = pd.DataFrame(publication_rows)
            if not publication_df.empty:
                publication_df.to_excel(writer, index=False, sheet_name='Publication_Stats')

                pub_ws = writer.sheets['Publication_Stats']
                pub_header_font = Font(bold=True)
                for col_num in range(1, len(publication_df.columns) + 1):
                    pub_ws.cell(row=1, column=col_num).font = pub_header_font

                p_col = publication_df.columns.get_loc('p-value') + 1
                flag_col = publication_df.columns.get_loc('p<0.005') + 1
                for row_num in range(2, len(publication_df) + 2):
                    p_cell = pub_ws.cell(row=row_num, column=p_col)
                    if isinstance(p_cell.value, (int, float, np.floating)) and p_cell.value < 0.005:
                        for col_num in range(1, len(publication_df.columns) + 1):
                            pub_ws.cell(row=row_num, column=col_num).fill = highlight_fill
                        pub_ws.cell(row=row_num, column=flag_col, value='YES')
            else:
                pd.DataFrame({'Info': ['No numeric columns available for publication stats.']}).to_excel(
                    writer,
                    index=False,
                    sheet_name='Publication_Stats'
                )

    return excel_buffer.getvalue()

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


   

 # --- 3️⃣ Process Data Section ---
if st.session_state.df_raw is not None:
    df_raw = st.session_state.df_raw
    st.divider()
    st.header("3️⃣ Process Data")

    # Dynamic Column Selection
    all_cols = df_raw.columns.tolist()

    col_a, col_b = st.columns(2)
    with col_a:
        sex_col = st.selectbox(
            "Select Column for Sex Classification", 
            options=all_cols,
            help="Select the column containing numeric values (e.g., Animal #)."
        )

    with col_b:
        threshold = st.number_input(
            f"Threshold for {sex_col}", 
            value=16, 
            step=1
        )

    if st.button("🚀 Run Processing Pipeline", type="primary", use_container_width=True):
        with st.spinner("Processing data..."):
            try:
                # 1. Apply basic cleaning
                df_processed = basic_clean(df_raw)
                
                # 2. Apply sex classification
                df_processed['Sex'] = df_processed[sex_col].apply(
                    lambda x: 'Male' if pd.notna(x) and x <= threshold else 'Female'
                )
                
                # 3. Add log features if enabled
                if add_log_features:
                    numeric_cols = df_processed.select_dtypes(include=['number']).columns
                    if len(numeric_cols) > 0:
                        df_processed = add_log_feature(df_processed, col=numeric_cols[0])
                
                # 4. Save results
                st.session_state.df_processed = df_processed
                st.success("✅ Processing complete!")
                
            except Exception as e:
                st.error(f"❌ Error during processing: {e}")
else:
    st.info("💡 Please upload a data file in Step 1 to begin processing.")
    # Visualization section
    # --- 5️⃣ Sex Differences Analysis Section ---
if st.session_state.df_processed is not None:
    df_processed = st.session_state.df_processed
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
            t_stat, p_value, n_male, n_female = ttest_for_groups(df_processed, selected_var)

            if not pd.isna(t_stat):

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
            else:
                st.warning(
                    f"Not enough non-missing values for a t-test on {selected_var}. "
                    f"Male n={n_male}, Female n={n_female}."
                )

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

                # Combined bar + scatter (mean with individual points)
                st.subheader("🎯 Combined Bar + Scatter")
                combo_var = st.selectbox(
                    "Select variable for combined bar + scatter",
                    selected_vars,
                    key="combo_var"
                )
                fig, ax = plt.subplots(figsize=(10, 5))
                barplot_common = {
                    'data': df_processed,
                    'x': 'Sex',
                    'y': combo_var,
                    'order': ['Male', 'Female'],
                    'estimator': np.mean,
                    'palette': ['#3498db', '#e74c3c'],
                    'alpha': 0.75,
                    'ax': ax,
                }
                try:
                    sns.barplot(errorbar=('ci', 95), **barplot_common)
                except TypeError:
                    # Older seaborn versions use `ci` instead of `errorbar`.
                    sns.barplot(ci=95, **barplot_common)
                sns.stripplot(
                    data=df_processed,
                    x='Sex',
                    y=combo_var,
                    order=['Male', 'Female'],
                    color='black',
                    alpha=0.5,
                    jitter=0.18,
                    size=4,
                    ax=ax
                )
                ax.set_title(f'{combo_var}: Mean Bar with Sample Scatter')
                ax.set_xlabel('Sex')
                ax.set_ylabel(combo_var)
                st.pyplot(fig)
                plt.close()

                # Density distribution (KDE)
                st.subheader("🌫️ Density Distribution")
                density_var = st.selectbox(
                    "Select variable for density distribution",
                    selected_vars,
                    key="density_var"
                )
                fig, ax = plt.subplots(figsize=(10, 5))
                male_density = df_processed[df_processed['Sex'] == 'Male'][density_var].dropna()
                female_density = df_processed[df_processed['Sex'] == 'Female'][density_var].dropna()

                if len(male_density) > 1:
                    sns.kdeplot(male_density, fill=True, alpha=0.4, label='Male', color='#3498db', ax=ax)
                if len(female_density) > 1:
                    sns.kdeplot(female_density, fill=True, alpha=0.4, label='Female', color='#e74c3c', ax=ax)

                ax.set_title(f'{density_var} Density by Sex')
                ax.set_xlabel(density_var)
                ax.set_ylabel('Density')
                if len(male_density) > 1 or len(female_density) > 1:
                    ax.legend()
                else:
                    st.info(
                        f"Not enough values to estimate density for {density_var}. "
                        "Need at least 2 non-missing values per group."
                    )
                st.pyplot(fig)
                plt.close()

                # Scatter plot
                st.subheader("🟢 Scatter Graph")
                scatter_cols = st.columns(2)
                with scatter_cols[0]:
                    x_var = st.selectbox("X-axis variable", selected_vars, key="scatter_x")
                with scatter_cols[1]:
                    y_candidates = [c for c in selected_vars if c != x_var] or selected_vars
                    y_var = st.selectbox("Y-axis variable", y_candidates, key="scatter_y")

                fig, ax = plt.subplots(figsize=(10, 5))
                sns.scatterplot(
                    data=df_processed,
                    x=x_var,
                    y=y_var,
                    hue='Sex',
                    palette={'Male': '#3498db', 'Female': '#e74c3c'},
                    alpha=0.75,
                    s=60,
                    ax=ax
                )
                ax.set_title(f'{y_var} vs {x_var} by Sex')
                ax.set_xlabel(x_var)
                ax.set_ylabel(y_var)
                ax.legend(title='Sex')
                st.pyplot(fig)
                plt.close()

                # Summary table
                summary_rows = []
                for var in selected_vars:
                    male_vals = df_processed[df_processed['Sex'] == 'Male'][var].dropna()
                    female_vals = df_processed[df_processed['Sex'] == 'Female'][var].dropna()
                    male_mean = male_vals.mean()
                    female_mean = female_vals.mean()
                    t_stat, p_value, n_male, n_female = ttest_for_groups(df_processed, var)

                    summary_rows.append({
                        'Variable': var,
                        'Male Mean': male_mean,
                        'Female Mean': female_mean,
                        'Difference': male_mean - female_mean,
                        'Diff %': safe_percent_diff(male_mean, female_mean),
                        'Male n': n_male,
                        'Female n': n_female,
                        't-stat': t_stat,
                        'p-value': p_value,
                        'Significance (alpha=0.05)': pvalue_to_label(p_value)
                    })

                comparison_df = pd.DataFrame({
                    'Variable': [row['Variable'] for row in summary_rows],
                    'Male Mean': [row['Male Mean'] for row in summary_rows],
                    'Female Mean': [row['Female Mean'] for row in summary_rows],
                    'Difference': [row['Difference'] for row in summary_rows],
                    'Diff %': [row['Diff %'] for row in summary_rows],
                    'Male n': [row['Male n'] for row in summary_rows],
                    'Female n': [row['Female n'] for row in summary_rows],
                    't-stat': [row['t-stat'] for row in summary_rows],
                    'p-value': [row['p-value'] for row in summary_rows],
                    'Significance (alpha=0.05)': [row['Significance (alpha=0.05)'] for row in summary_rows],
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
        excel_data = build_excel_export(df_processed)

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








