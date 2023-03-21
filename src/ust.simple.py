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
from calc.ratesOLD import par_curve_to_spot
import numpy as np

fp = __file__
fhead, ftail = os.path.split(fp)

CSV_PATH = 'rates.csv'

# load the rates.csv data into a dataframe, dropping the sub-6mo maturities
df_load = rates.load_rates(CSV_PATH)
df = df_load.drop(['1 Mo','2 Mo','3 Mo','4 Mo'], axis=1)

# print(df)

# get the first and last date in the rates file
first_date = df.index[0].strftime('%Y-%m-%d')
last_date = df.index[-1].strftime('%Y-%m-%d')

# UST input par yield tenors in months
# par_tenors = [1, 2, 3, 4, 6, 12, 24, 36, 60, 84, 120, 240, 360]
par_tenors = [6, 12, 24, 36, 60, 84, 120, 240, 360]   # Still mullling over [1, 2, 3, 4]

# A global: list of all semi-annual tenors, in months, to allow for simple spot rate extraction
COMPLETE_TENORS =  list(range(6, 361, 6))   # [6, 12, 18, ..., 360]

# Which tenors are selected for the Dash tables (months)
DISPLAY_TENORS_MNTHS = [6, 12, 18, 24, 30, 36, 60, 84, 120, 240, 360]
DISPLAY_TENORS_STR = [str(elem) for elem in DISPLAY_TENORS_MNTHS]   # string list
# Text header for the Dash tables)
DISPLAY_HDR = ['Maturity:', '6 Mo', '1 Yr', '18 Mo', '2 Yr', '30 Mo', '3 Yr', '5 Yr', '7 Yr', '10 Yr', '20 Yr', '30 Yr']

# global: this is the complete number of 6-month periods in the analysis
LEN = len(COMPLETE_TENORS)   

# All semi-annual tenors (months) as a list of strings
COMPLETE_TENORS_STR = [str(elem) for elem in COMPLETE_TENORS]
new_column_list =["Maturity(months):"] + COMPLETE_TENORS_STR

# generate more_par_rates by linear interpolation of given mkt par rates
# starting_mths = integer list of maturities in months; exaple [6, 12, 24, 36]
# starting_rates = list of given par rates at the starting_mths
# mnth = target month for a interpolated par rate 
def par_rates_LinearInterp(mnth, starting_mnths, starting_rates):
    return np.interp(mnth, starting_mnths, starting_rates)

# create a list: a complete set of par rates for months: 6, 7, 8, ..., 360
# input is reqdate, the currently selected evaluation date
def build_complete_par_rates(reqdate):
    df_tmp = build_df(reqdate)   # new header plus one row: the par rates at the requested date
    par_yields_loc = list(df_tmp['YIELD'])  # the par rates at the requested date
    # complete set of par rates (every 6 months from 6 mo to 30 years) by linear interpolation
    complete_par_rates_loc = [par_rates_LinearInterp(mnth, par_tenors, par_yields_loc) for mnth in COMPLETE_TENORS] 
    return complete_par_rates_loc

# create a list: a complete set of spot rates for months: 6, 7, 8, ..., 360
# input is current_complete_par_rates, the complete_par_rates at the currently selected date
def build_complete_spot_rates(current_complete_par_rates):
    
    # create the complete set of discount factors (every 6-month period)
    disc_factors = [0 for i in range(LEN)]
    disc_factors[0] = 1/(1 + 0.5*0.01*current_complete_par_rates[0])
    for n in range(LEN-1):
        lst = [0.5*0.01*current_complete_par_rates[n]*disc_factors[i] for i in range(n+1)]
        disc_factors[n+1] = (1 - sum(lst)) /(1 + 0.5*0.01*current_complete_par_rates[n])
 
    # create the complete set of spot rates from the complete set of discount factors 
    simple_spot_rates = [0 for i in range(LEN)]
    for n in range(LEN):
        simple_spot_rates[n] = 2*100*(np.power(disc_factors[n],-1/(n+1)) - 1)
    
    return simple_spot_rates    
     

app = Dash(__name__)


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

# complete_par_rates at the last data date 
complete_par_rates = build_complete_par_rates(last_date)
# complete set of (SIMPLE-method) spot rates at the last data date
simple_spot_rates = build_complete_spot_rates(complete_par_rates)
    
# format and prepare the SIMPLE-method spot rates for table display
simple_spot_rates_formatted =  [ '%.2f' % elem for elem in simple_spot_rates ] 
simple_spot_row = [last_date] + simple_spot_rates_formatted
# df_simple_spot = pd.DataFrame(columns=new_column_list)
df_simple_spot = pd.DataFrame(columns=new_column_list)
df_simple_spot.loc[0] = simple_spot_row

# build a new df for the SIMPLE-method spot data to display
df_simple_spot_display = df_simple_spot[DISPLAY_TENORS_STR]
df_simple_spot_display_new = pd.DataFrame(columns=DISPLAY_HDR)
new_row = [last_date] + list(df_simple_spot_display.loc[0])
df_simple_spot_display_new.loc[0] = new_row
selected_simple_spot_df = df_simple_spot_display_new.to_dict('records')      

# QuantLib-method spot rates
t, r = par_curve_to_spot(last_date, par_tenors, par_yields, COMPLETE_TENORS)
r_formatted = [ '%.2f' % elem for elem in r ]
full_spot_row = [last_date] + r_formatted
df_spot = pd.DataFrame(columns=new_column_list)
df_spot.loc[0] = full_spot_row
# build a new df for the QL-method spot data to display
df_ql_spot_display = df_spot[DISPLAY_TENORS_STR]
df_ql_spot_display_new = pd.DataFrame(columns=DISPLAY_HDR)
new_row = [last_date] + list(df_ql_spot_display.loc[0])
df_ql_spot_display_new.loc[0] = new_row
selected_spot_df = df_ql_spot_display_new.to_dict('records')


app.layout = html.Div(children=[
    html.H1(children='Yield Curve Transformations'),
    
    html.H2(children='file = '+ ftail),
               
             
    dcc.Graph(
        id='yield-curve-graph',
        figure=fig
    ),
    
    # Par Table    
    html.Div([
        html.B("UST Par Yields-to-Maturity (input data)"),
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
        html.B("UST Spot Rates (semi-annual compounding; QuantLib method)"),
        dtab.DataTable(
            id='spot-data-table',
            data = selected_spot_df, 
            columns = [{"name": i, "id": i} for i in DISPLAY_HDR],           
            page_size = 10
            )], style={'width': '49%'}
        ),
    
    html.Br(),
    html.Br(),
    
    # Simple Spot Rates Table    
    html.Div([
        html.B("UST Spot Rates (semi-annual compounding; SIMPLE method)"),
        dtab.DataTable(
            id='simple-spot-data-table',
            data = selected_simple_spot_df, 
            columns = [{"name": i, "id": i} for i in DISPLAY_HDR],   # was new_column_list           
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
    Output('simple-spot-data-table', 'data'),
    Input('date-picker-single', 'date')
)
def update_figure_and_tables(selected_date):
    # update the figure for the new date
    df_fig = build_df(selected_date)
    fig = px.line(df_fig, x="YEARS", y="YIELD", markers=True,
                  title='Daily US Treasury Par Yield Curve Rates: ' + selected_date)
    fig.update_traces(marker=dict(size=12,color='Red'))
    
    # update the first table, which is just the rates.csv input data at the selected date
    df_table = build_df2(selected_date)
    par_yields = list(df_fig['YIELD'])
    selected_df = df_table.to_dict('records')     
    
    # update the second table: the spot table using the QL method at the selected date
    t, r = par_curve_to_spot(selected_date, par_tenors, par_yields, DISPLAY_TENORS_MNTHS)
    r_formatted = [ '%.2f' % elem for elem in r ]
    full_spot_row = [selected_date] + r_formatted
    df_spot = pd.DataFrame(columns=DISPLAY_HDR)
    df_spot.loc[0] = full_spot_row
    selected_spot_df = df_spot.to_dict('records')
    
    # update the the third table: the spot table using the SIMPLE method at the selected date
    # see these same statements in the initializing table earlier for comments on what they do
    complete_par_rates = build_complete_par_rates(selected_date)
    simple_spot_rates = build_complete_spot_rates(complete_par_rates)
    simple_spot_rates_formatted =  [ '%.2f' % elem for elem in simple_spot_rates ] 
    simple_spot_row = [selected_date] + simple_spot_rates_formatted
    df_simple_spot = pd.DataFrame(columns=new_column_list)
    df_simple_spot.loc[0] = simple_spot_row
    df_simple_spot_display = df_simple_spot[DISPLAY_TENORS_STR]
    df_simple_spot_display_new = pd.DataFrame(columns=DISPLAY_HDR)
    new_row = [selected_date] + list(df_simple_spot_display.loc[0])
    df_simple_spot_display_new.loc[0] = new_row
    selected_simple_spot_df = df_simple_spot_display_new.to_dict('records')  
        
    return fig, selected_df, selected_spot_df, selected_simple_spot_df    

if __name__ == '__main__':
    app.run_server(debug=True)
