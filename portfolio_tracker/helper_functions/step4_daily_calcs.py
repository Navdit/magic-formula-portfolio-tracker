import pandas as pd
import numpy as np


def modified_cost_per_share(portfolio, adj_close, start_date):
    """
    If we want to track daily performance we’ll need to know the theoretical value of our holdings per day.
    This requires taking the amount of securities currently owned and then multiplying it by the daily close for each
    security owned.
    :param portfolio:
    :param adj_close:
    :param start_date:
    :return:
    """
    # To do this, we provide our new single df along with the per-day data we pulled using yfinance, as well as our
    # start date. We’ll then merge our portfolio to the daily close data by joining the date of the portfolio snapshot
    # to the date of the daily data, as well as joining on the ticker. For people more familiar with SQL this is
    # essentially a left join
    df = pd.merge(portfolio, adj_close, left_on=['Date Snapshot', 'Symbol'],
                  right_on=['Date', 'Ticker'], how='left')

    # We’ll rename the daily close to ‘Symbol Adj Close’, and then multiply the daily close by the quantity of shares
    # owned. Dropping extra columns will return the dataframe we need to proceed:
    df.rename(columns={'Close': 'Symbol Adj Close'}, inplace=True)
    df['Adj cost daily'] = df['Symbol Adj Close'] * df['Qty']
    df = df.drop(['Ticker', 'Date'], axis=1)
    return df


def benchmark_portfolio_calcs(portfolio, benchmark):
    """
    We’ll want to add in our benchmark to the dataset in order to make comparisons against our portfolio
    :param portfolio:
    :param benchmark:
    :return:
    """

    # We start by merging our daily benchmark data to the correct snapshots by using a merge similar to the one in
    # modified_cost_per_share
    portfolio = pd.merge(portfolio, benchmark, left_on=['Date Snapshot'],
                         right_on=['Date'], how='left')
    portfolio = portfolio.drop(['Date'], axis=1)
    portfolio.rename(columns={'Close': 'Benchmark Close'}, inplace=True)

    # Now that we have daily closes for our benchmark merged to our portfolio dataset, we’ll filter our daily_benchmark
    # data based on its max and min dates. It’s important to use max and min vs. your start and end date because the
    # max/min will take into account days where the market was open
    benchmark_max = benchmark[benchmark['Date'] == benchmark['Date'].max()]
    portfolio['Benchmark End Date Close'] = portfolio.apply(lambda x: benchmark_max['Close'], axis=1)
    benchmark_min = benchmark[benchmark['Date'] == benchmark['Date'].min()]
    portfolio['Benchmark Start Date Close'] = portfolio.apply(lambda x: benchmark_min['Close'], axis=1)

    # Now we have absolute start and end closes for our benchmark in the portfolio dataset as well, which will be
    # important when calculating returns on a daily basis
    return portfolio


def portfolio_end_of_year_stats(portfolio, adj_close_end):
    """
    Our goal here is to take the output of benchmark_portfolio_calcs, find the last day of close for all the stocks in
    the portfolio, and then add a Ticker End Date Close column to our portfolio dataset. We’ll do this by once again
    merging to the daily stock data, filtering for the max date, and then joining based on the ticker symbol
    :param portfolio:
    :param adj_close_end:
    :return:
    """

    # Merging to the daily stock data, filtering for the max date, and then joining based on the ticker symbol
    adj_close_end = adj_close_end[adj_close_end['Date'] == adj_close_end['Date'].max()]
    portfolio_end_data = pd.merge(portfolio, adj_close_end, left_on='Symbol',
                                  right_on='Ticker')
    portfolio_end_data.rename(columns={'Close': 'Ticker End Date Close'}, inplace=True)
    portfolio_end_data = portfolio_end_data.drop(['Ticker', 'Date'], axis=1)
    return portfolio_end_data


def portfolio_start_of_year_stats(portfolio, adj_close_start):
    """
    Takes the updated portfolio dataframe, the daily stock data from yfinance, and assigns start of year equivalent
    positions for the benchmark
    :param portfolio:
    :param adj_close_start:
    :return:
    """

    # We’ll first filter the daily close data to its beginning date, then merge our portfolio data to it using the
    # ticker symbol. We’ll then call this close Ticker Start Date Close for convenience
    adj_close_start = adj_close_start[adj_close_start['Date'] == adj_close_start['Date'].min()]
    portfolio_start = pd.merge(portfolio, adj_close_start[['Ticker', 'Close', 'Date']],
                               left_on='Symbol', right_on='Ticker')
    portfolio_start.rename(columns={'Close': 'Ticker Start Date Close'}, inplace=True)

    # Then we need to ‘true up’ our adjusted cost per share costs, but why? Imagine you bought Google a long time ago at
    # $500/share, but now you want to calculate YTD returns on your position in 2020. If you use $500 as your cost basis
    # for the beginning of 2020, you’re not going to have an accurate comparison since the cost basis is from years ago.
    # Simply put, this is saying
    #   if the open date is ≤ the date of the start date, then
    #       Adj cost per share is equal to Ticker Start Date Close’ (closing price of the stock from the min date on the
    #       yfinance data).
    #   If not, then
    #       use the existing Adj cost per share
    # To fix this, we’re going to use Numpy’s where function
    portfolio_start['Adj cost per share'] = np.where(portfolio_start['Open Date'] <= portfolio_start['Date'],
                                                     portfolio_start['Ticker Start Date Close'],
                                                     portfolio_start['Adj Cost per Share'])

    # Modifies the adjusted cost based on the modified cost per share, drops unneeded columns from the merge, and then
    # calculates the equivalent amount of benchmarks shares you would have owned based on your newly calculated adjusted
    # cost
    portfolio_start['Adj cost'] = portfolio_start['Adj cost per share'] * portfolio_start['Qty']
    portfolio_start = portfolio_start.drop(['Ticker', 'Date'], axis=1)
    portfolio_start['Equiv Benchmark Shares'] = portfolio_start['Adj cost'] / portfolio_start[
        'Benchmark Start Date Close']
    portfolio_start['Benchmark Start Date Cost'] = portfolio_start['Equiv Benchmark Shares'] * portfolio_start[
        'Benchmark Start Date Close']
    return portfolio_start


def calc_returns(portfolio):
    """
    Takes the aggregated dataframe from all the other functions, applies a bunch of calculations against the data we’ve
    been modifying, and returns a final dataframe
    :param portfolio:
    :return:
    """

    # The first set,Benchmark Return and Ticker Return, both use a current close price divided by their beginning cost
    # basis to calculate a return
    portfolio['Benchmark Return'] = portfolio['Benchmark Close'] / portfolio['Benchmark Start Date Close'] - 1
    portfolio['Ticker Return'] = portfolio['Symbol Adj Close'] / portfolio['Adj cost per share'] - 1

    # Share value for each is calculated the same way, using the modified per-day quantities and equivalent benchmark
    # shares we calculated earlier
    portfolio['Ticker Share Value'] = portfolio['Qty'] * portfolio['Symbol Adj Close']
    portfolio['Benchmark Share Value'] = portfolio['Equiv Benchmark Shares'] * portfolio['Benchmark Close']

    # We’ll do the same thing again to calculate monetary gain/loss, subtracting the share value columns from the
    # modified adjusted cost we calculated in the portfolio_start_of_year_stats function
    portfolio['Stock Gain / (Loss)'] = portfolio['Ticker Share Value'] - portfolio['Adj cost']
    portfolio['Benchmark Gain / (Loss)'] = portfolio['Benchmark Share Value'] - portfolio['Adj cost']

    # we’ll calculate absolute return values using the benchmark metrics we calculated earlier
    portfolio['Abs Value Compare'] = portfolio['Ticker Share Value'] - portfolio['Benchmark Start Date Cost']
    portfolio['Abs Value Return'] = portfolio['Abs Value Compare'] / portfolio['Benchmark Start Date Cost']
    portfolio['Abs. Return Compare'] = portfolio['Ticker Return'] - portfolio['Benchmark Return']

    return portfolio


def per_day_portfolio_calcs(per_day_holdings, daily_benchmark, daily_adj_close, stocks_start):
    """

    :param per_day_holdings:
    :param daily_benchmark:
    :param daily_adj_close:
    :param stocks_start:
    :return:
    """

    # Concatenate our list of dataframes into a single list
    df = pd.concat(per_day_holdings, sort=True)

    # If we want to track daily performance we’ll need to know the theoretical value of our holdings per day.
    # This requires taking the amount of securities currently owned and then multiplying it by the daily close for each
    # security owned.
    mcps = modified_cost_per_share(df, daily_adj_close, stocks_start)

    # Now that we have an accurate daily cost of our securities, we’ll want to add in our benchmark to the dataset in
    # order to make comparisons against our portfolio:
    bpc = benchmark_portfolio_calcs(mcps, daily_benchmark)

    # Our goal here is to take the output of benchmark_portfolio_calcs, find the last day of close for all the stocks in
    # the portfolio, and then add a Ticker End Date Close column to our portfolio dataset. We’ll do this by once again
    # merging to the daily stock data, filtering for the max date, and then joining based on the ticker symbol
    pes = portfolio_end_of_year_stats(bpc, daily_adj_close)

    # This step takes the updated portfolio dataframe, the daily stock data from yfinance, and assigns start of
    # year equivalent positions for the benchmark
    pss = portfolio_start_of_year_stats(pes, daily_adj_close)

    # The final step here simply takes the aggregated dataframe from all the other functions, applies a bunch of
    # calculations against the data we’ve been modifying, and returns a final dataframe
    returns = calc_returns(pss)
    return returns
