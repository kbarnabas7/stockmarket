import yfinance as yf
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import streamlit as st
import os
import logging

# Naplózási rendszer beállítása
logging.basicConfig(
    filename="Stock_Exchange/stock_app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# JSON fájl validálása
json_file_path = 'Stock_Exchange/company_tickers.json'
if not os.path.exists(json_file_path):
    st.error("A company_tickers.json fájl nem található!")
    logging.error("A company_tickers.json fájl nem található!")
    st.stop()

# Részvényeket tartalmazó JSON fájl betöltése
with open(json_file_path) as f:
    try:
        company_data = json.load(f)
    except json.JSONDecodeError as e:
        st.error("Hiba a JSON fájl beolvasása során!")
        logging.error(f"Hiba a JSON fájl beolvasása során: {e}")
        st.stop()

# Streamlit címek
st.title("Befektetési alkalmazás")
st.subheader("Elemzett részvények adatai")

# Befektetési összeg beállítása
investment_amount = st.number_input(
    "Adja meg a befektetési összeget (USD):",
    min_value=100.0, value=500.0, step=50.0
)

# Adatok előkészítése
def prepare_data(data, window_size=30):
    X, y = [], []
    for i in range(len(data) - window_size):
        X.append(data[i:i + window_size])
        y.append(data[i + window_size])
    return np.array(X), np.array(y)

# Lineáris regressziós modell létrehozása
def build_model():
    return LinearRegression()

# Hely fenntartása a táblázathoz és grafikonhoz
results_placeholder = st.empty()
chart_placeholder = st.empty()

# Eredmények tárolása
results_df = pd.DataFrame(columns=["Részvény", "Ticker", "Jelenlegi ár (USD)",
                                   "Előrejelzett ár (USD)", "P/E arány",
                                   "Dividend Yield", "Volatilitás",
                                   "Befektetett összeg (USD)", "Részvény mennyiség",
                                   "Várható hozam (%)", "Árváltozás (USD)"])

best_choice = None
best_investment_score = -float('inf')  # Legjobb befektetési pontszám

for i, (key, value) in enumerate(company_data.items()):
    if i >= 20:  # Csak az első 20 részvényt vizsgáljuk
        break

    ticker = value['ticker']
    try:
        # Részvény adatok lekérése
        stock = yf.Ticker(ticker)
        data = stock.history(period="1y")

        if data.empty:
            st.warning(f"Nincs elérhető adat a(z) {ticker} részvényhez.")
            logging.warning(f"Nincs adat a(z) {ticker} részvényhez.")
            continue

        close_prices = data['Close'].values
        current_price = close_prices[-1]

        # Modell betanítása
        window_size = 30
        X, y = prepare_data(close_prices, window_size)
        model = build_model()
        model.fit(X, y)
        predicted_price = model.predict([close_prices[-window_size:]])[0]

        # Kiegészítő adatok
        pe_ratio = stock.info.get('trailingPE', 0)  # P/E arány
        dividend_yield = stock.info.get('dividendYield', 0)  # Osztalék hozam
        volatility = np.std(close_prices)  # Volatilitás

        # Százalékos változás
        daily_start_price = stock.history(period="1d")['Open'].iloc[0]
        percent_change = ((current_price - daily_start_price) / daily_start_price) * 100

        # Részvények számának kiszámítása
        shares_to_buy = investment_amount / current_price

        # Várható hozam
        expected_return = ((predicted_price - current_price) / current_price) * 100

        # Befektetési pontszám
        investment_score = expected_return * 0.5 + dividend_yield * 0.3 - volatility * 0.2

        # Új eredmény hozzáadása
        new_row = {
            "Részvény": value['title'],
            "Ticker": ticker,
            "Jelenlegi ár (USD)": current_price,
            "Előrejelzett ár (USD)": predicted_price,
            "P/E arány": pe_ratio,
            "Dividend Yield": dividend_yield,
            "Volatilitás": volatility,
            "Befektetett összeg (USD)": investment_amount,
            "Részvény mennyiség": shares_to_buy,
            "Várható hozam (%)": expected_return,
            "Árváltozás (USD)": predicted_price - current_price
        }
        results_df = pd.concat([results_df, pd.DataFrame([new_row])], ignore_index=True)

        # Legjobb választás
        if investment_score > best_investment_score:
            best_investment_score = investment_score
            best_choice = new_row

    except Exception as e:
        st.error(f"Hiba a(z) {ticker} részvénynél: {e}")
        logging.error(f"Hiba a(z) {ticker} részvénynél: {e}")

# Táblázat és grafikon frissítése
results_placeholder.dataframe(results_df)
if not results_df.empty:
    chart_placeholder.line_chart(results_df[["Jelenlegi ár (USD)", "Előrejelzett ár (USD)"]])

# Legjobb választás megjelenítése
if best_choice:
    st.subheader("Legjobb befektetési lehetőség:")
    for key, value in best_choice.items():
        st.write(f"**{key}**: {value:.2f}" if isinstance(value, (float, int)) else f"**{key}**: {value}")
else:
    st.write("Nincs megfelelő részvény.")
