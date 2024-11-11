import yfinance as yf
import requests
import time

# API kulcsok
ALPHA_VANTAGE_API_KEY = '39FFIXLAC9ZYDXNU'
NEWS_API_KEY = '616d0278d29440c49cd70793f7c4ea49'
NEWS_API_URL = 'https://newsapi.org/v2/everything'

# Befektetett pénz és nyereség
investment_per_stock = 100  # Befektetett összeg részvényenként
investment_history = {"TSLA": [], "NVDA": []}  # Részvényekhez kapcsolódó befektetési adatok
total_investment = 0  # Összes befektetett pénz
cash_on_hand = 0  # Készpénz a további befektetésekhez

# 1. Részvény árfolyamának lekérése a Yahoo Finance API-ból
def get_stock_data(ticker):
    """
    Lekéri a részvény napi árait.
    """
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d")
    return data['Close'].iloc[-1]  # Az utolsó napi záró ár

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
    response = requests.get(url, params=params)
    data = response.json()
    gdp_growth = data.get('GDP_growth', None)  # GDP növekedés
    return gdp_growth

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

    response = requests.get(NEWS_API_URL, params=params)
    news_data = response.json()
    if news_data.get('status') == 'ok' and news_data['articles']:
        news_titles = [article['title'] for article in news_data['articles']]
        return news_titles
    return []

# 4. Döntéshozatal a hírek és gazdasági mutatók alapján
def make_decision(ticker):
    """
    Döntéshozatal a hírek és gazdasági mutatók alapján.
    """
    stock_data = get_stock_data(ticker)
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
        print(f"Jó időpont a vásárlásra: {ticker}, Ára: {current_price}")
        return True  # Vásárlásra javasolt
    elif negative_news:
        print(f"Eladásra érdemes: {ticker}, Ára: {current_price}")
        return False  # Eladásra javasolt
    else:
        print(f"Semleges döntés: {ticker}, Ára: {current_price}")
        return None  # Ne vegyük meg most

# 5. Részvények eladása, ha a veszteség túl nagy, de hírek figyelembevételével
def sell_stock_if_needed(ticker, purchase_price):
    """
    Eladja a részvényt, ha a veszteség meghaladja a 10%-ot,
    de nem adja el, ha a hírek arra utalnak, hogy hamarosan növekedhet.
    """
    current_price = get_stock_data(ticker)
    loss_percentage = (current_price - purchase_price) / purchase_price * 100
    news_titles = get_news(ticker)
    
    # Ha a veszteség több mint 10%, és nincsenek pozitív hírek, akkor eladjuk
    if loss_percentage <= -10 and not any("growth" in title.lower() or "increase" in title.lower() for title in news_titles):
        print(f"Eladás: {ticker}, Vásárlási ár: {purchase_price}, Jelenlegi ár: {current_price}, Veszteség: {loss_percentage:.2f}%")
        return current_price  # Eladjuk a részvényt, és visszakapjuk a pénzt
    elif loss_percentage <= -10:
        print(f"Veszteség van: {ticker}, Vásárlási ár: {purchase_price}, Jelenlegi ár: {current_price}, Veszteség: {loss_percentage:.2f}%, de pozitív hír van.")
        return None  # Ne adjuk el, mert lehet, hogy emelkedni fog
    return None  # Nincs eladás

# 6. Befektetési logika: hetente 100 dollár befektetés, eladás, ha szükséges
def invest():
    """
    Befektetési döntés alapján elvégzi a vásárlásokat.
    Hetente egyszer befektet.
    """
    global total_investment, cash_on_hand

    for ticker in ["TSLA", "NVDA"]:
        # Eladjuk a részvényt, ha túl sokat csökkent az ára
        for investment in investment_history[ticker]:
            sell_price = sell_stock_if_needed(ticker, investment['purchase_price'])
            if sell_price:
                cash_on_hand += investment['investment'] * sell_price / investment['purchase_price']
                total_investment -= investment['investment']  # Az eladás után csökkentjük a befektetett pénzt

        # Döntés a következő heti vásárlásról
        decision = make_decision(ticker)
        stock_data = get_stock_data(ticker)

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

    # Kiírjuk a jelenlegi befektetéseket és azok állapotát
    print("\nJelenlegi befektetési adatok:")
    for ticker, investments in investment_history.items():
        total_investment = sum([inv['investment'] for inv in investments])
        current_value = sum([inv['investment'] * get_stock_data(ticker) / inv['purchase_price'] for inv in investments])
        print(f"\n{ticker}:")
        print(f"Befektetett összeg: {total_investment}$")
        print(f"Jelenlegi érték: {current_value:.2f}$")
        print(f"Nyereség: {current_value - total_investment:.2f}$")

    print(f"\nKészpénz: {cash_on_hand}$")
