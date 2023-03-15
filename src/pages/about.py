import dash
from dash import html, dcc

dash.register_page(__name__, path='/about')

layout = html.Div(
    children=[
        html.H3(children='About'),
        html.Div(children='''
            This project is created by Alan Lewis, Thijs van den Berg
        '''),
    ],
    className='p-2'
)