import pandas as pd
import plotly.express as px
from plotly.offline import plot


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
    grouped_metrics = df.groupby(['Symbol','Date Snapshot'])[[val_1,val_2]].sum().reset_index()
    grouped_metrics = pd.melt(grouped_metrics, id_vars=['Symbol','Date Snapshot'],
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

