import pandas as pd
import datetime
import yfinance as yf
import pandas_market_calendars as mcal


# Step 1 — Grabbing the Data
def create_market_cal(stocks_start, stocks_end):
    """
    Uses the pandas_market_calendars library to find all relevant trading days within a specified timeframe.
    This library automatically filters out non-trading days based on the market, so no need to worry about trying to
    join data to invalid dates by using something like pandas.date_range.
    Since all stocks are US-based, so selected NYSE as calendar, and then standardized the timestamps to make them easy
    to join on later.
    :param stocks_start:
    :param stocks_end:
    :return:
    """
    nyse = mcal.get_calendar('NYSE')
    schedule = nyse.schedule(stocks_start, stocks_end)
    market_cal = mcal.date_range(schedule, frequency='1D')
    market_cal = market_cal.tz_localize(None)
    market_cal = [i.replace(hour=0) for i in market_cal]
    return market_cal


def get_data(stocks, start, end):
    """
    Takes an array of stock tickers along with a start and end date, and then grabs the data using the yfinance library.
    You’ll notice the end date parameter includes a timedelta shift, this is because yfinance is exclusive of the end
    date you provide. Since we don’t want to remember this caveat when setting our parameters, we’ll shift the date+1
    here using timedelta.
    :param stocks:
    :param start:
    :param end:
    :return:
    """

    def data(ticker):
        """
        Gets the data of the given ticker
        :param ticker: Unique Stock Code
        :return:
        """
        df = yf.download(ticker, start=start, end=(end + datetime.timedelta(days=1)))
        df['symbol'] = ticker
        df.index = pd.to_datetime(df.index)
        return df

    datas = map(data, stocks)
    return pd.concat(datas, keys=stocks, names=['Ticker', 'Date'], sort=True)


def get_benchmark(benchmark, start, end):
    """
    Function just feeds into get_data and then drops the ticker symbol
    :param benchmark:
    :param start:
    :param end:
    :return:
    """
    benchmark = get_data(benchmark, start, end)
    benchmark = benchmark.drop(['symbol'], axis=1)
    benchmark.reset_index(inplace=True)
    return benchmark
