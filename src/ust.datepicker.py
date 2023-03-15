# DO NOT start a web server; this code starts the server!
# visit http://localhost:8050/ in your web browser
# or visit http://127.0.0.1:8050/ in your web browser.

# tests datepicker; needs to catch 'callback errors' on non-market dates

from datetime import date
from dash import Dash, dcc, html, Input, Output
import os
import plotly.express as px
import pandas as pd
from data import rates

fp = __file__
fhead, ftail = os.path.split(fp)

CSV_PATH = 'rates.csv'

# load the rates.csv data into a dataframe
df = rates.load_rates(CSV_PATH)

# get the first and last date in the rates file
first_date = df.index[0].strftime('%Y-%m-%d')
last_date = df.index[-1].strftime('%Y-%m-%d')

app = Dash(__name__)

print(df)

def build_df(reqdate):
    df2 = df.loc[reqdate].dropna()
 
    d = {
        'YEARS': [rates.tenor_name_to_year(tenor_name) for tenor_name in df2.keys()],
        'YIELD':df2.values
    }
    df_test = pd.DataFrame(d)
    print(df_test)
    return df_test

df_current = build_df(last_date)
fig = px.line(df_current, x="YEARS", y="YIELD", markers=True)
fig.update_traces(marker=dict(size=12,color='Red'))

app.layout = html.Div(children=[
    html.H1(children='Testing Dash'),
    
    html.H2(children='file = '+ ftail),
               
             
    dcc.Graph(
        id='yield-curve-graph',
        figure=fig
    ),
    
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
    Input('date-picker-single', 'date')
)
def update_figure(selected_date):
    print('new selected date=' + selected_date)
    df_fig = build_df(selected_date)
    fig = px.line(df_fig, x="YEARS", y="YIELD", markers=True,
                  title='Yield Curve on '+ selected_date)
    fig.update_traces(marker=dict(size=12,color='Red'))
    return fig    

if __name__ == '__main__':
    app.run_server(debug=True)
