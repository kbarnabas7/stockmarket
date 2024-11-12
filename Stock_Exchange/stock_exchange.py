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
st.subheader("Befektetési ajánlások 100 USD összeggel")

investment_options = []

def prepare_data(data, window_size=30):
    X = []
    for i in range(len(data) - window_size):
        X.append(data[i:i + window_size])
    return np.array(X)

def build_model(input_shape):
    model = Sequential([
        LSTM(50, return_sequences=True, input_shape=input_shape),
        LSTM(50),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model

def get_google_news_sentiment(ticker):
    # Ezt cseréld le egy valós Google News sentiment analízisre
    sentiment_score = np.random.uniform(0, 1)
    return sentiment_score

# A részvények elemzése
for key, value in company_data.items():
    ticker = value['ticker']
    st.write(f"Elemzés alatt: {value['title']} ({ticker})")
    
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1y")
        
        if data.empty:
            st.write(f"Nincs elérhető adat {ticker} számára.")
            continue
        
        close_prices = data['Close'].values
        current_price = close_prices[-1]
        
        window_size = 30
        X = prepare_data(close_prices, window_size)
        X = X.reshape((X.shape[0], X.shape[1], 1))
        
        model = build_model((X.shape[1], 1))
        model.fit(X, close_prices[window_size:], epochs=50, batch_size=32, verbose=1)

        
        predicted_price = model.predict(X[-1].reshape(1, X.shape[1], 1))[0][0]
        sentiment_score = get_google_news_sentiment(ticker)
        
        st.write(f"Jelenlegi ár: {current_price:.2f} USD, "
                 f"Előrejelzett ár: {predicted_price:.2f} USD, "
                 f"Sentiment: {sentiment_score:.2f}")
        
        if predicted_price > current_price * 0.95 and sentiment_score > 0.4:
            investment_options.append({
                "title": value['title'],
                "ticker": ticker,
                "current_price": current_price,
                "predicted_price": predicted_price,
                "sentiment": sentiment_score
            })
    
    except Exception as e:
        st.write(f"**API hiba a {ticker} részvénynél:** {e}")

# Kiíratás csak az ajánlott befektetésekről
if not investment_options:
    st.write("Nincs megfelelő befektetési célpont az adott feltételek mellett.")
else:
    st.write("Ajánlott befektetések:")
    for option in investment_options:
        amount_invested = 100
        shares_bought = amount_invested / option["current_price"]
        st.write(f"### {option['title']} ({option['ticker']})")
        st.write(f"- **Jelenlegi ár:** {option['current_price']:.2f} USD")
        st.write(f"- **Előrejelzett ár:** {option['predicted_price']:.2f} USD")
        st.write(f"- **Sentiment:** {option['sentiment']:.2f}")
        st.write(f"- **Vásárolt részvénymennyiség:** {shares_bought:.4f} részvény")
