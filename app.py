import streamlit as st
import pandas as pd
import plotly.express as px
import ast
import io
import pyarrow.parquet as pq
import requests

@st.cache_data
def load_parquet_from_url(dropbox_url):
    # Stream download into memory (BytesIO)
    response = requests.get(dropbox_url, stream=True)
    response.raise_for_status()

    parquet_bytes = io.BytesIO(response.content)
    return parquet_bytes

@st.cache_data
def list_msas_from_parquet(parquet_bytes):
    # Read only MSA_NAME column to get unique MSAs
    table = pq.read_table(parquet_bytes, columns=['MSA_NAME'])
    msa_names = table.column('MSA_NAME').to_pylist()
    return sorted(list(set(msa_names)))

@st.cache_data
def load_msa_data(parquet_bytes, msa):
    columns_needed = [
        "TITLE_NAME", "SALARY_FROM", "SALARY_TO", "MIN_YEARS_EXPERIENCE", "MAX_YEARS_EXPERIENCE",
        "SKILLS_NAME", "EMPLOYMENT_TYPE_NAME", "REMOTE_TYPE_NAME", "COMPANY_NAME",
        "MIN_EDULEVELS_NAME", "SOC_2021_5_NAME", "NAICS2_NAME", "NAICS4_NAME", "NAICS6_NAME",
        "SPECIALIZED_SKILLS_NAME", "CERTIFICATIONS_NAME", "COMMON_SKILLS_NAME", "MSA_NAME"
    ]

    table = pq.read_table(parquet_bytes, columns=columns_needed, filters=[("MSA_NAME", "==", msa)])
    df = table.to_pandas()

    # Clean skill columns
    for col in ['SKILLS_NAME', 'SPECIALIZED_SKILLS_NAME', 'CERTIFICATIONS_NAME', 'COMMON_SKILLS_NAME']:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: ast.literal_eval(x) if pd.notnull(x) else [])

    return df

# --- Main App ---
DROPBOX_URL = "https://www.dropbox.com/scl/fi/2ajbqq5yqt637kjjez1pk/combined_data_screen7.parquet?rlkey=mun8x2i6teb6h4a9r69jgsk9k&st=wvis2997&dl=1"
parquet_bytes = load_parquet_from_url(DROPBOX_URL)

# Sidebar Filters
st.sidebar.title("Job Market Filters")
available_msas = list_msas_from_parquet(parquet_bytes)
msa = st.sidebar.selectbox("Select MSA", available_msas)
df = load_msa_data(parquet_bytes, msa)

# Sidebar Filters
job_type = st.sidebar.multiselect("Employment Type", df['EMPLOYMENT_TYPE_NAME'].dropna().unique())
df['REMOTE_TYPE_NAME'] = df['REMOTE_TYPE_NAME'].replace({'[None]': 'Unspecified'})
df['REMOTE_TYPE_NAME'].fillna('Unspecified', inplace=True)
df['REMOTE_TYPE_NAME'] = df['REMOTE_TYPE_NAME'].astype(str).str.strip()
remote = st.sidebar.multiselect("Remote Type", df['REMOTE_TYPE_NAME'].unique())
min_exp = st.sidebar.slider("Min Years Experience", 0, 20, 0)
max_exp = st.sidebar.slider("Max Years Experience", 0, 30, 30)
salary_range = st.sidebar.slider("Salary Range", 0, int(df['SALARY_TO'].dropna().max()), (0, 200000))

# Apply filters
filtered_df = df.copy()
if job_type:
    filtered_df = filtered_df[filtered_df['EMPLOYMENT_TYPE_NAME'].isin(job_type)]
if remote:
    filtered_df = filtered_df[filtered_df['REMOTE_TYPE_NAME'].isin(remote)]
filtered_df = filtered_df[
    (filtered_df['MIN_YEARS_EXPERIENCE'] >= min_exp) &
    (filtered_df['MAX_YEARS_EXPERIENCE'] <= max_exp) &
    (filtered_df['SALARY_FROM'] >= salary_range[0]) &
    (filtered_df['SALARY_TO'] <= salary_range[1])
]

st.title(f"Job Insights for {msa}")

# CSV Download
st.markdown("### Download Filtered Results")
csv_buffer = io.StringIO()
filtered_df.to_csv(csv_buffer, index=False)
st.download_button(
    label="📥 Download CSV",
    data=csv_buffer.getvalue(),
    file_name=f"filtered_jobs_{msa.replace(' ', '_')}.csv",
    mime="text/csv"
)
# Industry (NAICS2, NAICS4, NAICS6)
for level, label in [("NAICS2_NAME", "NAICS 2")]:
    if level in filtered_df.columns:
        industry_filtered = filtered_df[filtered_df[level] != 'Unclassified Industry']
        industry_counts = industry_filtered[level].value_counts().nlargest(10).reset_index()
        industry_counts.columns = [label, 'Count']
        fig = px.bar(industry_counts, x='Count', y=label, orientation='h', title=f"Top Industries - {label}", category_orders={label: industry_counts[label].tolist()})
        st.plotly_chart(fig)

# Occupation by SOC 5
if 'SOC_2021_5_NAME' in filtered_df.columns:
    soc_filtered = filtered_df[filtered_df['SOC_2021_5_NAME'] != 'Unclassified Occupation']
    soc_counts = soc_filtered['SOC_2021_5_NAME'].value_counts().nlargest(10).reset_index()
    soc_counts.columns = ['Occupation (SOC 5)', 'Count']
    fig_soc = px.bar(
        soc_counts,
        x='Count',
        y='Occupation (SOC 5)',
        orientation='h',
        title="Top Occupations (SOC 5)",
        category_orders={'Occupation (SOC 5)': soc_counts['Occupation (SOC 5)'].tolist()}
    )
    st.plotly_chart(fig_soc)


# Salary Distribution
if 'SALARY_FROM' in filtered_df.columns and 'SALARY_TO' in filtered_df.columns:
    filtered_df['Average_Salary'] = filtered_df[['SALARY_FROM', 'SALARY_TO']].mean(axis=1)
    fig2 = px.histogram(filtered_df, x='Average_Salary', nbins=30, title="Salary Distribution")
    st.plotly_chart(fig2)

# Top Skills
if 'SPECIALIZED_SKILLS_NAME' in filtered_df.columns:
    exploded_skills = filtered_df.explode('SPECIALIZED_SKILLS_NAME')
    top_skills = exploded_skills['SPECIALIZED_SKILLS_NAME'].value_counts().nlargest(10).reset_index()
    top_skills.columns = ['Skill', 'Count']
    fig4 = px.bar(top_skills, x='Count', y='Skill', orientation='h', title="Top Specialized Skills", category_orders={'Skill': top_skills['Skill'].tolist()})
    st.plotly_chart(fig4)

# Company Job Counts
if 'COMPANY_NAME' in filtered_df.columns:
    top_companies = filtered_df[filtered_df['COMPANY_NAME'] != 'Unclassified']['COMPANY_NAME'] \
                        .value_counts().nlargest(10).reset_index()
    top_companies.columns = ['Company', 'Count']
    fig5 = px.bar(
        top_companies,
        x='Count',
        y='Company',
        orientation='h',
        title="Top Hiring Companies",
        category_orders={'Company': top_companies['Company'].tolist()}
    )
    st.plotly_chart(fig5)


# Education Levels
if 'MIN_EDULEVELS_NAME' in filtered_df.columns:
    edu_counts = filtered_df['MIN_EDULEVELS_NAME'].value_counts().reset_index()
    edu_counts.columns = ['Education Level', 'Count']
    fig6 = px.pie(edu_counts, names='Education Level', values='Count', title="Minimum Education Required")
    st.plotly_chart(fig6)


# Tree Maps for Specialized, Certification, and Common Skills by Industry
for skill_col, label in [
    ('SPECIALIZED_SKILLS_NAME', 'Specialized Skills'),
    ('CERTIFICATIONS_NAME', 'Certifications'),
    # ('COMMON_SKILLS_NAME', 'Common Skills')
]:
    if 'NAICS2_NAME' in filtered_df.columns and skill_col in filtered_df.columns:
        exploded_skills = filtered_df.explode(skill_col)
        exploded_skills = exploded_skills[exploded_skills['NAICS2_NAME'] != 'Unclassified Industry']
        skill_data = exploded_skills.groupby(['NAICS2_NAME', skill_col]).size().reset_index(name='count')
        skill_data.columns = ['Industry', 'Skill', 'Count']
        fig = px.treemap(skill_data, path=['Industry', 'Skill'], values='Count', title=f"Top {label} by Industry (NAICS2)")
        st.plotly_chart(fig)

