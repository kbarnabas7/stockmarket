import yfinance as yf
import json
import streamlit as st
import numpy as np
import pandas as pd
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM
from sklearn.preprocessing import MinMaxScaler
import time

# A részvényeket tartalmazó JSON fájl betöltése
with open('Stock_Exchange/company_tickers.json') as f:
    company_data = json.load(f)

# Streamlit címek és bevezető szöveg
st.title("Befektetési alkalmazás")
st.subheader("Jelenlegi befektetési adatok (maximum 20 részvény):")

# Üres hely lefoglalása a táblázat számára
table_placeholder = st.empty()

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

# Eredmények tárolása egy DataFrame-ben
results_df = pd.DataFrame(columns=["Részvény", "Ticker", "Jelenlegi ár (USD)", 
                                   "Előrejelzett ár (USD)", "Ajánlás", 
                                   "Aktuális ár (USD)", "Változás (%)"])

# A részvények elemzése (csak az első 20 elem)
for i, (key, value) in enumerate(company_data.items()):
    if i >= 20:
        break  # Csak az első 20 részvényt vizsgáljuk
    
    ticker = value['ticker']
    
    try:
        # Részvény adatok lekérése a Yahoo Finance API-val
        stock = yf.Ticker(ticker)
        data = stock.history(period="1y")  # Egy évnyi adat

        if data.empty:
            st.write(f"Nincs elérhető adat a(z) {ticker} részvényhez.")
            continue
        
        close_prices = data['Close'].values
        current_price = close_prices[-1]
        daily_start_price = stock.history(period="1d")['Open'].iloc[0]

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
            "Aktuális ár (USD)": current_price,
            "Változás (%)": percent_change
        }
        results_df = pd.concat([results_df, pd.DataFrame([new_row])], ignore_index=True)

        # Táblázat frissítése
        table_placeholder.dataframe(results_df)
    
    except Exception as e:
        st.write(f"**Hiba a(z) {ticker} részvénynél:** {e}")

# Dinamikus árfrissítés
while True:
    for index, row in results_df.iterrows():
        try:
            # Új ár lekérése
            stock = yf.Ticker(row["Ticker"])
            live_data = stock.history(period="1d")
            new_price = live_data['Close'].iloc[-1]
            daily_start_price = live_data['Open'].iloc[0]

            # Százalékos változás újraszámítása
            percent_change = ((new_price - daily_start_price) / daily_start_price) * 100

            # Ár frissítése és színezése
            if new_price != row["Aktuális ár (USD)"]:
                results_df.at[index, "Aktuális ár (USD)"] = f"**:green[{new_price:.2f}]**"
                results_df.at[index, "Változás (%)"] = f"**:green[{percent_change:.2f}%]**"
                table_placeholder.dataframe(results_df)
                time.sleep(1)  # Zöld szín egy másodpercig
                results_df.at[index, "Aktuális ár (USD)"] = new_price
                results_df.at[index, "Változás (%)"] = percent_change
        
        except Exception as e:
            st.write(f"**Hiba az ár frissítésekor:** {e}")
    
    # Táblázat frissítése
    table_placeholder.dataframe(results_df)
    time.sleep(5)  # Új árak frissítése 5 másodpercenként
