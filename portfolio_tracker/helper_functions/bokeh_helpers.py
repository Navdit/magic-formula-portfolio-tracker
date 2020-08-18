import pandas as pd
from bokeh.layouts import Column
from bokeh.models import (ColumnDataSource, HoverTool, Legend, LinearAxis,
                          Range1d)
from bokeh.models.formatters import DatetimeTickFormatter
from bokeh.models.widgets import Panel, Tabs
from bokeh.palettes import d3
from bokeh.plotting import figure, output_file, save


########################################################################################################################
# Function Name: get_y_range_of_graph
# Description  : Gives the Right and Left Y-axis range of the graph based on the max value in dataframe
# @param       : Scenario Metrics Dataframe
# @param       : right_y_axis_filters_list - List of rigth y-Axis filters
# @return      : Left and Right Y-Axis Range of Bokeh Graph
# Author       : Navdit Sharma
# Comments     : Created on 05/09/2018
########################################################################################################################
def get_y_range_of_graph(scenario_metrics_df: pd.DataFrame, right_y_axis_filter: str) -> (int, int):
    tmp_max_val_df = scenario_metrics_df
    tmp_max_val_df = tmp_max_val_df.apply(pd.to_numeric)

    # Right y-Axis Range
    right_y_axis_range = tmp_max_val_df[right_y_axis_filter].max() + 1

    # Left y-axis Range
    tmp_max_val_df = tmp_max_val_df.drop(["LocalTime"], axis=1)

    # Drop Right-Y-Axis Columns
    tmp_max_val_df = tmp_max_val_df.drop([right_y_axis_filter], axis=1)

    left_y_axis_range = (0, tmp_max_val_df.values.max() + 50)

    return left_y_axis_range, right_y_axis_range


########################################################################################################################


########################################################################################################################
# Function Name: get_color_palette
# Description  : To set the color palette, which will be used in plotting Bokeh Graph
# @param       : Scenario Metrics Dataframe
# @param       : Scenario Name, for which the Color Palette has to be set
# @return      : Color Palette
# Author       : Navdit Sharma
# Comments     : Created on 05/09/2018
########################################################################################################################
def get_color_palette(scenario_metrics_df: pd.DataFrame, scenario: str) -> list:
    # Number of Lines to plot
    num_lines = len(scenario_metrics_df.columns)

    # Get the colors
    if num_lines > 20:
        raise Exception("At present maximum of 19 transactions/scenario is permissible. "
                        "Please check Scenario {}, which has {} transactions".format(scenario, num_lines))
    elif num_lines < 3:
        color_palette = ['#1f77b4', '#2ca02c']
    else:
        color_palette = d3['Category20'][num_lines]

        # Removing Red Color which is on index 5
        if "#d62728" in color_palette:
            color_palette.remove("#d62728")

    return color_palette


########################################################################################################################


########################################################################################################################
# Function Name: set_hover_tool_tips
# Description  : Set the properties of the hover tool tips.
# @return      : hover_tool_tips
# Author       : Navdit Sharma
# Comments     : Created on 05/09/2018
########################################################################################################################
def set_hover_tool_tips() -> object:
    hover_tool_tips = HoverTool(
        tooltips=[
            ('Date', '$x{%d-%M-%Y}'),
            ('Return', '@$name')  # use @{ } for field names with spaces,
        ],

        formatters={
            '$x': 'datetime',  # use 'datetime' formatter for 'date' field
            '@$name': 'printf'
            # 'Ticker Return': 'printf',  # use 'printf' formatter for 'adj close' field
            # use default 'numeral' formatter for other fields
        },

        # display a tooltip whenever the cursor is vertically in line with a glyph
        mode='vline'
    )

    return hover_tool_tips


########################################################################################################################


########################################################################################################################
# Function Name: plot_new_graph
# Description  : Set the properties of the hover tool tips.
# @param       : x_axis_label - Label of X-Axis
# @param       : x_axis_type
# @param       : y_axis_label - Label of Y-Axis
# @param       : plot_width - Width of the graph to be plotted
# @param       : plot_height - Height of the graph to be plotted
# @param       : left_y_range - Range of Y-Axis
# @param       : toolbar_location - Location of Bokeh Toolbar
# @param       : tools_to_show - Bokeh tools, which you would like to show on graph
# @return      : figure
# Author       : Navdit Sharma
# Comments     : Created on 05/09/2018
########################################################################################################################
def plot_new_graph(x_axis_label: str, x_axis_type: str, y_axis_label: str, plot_width: int, plot_height: int,
                   left_y_range: int, toolbar_location: str, tools_to_show: str) -> figure():
    plot = figure(x_axis_label=x_axis_label,
                  x_axis_type=x_axis_type,
                  y_axis_label=y_axis_label,
                  plot_width=plot_width,
                  plot_height=plot_height,
                  y_range=left_y_range,
                  toolbar_location=toolbar_location,
                  tools=tools_to_show)

    return plot


########################################################################################################################


########################################################################################################################
# Function Name: set_graph_and_legend_properties
# Description  : Sets the Properties of the graph and the legend of the graph
# @param       : Graph and the legend it will be using, Scenario Name
# @return      : Returns the plotted graph with the properties
# Author       : Navdit Sharma
# Comments     : Created on 05/09/2018
########################################################################################################################
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

########################################################################################################################
