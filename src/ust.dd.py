# DO NOT start a web server; this code starts the server!
# visit http://localhost:8050/ in your web browser
# or visit http://127.0.0.1:8050/ in your web browser.


from dash import Dash, dcc, html, Input, Output
import os
import plotly.express as px
import pandas as pd

fp = __file__
fhead, ftail = os.path.split(fp)

CSV_PATH = 'rates.csv'
init_date = '2023-03-09'    # all yields there, works fine
# reqdate = '1990-01-04'  # some yields missing, works fine
# reqdate = '1990-01-06'  # Todo: FAILS BADLY: needs handler for missing/bad dates
UST_YEARS = [30/365,60/365,90/365,120/365,182/365,1,2,3,5,7,10,20,30]

app = Dash(__name__)

df = pd.read_csv(CSV_PATH,parse_dates=["Date"]).set_index("Date")
print(df)

def build_df(reqdate):
    df2 = df.loc[reqdate]
    #if(df2.empty == True):
    #    sys.exit("No data for requested date")    
    RAW_YIELDS = df2.values.tolist()   # 13 element list containing yields(%)

    # drop entries where yield is zero or missing
    numcols = len(RAW_YIELDS) 
    NEW_YEARS = []
    NEW_YIELDS = []
    for i in range(numcols):
        if RAW_YIELDS[i] > 0:
            NEW_YEARS.append(UST_YEARS[i])
            NEW_YIELDS.append(RAW_YIELDS[i])
    print("final data has len=",len(NEW_YIELDS))

# d = {'YEARS':UST_YEARS,'YIELD':list}
    d = {'YEARS':NEW_YEARS,'YIELD':NEW_YIELDS}
    df_test = pd.DataFrame(d)
    print(df_test)
    return df_test

df_current = build_df(init_date)
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
        dcc.Dropdown(['1990-01-02','2023-03-08','2023-03-09'],'2023-03-09',
                     id='my-input-date'),
        html.Div(id='my-output-date')
    ], style={"width": "20%"})
])

@app.callback(
    Output('yield-curve-graph', 'figure'),  
    Input('my-input-date', 'value')
)
def update_figure(selected_date):
    df_fig = build_df(selected_date)
    fig = px.line(df_fig, x="YEARS", y="YIELD", markers=True,
                  title='Yield Curve on '+ selected_date)
    fig.update_traces(marker=dict(size=12,color='Red'))
    return fig    

if __name__ == '__main__':
    app.run_server(debug=True)
