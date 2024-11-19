import yfinance as yf
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import streamlit as st
import requests
from bs4 import BeautifulSoup

def get_news_from_api(ticker):
    api_key = 'e81c3cf2fceb4e7390fefff1892da5cf'  # Itt add meg a saját API kulcsodat
    url = f'https://newsapi.org/v2/everything?q={ticker}&apiKey={api_key}'

    try:
        response = requests.get(url)
        data = response.json()

        if response.status_code != 200 or 'articles' not in data:
            return ["Nem sikerült lekérni a híreket."]
        
        # Az első 5 hír címének kiírása
        articles = data['articles'][:5]
        news_list = [f"{article['title']} - {article['source']['name']}" for article in articles]
        return news_list

    except Exception as e:
        return [f"Hiba történt a hírek lekérésekor: {e}"]
# A részvényeket tartalmazó JSON fájl betöltése
with open('Stock_Exchange/company_tickers.json') as f:
    company_data = json.load(f)

st.title("Befektetési alkalmazás")
st.subheader("Elemzett részvények adatai")

def prepare_data(data, window_size=30):
    X, y = [], []
    for i in range(len(data) - window_size):
        X.append(data[i:i + window_size])
        y.append(data[i + window_size])
    return np.array(X), np.array(y)

def build_model():
    return LinearRegression()

results_placeholder = st.empty()

results_df = pd.DataFrame(columns=["Részvény", "Ticker", "Jelenlegi ár (USD)", 
                                   "Előrejelzett ár (USD)", "Ajánlás", 
                                   "Változás (%)"])

for i, (key, value) in enumerate(company_data.items()):
    if i >= 2000:
        break
    
    ticker = value['ticker']
    
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1y")
        if data.empty:
            st.warning(f"Nincs elérhető adat a(z) {ticker} részvényhez.")
            continue
        
        close_prices = data['Close'].values
        current_price = close_prices[-1]
        daily_start_price = stock.history(period="1d")['Open'].iloc[0]

        window_size = 30
        X, y = prepare_data(close_prices, window_size)
        model = build_model()
        model.fit(X, y)
        predicted_price = model.predict([close_prices[-window_size:]])[0]
        recommendation = "Vásárlás javasolt" if predicted_price > current_price else "Tartás javasolt"
        percent_change = ((current_price - daily_start_price) / daily_start_price) * 100

        new_row = {
            "Részvény": value['title'],
            "Ticker": ticker,
            "Jelenlegi ár (USD)": current_price,
            "Előrejelzett ár (USD)": predicted_price,
            "Ajánlás": recommendation,
            "Változás (%)": percent_change
        }
        results_df = pd.concat([results_df, pd.DataFrame([new_row])], ignore_index=True)
        
        results_placeholder.dataframe(results_df)
    
    except Exception as e:
        st.error(f"Hiba a(z) {ticker} részvénynél: {e}")

if not results_df.empty:
    results_df['Árváltozás (USD)'] = results_df['Előrejelzett ár (USD)'] - results_df['Jelenlegi ár (USD)']
    max_change_row = results_df.loc[results_df['Árváltozás (USD)'].idxmax()]
    
    st.subheader("Legnagyobb várható árváltozás:")
    st.write(f"**{max_change_row['Részvény']} ({max_change_row['Ticker']})**: "
             f"{max_change_row['Árváltozás (USD)']:.2f} USD különbség "
             f"(Jelenlegi ár: {max_change_row['Jelenlegi ár (USD)']:.2f} USD, "
             f"Előrejelzett ár: {max_change_row['Előrejelzett ár (USD)']:.2f} USD)")

# Legnagyobb változás magyarázata
# Legnagyobb változás magyarázata
st.subheader("Legnagyobb változás magyarázata:")
news = get_news_from_api(max_change_row['Ticker'])
if news:
    for item in news:
        st.write(f"- {item}")
else:
    st.write("Nem érhető el releváns információ a változás okairól.")
