import threading
import time
import schedule
import pyupbit
import pandas as pd
import datetime
import logging

logging.basicConfig(filename='trading_bot.log', level=logging.ERROR)

class Worker(threading.Thread):
    """
    Thread for running trading strategies.
    """
    def __init__(self, _upbit, _method):
        super().__init__()
        self._kill = threading.Event()
        self._upbit = _upbit
        self._method = _method
        self.ticker = "KRW-BTC"
        self.one_time = True

    def run(self):
        """
        Start the thread and execute the selected trading strategy.
        """
        while not self._kill.is_set():
            print(f'[{datetime.datetime.now()}] Running strategy {self._method}')
            if self._method == 1:
                a_volatility_strategy(self.ticker, self._upbit)
            elif self._method == 2:
                bollinger_band(self.ticker, self._upbit)
            elif self._method == 3:
                self.five_ten_strategy()
            time.sleep(10)

    def kill(self):
        self._kill.set()

    def five_ten_strategy(self):
        """ 5-10 Moving Average Crossover Strategy """
        try:
            schedule.run_pending()
            now = datetime.datetime.now()
            start_time = get_start_time(self.ticker)

            if start_time < now < start_time + datetime.timedelta(minutes=1) and self.one_time:
                krw = get_balance(self._upbit, "KRW")
                btc = get_balance(self._upbit, self.ticker[4:])
                current_price = get_current_price(self.ticker)

                if krw > 5000 and chk(self.ticker):
                    self._upbit.buy_market_order(self.ticker, krw * 0.9995)
                    self.one_time = False
                elif btc > 0.00008 and not chk(self.ticker):
                    self._upbit.sell_market_order(self.ticker, btc * 0.9995)
                    self.one_time = False
                else:
                    print(f"Insufficient balance: KRW = {krw}, BTC = {btc}")
            else:
                self.one_time = True
        except Exception as e:
            logging.error(f"Exception in fiveTen strategy: {e}", exc_info=True)


def a_volatility_strategy(_ticker, _upbit):
    """ Volatility Breakout Strategy """
    try:
        now = datetime.datetime.now()
        start_time = get_start_time(_ticker)
        end_time = start_time + datetime.timedelta(days=1)
        schedule.run_pending()

        if start_time < now < end_time - datetime.timedelta(seconds=10):
            target_price = get_target_price(_ticker, 0.5)
            current_price = get_current_price(_ticker)
            if target_price < current_price:
                krw = get_balance(_upbit, "KRW")
                if krw > 5000:
                    _upbit.buy_market_order(_ticker, krw * 0.9995)
                else:
                    print(f"Insufficient balance: KRW = {krw}")
        else:
            ticker_balance = get_balance(_upbit, _ticker[4:])
            if int(current_price * ticker_balance) > 5000:
                _upbit.sell_market_order(_ticker, ticker_balance * 0.9995)
    except Exception as e:
        logging.error(f"Exception in a_volatility_strategy: {e}", exc_info=True)


def bollinger_band(_ticker, _upbit):
    """ Bollinger Band Strategy """
    cnt = 20
    k = 2
    try:
        schedule.run_pending()
        current_price = get_current_price(_ticker)
        krw = get_balance(_upbit, "KRW")
        ticker_balance = get_balance(_upbit, _ticker[4:])

        if krw > 5000:
            bbh = calculate_bollinger_band(_ticker, "minute60", cnt, k)
            if bbh.iloc[21]['close'] < bbh.iloc[21]['lower'] * 0.985 and bbh.iloc[19]['close'] < bbh.iloc[19]['lower']:
                bbm = calculate_bollinger_band(_ticker, "minute15", cnt, k)
                if bbm.iloc[21]['close'] < bbm.iloc[21]['lower'] * 0.985 and bbh.iloc[19]['close'] < bbh.iloc[19]['lower']:
                    _upbit.buy_market_order(_ticker, krw * 0.9999)
        elif int(current_price * ticker_balance) > 5000:
            if current_price < get_valuation_gain_loss(_upbit, _ticker[4:]) * 1.015:
                _upbit.sell_market_order(_ticker, ticker_balance * 0.9995)
        else:
            print(f"Insufficient balance: KRW = {krw}")
    except Exception as e:
        logging.error(f"Exception in bollinger_band: {e}", exc_info=True)


def chk(_ticker):
    """ Check if MA(5) > MA(10) """
    df = pyupbit.get_ohlcv(_ticker, interval="minute10", count=11)
    ma5 = df['close'].rolling(window=5).mean().iloc[-1]
    ma10 = df['close'].rolling(window=10).mean().iloc[-1]
    return ma5 > ma10


def get_target_price(ticker, k):
    """ Set target price for buying """
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price


def get_start_time(ticker):
    """ Get market start time """
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    return df.index[0]


def get_current_price(ticker):
    """ Get current price """
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]


def get_balance(_upbit, ticker):
    """ Get balance of specific ticker """
    balances = _upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
    return 0


def get_valuation_gain_loss(_upbit, ticker):
    """ Get valuation gain/loss """
    balances = _upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['avg_buy_price'] is not None:
                return float(b['avg_buy_price'])
    return 0


def calculate_bollinger_band(ticker, interval, cnt=20, k=2):
    """ Calculate Bollinger Bands """
    df = pyupbit.get_ohlcv(ticker, interval=interval, count=cnt + 2)
    df['mid'] = df['close'].rolling(window=cnt).mean()
    df['std'] = df['close'].rolling(window=cnt).std()
    df['upper'] = df['mid'] + (df['std'] * k)
    df['lower'] = df['mid'] - (df['std'] * k)
    return df.reset_index()
