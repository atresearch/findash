import dash
from dash import html, dcc

dash.register_page(__name__, path='/')

layout = html.Div(
    children=[
    html.H3(children='Home'),
    html.Div(children='''
       This is the home page.
    '''),
    ],
    className='p-2'
)