# noinspection PyInterpreter
import datetime
import time
import pandas as pd
from portfolio_tracker.helper_functions.step1_stocks_get_data import get_data, get_benchmark, create_market_cal
from portfolio_tracker.helper_functions.step2_active_positons import portfolio_start_balance
from portfolio_tracker.helper_functions.step3_time_fill_daily import time_fill
from portfolio_tracker.helper_functions.step4_daily_calcs import per_day_portfolio_calcs
from portfolio_tracker.helper_functions.step5_agg_line_chart import line, line_facets, total_return

# Based on Code - https://towardsdatascience.com/modeling-your-stock-portfolio-performance-with-python-fbba4ef2ef11
if __name__ == '__main__':
    # LOGGER.info("CUSTOM INFO: Script Started...")
    print("CUSTOM INFO: Script Started...")
    # Start Time of Code
    start_time = time.time()

    # Step 1 — Grabbing the Data
    # our buy/sell transaction history
    portfolio_df = pd.read_csv('mfi_log_book.csv')
    portfolio_df['Open Date'] = pd.to_datetime(portfolio_df['Open Date'])
    symbols = portfolio_df.Symbol.unique()
    stocks_start = datetime.datetime(2020, 7, 27)
    stocks_end = datetime.datetime(2020, 8, 12)

    # Daily closes for all tickers in our inventory before the end date specified
    daily_adj_close = get_data(symbols, stocks_start, stocks_end)
    daily_adj_close = daily_adj_close[['Close']].reset_index()

    # Daily closes for our benchmark comparison
    daily_benchmark = get_benchmark(['SPY'], stocks_start, stocks_end)
    daily_benchmark = daily_benchmark[['Date', 'Close']]

    # Contains dates that the market was open in our timeframe
    market_cal = create_market_cal(stocks_start, stocks_end)

    # Step 2 — Finding our Initial Active Portfolio
    # Now that we have these four datasets, we need to figure out how many shares we actively held during the start date
    # specified. Assigning the output to a variable should give you the active positions within your portfolio
    active_portfolio = portfolio_start_balance(portfolio_df, stocks_start)

    # Step 3 — Creating Daily Performance Snapshots
    # Running this line of code should return back a list of all trading days within the time range specified,
    # along with an accurate count of positions per-day
    positions_per_day = time_fill(active_portfolio, market_cal)

    # Step 4 — Making Portfolio Calculations
    # Now that we have an accurate by-day ledger of our active holdings, we can go ahead and create the final
    # calculations needed to generate graphs!
    combined_df = per_day_portfolio_calcs(positions_per_day, daily_benchmark, daily_adj_close, stocks_start)
    combined_df.to_csv("Combined_DF_csv.csv")

    # Step 5 — Visualize the Data
    # The biggest benefit of this daily data is to see how your positions perform over time, so let’s try looking at our
    # data on an aggregated basis first. We’ll supply ticker and benchmark gain/loss as the metrics, then use a groupby
    # to aggregate the daily performance to the portfolio-level
    line(combined_df, 'Stock Gain / (Loss)', 'Benchmark Gain / (Loss)')

    # The most useful view, in my opinion, can be generated by using the facet_col option in plotly express to generate
    # a chart per ticker that compares the benchmark against each ticker’s performance
    line_facets(combined_df, 'Ticker Return', 'Benchmark Return')

    # Provides the absolute return of the portfolio
    total_return(combined_df, 'Ticker Return', 'Benchmark Return')

    # Print Time taken to execute script
    print("CUSTOM INFO: --- Script Execution Time: %s seconds ---" % (time.time() - start_time))
    # LOGGER.info("CUSTOM INFO: --- Script Execution Time: %s seconds ---" % (time.time() - start_time))