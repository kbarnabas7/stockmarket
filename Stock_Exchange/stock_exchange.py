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
                                   "Előrejelzett ár (USD)", "Várható hozam (%)", 
                                   "Árváltozás (USD)"])

# Meghatározott befektetési összeg
investment_amount = 500  # Az automatikusan felhasznált befektetési összeg

# Lista a legjobb választás kiválasztásához
best_choice = None
best_investment_score = -float('inf')  # Kezdő érték, hogy találjunk jobb választást

for i, (key, value) in enumerate(company_data.items()):
    if i >= 2000:  # Csak az első 20 részvényt vizsgáljuk
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

        # Százalékos változás kiszámítása
        daily_start_price = stock.history(period="1d")['Open'].iloc[0]
        percent_change = ((current_price - daily_start_price) / daily_start_price) * 100

        # Az automatikus befektetés kiszámítása
        shares_to_buy = investment_amount / current_price

        # Várható hozam kiszámítása (százalékos változás az előrejelzett ár alapján)
        expected_return = ((predicted_price - current_price) / current_price) * 100

        # Befektetési döntési pontozás: figyelembe veszi a várható hozamot
        investment_score = expected_return * 0.5

        # Új sor hozzáadása az eredményekhez
        new_row = {
            "Részvény": value['title'],
            "Ticker": ticker,
            "Jelenlegi ár (USD)": current_price,
            "Előrejelzett ár (USD)": predicted_price,
            "Várható hozam (%)": expected_return,
            "Árváltozás (USD)": predicted_price - current_price
        }

        # Frissítés a táblázatban minden egyes ticker után
        results_df = pd.concat([results_df, pd.DataFrame([new_row])], ignore_index=True)
        results_placeholder.dataframe(results_df)

        # Legjobb választás meghatározása a befektetési pontozás alapján
        if investment_score > best_investment_score:
            best_investment_score = investment_score
            best_choice = new_row
    
    except Exception as e:
        st.error(f"Hiba a(z) {ticker} részvénynél: {e}")

# A legjobb választás megjelenítése
if best_choice:
    st.subheader("Legjobb hosszú távú befektetési lehetőség:")
    st.write(f"Részvény: **{best_choice['Részvény']}**")
    st.write(f"Ticker: **{best_choice['Ticker']}**")
    st.write(f"Jelenlegi ár: **{best_choice['Jelenlegi ár (USD)']:.2f} USD**")
    st.write(f"Előrejelzett ár: **{best_choice['Előrejelzett ár (USD)']:.2f} USD**")
    st.write(f"Várható hozam: **{best_choice['Várható hozam (%)']:.2f}%**")
    st.write(f"Árváltozás (USD): **{best_choice['Árváltozás (USD)']:.2f} USD**")
else:
    st.write("Nincs elérhető részvény, amely megfelel a hosszú távú befektetési feltételeknek.")
