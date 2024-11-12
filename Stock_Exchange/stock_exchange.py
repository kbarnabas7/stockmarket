import yfinance as yf
import requests
import time
import streamlit as st
import datetime

# API kulcsok
ALPHA_VANTAGE_API_KEY = 'KOXMHR58ZK1JGSKV'
NEWS_API_KEY = '755a59d332454cd58d7371c962b51734'
NEWS_API_URL = 'https://newsapi.org/v2/everything'

# Befektetett pénz és nyereség
investment_per_stock = 100  # Befektetett összeg részvényenként
investment_history = {"TSLA": [], "NVDA": []}  # Részvényekhez kapcsolódó befektetési adatok
total_investment = 0  # Összes befektetett pénz
cash_on_hand = 500  # Készpénz a további befektetésekhez (több készpénz a teszteléshez)

# 1. Részvény árfolyamának lekérése a Yahoo Finance API-ból
def get_stock_data(ticker):
    """
    Lekéri a részvény napi árait.
    """
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d")
    if not data.empty:
        return data['Close'].iloc[-1], data['Open'].iloc[0]  # Záró és nyitó árak
    else:
        st.write(f"Nem található árfolyam adat a(z) {ticker} részvényhez.")
        return None, None

# 2. Gazdasági mutatók lekérése az Alpha Vantage API-ból
def get_economic_indicators():
    """
    Lekéri a gazdasági mutatókat (például GDP és kamatláb).
    """
    url = f'https://www.alphavantage.co/query'
    params = {
        'function': 'ECO_INDICATOR',
        'indicator': 'GDP',
        'apikey': ALPHA_VANTAGE_API_KEY
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Ha nem sikerült a kérés, hibát dob
        data = response.json()
        gdp_growth = data.get('GDP_growth', None)  # GDP növekedés
        return gdp_growth
    except requests.exceptions.RequestException as e:
        st.write(f"API hiba: {e}")
        return None

# 3. Hírek lekérése a NewsAPI segítségével
def get_news(query):
    """
    Lekéri a legfrissebb híreket a megadott témában.
    """
    params = {
        'q': query,
        'apiKey': NEWS_API_KEY,
        'language': 'en',
        'sortBy': 'publishedAt',
        'pageSize': 5
    }

    try:
        response = requests.get(NEWS_API_URL, params=params)
        response.raise_for_status()  # Ha nem sikerült a kérés, hibát dob
        news_data = response.json()
        if news_data.get('status') == 'ok' and news_data['articles']:
            news_titles = [article['title'] for article in news_data['articles']]
            return news_titles
    except requests.exceptions.RequestException as e:
        st.write(f"API hiba: {e}")
        return []
    return []

# 4. Döntéshozatal a hírek és gazdasági mutatók alapján
def make_decision(ticker):
    """
    Döntéshozatal a hírek és gazdasági mutatók alapján.
    """
    stock_data, open_price = get_stock_data(ticker)
    if stock_data is None:
        return None
    news_titles = get_news(ticker)
    gdp_growth = get_economic_indicators()

    # Hírek elemzése: ha van növekedési hír, az pozitív jel
    positive_news = any("growth" in title.lower() or "increase" in title.lower() for title in news_titles)
    negative_news = any("decline" in title.lower() or "fall" in title.lower() for title in news_titles)

    # Gazdasági mutatók elemzése: ha a GDP növekedés pozitív, az jó jel
    positive_economy = gdp_growth and gdp_growth > 2  # Példa: GDP növekedés > 2%

    current_price = stock_data

    # Döntés logikája
    if positive_news and positive_economy:
        st.write(f"Jó időpont a vásárlásra: {ticker}, Ára: {current_price}")
        return True  # Vásárlásra javasolt
    elif negative_news:
        st.write(f"Eladásra érdemes: {ticker}, Ára: {current_price}")
        return False  # Eladásra javasolt
    else:
        return None  # Ne vegyük meg most

# 5. Befektetési logika
def invest():
    """
    Befektetési döntés alapján elvégzi a vásárlásokat.
    """
    global total_investment, cash_on_hand

    for ticker in ["TSLA", "NVDA"]:
        decision = make_decision(ticker)
        stock_data, _ = get_stock_data(ticker)

        if decision is not None and cash_on_hand >= investment_per_stock:
            cash_on_hand -= investment_per_stock
            total_investment += investment_per_stock
            investment_history[ticker].append({
                'investment': investment_per_stock,
                'purchase_price': stock_data,
                'date': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            })
            st.write(f"Részvény vásárlás megtörtént: {ticker}, Ár: {stock_data}, Befektetett összeg: {investment_per_stock}")

    st.write("\nJelenlegi befektetési adatok:")
    for ticker, investments in investment_history.items():
        total_investment_ticker = sum([i['investment'] for i in investments])
        st.write(f"{ticker}: {total_investment_ticker} USD")

# 6. Visszaszámláló a következő vásárlásig
def countdown_to_next_monday():
    today = datetime.date.today()
    next_monday = today + datetime.timedelta(days=(7 - today.weekday()))
    time_left = next_monday - today

    st.write(f"A legközelebbi vásárlásig ({next_monday}) {time_left.days} nap van hátra.")

# Streamlit UI
st.title("Befektetési alkalmazás")
st.write("A rendszer azonnal végrehajtja a vásárlást, és az élő részvényadatokat mutatja.")

invest()
countdown_to_next_monday()

# Kezdő árfolyamok lekérdezése
tsla_price = get_stock_data("TSLA")[0]
nvda_price = get_stock_data("NVDA")[0]

# Streamlit elemző táblázatok
st.write(f"TESLA (TSLA) kezdő ár: {tsla_price} USD")
st.write(f"NVDA kezdő ár: {nvda_price} USD")
