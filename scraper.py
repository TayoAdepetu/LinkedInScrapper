import os
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

# To run this, paste the html in leads.html and run the following consecutively:
# 1. source venv/bin/activate
# 2. python3 scraper.py
# Then the script will save the leads to extracted_leads.xlsx without 
# duplicates and without deleting what we have there already

# 1. Configuration
INPUT_FILE = 'leads.html'
OUTPUT_FILE = 'extracted_leads.xlsx'

def parse_html_to_list(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    leads_data = []
    items = soup.find_all('li', class_='artdeco-list__item')
    
    timestamp = datetime.now().strftime("%Y-%m-%d") # Simplified date
    
    for item in items:
        # Extract Name
        name_tag = item.find('span', class_='a11y-text')
        name = name_tag.get_text(strip=True).replace('Add ', '').replace(' to selection', '') if name_tag else "Unknown"
        
        # Extract Role
        title_tag = item.find('span', {'data-anonymize': 'title'})
        
        # Extract Company
        company_tag = item.find('a', {'data-anonymize': 'company-name'})
        
        leads_data.append({
            'Name': name,
            'Role': title_tag.get_text(strip=True) if title_tag else "N/A",
            'Company': company_tag.get_text(strip=True) if company_tag else "N/A"
        })
    
    return leads_data

def save_and_append_to_excel(new_data_list):
    df_new = pd.DataFrame(new_data_list)
    path = os.path.join(os.getcwd(), OUTPUT_FILE)
    
    if os.path.exists(path):
        df_existing = pd.read_excel(path, engine='openpyxl')
        df_final = pd.concat([df_existing, df_new], ignore_index=True)
        # De-duplicate based on Name and Company to avoid double-counting
        df_final = df_final.drop_duplicates(subset=['Name', 'Company'], keep='first')
        print(f"Adding {len(df_new)} new leads...")
    else:
        df_final = df_new
        print(f"Creating new Excel file...")

    df_final.to_excel(path, index=False, engine='openpyxl')
    print(f"✅ Success! Total leads in file: {len(df_final)}")

if __name__ == "__main__":
    if os.path.exists(INPUT_FILE):
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            html = f.read()
            
        if not html.strip():
            print("Wait! 'leads.html' is empty. Paste your HTML first.")
        else:
            leads = parse_html_to_list(html)
            if leads:
                save_and_append_to_excel(leads)
            else:
                print("❌ No leads found in the HTML format provided.")
    else:
        # Create the file if it doesn't exist to make it easier for the user
        open(INPUT_FILE, 'w').close()
        print(f"Created '{INPUT_FILE}'. Please paste your HTML inside it and run again.")