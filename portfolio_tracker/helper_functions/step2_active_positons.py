import pandas as pd


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
