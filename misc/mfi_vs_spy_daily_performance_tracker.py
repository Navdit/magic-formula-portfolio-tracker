# noinspection PyInterpreter
import time
import pandas as pd
import numpy as np
import datetime
import yfinance as yf
import pandas_market_calendars as mcal
from bokeh.plotting import figure, output_file, show
from bokeh.models import ColumnDataSource, DatetimeTickFormatter


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


#  Step 2 — Finding our Initial Active Portfolio
def position_adjust(daily_positions, sale):
    """

    :param daily_positions:
    :param sale:
    :return:
    """
    # First, we’ll create an empty dataframe called stocks_with_sales where we’ll later add adjusted positions, and
    # another dataframe holding all of the transactions labeled as ‘buys’
    # Remember that we already filtered out ‘buys in the future’ in the portfolio_start_balance function, so no need
    # to do it again here. You’ll also notice that we’re sorting by ‘Open Date’, and that will be important given we
    # want to subtract positions using the FIFO method. By sorting the dates, we know we can move iteratively through a
    # list of old-to-new positions
    stocks_with_sales = pd.DataFrame()
    buys_before_start = daily_positions[daily_positions['Type'] == 'Buy'].sort_values(by='Open Date')

    # Now that we have all buys in a single dataframe, we’re going to filter for all buys where the stock symbol
    # matches the stock symbol of the sold position.
    # You’ll notice that we’re using indexing to access the ‘Symbol’ column in our data. That’s because using iterrows()
    # creates a tuple from the index [0] and the series of data [1]. This is the same reason we’ll use indexing when we
    # loop through buys_before_start.
    # So what’s happening in the loop here is that for every buy in buys_before_start:
    #   If the quantity of the oldest buy amount is ≤ the sold quantity (you sold more than your initial purchase amnt),
    #       subtract the amount of the buy position from the sell,
    #       then set the buy quantity to 0
    #   Else (the amount you bought on a certain day > the quantity sold),
    #       subtract the sales quantity from the buy position,
    #       then subtract that same amount from the sales position
    #   Append that adjusted position to our empty stock_with_sales dataframe
    for position in buys_before_start[buys_before_start['Symbol'] == sale[1]['Symbol']].iterrows():
        if position[1]['Qty'] <= sale[1]['Qty']:
            sale[1]['Qty'] -= position[1]['Qty']
            position[1]['Qty'] = 0
        else:
            position[1]['Qty'] -= sale[1]['Qty']
            sale[1]['Qty'] -= sale[1]['Qty']
        stocks_with_sales = stocks_with_sales.append(position[1])
    return stocks_with_sales


def portfolio_start_balance(portfolio, start_date):
    """

    :param portfolio:
    :param start_date:
    :return:
    """
    # First, we supply our CSV data and start date to the portfolio_start_balance function and create a dataframe of all
    # trades that happened before our start date. We’ll then check to see if there are future sales after the start_date
    # since we will reconstruct a snapshot of this dataframe in the end
    positions_before_start = portfolio[portfolio['Open Date'] <= start_date]
    future_sales = portfolio[(portfolio['Open Date'] >= start_date) & (portfolio['Type'] == 'Sell')]

    # We’ll then create a dataframe of sales that occurred before the start_date. We need to make sure that these are
    # all factored out of our active portfolio on the specified start_date
    sales = positions_before_start[positions_before_start['Type'] == 'Sell'].groupby(['Symbol'])['Qty'].sum()
    sales = sales.reset_index()

    # Next, we’ll make a final dataframe of positions that did not have any sales occur over the specified time period
    positions_no_change = positions_before_start[~positions_before_start['Symbol'].isin(sales['Symbol'].unique())]
    adj_positions_df = pd.DataFrame()

    # Now we’ll loop through every sale in our sales dataframe, call our position_adjust function, and then append the
    # output of that into our empty adj_postitions_df
    for sale in sales.iterrows():
        adj_positions = position_adjust(positions_before_start, sale)
        adj_positions_df = adj_positions_df.append(adj_positions)

    # Once loops (for position in buys_before_start[buys_before_start['Symbol'] == sale[1]['Symbol']].iterrows())
    # goes through every sales position your code will now execute the final lines:
    adj_positions_df = adj_positions_df.append(positions_no_change)
    adj_positions_df = adj_positions_df.append(future_sales)
    adj_positions_df = adj_positions_df[adj_positions_df['Qty'] > 0]

    # So we’re taking our adjusted positions in adj_positions_df, adding back positions that never had sales, adding
    # back sales that occur in the future, and finally filtering out any rows that position_adjust zeroed out.
    # You should now have an accurate record of your active holdings as of the start date!
    return adj_positions_df


# Step 3 — Creating Daily Performance Snapshots.
# So now that we have an accurate statement of positions held at the start date, let’s create daily performance data!
# Our strategy is similar to what we did in step 2, in fact, we’ll re-use the position_adjust method again since we’ll
# need to account for potential sales within our date range. We’ll go ahead and create two new functions, time_fill and
# fifo
def fifo(daily_positions, sales, date):
    """
    Takes your active portfolio positions, the sales dataframe created in time_fill, and the
    current date in the market_cal list
    :param daily_positions:
    :param sales:
    :param date:
    :return:
    """
    # Our fifo function takes your active portfolio positions, the sales dataframe created in time_fill, and the
    # current date in the market_cal list. It then filters sales to find any that have occurred on the current date,
    # and create a dataframe of positions not affected by sales
    sales = sales[sales['Open Date'] == date]
    daily_positions = daily_positions[daily_positions['Open Date'] <= date]
    positions_no_change = daily_positions[~daily_positions['Symbol'].isin(sales['Symbol'].unique())]

    # We’ll then use our trusty position_adjust function to zero-out any positions with active sales. If there were no
    # sales for the specific date, our function will simply append the positions_no_change onto the empty adj_positions
    # dataframe, leaving you with an accurate daily snapshot of positions:
    adj_positions = pd.DataFrame()
    for sale in sales.iterrows():
        adj_positions = adj_positions.append(position_adjust(daily_positions, sale))
    adj_positions = adj_positions.append(positions_no_change)
    adj_positions = adj_positions[adj_positions['Qty'] > 0]
    return adj_positions


def time_fill(portfolio, market_cal):
    """

    :param portfolio:
    :param market_cal:
    :return:
    """

    # Similar to portfolio_start_balance, our goal is to provide our dataframe of active positions, find the sales, and
    # zero-out sales against buy positions. The main difference here is that we are going to loop through using our
    # market_cal list with valid trading days
    sales = portfolio[portfolio['Type'] == 'Sell'].groupby(['Symbol', 'Open Date'])['Qty'].sum()
    sales = sales.reset_index()
    per_day_balance = []
    for date in market_cal:
        if (sales['Open Date'] == date).any():
            portfolio = fifo(portfolio, sales, date)

        # This way we can go day-by-day and see if any sales occurred, adjust positions correctly, and then return a
        # correct snapshot of the daily data. In addition, we’ll also filter to positions that have occurred before or
        # at the current date and make sure there are only buys. We’ll then add a Date Snapshot column with the current
        # date in the market_cal loop, then append it to our per_day_balance list
        daily_positions = portfolio[portfolio['Open Date'] <= date]
        daily_positions = daily_positions[daily_positions['Type'] == 'Buy']
        daily_positions['Date Snapshot'] = date
        per_day_balance.append(daily_positions)
    return per_day_balance


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


def set_graph_and_legend_properties(plot_graph: figure(), graph_title: str) -> figure():
    """
    Sets the Properties of the graph and the legend of the graph
    :param plot_graph:
    :param legends:
    :param graph_title:
    :return:
    """
    # Add Tool - Hovertool
    # Hover Tool Properties
    # @Todo - Add hovertool tips
    # hover_tool_tips = set_hover_tool_tips()
    # plot_graph.add_tools(hover_tool_tips)

    # Remove Logo
    plot_graph.toolbar.logo = None

    # Legend related formatting
    # legend = Legend(items=legends, location=(0, 0))
    plot_graph.legend.click_policy = "hide"
    plot_graph.legend.background_fill_color = "#2F2F2F"
    plot_graph.legend.label_text_color = "white"
    plot_graph.legend.border_line_color = "#2F2F2F"
    plot_graph.legend.inactive_fill_color = "#2F2F2F"
    plot_graph.legend.location = "top_left"
    # plot_graph.add_layout(legend, 'right')

    # X-Axis related formatting
    plot_graph.xgrid.grid_line_color = "white"
    plot_graph.xgrid.grid_line_dash = [6, 4]
    plot_graph.xgrid.grid_line_alpha = .3
    plot_graph.xaxis.axis_line_color = "white"
    plot_graph.xaxis.axis_label_text_color = "white"
    plot_graph.xaxis.major_label_text_color = "white"
    plot_graph.xaxis.major_tick_line_color = "white"
    plot_graph.xaxis.minor_tick_line_color = "white"
    plot_graph.xaxis.formatter = DatetimeTickFormatter(microseconds=["%b '%y"],
                                                       milliseconds=["%b '%y"],
                                                       seconds=["%b '%y"],
                                                       minsec=["%b '%y"],
                                                       minutes=["%b '%y"],
                                                       hourmin=["%b '%y"],
                                                       hours=["%b '%y"],
                                                       days=["%b '%y"],
                                                       months=["%b '%y"],
                                                       years=["%b '%y"])

    # Y-axis related formatting
    plot_graph.ygrid.grid_line_color = "white"
    plot_graph.ygrid.grid_line_dash = [6, 4]
    plot_graph.ygrid.grid_line_alpha = .3
    plot_graph.yaxis.axis_line_color = "white"
    plot_graph.yaxis.axis_label_text_color = "white"
    plot_graph.yaxis.major_label_text_color = "white"
    plot_graph.yaxis.major_tick_line_color = "white"
    plot_graph.yaxis.minor_tick_line_color = "white"

    # Graph related Formatting
    plot_graph.min_border_left = 80
    plot_graph.title.text = graph_title
    plot_graph.title.text_color = "white"
    plot_graph.title.text_font = "times"
    plot_graph.title.text_font_style = "normal"
    plot_graph.title.text_font_size = "14pt"
    plot_graph.title.align = "center"
    plot_graph.background_fill_color = '#2F2F2F'
    plot_graph.border_fill_color = '#2F2F2F'
    plot_graph.outline_line_color = '#444444'

    return plot_graph


def mfi_vs_spy(df, val_1, val_2):
    """
    Takes your completed dataframe and two metrics you want to plot against each other
    :param df:
    :param val_1:
    :param val_2:
    :return:
    """
    grouped_metrics = df.groupby(['Date Snapshot'])[[val_1, val_2]].sum().reset_index()
    # grouped_metrics.to_csv("grouped_metrics_1.csv")
    output_file("mfi_vs_spy.html")
    source = ColumnDataSource(grouped_metrics)

    fig = figure(x_axis_label="Time",
                 x_axis_type="datetime",
                 y_axis_label="%age Return",
                 toolbar_location="below",
                 tools="reset",
                 sizing_mode='scale_both')

    fig.line(x="Date Snapshot",
             y=val_1,
             source=source,
             line_width=2,
             line_color="green",
             legend_label="MFI",
             name="mfi")

    fig.line(x="Date Snapshot",
             y=val_2,
             source=source,
             line_width=2,
             line_color="red",
             legend_label="SPY",
             name="s&p")

    set_graph_and_legend_properties(fig, "MFI vs S&P500")

    show(fig)


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
    stocks_start = datetime.datetime(2020, 7, 24)  # On 24th July 2020 first 30 stocks of MFI were bought
    # stocks_end = datetime.datetime(2020, 8, 10)
    stocks_end = datetime.date.today() - datetime.timedelta(days=1)  # Returns are calculated to one previous day
    # print(stocks_end)

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
    # combined_df.to_csv("Combined_DF_csv.csv")

    # # Step 5 — Visualize the Data
    # # The biggest benefit of this daily data is to see how your positions perform over time, so let’s try looking at our
    # # data on an aggregated basis first. We’ll supply ticker and benchmark gain/loss as the metrics, then use a groupby
    # # to aggregate the daily performance to the portfolio-level
    # line(combined_df, 'Stock Gain / (Loss)', 'Benchmark Gain / (Loss)')
    #
    # # The most useful view, in my opinion, can be generated by using the facet_col option in plotly express to generate
    # # a chart per ticker that compares the benchmark against each ticker’s performance
    # line_facets(combined_df, 'Ticker Return', 'Benchmark Return')

    # Provides the absolute return of the portfolio
    # total_return(combined_df, 'Ticker Return', 'Benchmark Return')

    # Bokeh graph
    mfi_vs_spy(combined_df, 'Ticker Return', 'Benchmark Return')

    # Print Time taken to execute script
    print("CUSTOM INFO: --- Script Execution Time: %s seconds ---" % (time.time() - start_time))
    # LOGGER.info("CUSTOM INFO: --- Script Execution Time: %s seconds ---" % (time.time() - start_time))
