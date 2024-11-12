import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.model_selection import GridSearchCV
from sklearn.base import BaseEstimator, RegressorMixin
import time

# KerasRegressor osztály
class KerasRegressor(BaseEstimator, RegressorMixin):
    def __init__(self, build_fn, batch_size=32, epochs=10):
        self.build_fn = build_fn
        self.batch_size = batch_size
        self.epochs = epochs

    def fit(self, X, y, **kwargs):
        self.model = self.build_fn(X, batch_size=self.batch_size, epochs=self.epochs)
        self.model.fit(X, y, **kwargs)
        return self

    def predict(self, X):
        return self.model.predict(X)

# Funkciók a pénzügyi és gazdasági adatok betöltéséhez
def load_financial_data(stock_ticker="AAPL", start_date="2023-01-01", end_date="2024-01-01"):
    stock_data = yf.download(stock_ticker, start=start_date, end=end_date)
    stock_data['Returns'] = stock_data['Close'].pct_change()
    stock_data['Volatility'] = stock_data['Close'].pct_change().rolling(window=14).std()
    stock_data.dropna(inplace=True)
    X = stock_data[['Close', 'Volatility', 'Returns']].values
    y = stock_data['Close'].shift(-1).dropna().values
    X = X[:-1]
    return X, y

# Modell felépítése
def build_model(X, batch_size=32, epochs=3):
    model = Sequential([
        LSTM(50, return_sequences=True, input_shape=(X.shape[1], 1)),
        LSTM(50),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model

# Keresés legjobb paraméterek után
param_grid = {
    'batch_size': [8, 16, 32, 64],
    'epochs': [3,5,10, 20, 30]
}

model = KerasRegressor(build_fn=build_model, batch_size=32, epochs=10)
grid_search = GridSearchCV(estimator=model, param_grid=param_grid, n_jobs=-1, cv=3)

# Szimulációs funkció
def simulate_investment(X, y, model, tickers, investment_amount=100):
    results = []
    for ticker in tickers:
        X_ticker, y_ticker = load_financial_data(stock_ticker=ticker)
        predictions = model.predict(X_ticker)
        profit = (predictions[-1] - y_ticker[-1]) / y_ticker[-1] * 100
        results.append((ticker, profit))
    
    results.sort(key=lambda x: x[1], reverse=True)
    best_ticker = results[0]
    best_ticker_name = best_ticker[0]
    profit = best_ticker[1]
    
    # A 100$-os befektetés szimulálása
    invested_amount = investment_amount * (1 + profit / 100)
    
    return best_ticker_name, profit, invested_amount

# Streamlit alkalmazás
def main():
    st.title("Részvény előrejelzés és szimulált befektetés")
    st.write("Ez az alkalmazás bemutatja, hogyan lehet a részvények árfolyamát előrejelezni gazdasági adatok alapján, és szimulálja a 100$ befektetést.")

    # Modell tanítása
    if st.button("Kezd el a tanulást"):
        with st.spinner('Modell tanítása folyamatban...'):
            X, y = load_financial_data(stock_ticker="AAPL")
            grid_search_result = grid_search.fit(X, y, callbacks=[EarlyStopping(monitor='loss', patience=5, restore_best_weights=True)])

            best_params = grid_search_result.best_params_
            best_score = grid_search_result.best_score_
            st.write(f"Legjobb paraméterek: {best_params}")
            st.write(f"Legjobb eredmény: {best_score:.4f}")

            st.success("A modell megtanulta a legjobb paramétereket!")

    # Befektetés szimulálása
    if st.button("Szimulálj befektetést 100$-val"):
        st.write("Befektetés szimulálása...")
        X, y = load_financial_data(stock_ticker="AAPL")
        grid_search_result = grid_search.fit(X, y, callbacks=[EarlyStopping(monitor='loss', patience=5, restore_best_weights=True)])

        best_ticker, profit, invested_amount = simulate_investment(X, y, grid_search_result.best_estimator_, tickers=["AAPL", "GOOG", "MSFT", "AMZN", "TSLA", "NFLX", "FB", "NVDA", "DIS", "BA"])
        
        st.write(f"A legjobb részvény: {best_ticker}")
        st.write(f"Profit: {profit:.2f}%")
        st.write(f"Végső összeg: {invested_amount:.2f} $")

if __name__ == "__main__":
    main()
