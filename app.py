import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from io import BytesIO

# --- PAGE CONFIG ---
st.set_page_config(page_title="LinkedIn Lead Extractor", page_icon="📊")

# --- INITIALIZE SESSION STATE ---
# This keeps your data even when the app re-runs
if 'leads_list' not in st.session_state:
    st.session_state.leads_list = []

# --- PARSING LOGIC ---
def parse_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    new_leads = []
    items = soup.find_all('li', class_='artdeco-list__item')
    timestamp = datetime.now().strftime("%Y-%m-%d")
    
    for item in items:
        name_tag = item.find('span', class_='a11y-text')
        name = name_tag.get_text(strip=True).replace('Add ', '').replace(' to selection', '') if name_tag else "Unknown"
        title_tag = item.find('span', {'data-anonymize': 'title'})
        company_tag = item.find('a', {'data-anonymize': 'company-name'})
        
        new_leads.append({
            'Date Added': timestamp,
            'Name': name,
            'Role': title_tag.get_text(strip=True) if title_tag else "N/A",
            'Company': company_tag.get_text(strip=True) if company_tag else "N/A"
        })
    return new_leads

# --- UI LAYOUT ---
st.title("🚀 Sales Navigator Lead Extractor")
st.write("Paste your HTML below to extract names, roles, and companies.")

# Input Area
html_input = st.text_area("Paste HTML code here:", height=300)

if st.button("Extract & Add Leads"):
    if html_input.strip():
        extracted = parse_html(html_input)
        if extracted:
            # Add to the session list and remove duplicates
            combined = st.session_state.leads_list + extracted
            # Convert to DF to drop duplicates easily
            df_temp = pd.DataFrame(combined).drop_duplicates(subset=['Name', 'Company'])
            st.session_state.leads_list = df_temp.to_dict('records')
            st.success(f"Added {len(extracted)} leads! Total in list: {len(st.session_state.leads_list)}")
        else:
            st.error("No leads found. Check your HTML snippet.")
    else:
        st.warning("Please paste some HTML first.")

# --- DATA DISPLAY & DOWNLOAD ---
if st.session_state.leads_list:
    df = pd.DataFrame(st.session_state.leads_list)
    st.divider()
    st.subheader("Current Lead List")
    st.dataframe(df, use_container_width=True)

    # Conversion logic for Excel Download
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Leads')
    
    st.download_button(
        label="📥 Download Excel Sheet",
        data=output.getvalue(),
        file_name="extracted_leads.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    if st.button("🗑️ Clear All Leads"):
        st.session_state.leads_list = []
        st.rerun()