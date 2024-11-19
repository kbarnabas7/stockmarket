import yfinance as yf
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import MinMaxScaler
import time

# A részvényeket tartalmazó JSON fájl betöltése
with open('Stock_Exchange/company_tickers.json') as f:
    company_data = json.load(f)

# Adatok előkészítése és egyszerű modell használata mozgóátlaggal vagy lineáris regresszióval
def prepare_data(data, window_size=30):
    X, y = [], []
    for i in range(len(data) - window_size):
        X.append(data[i:i + window_size])
        y.append(data[i + window_size])
    return np.array(X), np.array(y)

def build_model():
    return LinearRegression()

# Eredmények tárolása egy DataFrame-ben
results_df = pd.DataFrame(columns=["Részvény", "Ticker", "Jelenlegi ár (USD)", 
                                   "Előrejelzett ár (USD)", "Ajánlás", 
                                   "Változás (%)"])

for i, (key, value) in enumerate(company_data.items()):
    if i >= 20:
        break  # Csak az első 20 részvényt vizsgáljuk
    
    ticker = value['ticker']
    
    try:
        # Részvény adatok lekérése a Yahoo Finance API-val
        stock = yf.Ticker(ticker)
        data = stock.history(period="1y")  # Egy évnyi adat

        if data.empty:
            print(f"Nincs elérhető adat a(z) {ticker} részvényhez.")
            continue
        
        close_prices = data['Close'].values
        current_price = close_prices[-1]
        daily_start_price = stock.history(period="1d")['Open'].iloc[0]

        # Adatok előkészítése és modell betanítása
        window_size = 30
        X, y = prepare_data(close_prices, window_size)
        model = build_model()
        model.fit(X, y)

        # Jövőbeli ár előrejelzése
        predicted_price = model.predict([close_prices[-window_size:]])[0]

        # Ajánlás meghatározása
        recommendation = "Vásárlás javasolt" if predicted_price > current_price else "Tartás javasolt"

        # Százalékos változás kiszámítása
        percent_change = ((current_price - daily_start_price) / daily_start_price) * 100

        # Új sor hozzáadása az eredményekhez
        new_row = {
            "Részvény": value['title'],
            "Ticker": ticker,
            "Jelenlegi ár (USD)": current_price,
            "Előrejelzett ár (USD)": predicted_price,
            "Ajánlás": recommendation,
            "Változás (%)": percent_change
        }
        results_df = pd.concat([results_df, pd.DataFrame([new_row])], ignore_index=True)
    
    except Exception as e:
        print(f"Hiba a(z) {ticker} részvénynél: {e}")

# Eredmények kiírása
print(results_df)
