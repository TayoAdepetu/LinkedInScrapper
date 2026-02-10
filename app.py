import streamlit as st
from supabase import create_client
import pandas as pd
from bs4 import BeautifulSoup
from io import BytesIO
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="LinkedIn Lead Database", page_icon="🟢")

# --- SUPABASE CONNECTION ---
supabase = create_client(
    st.secrets["supabase"]["url"],
    st.secrets["supabase"]["key"]
)

TABLE_NAME = "leads"

def parse_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    new_leads = []
    items = soup.find_all('li', class_='artdeco-list__item')

    for item in items:
        name_tag = item.find('span', class_='a11y-text')
        name = name_tag.get_text(strip=True).replace('Add ', '').replace(' to selection', '') if name_tag else "Unknown"
        title_tag = item.find('span', {'data-anonymize': 'title'})
        company_tag = item.find('a', {'data-anonymize': 'company-name'})

        # Skip skeleton/lazy-loaded items that only have a name but no real data
        if not title_tag and not company_tag:
            continue

        new_leads.append({
            'name': name,
            'role': title_tag.get_text(strip=True) if title_tag else "N/A",
            'company': company_tag.get_text(strip=True) if company_tag else "N/A"
        })
    return new_leads

def get_all_leads():
    """Fetch all leads from Supabase."""
    response = supabase.table(TABLE_NAME).select("*").order("created_at", desc=True).execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()

def upsert_leads(new_leads):
    """Insert new leads, skipping duplicates (same name + company)."""
    existing = get_all_leads()
    added = 0

    for lead in new_leads:
        # Check if this lead already exists
        if not existing.empty:
            duplicate = existing[
                (existing['name'] == lead['name']) &
                (existing['company'] == lead['company'])
            ]
            if not duplicate.empty:
                continue

        supabase.table(TABLE_NAME).insert(lead).execute()
        added += 1

    return added

# --- UI LAYOUT ---
st.title("🟢 LinkedIn Lead Database")
st.write("Leads are stored in Supabase and accessible from anywhere.")

html_input = st.text_area("Paste LinkedIn HTML here:", height=200)

if st.button("🚀 Sync Leads"):
    if html_input.strip():
        extracted_list = parse_html(html_input)
        if extracted_list:
            try:
                added = upsert_leads(extracted_list)
                st.success(f"Done! {added} new leads added ({len(extracted_list) - added} duplicates skipped).")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Failed to sync: {e}")
        else:
            st.error("No leads found in the pasted HTML.")
    else:
        st.warning("Please paste HTML first.")

# --- DISPLAY & DOWNLOAD ---
df_display = get_all_leads()

if not df_display.empty:
    st.divider()

    # Only show the useful columns
    display_cols = [c for c in ['name', 'role', 'company', 'created_at'] if c in df_display.columns]
    df_show = df_display[display_cols].copy()

    # Format the timestamp if present
    if 'created_at' in df_show.columns:
        df_show['created_at'] = pd.to_datetime(df_show['created_at']).dt.strftime('%Y-%m-%d %H:%M')

    # Download as Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_show.to_excel(writer, index=False)

    st.download_button(
        label="📥 Download Excel",
        data=output.getvalue(),
        file_name="leads_backup.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.subheader(f"📊 All Leads ({len(df_show)})")
    st.dataframe(df_show, use_container_width=True)
else:
    st.info("No leads yet. Paste LinkedIn HTML above and sync to get started.")
