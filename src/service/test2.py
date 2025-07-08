import yfinance as yf


def get_imoex_price():
    """
    Получает последнюю цену индекса IMOEX (IMOEX.ME).
    :return: Цена индекса, округленная до двух знаков после запятой.
    """
    imoex_data = yf.Ticker("IMOEX.ME")
    imoex_price = imoex_data.history(period="1d", interval="5m")['Close']
    return round(imoex_price, 2) if imoex_price is not None else None


# Пример использования функции
if __name__ == "__main__":
    imoex_price = get_imoex_price()
    print(f"Последняя цена индекса IMOEX: {imoex_price}")
