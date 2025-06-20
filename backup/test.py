from vnstock import Vnstock
stock = Vnstock().stock(symbol='VCI', source='VCI')
stock.quote.history(start='2020-01-01', end='2024-05-25')
print(stock.quote.history(start='2020-01-01', end='2024-05-25'))
stock.quote.intraday(symbol='ACB', page_size=10_000, show_log=False)
print(stock.quote.intraday(symbol='ACB', page_size=10_000, show_log=False))