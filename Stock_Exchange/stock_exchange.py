import yfinance as yf

ticker = yf.Ticker("TSLA")
print(ticker.history(period="1d"))
