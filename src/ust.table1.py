from dash import Dash, dcc, html, Input, Output
import os
import datetime as dt
import dateutil.relativedelta
import pandas as pd
from dash import dash_table as dtab
from data import rates 

# bug? can't display earlier than 2022-10-19?

fp = __file__
fhead, ftail = os.path.split(fp)

CSV_PATH = 'rates.csv'

# load the rates.csv data into a dataframe
df = rates.load_rates(CSV_PATH)

# get the first and last date in the rates file
first_date = df.index[0].strftime('%Y-%m-%d')
last_date_raw = df.index[-1]
last_date = df.index[-1].strftime('%Y-%m-%d')
# print(df)

# init_date = '2023-02-01'
# initial view is last month of data
init_date_raw = last_date_raw + dateutil.relativedelta.relativedelta(months=-1)
init_date = init_date_raw.strftime('%Y-%m-%d')

app = Dash(__name__)

def build_df(reqdate):
    df2 = df.loc[reqdate:last_date].dropna()    
    df3 = pd.DataFrame(df2)
    df_table_out = df3.reset_index()  # move Dates from index into col 1
    df_table_out['Date'] = df_table_out['Date'].dt.date # delete times in Date column
    return df_table_out

# test that build_df works
df_tmp = build_df(init_date)
column_list = df_tmp.columns
selected_df = df_tmp.to_dict('records')  # the dash table component uses this form for its 'data' property

app.layout = html.Div(children=[
    html.H1(children='Testing Dash: tables'),
    
    html.H2(children='file = '+ ftail),   
    
    html.Div(children=[
        html.Label('Choose a different starting date: '),
        dcc.DatePickerSingle(
        id='date-picker-single',
        min_date_allowed=first_date,
        max_date_allowed=last_date,
        initial_visible_month=last_date,
        disabled_days=rates.missing_dates(df),
        date=init_date
        )       
    ]),     
    
    # Table    
    html.Div([
        dtab.DataTable(
            id='data-table',
            data = selected_df, 
            columns = [{"name": i, "id": i} for i in column_list],
            page_size = 10
            )], style={'width': '49%'})   
    
])

@app.callback(
    Output('data-table', 'data'),  # the table property 'data' is being updated by update_table 
    Input('date-picker-single', 'date')
)
    
def update_table(selected_date):
    df_table = build_df(selected_date)
    selected_df = df_table.to_dict('records')
    return selected_df    

if __name__ == '__main__':
    app.run_server(host='127.0.0.1', debug=True)