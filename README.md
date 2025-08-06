# 📊 Job Market Analytics Dashboard (Streamlit)

This is an interactive **Streamlit Dashboard** that visualizes job market insights using a large **Parquet file**. It allows filtering job postings by **Metropolitan Statistical Area (MSA)**, **Employment Type**, **Remote Options**, **Experience Range**, and **Salary Range**. The dashboard generates insightful visualizations like bar charts, pie charts, histograms, and treemaps based on industry, occupation, skills, companies, and education levels.

---

## 🚀 Features

- **Load Parquet from Dropbox URL** (in-memory streaming)
- **Filter Job Postings** by:
  - MSA (Metropolitan Statistical Area)
  - Employment Type
  - Remote Type
  - Experience Range
  - Salary Range
- **Download Filtered Data** as CSV
- **Visualizations**:
  - Top Industries (NAICS 2-digit)
  - Top Occupations (SOC 5-digit)
  - Salary Distribution Histogram
  - Top Specialized Skills
  - Top Hiring Companies
  - Minimum Education Level Pie Chart
  - Treemaps for Specialized Skills & Certifications by Industry

---

## 🗂️ Project Structure

```bash
.
├── app.py                    # Main Streamlit Application Script
├── README.md                  # Project Documentation
