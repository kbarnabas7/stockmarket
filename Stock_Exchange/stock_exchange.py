import yfinance as yf
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import streamlit as st

# A részvényeket tartalmazó JSON fájl betöltése
with open('Stock_Exchange/company_tickers.json') as f:
    company_data = json.load(f)

# Streamlit címek
st.title("Befektetési alkalmazás")
st.subheader("Elemzett részvények adatai")

# Adatok előkészítése és egyszerű modell használata
def prepare_data(data, window_size=30):
    X, y = [], []
    for i in range(len(data) - window_size):
        X.append(data[i:i + window_size])
        y.append(data[i + window_size])
    return np.array(X), np.array(y)

def build_model():
    return LinearRegression()

# Hely fenntartása a dinamikus táblázathoz
results_placeholder = st.empty()

# Eredmények tárolása egy DataFrame-ben
results_df = pd.DataFrame(columns=["Részvény", "Ticker", "Jelenlegi ár (USD)", 
                                   "Előrejelzett ár (USD)", "Ajánlás", 
                                   "Változás (%)", "Befektetett összeg (USD)", 
                                   "Részvény mennyiség", "Árváltozás (USD)"])

# Meghatározott befektetési összeg
investment_amount = 500  # Az automatikusan felhasznált befektetési összeg

# Lista a legnagyobb előrejelzett árváltozást mutató részvényekhez
best_choice = None
max_price_change = -float('inf')  # Kezdő érték, hogy találjunk nagyobb árváltozást

for i, (key, value) in enumerate(company_data.items()):
    if i >= 20:  # Csak az első 20 részvényt vizsgáljuk
        break
    
    ticker = value['ticker']
    
    try:
        # Részvény adatok lekérése a Yahoo Finance API-val
        stock = yf.Ticker(ticker)
        data = stock.history(period="1y")

        if data.empty:
            st.warning(f"Nincs elérhető adat a(z) {ticker} részvényhez.")
            continue
        
        close_prices = data['Close'].values
        current_price = close_prices[-1]

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
        daily_start_price = stock.history(period="1d")['Open'].iloc[0]
        percent_change = ((current_price - daily_start_price) / daily_start_price) * 100

        # Az automatikus befektetés kiszámítása
        # Hány darab részvényt vehetünk a $500-os befektetéssel?
        shares_to_buy = investment_amount / current_price

        # Árváltozás (USD) kiszámítása
        price_change = predicted_price - current_price

        # Új sor hozzáadása az eredményekhez
        new_row = {
            "Részvény": value['title'],
            "Ticker": ticker,
            "Jelenlegi ár (USD)": current_price,
            "Előrejelzett ár (USD)": predicted_price,
            "Ajánlás": recommendation,
            "Változás (%)": percent_change,
            "Befektetett összeg (USD)": investment_amount,
            "Részvény mennyiség": shares_to_buy,
            "Árváltozás (USD)": price_change
        }
        results_df = pd.concat([results_df, pd.DataFrame([new_row])], ignore_index=True)

        # Legnagyobb árváltozás keresése
        if price_change > max_price_change:
            max_price_change = price_change
            best_choice = new_row
    
    except Exception as e:
        st.error(f"Hiba a(z) {ticker} részvénynél: {e}")

# Táblázat frissítése
results_placeholder.dataframe(results_df)

# A legjobb választás megjelenítése
if best_choice:
    st.subheader("Legjobb befektetési lehetőség:")
    st.write(f"Részvény: **{best_choice['Részvény']}**")
    st.write(f"Ticker: **{best_choice['Ticker']}**")
    st.write(f"Jelenlegi ár: **{best_choice['Jelenlegi ár (USD)']:.2f} USD**")
    st.write(f"Előrejelzett ár: **{best_choice['Előrejelzett ár (USD)']:.2f} USD**")
    st.write(f"Várt árváltozás: **{best_choice['Árváltozás (USD)']:.2f} USD**")
    st.write(f"Befektetett összeg: **{best_choice['Befektetett összeg (USD)']} USD**")
    st.write(f"Vásárolható részvények száma: **{best_choice['Részvény mennyiség']:.2f} db**")
