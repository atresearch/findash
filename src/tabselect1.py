# 4/6/2023 alan: created
# 4/6/2023 alan: now table display is from latest date to earliest
# 4/7/2023 alan: still problems with reverse date order table; here 2023-03-14 is highlighted(good),
#           but seems to now require the initial chart to show both the first and last dates.  
# 4/7/2023  alan: finally fixed the problem with reverse date order

from dash import Dash, dcc, html, Input, Output, dash_table, no_update  
import plotly.graph_objects as go
import plotly.express as px
import datetime as dt
import dateutil.relativedelta
import pandas as pd
from data import rates 
import os


# max number of charts at one time
MAX_CHARTS = 8
INIT = 0

fp = __file__
fhead, ftail = os.path.split(fp)

CSV_PATH = 'rates.csv'

# load the rates.csv data into a dataframe
df = rates.load_rates(CSV_PATH)


# dictionary mapping rates.csv headers to months
hdrs_to_months_dict = {
    "1 Mo": 1,
    "2 Mo": 2,
    "3 Mo": 3,
    "4 Mo": 4,
    "6 Mo": 6,
    "1 Yr": 12,
    "2 Yr": 24,
    "3 Yr": 36,
    "5 Yr": 60,
    "7 Yr": 84,
    "10 Yr": 120,
    "20 Yr": 240,
    "30 Yr": 360
}

# get the first and last date in the rates file
first_date = df.index[0].strftime('%Y-%m-%d')
last_date_raw = df.index[-1]
last_date = df.index[-1].strftime('%Y-%m-%d')
# print("first_date=",first_date)
# print("last_date=",last_date)
init_date = first_date

def build_df(reqdate):
    df2 = df.loc[reqdate:last_date] 
    df3 = pd.DataFrame(df2)
    df_table_out = df3.reset_index()  # move Dates from index into col 1
    df_table_out['Date'] = df_table_out['Date'].dt.date # delete times in Date column
    return df_table_out

def build_df_row(reqdate):
    df2 = df.loc[reqdate:reqdate]     
    d = {
        'MONTHS': [hdrs_to_months_dict[tenor_name] for tenor_name in df2.keys()],
        'YEARS': [rates.tenor_name_to_year(tenor_name) for tenor_name in df2.keys()],
        'YIELD': df2.values[0]       
    }
    df_req = pd.DataFrame(d)
    return df_req

# reverse the row counting
def rev_row(row, MAX_ROW_INDEX):
    return MAX_ROW_INDEX - row


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)


df0 = build_df(init_date)  # filtered df from init_date to last_date
MAX_ROW_INDEX = len(df0) - 1
df0["id"] = df0.index
dff = df0
dff = dff.sort_index(ascending=False)    # latest date first
# print(dff)

columns = ['Date', '1 Mo', '2 Mo', '3 Mo', '4 Mo', '6 Mo', '1 Yr',
               '2 Yr', '3 Yr', '5 Yr', '7 Yr', '10 Yr', '20 Yr', '30 Yr']
initial_active_cell = {"row": 0, "column": 0, "column_id": "Date", "row_id": MAX_ROW_INDEX}

row = initial_active_cell["row_id"]
initial_date = dff.at[len(dff)-1, "Date"]    # this is a datetime object!
selected_dates = [initial_date]
# print("PRE-LAYOUT: selected_dates=",selected_dates)

app.layout = html.Div(
    [
        html.Div(
            [
                html.Label("UST PAR YIELDS", style={"textAlign":"center"}),
                dash_table.DataTable(
                    id="table",
                    columns=[{"name": c, "id": c} for c in columns],
                    data=dff.to_dict("records"),
                    page_size=20,
                    sort_action="native",
                    row_selectable="multi",   # new
                    selected_rows=[0],   # new  
                    active_cell=initial_active_cell,
                    style_data={
                       'color': 'white',
                       'backgroundColor': 'black'
                    },
                    style_data_conditional=[                
                        {
                           "if": {"state": "active"},        # 'active' | 'selected'  
                           "backgroundColor": "orange",
                           "border": "1px solid black",
                        }
                    ],
                    style_header={
                        'backgroundColor': 'rgb(210, 210, 210)',
                        'color': 'black',
                        'fontWeight': 'bold'
                        }
                    ),
            ],
            style={"margin": 50},
            className="five columns"
        ),
        html.Div(id="output-graph", className="six columns"),  
    ],
    className="row"
)


# @app.callback(
#    Output("output-graph", "children"), Input("table", "active_cell"),
# )
@app.callback(
    Output("output-graph", "children"), Input("table", "selected_rows"),
)
# def cell_clicked(active_cell):
def radio_clicked(selected_rows):
    if selected_rows is None:     # was:  if active_cell is None:
        selected_rows = [0]
          
    selected_dates = [dff.at[rev_row(row, MAX_ROW_INDEX), "Date"] for row in selected_rows]               
         
    # graph the latest selection
    date = selected_dates[-1]
    df_row = build_df_row(date)
    fig = go.Figure([go.Scatter(x=df_row['YEARS'], y=df_row['YIELD'], 
                                connectgaps=True, name=date.strftime('%Y-%m-%d'))])  
    fig.update_layout(xaxis_title="YEARS", yaxis_title="PAR YIELD")
    fig.update_layout(height=800),
    fig.update_layout(legend=dict(
        orientation="h", entrywidth=70, yanchor="bottom", y=1.02,xanchor="right",x=1))       
                                  
    if len(selected_dates) > 1:   # graph the other recently selected dates
        remainder_dates = selected_dates[:-1]
        for date in remainder_dates:
            df_row = build_df_row(date)
            fig.add_scatter(x=df_row['YEARS'], y=df_row['YIELD'], 
                           connectgaps=True, name=date.strftime('%Y-%m-%d'))                   
            fig.update_layout(xaxis_title="YEARS", yaxis_title="PAR YIELD")    
            
      
    return dcc.Graph(figure=fig)


if __name__ == "__main__":
    app.run_server(debug=True)