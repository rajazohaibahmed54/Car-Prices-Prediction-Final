import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import os
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

# ==========================================
# CONFIGURATION
# ==========================================
DATASET_PATH = 'Dataset/Cleaned_Data_Final.csv'
MODEL_PATH = 'model/car_price_model_new.pkl'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def scrape_pakwheels(pages=1):
    """
    Scrapes the first few pages of PakWheels Used Car Search.
    Returns a DataFrame with the new data.
    """
    print(f"🕷️ Starting Scraper (Targeting {pages} pages)...")
    
    scraped_data = []

    for page in range(1, pages + 1):
        url = f"https://www.pakwheels.com/used-cars/search/-/?page={page}"
        print(f"   Fetching URL: {url}")
        
        try:
            response = requests.get(url, headers=HEADERS)
            if response.status_code != 200:
                print("   ❌ Failed to fetch page. Anti-bot might be active.")
                continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            listings = soup.find_all(class_='classified-listing')

            for item in listings:
                try:
                    
                    title = item.find(class_='classified-link').get_text(strip=True)
                    price_text = item.find(class_='price-details').get_text(strip=True)
                    
                    details_ul = item.find(class_='classified-details-list')
                    details = [li.get_text(strip=True) for li in details_ul.find_all('li')]
                    
                    if len(details) >= 5:
                        model_year = details[0] 
                        km = details[1]         
                        fuel = details[2]       
                        cc = details[3]         
                        trans = details[4]      
                        
                        model_name = " ".join(title.split()[:2]) 

                        scraped_data.append({
                            'Model': model_name,
                            'CC': cc,
                            'Engine_type': fuel,
                            'Transmission': trans,
                            'Km_Driven': km,
                            'prices': price_text
                        })
                except AttributeError:
                    continue 
                    
        except Exception as e:
            print(f"   ⚠️ Error scraping page {page}: {e}")

    print(f"✅ Scraped {len(scraped_data)} new cars.")
    return pd.DataFrame(scraped_data)

def clean_price(price_val):
    try:
        if isinstance(price_val, str):
            price_val = price_val.lower().replace('pkr', '').replace(',', '').strip()
            if 'lacs' in price_val or 'lac' in price_val:
                return float(price_val.replace('lacs', '').replace('lac', '')) * 100000
            if 'crore' in price_val:
                return float(price_val.replace('crore', '')) * 10000000
        
        val = float(price_val)
        if val < 10000: return val * 100000 
        return val
    except:
        return None

def clean_cc(cc_text):
    if isinstance(cc_text, str):
        cc_text = cc_text.lower().strip()
        if 'kwh' in cc_text: return None 
        return float(cc_text.replace('cc', '').strip())
    return float(cc_text)

def clean_km(km_text):
    if isinstance(km_text, str):
        return float(km_text.lower().replace('km', '').replace(',', '').strip())
    return float(km_text)

def run_pipeline():
    
    new_data = scrape_pakwheels(pages=1) 
    
    
    if os.path.exists(DATASET_PATH):
        old_data = pd.read_csv(DATASET_PATH)
    else:
        old_data = pd.DataFrame()

    if new_data is not None and not new_data.empty:
        print("🔄 Merging new data with historical dataset...")
        combined_df = pd.concat([old_data, new_data], ignore_index=True)
        combined_df.to_csv(DATASET_PATH, index=False)
        df = combined_df
    else:
        print("⚠️ No new data found. Training on existing dataset only.")
        df = pd.read_csv(DATASET_PATH)

    print(f"🧹 Preprocessing {len(df)} records...")
    df['prices'] = df['prices'].apply(clean_price)
    df['CC'] = df['CC'].apply(clean_cc)
    df['Km_Driven'] = df['Km_Driven'].apply(clean_km)
    df.dropna(subset=['prices', 'CC', 'Km_Driven'], inplace=True)

    
    print("🧠 Training AI Model...")
    X = df[['Model', 'CC', 'Engine_type', 'Transmission', 'Km_Driven']]
    y = df['prices']

    
    categorical_features = ['Model', 'Engine_type', 'Transmission']
    numerical_features = ['CC', 'Km_Driven']

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', 'passthrough', numerical_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ])

    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
    ])

    model.fit(X, y)
    
    # 5. SAVE
    with open(MODEL_PATH, 'wb') as file:
        pickle.dump(model, file)
        
    print(f"✅ SYSTEM UPDATED: Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    run_pipeline()