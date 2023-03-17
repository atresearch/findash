# DO NOT start a web server; this code starts the server!
# visit http://localhost:8050/ in your web browser
# or visit http://127.0.0.1:8050/ in your web browser.

# using https://plotly.com/python/horizontal-vertical-shapes/ to add recession period to ts plots


from dash import Dash, dcc, html
import os
import pandas as pd
import plotly.graph_objects as go
import datetime as dt
import dateutil.relativedelta  

fp = __file__
fhead, ftail = os.path.split(fp)

CSV_PATH = 'rates.csv'
USREC_PATH = 'USREC.csv'



GOOD_COLS = ['Date','3 Mo','6 Mo','1 Yr','2 Yr','3 Yr','5 Yr','7 Yr','10 Yr','30 Yr']
df = pd.read_csv(CSV_PATH)
df_rec = pd.read_csv(USREC_PATH)

# USREC.csv has columns 'DATE' (a date in form YYYY-MM-DD) and USREC (an integer = 0 or 1 ) 
# a recession start-date is a DATE such that USREC=1 and the prior DATE has USREC=0
# a recession end-date is a DATE such that USREC=1 and the subsequent DATE has USREC=0
df_rec["Prior_Row"] = ""
df_rec["Prior_Row"] = df_rec["USREC"].shift(1)
df_rec["Next_Row"] = ""
df_rec["Next_Row"] = df_rec["USREC"].shift(-1)

# print(df_rec)

df_rec_ends = df_rec.loc[(df_rec["USREC"] == 0) & (df_rec["Prior_Row"] == 1.0)]
x_rec_ends = list(df_rec_ends["DATE"])
# remove the first element, 1855-01-01, so every stop has a preceding start:
x_rec_ends.pop(0)


df_rec_starts = df_rec.loc[(df_rec["USREC"] == 0) & (df_rec["Next_Row"] == 1.0)]
x_rec_starts = list(df_rec_starts["DATE"])
        
# print("RECESSION STARTS: LEN=", len(x_rec_starts))
# print(x_rec_starts)    

# print("RECESSION ENDS: LEN=",len(x_rec_ends))
# print(x_rec_ends)  

# select only the good columns with more-or-less continuity from 1990
df1 = df[GOOD_COLS]
data_start_date = list(df1['Date'])[0]
# print("data start date=",data_start_date)

fig = go.Figure([go.Scatter(x=df1['Date'], y=df1['3 Mo'], name='3 Mo')])                    
fig.add_scatter(x=df1['Date'], y=df1['10 Yr'], name='10 Yr',mode='lines')
fig.add_scatter(x=df1['Date'], y=df1['30 Yr'], name='30 Yr',mode='lines')

# if the two recession start/stop lists have the same length, add the start/stop pairs
if len(x_rec_starts) == len(x_rec_ends):
    for idx, x0 in enumerate(x_rec_starts):
        x1 = x_rec_ends[idx]
        if x0 >= data_start_date:
            # print("painting a recession band from ",x0," to ",x1)
            fig.add_vrect(x0, x1, fillcolor="green", opacity=0.25, line_width=0)  
fig.update_layout(legend_title_text='Maturity')
fig.update_layout(title_text="Constant Maturity Yields(%) [Shaded areas indicate US recessions]")                             

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
