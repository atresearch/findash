# DO NOT start a web server; this code starts the server!
# visit http://localhost:8050/ in your web browser
# or visit http://127.0.0.1:8050/ in your web browser.

# 3/22/2023 alan: error in build_complete_spot_rates corrected, [n]->[n+1] in two places
# 3/23/2023 alan: add sub-6m spot rates using thijs's rule
# 3/23/2023 alan: major overhaul: fixed errors associated to missing yields: for example, try init_date = '1993-10-01'
# 3/25/2023 alan: reworked SIMPLE bootstrap method to compute spot rates for every maturity month 1, 2, 3, ..., 360

from datetime import date
from dash import Dash, dcc, html, Input, Output
from dash import dash_table as dtab
import os
import plotly.express as px
import pandas as pd
from data import rates
# from calc.ratesOLD import par_curve_to_spot
from calc.rates import par_curve_to_spot
import numpy as np

fp = __file__
fhead, ftail = os.path.split(fp)

CSV_PATH = 'rates.csv'

# load the rates.csv data into a dataframe
df = rates.load_rates(CSV_PATH)

# get the first and last date in the rates file
first_date = df.index[0].strftime('%Y-%m-%d')
last_date = df.index[-1].strftime('%Y-%m-%d')
# init_date = last_date  
init_date = "2023-03-01"

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

# UST INPUT par yield tenors in months 
par_tenors = [1, 2, 3, 4, 6, 12, 24, 36, 60, 84, 120, 240, 360]

TENORS = list(range(1, 361))   # [1, 2, ... 360]
TENORS_STR = [str(elem) for elem in TENORS]   # ['1', '2', ..., '360']

# Which tenors are selected in Dash table display (months) for spot rates
DISPLAY_TENORS_MNTHS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 18, 24, 30, 36, 60, 84, 120, 240, 360]
DISPLAY_TENORS_STR = [str(elem) for elem in DISPLAY_TENORS_MNTHS]   # string list

# Header for the Dash table display for spot rates (2 tables)
DISPLAY_HDR = ['Maturity:', '1 Mo', '2 Mo', '3 Mo', '4 Mo', '5 Mo', '6 Mo', '7 Mo','8 Mo','9 Mo','10 Mo','11 Mo','1 Yr',
               '18 Mo','2 Yr', '30 Mo', '3 Yr', '5 Yr', '7 Yr', '10 Yr', '20 Yr', '30 Yr']

new_column_list =["Anything"] + TENORS_STR 

# generate 360 monthly par rates by linear interpolation of given UST par rates
# starting_mths = integer list of maturities in months; exaple [6, 12, 24, 36]
# starting_rates = list of given par rates at the starting_mths
# mnth = target month for a interpolated par rate 
# NOTE: np.interp uses constant extrapolation, 
#   defaulting to extending the first and last values of the y array in the interpolation interval
#   This comes in to play pre-July 30, 2001 when there is no '1 Mo' par rate in rates.csv 
def par_rates_LinearInterp(mnth, starting_mnths, starting_rates):
    return np.interp(mnth, starting_mnths, starting_rates)

# create a list: a complete set of par rates for months: 1,2, ..., 360  
# input is reqdate, the currently selected evaluation date
def ust_to_par_rates(reqdate):
    df_tmp = build_df(reqdate)   # contains the par rates at the requested date from the US Treasury
    par_tenors_loc = list(df_tmp['MONTHS']) 
    par_yields_loc = list(df_tmp['YIELD'])  # the par rates at the requested date
    par_rates_loc = [par_rates_LinearInterp(mnth, par_tenors_loc, par_yields_loc) for mnth in TENORS] 
    
    return par_rates_loc


# output: DF = a list = a partial set of discount_factors (DF) for maturity months: 
# n, n+6, n+12, n+18, n+24, ..., nmax <= 360, where n = nstart = 1, 2, 3, 4, 5, or 6
# input: DF_short_list is a list of the known DF's for months 1, 2, 3, 4, 5, 6
# input: nstart = one of 1, 2, 3, 4, 5, 6
# input: par_rates is the complete list of par rates (=coupon rates) in percent at maturity months 1, 2, 3, ..., 360
def par_rates_to_DF_semiannual(DF_short_list, nstart, par_rates):
    
    lenp = 60     
    DF = [0 for i in range(lenp)]
    DF[0] = DF_short_list[nstart-1]
    months = nstart
    Delta = [0.5 for i in range(lenp)]  # fraction of the annual coupon paid on coupon days        
    for n in range(lenp-1):
        m = nstart + 6*(n+1)  # max value of m is 6 + 6*59 = 360
        coupon = 0.01*par_rates[m-1]    # these are par bonds, so coupon = yield-to-maturity
        accrued_interest = 0.5*coupon*(1 - (months/6))
        pv_items = [Delta[i]*coupon*DF[i] for i in range(n+1)]  # list of present values of coupons received prior to maturity
        DF[n+1] = (1 + accrued_interest - sum(pv_items)) /(1 + Delta[n]*coupon)
     
    return DF    
        
# create the short list of starting discount factors for maturity months: 1, 2, 3, 4, 5, 6
# these starting DF's are the inputs to par_rates_to_DF_semiannual(...)
# input: par_rates is the complete list of par rates (=coupon rates) in percent at maturity months 1, 2, 3, ..., 360
# the par_rates are interpretted as coming froms BONDS in their last semi-annual coupon period, so the buyer pays dirty price = par + accrued interest
def par_rates_to_DF_short(par_rates):  
     
    len1 = 6
    DF_short_list = [1 for n in range(len1)]
    for n in range(len1):
        m = n + 1  # months to maturity
        coupon = par_rates[n]    # these are par bonds, so coupon = yield-to-maturity
        payoff_amt = 100 + 0.5*coupon
        accrued_interest = 0.5*coupon*(1 - (m/6))
        dirty_price = 100 + accrued_interest
        DF_short_list[n] = dirty_price/payoff_amt
    return DF_short_list   

# create the full set of discount factors for maturity months: 1, 2, .., 360
# input: par_rates is the complete list of par rates (=coupon rates) in percent at maturity months 1, 2, 3, ..., 360
# the par_rates are interpretted as coming froms BONDS in their last semi-annual coupon period, so the buyer pays dirty price = par + accrued interest
def par_rates_to_DF_full(par_rates):  
     
    len1 = 6
    len2 = 60
    len3 = 360
    DF_full_list = [1 for n in range(len3)]
    for n in range(len1):
        DF_short_list = par_rates_to_DF_short(par_rates)  # DF_short_list has length=len1
        DF_cycle = par_rates_to_DF_semiannual(DF_short_list, n+1, par_rates)  # length=len2, the DF's for months n, n + 6, n + 12, ...
        for m in range(len2):
            DF_full_list[n + 6*m] = DF_cycle[m]   # insert the cycle DF's into the appropriate spot in the full list
    return DF_full_list   
    
# map the discount factors to spot rates (semi-annual compounding, percent)
# input: DF_list is the complete list of discoun factors for maturity months 1, 2, 3, ..., 360
def DF_to_spot_rates(DF_list): 
    len3 = 360
    spot_rates = [0 for n in range(len3)]
    for n in range(len3):
        t_years = (n+1)/12
        pow = -1/(2*t_years)
        spot_rates[n] = 2*100*(np.power(DF_list[n],pow) - 1) 
    return spot_rates  

# create the full set of spot rates for maturity months: 1, 2, .., 360
# input: par_rates is the complete list of par rates (=coupon rates) in percent at maturity months 1, 2, 3, ..., 360
def par_rates_to_spot(par_rates):   
    DF_list  =  par_rates_to_DF_full(par_rates)
    return DF_to_spot_rates(DF_list)         


def build_df(reqdate):
    df2 = df.loc[reqdate].dropna()
 
    d = {
        'MONTHS': [hdrs_to_months_dict[tenor_name] for tenor_name in df2.keys()],
        'YEARS': [rates.tenor_name_to_year(tenor_name) for tenor_name in df2.keys()],
        'YIELD':df2.values
    }
    df_req = pd.DataFrame(d)
    return df_req

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
     

app = Dash(__name__)

# initial ust data
df_current = build_df(init_date)
par_yields = list(df_current['YIELD'])
par_tenors = list(df_current['MONTHS'])

# init the chart
fig = px.line(df_current, x="YEARS", y="YIELD", markers=True)
fig.update_traces(marker=dict(size=12,color='Red'))

# init the one-line par rate table
df_tmp = build_df2(init_date)
column_list = df_tmp.columns
selected_df = df_tmp.to_dict('records')  # the dash table component uses this form for its 'data' property

# complete list of monthly par rates at the initial date 
par_rates = ust_to_par_rates(init_date)
# complete list of monthly spot rates at the initial date 
simple_spot_rates = par_rates_to_spot(par_rates)
    
# format and prepare the SIMPLE-method spot rates for table display
simple_spot_rates_formatted =  [ '%.4f' % elem for elem in simple_spot_rates ] 
simple_spot_row = [init_date] + simple_spot_rates_formatted
df_simple_spot = pd.DataFrame(columns=new_column_list)
df_simple_spot.loc[0] = simple_spot_row

# build a new df for the SIMPLE-method spot data to display
df_simple_spot_display = df_simple_spot[DISPLAY_TENORS_STR]
df_simple_spot_display_new = pd.DataFrame(columns=DISPLAY_HDR)
new_row = [last_date] + list(df_simple_spot_display.loc[0])
df_simple_spot_display_new.loc[0] = new_row
selected_simple_spot_df = df_simple_spot_display_new.to_dict('records') 

# call QL at the initial date
t, r = par_curve_to_spot(init_date, par_tenors, par_yields, TENORS)
r_formatted = [ '%.4f' % elem for elem in r ]
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
        html.B("UST Spot Rates (semi-annual compounding, bootstrapped, QuantLib method)"),
        dtab.DataTable(
            id='spot-data-table',
            data = selected_spot_df, 
            columns = [{"name": i, "id": i} for i in DISPLAY_HDR],           
            page_size = 10
            )], style={'width': '70%'}
        ),
    
    html.Br(),
    html.Br(),
    
    # Simple Spot Rates Table    
    html.Div([
        html.B("UST Spot Rates (semi-annual compounding, bootstrapped, SIMPLE method)"),
        dtab.DataTable(
            id='simple-spot-data-table',
            data = selected_simple_spot_df, 
            columns = [{"name": i, "id": i} for i in DISPLAY_HDR],   # was new_column_list           
            page_size = 10
            )], style={'width': '70%'}
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
        date=init_date
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
    selected_df = df_table.to_dict('records')     
    
    # update the second table: the spot table using the QL method at the selected date
    par_tenors = list(df_fig['MONTHS'])  
    par_yields = list(df_fig['YIELD'])
    t, r = par_curve_to_spot(selected_date, par_tenors, par_yields, TENORS)
    r_formatted = [ '%.4f' % elem for elem in r ]
    full_spot_row = [selected_date] + r_formatted
    df_spot = pd.DataFrame(columns=new_column_list)
    df_spot.loc[0] = full_spot_row
        
    # build a new df for the QL-method spot data to display
    df_ql_spot_display = df_spot[DISPLAY_TENORS_STR]
    df_ql_spot_display_new = pd.DataFrame(columns=DISPLAY_HDR)
    new_row = [last_date] + list(df_ql_spot_display.loc[0])
    df_ql_spot_display_new.loc[0] = new_row
    selected_spot_df = df_ql_spot_display_new.to_dict('records')
    
    # update the the third table: the spot table using the SIMPLE method at the selected date
    # see these same statements in the initializing table earlier for comments on what they do
    par_rates = ust_to_par_rates(selected_date)
    simple_spot_rates = par_rates_to_spot(par_rates)     
    simple_spot_rates_formatted =  [ '%.4f' % elem for elem in simple_spot_rates ] 
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
