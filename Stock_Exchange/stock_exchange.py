import yfinance as yf
import requests
import time
import streamlit as st
import datetime

# API kulcsok
ALPHA_VANTAGE_API_KEY = '39FFIXLAC9ZYDXNU'
NEWS_API_KEY = '616d0278d29440c49cd70793f7c4ea49'
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
    return data['Close'].iloc[-1], data['Open'].iloc[0]  # Záró és nyitó árak

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
        # Ne írjon ki semleges döntést
        return None  # Ne vegyük meg most

# 5. Befektetési logika: most vásárlás, a következő vásárlás a hét első napján
def invest():
    """
    Befektetési döntés alapján elvégzi a vásárlásokat.
    Az e heti vásárlás most történik, a következő hétfőn következik.
    """
    global total_investment, cash_on_hand

    # Mai dátum
    today = datetime.date.today()

    # Csak hétfőn történjen új vásárlás, most az e heti vásárlás történik
    if today.weekday() == 0:  # Hétfő
        st.write("Ma új vásárlás történik, mivel hétfő van.")

        for ticker in ["TSLA", "NVDA"]:
            # Döntés a vásárlásról
            decision = make_decision(ticker)
            stock_data, open_price = get_stock_data(ticker)

            if decision is not None:
                if cash_on_hand >= investment_per_stock:
                    cash_on_hand -= investment_per_stock  # Használjuk fel a készpénzt
                    total_investment += investment_per_stock  # Növeljük a befektetett összeget

                    # Részvény vásárlása
                    investment_history[ticker].append({
                        'investment': investment_per_stock,
                        'purchase_price': stock_data,
                        'date': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                    })
                    st.write(f"Részvény vásárlás megtörtént: {ticker}, Ár: {stock_data}, Befektetett összeg: {investment_per_stock}")

    # Kiírjuk a jelenlegi befektetéseket és azok állapotát
    st.write("\nJelenlegi befektetési adatok:")
    for ticker, investments in investment_history.items():
        total_investment_ticker = sum([i['investment'] for i in investments])
        st.write(f"{ticker}: {total_investment_ticker} USD")

# 6. Visszaszámláló a következő vásárlásig (következő hétfő)
def countdown_to_next_monday():
    today = datetime.date.today()
    next_monday = today + datetime.timedelta(days=(7 - today.weekday()))  # Következő hétfő
    time_left = next_monday - today  # Idő különbség a következő hétfőig

    st.write(f"A legközelebbi vásárlásig ({next_monday}) {time_left.days} nap van hátra.")

# Streamlit UI
st.title("Befektetési alkalmazás")
st.write("A rendszer azonnal végrehajtja a vásárlást, és az élő részvényadatokat mutatja.")

# Befektetési döntés
invest()

# Visszaszámláló a következő vásárlásig
countdown_to_next_monday()

# Használjuk az empty() metódust a dinamikus frissítéshez
tsla_price = st.empty()
nvda_price = st.empty()

# Kezdeti árak tárolása
previous_tsla_price = get_stock_data("TSLA")[0]
previous_nvda_price = get_stock_data("NVDA")[0]

while True:
    tsla_new_price, tsla_open_price = get_stock_data("TSLA")
    nvda_new_price, nvda_open_price = get_stock_data("NVDA")

    # Frissítsük az árat, ha változott
    if tsla_new_price != previous_tsla_price:
        tsla_price.markdown(
            f'TESLA Ár: <span style="color: green; font-weight: bold;">{tsla_new_price}</span> '
            f'Változás: {((tsla_new_price - tsla_open_price) / tsla_open_price) * 100:.2f}%',
            unsafe_allow_html=True
        )
        time.sleep(1)  # 1 másodpercig zöld, majd vissza
        tsla_price.markdown(f'TESLA Ár: {tsla_new_price} USD')

    if nvda_new_price != previous_nvda_price:
        nvda_price.markdown(
            f'NVDA Ár: <span style="color: green; font-weight: bold;">{nvda_new_price}</span> '
            f'Változás: {((nvda_new_price - nvda_open_price) / nvda_open_price) * 100:.2f}%',
            unsafe_allow_html=True
        )
        time.sleep(1)  # 1 másodpercig zöld, majd vissza
        nvda_price.markdown(f'NVDA Ár: {nvda_new_price} USD')
