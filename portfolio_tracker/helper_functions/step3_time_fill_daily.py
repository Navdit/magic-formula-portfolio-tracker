import pandas as pd
from portfolio_tracker.helper_functions.step2_active_positons import position_adjust


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
