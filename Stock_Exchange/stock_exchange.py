import yfinance as yf
import json
import streamlit as st
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM
from sklearn.preprocessing import MinMaxScaler
import requests

# A részvényeket tartalmazó JSON fájl betöltése
with open('Stock_Exchange/company_tickers.json') as f:
    company_data = json.load(f)

# Google News API Key (helyettesítsd a saját API-kulcsoddal)
GOOGLE_NEWS_API_KEY = '10e31d449a6ee61bf16205871ce36194344edb72dbb2e94a08b4d55750d3d4ed'
NEWS_ENDPOINT = 'https://newsapi.org/v2/everything'

# Streamlit címek és bevezető szöveg
st.title("Befektetési alkalmazás")
st.subheader("Ajánlott befektetések (100 USD)")

# Deep Learning model betöltése
def prepare_data(data, window_size=30):
    scaler = MinMaxScaler(feature_range=(0, 1))
    data_scaled = scaler.fit_transform(data.reshape(-1, 1))
    
    X, y = [], []
    for i in range(len(data_scaled) - window_size):
        X.append(data_scaled[i:i+window_size])
        y.append(data_scaled[i+window_size])
    return np.array(X), np.array(y), scaler

def build_model(input_shape):
    model = Sequential([
        LSTM(50, return_sequences=True, input_shape=input_shape),
        LSTM(50),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model

def fetch_news(ticker):
    """Lekéri a híreket egy adott részvényhez."""
    params = {
        'q': ticker,
        'apiKey': GOOGLE_NEWS_API_KEY,
        'language': 'en',
        'sortBy': 'relevancy'
    }
    response = requests.get(NEWS_ENDPOINT, params=params)
    if response.status_code == 200:
        articles = response.json().get('articles', [])
        return articles
    else:
        return []

def analyze_news(articles):
    """Elemzi a híreket, és egyszerű pontszámot ad vissza."""
    score = 0
    positive_keywords = ['growth', 'increase', 'profit', 'gain', 'success']
    negative_keywords = ['loss', 'decrease', 'decline', 'risk', 'drop']
    
    for article in articles:
        title = article['title'].lower()
        content = (article.get('content') or '').lower()
        for keyword in positive_keywords:
            if keyword in title or keyword in content:
                score += 1
        for keyword in negative_keywords:
            if keyword in title or keyword in content:
                score -= 1
    return score

best_investment = None
best_growth = -np.inf

# A részvények elemzése
for key, value in company_data.items():
    ticker = value['ticker']
    
    try:
        # Részvény adatok lekérése a Yahoo Finance API-val
        stock = yf.Ticker(ticker)
        data = stock.history(period="1y")  # Egy évnyi adat

        if data.empty:
            continue
        
        close_prices = data['Close'].values
        current_price = close_prices[-1]

        # Adatok előkészítése a modell számára
        window_size = 30
        X, y, scaler = prepare_data(close_prices, window_size)
        X = X.reshape((X.shape[0], X.shape[1], 1))

        # Modell létrehozása és betanítása
        model = build_model((X.shape[1], 1))
        model.fit(X, y, epochs=50, batch_size=32, verbose=0)

        # Jövőbeli ár előrejelzése
        predicted_price_scaled = model.predict(X[-1].reshape(1, X.shape[1], 1))[0][0]
        predicted_price = scaler.inverse_transform([[predicted_price_scaled]])[0][0]

        # Növekedési arány kiszámítása
        growth_rate = (predicted_price - current_price) / current_price * 100

        # Hírek elemzése
        articles = fetch_news(ticker)
        news_score = analyze_news(articles)

        # Kombinált értékelés
        combined_score = growth_rate + news_score

        if combined_score > best_growth:
            best_growth = combined_score
            best_investment = {
                "title": value['title'],
                "ticker": ticker,
                "current_price": current_price,
                "predicted_price": predicted_price,
                "growth_rate": growth_rate,
                "news_score": news_score,
                "combined_score": combined_score
            }
    
    except Exception as e:
        st.write(f"Hiba a(z) {ticker} részvénynél: {e}")

# Legjobb befektetés kiíratása
if best_investment:
    st.subheader("Ajánlott befektetés:")
    st.write(f"### {best_investment['title']} ({best_investment['ticker']})")
    st.write(f"**Jelenlegi ár:** {best_investment['current_price']:.2f} USD")
    st.write(f"**Előrejelzett ár:** {best_investment['predicted_price']:.2f} USD")
    st.write(f"**Növekedési arány:** {best_investment['growth_rate']:.2f}%")
    st.write(f"**Hírek alapján számított pontszám:** {best_investment['news_score']}")
    st.write(f"**Kombinált pontszám:** {best_investment['combined_score']:.2f}")
    
    # Tört részvény vásárlása
    shares_to_buy = 100 / best_investment['current_price']
    st.write(f"**100 USD-ból vásárolható részvények száma:** {shares_to_buy:.4f}")
else:
    st.write("Nincs elérhető befektetési ajánlás.")
