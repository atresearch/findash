# DO NOT start a web server; this code starts the server!
# visit http://localhost:8050/ in your web browser
# or visit http://127.0.0.1:8050/ in your web browser.

# tests datepicker; needs to catch 'callback errors' on non-market dates

from datetime import date
from dash import Dash, dcc, html, Input, Output
from dash import dash_table as dtab
import os
import plotly.express as px
import pandas as pd
from data import rates
from calc.rates import par_curve_to_spot

fp = __file__
fhead, ftail = os.path.split(fp)

CSV_PATH = 'rates.csv'

# load the rates.csv data into a dataframe
df = rates.load_rates(CSV_PATH)

# get the first and last date in the rates file
first_date = df.index[0].strftime('%Y-%m-%d')
last_date = df.index[-1].strftime('%Y-%m-%d')

# UST par yield tenors in months
par_tenors = [1, 2, 3, 4, 6, 12, 24, 36, 60, 84, 120, 240, 360]

app = Dash(__name__)

# print(df)

t, r = par_curve_to_spot('2023-02-19', [12, 24], [4.25, 4.50], [3, 6, 12, 18, 24])
print(t)
print(r)

# test that build_df works
# df_tmp = build_df(init_date)
# column_list = df_tmp.columns
# selected_df = df_tmp.to_dict('records')  # the dash table component uses this form for its 'data' property

def build_df(reqdate):
    df2 = df.loc[reqdate].dropna()
 
    d = {
        'YEARS': [rates.tenor_name_to_year(tenor_name) for tenor_name in df2.keys()],
        'YIELD':df2.values
    }
    df_test = pd.DataFrame(d)
    # print(df_test)
    return df_test

def build_df2(reqdate):
    df2 = df.loc[reqdate:reqdate]    
    df3 = pd.DataFrame(df2)
    df_table_out = df3.reset_index()  # move Dates from index into col 1
    df_table_out['Date'] = df_table_out['Date'].dt.date # delete times in Date column
    return df_table_out

def build_df_spot(reqdate,spot_yields):
    df2 = df.loc[reqdate:reqdate]    
    df3 = pd.DataFrame(df2)
    df_table_out = df3.reset_index()  # move Dates from index into col 1
    df_table_out['Date'] = df_table_out['Date'].dt.date # delete times in Date column
    return df_table_out

# init the chart
df_current = build_df(last_date)
fig = px.line(df_current, x="YEARS", y="YIELD", markers=True)
fig.update_traces(marker=dict(size=12,color='Red'))

# init the one-line par rate table
df_tmp = build_df2(last_date)
column_list = df_tmp.columns
selected_df = df_tmp.to_dict('records')  # the dash table component uses this form for its 'data' property

# init the one-line spot rate table
par_yields = list(df_current['YIELD'])
t, r = par_curve_to_spot(last_date, par_tenors, par_yields, par_tenors)
r_formatted = [ '%.2f' % elem for elem in r ]
full_spot_row = [last_date] + r_formatted
df_spot = pd.DataFrame(columns=column_list)
df_spot.loc[0] = full_spot_row
# print(df_spot)
selected_spot_df = df_spot.to_dict('records')



app.layout = html.Div(children=[
    html.H1(children='Yield Curve Transformations'),
    
    html.H2(children='file = '+ ftail),
               
             
    dcc.Graph(
        id='yield-curve-graph',
        figure=fig
    ),
    
    # Par Table    
    html.Div([
        html.B("Par Yields"),
        dtab.DataTable(
            id='par-data-table',
            data = selected_df, 
            columns = [{"name": i, "id": i} for i in column_list],           
            page_size = 10
            )], style={'width': '49%'}
        ),
    
    html.Br(),
    html.Br(),
    
    # Spot Table    
    html.Div([
        html.B("Spot Yields"),
        dtab.DataTable(
            id='spot-data-table',
            data = selected_spot_df, 
            columns = [{"name": i, "id": i} for i in column_list],           
            page_size = 10
            )], style={'width': '49%'}
        ),
    
    html.Br(),
    html.Br(),
    
    html.Div(children=[
        html.Label('Choose a date: '),
        dcc.DatePickerSingle(
        id='date-picker-single',
        min_date_allowed=first_date,
        max_date_allowed=last_date,
        initial_visible_month=last_date,
        disabled_days=rates.missing_dates(df),
        date=last_date
        )       
    ])
])

@app.callback(
    Output('yield-curve-graph', 'figure'), 
    Output('par-data-table', 'data'),
    Output('spot-data-table', 'data'),
    Input('date-picker-single', 'date')
)
def update_figure_and_tables(selected_date):
    # print('new selected date=' + selected_date)
    df_fig = build_df(selected_date)
    fig = px.line(df_fig, x="YEARS", y="YIELD", markers=True,
                  title='Daily Treasury Par Yield Curve Rates on ' + selected_date)
    fig.update_traces(marker=dict(size=12,color='Red'))
    df_table = build_df2(selected_date)
    par_yields = list(df_fig['YIELD'])
    selected_df = df_table.to_dict('records')
    
    t, r = par_curve_to_spot(selected_date, par_tenors, par_yields, par_tenors)
    r_formatted = [ '%.2f' % elem for elem in r ]
    # print(t)
    # print(r_formatted)
    full_spot_row = [selected_date] + r_formatted
    # print(column_list)
    # print(full_spot_row)
    df_spot = pd.DataFrame(columns=column_list)
    df_spot.loc[0] = full_spot_row
    # print(df_spot)
    selected_spot_df = df_spot.to_dict('records')
    
    return fig, selected_df, selected_spot_df    

if __name__ == '__main__':
    app.run_server(debug=True)
