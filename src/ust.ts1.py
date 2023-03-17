# DO NOT start a web server; this code starts the server!
# visit http://localhost:8050/ in your web browser
# or visit http://127.0.0.1:8050/ in your web browser.


from dash import Dash, dcc, html
import os
import pandas as pd
import plotly.graph_objects as go

fp = __file__
fhead, ftail = os.path.split(fp)

CSV_PATH = 'rates.csv'
GOOD_COLS = ['Date','3 Mo','6 Mo','1 Yr','2 Yr','3 Yr','5 Yr','7 Yr','10 Yr','30 Yr']
df = pd.read_csv(CSV_PATH)

# select only the good columns with more-or-less continuity from 1990
df1 = df[GOOD_COLS]

fig = go.Figure([go.Scatter(x=df1['Date'], y=df1['3 Mo'], name='3 Mo')])                    
fig.add_scatter(x=df1['Date'], y=df1['10 Yr'], name='10 Yr',mode='lines')
fig.add_scatter(x=df1['Date'], y=df1['30 Yr'], name='30 Yr',mode='lines')
fig.update_layout(legend_title_text='Maturity')
fig.update_layout(title_text="Constant Maturity Yields(%)")                             

app = Dash(__name__)

app.layout = html.Div(children=[
    html.H1(children='Testing Dash'),    
    html.H2(children='file = '+ ftail),    
    dcc.Graph(
        id='multi-time-series',
        figure=fig
    )       
])

if __name__ == '__main__':
    app.run_server(debug=True)
