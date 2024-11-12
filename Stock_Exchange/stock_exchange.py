import yfinance as yf
import json
import streamlit as st
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM

# A részvényeket tartalmazó JSON fájl betöltése
with open('Stock_Exchange/company_tickers.json') as f:
    company_data = json.load(f)

# Streamlit címek és bevezető szöveg
st.title("Befektetési alkalmazás")
st.subheader("Jelenlegi befektetési adatok:")

# Deep Learning model betöltése
def prepare_data(data, window_size=30):
    X = []
    for i in range(len(data) - window_size):
        X.append(data[i:i+window_size])
    X = np.array(X)
    st.write(X)  # Ellenőrizd a kész adatokat
    return X

def build_model(input_shape):
    model = Sequential([
        LSTM(50, return_sequences=True, input_shape=input_shape),
        LSTM(50),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model

# A részvények elemzése
for key, value in company_data.items():
    ticker = value['ticker']
    
    try:
        # Részvény adatok lekérése a Yahoo Finance API-val
        stock = yf.Ticker(ticker)
        data = stock.history(period="1y")  # Egy évnyi adat
        
        # Ellenőrizd, hogy valóban lekértük az adatokat
        st.write(data)  # Kiíratjuk az adatokat a Streamlit felületre
        
        close_prices = data['Close'].values
        current_price = close_prices[-1]

        # Adatok előkészítése a modell számára
        window_size = 30
        X = prepare_data(close_prices, window_size)
        X = X.reshape((X.shape[0], X.shape[1], 1))

        # Modell létrehozása és betanítása
        model = build_model((X.shape[1], 1))
        model.fit(X, close_prices[window_size:], epochs=50, batch_size=32, verbose=1)

        # Jövőbeli ár előrejelzése
        predicted_price = model.predict(X[-1].reshape(1, X.shape[1], 1))[0][0]
        
        # Kiíratjuk az előrejelzett árat
        st.write(f"Predicted price: {predicted_price}")  # Ellenőrizd, hogy valóban van előrejelzés
        
        # Ajánlás megjelenítése
        if predicted_price > current_price:
            recommendation = "Vásárlás javasolt"
        else:
            recommendation = "Tartás javasolt"

        st.write(f"### {value['title']} ({ticker})")
        st.write(f"**Jelenlegi ár:** {current_price:.2f} USD")
        st.write(f"**Előrejelzett ár:** {predicted_price:.2f} USD")
        st.write(f"**Ajánlás:** {recommendation}")
    
    except Exception as e:
        st.write(f"**API hiba a {ticker} részvénynél:** {e}")
