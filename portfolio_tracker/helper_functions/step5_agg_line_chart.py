import pandas as pd
import plotly.express as px
from plotly.offline import plot
from bokeh.plotting import figure, output_file, show
from bokeh.models import ColumnDataSource

from portfolio_tracker.helper_functions.bokeh_helpers import plot_new_graph, set_graph_and_legend_properties


def line(df, val_1, val_2):
    """
    Takes your completed dataframe and two metrics you want to plot against each other
    :param df:
    :param val_1:
    :param val_2:
    :return:
    """
    grouped_metrics = df.groupby(['Date Snapshot'])[[val_1, val_2]].sum().reset_index()
    grouped_metrics = pd.melt(grouped_metrics, id_vars=['Date Snapshot'],
                              value_vars=[val_1, val_2])
    grouped_metrics.to_csv("grouped_metrics.csv")
    fig = px.line(grouped_metrics, x="Date Snapshot", y="value",
                  color='variable')
    plot(fig)


def line_facets(df, val_1, val_2):
    """
    Generate a chart per ticker that compares the benchmark against each ticker’s performance
    :param df:
    :param val_1:
    :param val_2:
    :return:
    """
    grouped_metrics = df.groupby(['Symbol', 'Date Snapshot'])[[val_1, val_2]].sum().reset_index()
    grouped_metrics = pd.melt(grouped_metrics, id_vars=['Symbol', 'Date Snapshot'],
                              value_vars=[val_1, val_2])
    fig = px.line(grouped_metrics, x="Date Snapshot", y="value",
                  color='variable', facet_col="Symbol", facet_col_wrap=5)
    plot(fig)


def total_return(df, val_1, val_2):
    """
    Takes your completed dataframe and two metrics you want to plot against each other
    :param df:
    :param val_1:
    :param val_2:
    :return:
    """
    grouped_metrics = df.groupby(['Date Snapshot'])[[val_1, val_2]].sum().reset_index()
    grouped_metrics = pd.melt(grouped_metrics, id_vars=['Date Snapshot'],
                              value_vars=[val_1, val_2])
    grouped_metrics.to_csv("grouped_metrics.csv")
    fig = px.line(grouped_metrics, x="Date Snapshot", y="value",
                  color='variable')
    plot(fig)


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
