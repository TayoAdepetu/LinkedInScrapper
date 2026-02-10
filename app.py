import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from bs4 import BeautifulSoup
from io import BytesIO

# --- PAGE CONFIG ---
st.set_page_config(page_title="LinkedIn Google Sheets DB", page_icon="🟢")

# --- GOOGLE SHEETS CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

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
            'Name': name,
            'Role': title_tag.get_text(strip=True) if title_tag else "N/A",
            'Company': company_tag.get_text(strip=True) if company_tag else "N/A"
        })
    return new_leads

def read_existing_data():
    """Safely read existing data from Google Sheets, returning empty DF if sheet is empty."""
    try:
        existing = conn.read(worksheet="Sheet1", usecols=[0, 1, 2])
        existing = existing.dropna(how="all")
        return existing
    except Exception:
        # Sheet is empty or not yet initialized — return empty DataFrame
        return pd.DataFrame(columns=['Name', 'Role', 'Company'])

# --- UI LAYOUT ---
st.title("🟢 Google Sheets Lead Database")
st.write("Leads are synced directly to your private Google Sheet.")

html_input = st.text_area("Paste HTML code here:", height=200)

if st.button("🚀 Sync to Google Sheets"):
    if html_input.strip():
        extracted_list = parse_html(html_input)
        if extracted_list:
            # 1. Fetch current data from Google Sheets (safely)
            existing_data = read_existing_data()
            
            # 2. Prepare new data
            df_new = pd.DataFrame(extracted_list)
            
            # 3. Combine and De-duplicate
            df_final = pd.concat([existing_data, df_new], ignore_index=True)
            df_final = df_final.drop_duplicates(subset=['Name', 'Company'], keep='first')
            
            # 4. Update the Google Sheet
            try:
                conn.update(worksheet="Sheet1", data=df_final)
                st.success(f"Successfully synced {len(extracted_list)} leads!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Failed to write to Google Sheet: {e}")
                st.info("Make sure the Google Sheet is set to 'Anyone with the link' → **Editor**.")
        else:
            st.error("No leads found in the pasted HTML.")
    else:
        st.warning("Please paste HTML first.")

# --- DISPLAY & DOWNLOAD ---
df_display = read_existing_data()

if not df_display.empty:
    st.divider()
    
    # Download as Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_display.to_excel(writer, index=False)
        
    st.download_button(
        label="📥 Download local Excel backup",
        data=output.getvalue(),
        file_name="leads_backup.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    st.subheader(f"Stored in Cloud ({len(df_display)} leads)")
    st.dataframe(df_display, use_container_width=True)
else:
    st.info("No leads yet. Paste LinkedIn HTML above and sync to get started.")
