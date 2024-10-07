import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import calendar
import warnings
warnings.filterwarnings('ignore')
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import dash_table
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_table
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
import flask as Flask

web_link = "https://drive.google.com/uc?export=download&id=1cwN3B9hWxyYleov2LDNmSPWz0nih4B47"
df = pd.read_csv(web_link)

# Remove rows where the CAP_UOM is not 'BBL/d'
df_filtered = df[df["CAP_UOM"] == "BBL/d"]

# Convert TA_START and TA_END columns to datetime for date manipulation
df_filtered['TA_START'] = pd.to_datetime(df_filtered['TA_START'], format="%Y%m%d", errors='coerce')
df_filtered['TA_END'] = pd.to_datetime(df_filtered['TA_END'], format="%Y%m%d", errors='coerce')

df_filtered['start_year'] = df_filtered['TA_START'].dt.year
df_filtered['start_month'] = df_filtered['TA_START'].dt.month
df_filtered['end_year'] = df_filtered['TA_END'].dt.year
df_filtered['end_month'] = df_filtered['TA_END'].dt.month
df_filtered["CAP_OFFLINE"] = df_filtered["CAP_OFFLINE"].fillna(0)
df_filtered['CAP_OFFLINE_KBD'] = round(df_filtered["CAP_OFFLINE"] / 1000, 2)

start = df_filtered["TA_START"].min() - pd.DateOffset(months = 1)
end = df_filtered["TA_END"].max()
date_range = pd.date_range(start = start, end = end, freq = "MS").tolist()

date_dict = {date: 0 for date in date_range}


import calendar

def what_you_want(filter, df_filtered):
    start = df_filtered["TA_START"].min() - pd.DateOffset(months = 1)
    end = df_filtered["TA_END"].max()
    date_range = pd.date_range(start = start, end = end, freq = "MS").tolist()

    date_dict = {date: 0 for date in date_range}
    
    dic = {}
    for country in df_filtered[filter].unique():
        dic[country] = date_dict.copy()

    for i, row in df_filtered.iterrows():
        element = row[filter]
        start = row["TA_START"]
        end = row["TA_END"]
        value = row["CAP_OFFLINE"] 
        # print(start, end, value, element)

        months = pd.date_range(start = start, end = end, freq = "MS").tolist()
        # print(months)
        # print()

        # Settle the start month first
        # if it is an empty datetime index >. it means that it is in the same month
        if not months:
            days_difference = (end - start).days
            total_val = days_difference * value
            first_day_of_month = start.replace(day = 1)
            dic[element][first_day_of_month] += total_val
            # print(dic)
        else:
            if start.day == 1:
                for i in range(len(months)):
                    if i != len(months) - 1:
                        temp_month = months[i].month
                        temp_year = months[i].year
                        days_in_month = calendar.monthrange(temp_year, temp_month)[1]
                        total_val = days_in_month * value
                        dic[element][months[i]] += total_val
                    else:
                        # last value, take difference
                        last_month_diff = (end - months[i]).days
                        total_val = last_month_diff * value
                        dic[element][months[i]] += total_val

            else:
                ## handle the first day >> what should we do to handle the first day
                end_date = start + pd.offsets.MonthEnd(0)
                date_diff = (end_date - start).days
                first_month_val = date_diff * value
                dic[element][start.replace(day = 1)] += first_month_val

                for i in range(len(months)):
                    if i != len(months) - 1:
                        temp_month = months[i].month
                        temp_year = months[i].year
                        days_in_month = calendar.monthrange(temp_year, temp_month)[1]
                        total_val = days_in_month * value
                        dic[element][months[i]] += total_val
                    else:
                        # last value, take difference
                        last_month_diff = (end - months[i]).days
                        total_val = last_month_diff * value
                        dic[element][months[i]] += total_val

    df_aggregated = pd.DataFrame(dic)
    df_aggregated["Year"] = df_aggregated.index.year
    df_aggregated["Month"] = df_aggregated.index.month

    return df_aggregated
# print(df_filtered.select_dtypes(include=['object']).columns)
# flask_server = Flask(__name__)

# Initialize Dash app
app = dash.Dash(__name__)#, server = flask_server, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
# App layout
app.layout = html.Div(style={'backgroundColor': '#f8f9fa', 'padding': '20px'}, children=[

    # Title
    html.H1("Dynamic Offline Capacity Dashboard", style={'textAlign': 'center', 'color': '#007bff'}),

    # Dropdown for selecting filter column (e.g., U_COUNTRY)
    html.Label('Select Filter Column:', style={'fontWeight': 'bold'}),
    dcc.Dropdown(
        id='filter-column',
        options=[{'label': col, 'value': col} for col in df_filtered.select_dtypes(include=['object']).columns],
        value=df_filtered.select_dtypes(include=['object']).columns[0],  # Default value as first categorical column
        style={'backgroundColor': '#f8f9fa', 'color': '#000', 'marginBottom': '20px'}
    ),

    # Dropdown for selecting specific elements to plot (e.g., countries)
    html.Label('Select Elements to Plot:', style={'fontWeight': 'bold'}),
    dcc.Dropdown(
        id='filter-values',
        multi=True,  # Allow multiple selections
        style={'backgroundColor': '#f8f9fa', 'color': '#000', 'marginBottom': '20px'}
    ),

    # Date picker for selecting TA_START and TA_END
    html.Label('Select Date Range:', style={'fontWeight': 'bold'}),
    dcc.DatePickerRange(
        id='date-picker',
        start_date=df_filtered['TA_START'].min(),
        end_date=df_filtered['TA_END'].max(),
        display_format='YYYY-MM-DD',
        style={'marginBottom': '20px'}
    ),

    # Div to hold multiple graphs (stacked)
    html.Div(id='graph-container'),

    # DataTable to display the aggregated DataFrame
    html.Div(id='table-container', style={'marginTop': '20px'})
])

# Callback to dynamically update the available values based on the selected filter column
@app.callback(
    Output('filter-values', 'options'),
    Input('filter-column', 'value')
)
def set_filter_values_options(selected_column):
    # Get the unique values of the selected column
    unique_values = df_filtered[selected_column].unique()
    return [{'label': val, 'value': val} for val in unique_values]

# Callback to update the chart and table based on selected filter, elements, and date range
@app.callback(
    [Output('graph-container', 'children'),
     Output('table-container', 'children')],
    [Input('filter-column', 'value'),
     Input('filter-values', 'value'),
     Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date')]
)
def update_chart_and_table(filter_column, selected_values, start_date, end_date):
    # Filter the dataframe based on the selected date range
    df_filter = df_filtered[(df_filtered['TA_START'] >= pd.to_datetime(start_date)) & (df_filtered['TA_START'] <= pd.to_datetime(end_date))]

    # If there are no selected values, return empty content
    if not selected_values:
        return [html.H5("Please select values to plot.")], []

    # List to hold all graphs
    graph_components = []

    # List to hold the final aggregated DataFrame for table display
    aggregated_list = []

    # Loop through each selected value and create a graph for each
    for value in selected_values:
        # Filter the data for the current value
        df_value_filtered = df_filter[df_filter[filter_column] == value]

        # Use 'what_you_want' function to aggregate the data
        df_aggregated = what_you_want(filter_column, df_value_filtered)
        # display(df_aggregated)
        # Generate a Plotly line chart with Month as x-axis and Year as the lines
        fig = px.line(df_aggregated, x='Month', y=value, color='Year',
                      labels={'Month': 'Month', 'Offline Capacity': value},
                      title=f"Offline Capacity for {value}")

        # Append the graph to the list
        graph_components.append(dcc.Graph(figure=fig))

        # Add the current df_aggregated to the aggregated_list for table
        aggregated_list.append(df_aggregated)

    # Concatenate all DataFrames to display in a single table
    if len(aggregated_list) > 0:
        df_final = pd.concat(aggregated_list, axis = 1)
        # print(df_final)
        df_final.drop(columns = ["Month", "Year"], inplace = True)
        df_final.index = df_final.index.strftime('%Y-%m')
        df_final = df_final.T
        df_final[""] = df_final.index
        df_final = df_final[[""] + [c for c in df_final if c != ""]]
        df_final.fillna(0, inplace = True)
        # print(df_final.index)
        # df_final = df_final.pivot_table(index=filter_column, columns='Month', values='CAP_OFFLINE', aggfunc='sum').fillna(0)
    else:
        df_final = pd.DataFrame()

    # Create a DataTable for the aggregated DataFrame
    table = dash_table.DataTable(
        columns=[{"name": str(i), "id": str(i)} for i in df_final.columns],
        data=df_final.reset_index().to_dict('records'),
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left'},
        page_size=10  # Set the number of rows to display per page
    )

    return graph_components, table

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, host='127.0.0.1', port=8070)
