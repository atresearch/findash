# DO NOT start a web server; this code starts the server!
# visit http://localhost:8050/ in your web browser
# or visit http://127.0.0.1:8050/ in your web browser.

# 3/22/2023 alan: error in build_complete_spot_rates corrected, [n]->[n+1] in two places
# 3/23/2023 alan: add sub-6m spot rates using thijs's rule
# 3/23/2023 alan: major overhaul: fixed errors associated to missing yields: for example, try init_date = '1993-10-01'
# 3/25/2023 alan: reworked SIMPLE bootstrap method to compute spot rates for every maturity month 1, 2, 3, ..., 360
# 3/28/2023 alan: added forward rates table (one month rate, starting in m months, m = 0, 1, 2, ..., 359, cont-comp)
# 3/28/2023 alan: add new chart with spot and forward rates
# 3/28/2023 alan: trying cubic spline interpolation on the par rates prior to extracting spot rates
# 3/29/2023 alan: trying monotone cubic spline
# 3/31/2023 alan: revamp: apply the spline to the SPOT rates, using the optimizer to fit the input UST par yield data  
# 4/3/2023  alan: cleanup: removed unused functions
# 4/5/2023  alan: now using Jan Mayle(2022) Formulas 5,6 for maturities < 6m 

from datetime import date
from dash import Dash, dcc, html, Input, Output
from dash import dash_table as dtab
import os
import plotly.express as px
import pandas as pd
from data import rates  # won't run: missing "data.storage_backend"?
# from dataOLD import rates
# from calc.ratesOLD import par_curve_to_spot
from calc.rates import par_curve_to_spot
import numpy as np
# from scipy.interpolate import CubicSpline 
from scipy.interpolate import PchipInterpolator, CubicSpline
from scipy.optimize import minimize
import plotly.graph_objects as go
import math
from timeit import default_timer as timer


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
# init_date = "1999-06-28"    # compare against Brian Sack 2000 paper 

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

# map the monthly cc-spot-rates to one-month forward rates (continuous-compounding, percent)
# input: cc_spot_rates is complete list of cont-comp spot-rates (%) for maturity months 1, 2, 3, ..., 360
# output: one-month foward rate starting in m months, m = 0, 1, 2, ..., 359
def cc_spot_rates_to_cc_forward_rates(cc_spot_rates): 
    len3 = 360
    forward_rates = [0 for n in range(len3)]
    DF1 = 1.0
    t_years = 1/12
    for n in range(len3):
        T = (n+1)/12
        DF2 = np.exp(-0.01*cc_spot_rates[n]*T)
        forward_rates[n] = -(100/t_years)*(np.log(DF2/DF1)) 
        DF1 = DF2
    return forward_rates  


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

# construct a dataframe for the par rate spline scatter
def build_df_chart_par(par_rates):
    Years = [i/12 for i in range(1,361)]
    d = {
        'YEARS': Years,
        'YIELD': par_rates
    }
    df_chart = pd.DataFrame(d)
    return df_chart

# construct a dataframe for the spot rate scatter
def build_df_chart_spot(spot_rates):
    Years = [i/12 for i in range(1,361)]
    d = {
        'YEARS': Years,
        'YIELD': spot_rates
    }
    df_chart = pd.DataFrame(d)
    return df_chart

# construct a dataframe for the forward rate scatter
def build_df_chart_forward(forward_rates):
    Years = [i/12 for i in range(1,361)]
    d = {
        'YEARS': Years,
        'YIELD': forward_rates
    }
    df_chart = pd.DataFrame(d)
    return df_chart

# convert semiannual-compounded rates to continuously compounded rates, both in percent
def sa_to_cc(sa_rates):
    len1 = len(sa_rates)
    cc_rates = [0 for i in range(len1)]
    for i in range(len1):
        accum_factor = 1 + 0.01*sa_rates[i]/2
        cc_rate = 2*np.log(accum_factor)
        cc_rates[i] = 100*cc_rate 
    return cc_rates   

# convert cont-comp rates to semiannual-compounded rates, both in percent
def cc_to_sa(cc_rates):
    len1 = len(cc_rates)
    sa_rates = [0 for i in range(len1)]
    for i in range(len1):
        # accum_factor = (1 + 0.01*sa_rates[i]/2)**2
        accum_factor = np.exp(0.01*cc_rates[i])
        sa_rate = 2*(np.power(accum_factor,0.5) - 1.0)
        sa_rates[i] = 100*sa_rate 
    return sa_rates 

# convert a complete list of arbitrary spot rates (cc, percent) to a clean bond price with maturity M (months) = one of 1, 2, ..., 360 
# input: M, coupon (annual dollars per $100 par value), spot rates (continuously compounded, percent (list of length 360) 
# Uses Mayle (Formula 6) for bond price for  M < 6
def cc_spot_rates_to_clean_bond_price(M, coupon, cc_spot_rates):
    
    # months_to_next_coupon = M % 6  # months until the next cash-flow/coupon payment
    months_to_next_coupon = 1 + (M-1) % 6  # months until the next cash-flow/coupon payment
    # num_coupons = 1 + math.floor(M/6)  # number of coupon payments to be received until maturity
    num_coupons = max(math.floor(M/6),1) 
    # print("months_to_next_coupon=",months_to_next_coupon," num_coupons=",num_coupons)
    Mc = [months_to_next_coupon + 6*n for n in range(num_coupons)]  # time in months to each coupon payment
    if M < 6:
        Rspot = cc_to_sa([cc_spot_rates[M-1]])[0]  # semi-annual spot rate in percent
        ratio = (1 + 0.5*0.01*coupon)/(1 + 0.5*0.01*Rspot*months_to_next_coupon/6) # note ratio=1 for 6 months and coupon=Rspot
        dirty_price = 100*ratio  # Mayle Formula 6        
    else:
        disc_factors = [np.exp(-0.01*cc_spot_rates[m-1]*m/12) for m in Mc] # discount factors at each coupon payment time        
        dirty_price =  0.5*coupon*sum(disc_factors) + 100*disc_factors[-1]  # dirty price of the bond    
    accrued_interest =  0.5*coupon*(1 - (months_to_next_coupon/6)) # accrued interest the buyer must pay 
    clean_price = dirty_price - accrued_interest  # clean_price which is the optimizer target    
     
    return clean_price    
    

# create a list: a complete set of spot rates for months: 1,2, ..., 360 using cubic spline interpolation through the 13 ust_spot_rates
def ust_spot_to_all_spot_rates(ust_tenors, ust_spot_rates):
#   f = PchipInterpolator(ust_tenors, ust_spot_rates, extrapolate=True)     # monotone
    f = CubicSpline(ust_tenors, ust_spot_rates, bc_type='natural') 
    return f(TENORS)     

# objective function to be minimized: the sum of the squares of (clean bond price - 100)
# cc_ust_spot_rates is the list of cc spot rates at the 13 par_tenors
# these will be varied until the clean price of all the bonds at those tenors is 100
def obj(cc_ust_spot_rates, df_input):
    par_tenors = list(df_input['MONTHS'])  
    par_yields = list(df_input['YIELD'])
    cc_all_spot_rates = ust_spot_to_all_spot_rates(par_tenors, cc_ust_spot_rates)
    sq_err = 0
    n = 0
    for M in par_tenors:
        coupon = par_yields[n]
        bond_price = cc_spot_rates_to_clean_bond_price(M, coupon, cc_all_spot_rates)
        sq_err += (bond_price - 100)**2
        n += 1
    return sq_err
    

app = Dash(__name__)

# initial ust data
df_current = build_df(init_date)
par_yields = list(df_current['YIELD'])
par_tenors = list(df_current['MONTHS'])

# init the par rates chart
# df_p = build_df_chart_par(par_rates)
fig = go.Figure([go.Scatter(x=df_current['YEARS'], y=df_current['YIELD'], name='UST par rates')])                    
# fig.add_scatter(x=df_p['YEARS'], y=df_p['YIELD'], name='Cubic Spline',mode='lines')
fig.update_layout(title_text="Par Yields-to-Maturity (semiannual compounding)",
                      xaxis_title="YEARS", yaxis_title="YIELD")

# init the one-line par rate table
df_tmp = build_df2(init_date)
column_list = df_tmp.columns
selected_df = df_tmp.to_dict('records')  # the dash table component uses this form for its 'data' property
  
# build complete list of optimal monthly spot rates at the initial date, sa compounding 
init_rates = sa_to_cc(par_yields)   # initial rates are the cc par_yields
res = minimize(obj, init_rates, args=df_current, tol=1e-6)
optimal_cc_ust_spot_rates = res.x.tolist()
optimal_cc_all_spot_rates = ust_spot_to_all_spot_rates(par_tenors, optimal_cc_ust_spot_rates)
simple_spot_rates = cc_to_sa(optimal_cc_all_spot_rates) 

# format and prepare the SIMPLE-method spot rates for table display
simple_spot_rates_formatted =  [ '%.4f' % elem for elem in simple_spot_rates ] 
simple_spot_row = [init_date] + simple_spot_rates_formatted
df_simple_spot = pd.DataFrame(columns=new_column_list)
df_simple_spot.loc[0] = simple_spot_row

# build a new df for the SIMPLE-method spot data to display
df_simple_spot_display = df_simple_spot[DISPLAY_TENORS_STR]
df_simple_spot_display_new = pd.DataFrame(columns=DISPLAY_HDR)
new_row = [init_date] + list(df_simple_spot_display.loc[0])
df_simple_spot_display_new.loc[0] = new_row
selected_simple_spot_df = df_simple_spot_display_new.to_dict('records') 

# build complete list of new/optimal monthly forward rates (CC) at the initial date 
forward_rates_cc = cc_spot_rates_to_cc_forward_rates(optimal_cc_all_spot_rates)
# format and prepare the forwards for table display
forwards_formatted =  [ '%.4f' % elem for elem in forward_rates_cc ] 
forwards_row = [init_date] + forwards_formatted
df_forwards = pd.DataFrame(columns=new_column_list)
df_forwards.loc[0] = forwards_row

# init the spot rates chart
df_s = build_df_chart_spot(simple_spot_rates)
fig_s = px.scatter(df_s, x="YEARS", y="YIELD", title="Fitted Spot Rates (cubic spline, semiannual compounding)")
fig_s.update_traces(marker=dict(size=3,color='Blue'))

# init the forward rates chart
df_f = build_df_chart_forward(forward_rates_cc)
fig_f = px.scatter(df_f, x="YEARS", y="YIELD", title="Forward Rates (continuous compounding)")
fig_f.update_traces(marker=dict(size=3,color='Green'))

# build a new df for the forwards to display
df_forwards_display = df_forwards[DISPLAY_TENORS_STR]
df_forwards_display_new = pd.DataFrame(columns=DISPLAY_HDR)
new_row = [init_date] + list(df_forwards_display.loc[0])
df_forwards_display_new.loc[0] = new_row
selected_forwards_df = df_forwards_display_new.to_dict('records') 

# call QL at the initial date
t, r = par_curve_to_spot(init_date, par_tenors, par_yields, TENORS)
r_formatted = [ '%.4f' % elem for elem in r ]
full_spot_row = [init_date] + r_formatted
df_spot = pd.DataFrame(columns=new_column_list)
df_spot.loc[0] = full_spot_row

# build a new df for the QL-method spot data to display
df_ql_spot_display = df_spot[DISPLAY_TENORS_STR]
df_ql_spot_display_new = pd.DataFrame(columns=DISPLAY_HDR)
new_row = [init_date] + list(df_ql_spot_display.loc[0])
df_ql_spot_display_new.loc[0] = new_row
selected_spot_df = df_ql_spot_display_new.to_dict('records')

app.layout = html.Div(children=[
    html.H1(children='UST Yield Curve Transformations'),
    
    html.H2(children='file = '+ ftail),
               
             
    dcc.Graph(
        id='yield-curve-graph',
        figure=fig
    ),
    
    dcc.Graph(
        id='spot-graph',
        figure=fig_s
    ),
    
     dcc.Graph(
        id='forward-graph',
        figure=fig_f
    ),
    
    # Par Table    
    html.Div([
        html.B("Par Yields-to-Maturity (input data)"),
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
        html.B("Spot Rates (semi-annual compounding, QuantLib method)"),
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
        html.B("Spot Rates from Fitted Cubic Spline (semi-annual compounding)"),
        dtab.DataTable(
            id='simple-spot-data-table',
            data = selected_simple_spot_df, 
            columns = [{"name": i, "id": i} for i in DISPLAY_HDR],   # was new_column_list           
            page_size = 10
            )], style={'width': '70%'}
        ),
    
    html.Br(),
    html.Br(),
    
    # Forward Rates Table    
    html.Div([
        html.B("Forward Rates from Fitted Spot Rates (continuous compounding)"),
        dtab.DataTable(
            id='forwards-table',
            data = selected_forwards_df, 
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
    Output('spot-graph', 'figure'), 
    Output('forward-graph', 'figure'),
    Output('par-data-table', 'data'),
    Output('spot-data-table', 'data'),
    Output('simple-spot-data-table', 'data'),
    Output('forwards-table', 'data'),
    Input('date-picker-single', 'date')
)
def update_figure_and_tables(selected_date):
    
    # update the par rates chart
    df_fig = build_df(selected_date)
    fig = go.Figure([go.Scatter(x=df_fig['YEARS'], y=df_fig['YIELD'], name='UST par rates')])                    
#   fig.add_scatter(x=df_p['YEARS'], y=df_p['YIELD'], name='Cubic Spline',mode='lines')
    fig.update_layout(title_text="Par Yields-to-Maturity (semiannual compounding)",
                      xaxis_title="YEARS", yaxis_title="YIELD") 
    
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
    new_row = [selected_date] + list(df_ql_spot_display.loc[0])
    df_ql_spot_display_new.loc[0] = new_row
    selected_spot_df = df_ql_spot_display_new.to_dict('records')
    
    # update the the third table: the spot table using the SIMPLE method at the selected date
    starting_rates = sa_to_cc(par_yields)   # initial rates are the cc par_yields
    df_current = build_df(selected_date)
    start = timer()
    res = minimize(obj, starting_rates, args=df_current, tol=1e-6)
    end = timer()
    print(res.message)
    print("run-time1 was {:.4f} seconds".format(end-start))
    print("Number of iterations:",res.nit)
    optimal_cc_ust_spot_rates = res.x.tolist()
    # print("optimizer returned these sa rates=",cc_to_sa(optimal_cc_ust_spot_rates))
    optimal_cc_all_spot_rates = ust_spot_to_all_spot_rates(par_tenors, optimal_cc_ust_spot_rates)
    simple_spot_rates = cc_to_sa(optimal_cc_all_spot_rates)  
    simple_spot_rates_formatted =  [ '%.4f' % elem for elem in simple_spot_rates ] 
    simple_spot_row = [selected_date] + simple_spot_rates_formatted
    df_simple_spot = pd.DataFrame(columns=new_column_list)
    df_simple_spot.loc[0] = simple_spot_row
    df_simple_spot_display = df_simple_spot[DISPLAY_TENORS_STR]
    df_simple_spot_display_new = pd.DataFrame(columns=DISPLAY_HDR)
    new_row = [selected_date] + list(df_simple_spot_display.loc[0])
    df_simple_spot_display_new.loc[0] = new_row
    selected_simple_spot_df = df_simple_spot_display_new.to_dict('records')  
    
    # update the the 4th table: the forward rates
    forward_rates_cc = cc_spot_rates_to_cc_forward_rates(optimal_cc_all_spot_rates)
    forwards_formatted =  [ '%.4f' % elem for elem in forward_rates_cc ] 
    forwards_row = [selected_date] + forwards_formatted
    df_forwards = pd.DataFrame(columns=new_column_list)
    df_forwards.loc[0] = forwards_row
    df_forwards_display = df_forwards[DISPLAY_TENORS_STR]
    df_forwards_display_new = pd.DataFrame(columns=DISPLAY_HDR)
    new_row = [selected_date] + list(df_forwards_display.loc[0])
    df_forwards_display_new.loc[0] = new_row
    selected_forwards_df = df_forwards_display_new.to_dict('records') 
    
    # update the spot and forward charts
    df_s = build_df_chart_spot(simple_spot_rates)
    fig_s = px.scatter(df_s, x="YEARS", y="YIELD", title="Fitted Spot Rates (cubic spline, semiannual compounding)")
    fig_s.update_traces(marker=dict(size=3,color='Blue'))

    df_f = build_df_chart_forward(forward_rates_cc)
    fig_f = px.scatter(df_f, x="YEARS", y="YIELD", title="Forward Rates (continuous compounding)")
    fig_f.update_traces(marker=dict(size=3,color='Green'))      
        
    return fig, fig_s, fig_f, selected_df, selected_spot_df, selected_simple_spot_df, selected_forwards_df    

if __name__ == '__main__':
    app.run_server(debug=True)
