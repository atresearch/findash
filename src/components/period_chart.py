import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc


period_input = html.Div(
    [
        dbc.RadioItems(
            id="radios",
            className="btn-group",
            inputClassName="btn-check",
            labelClassName="btn btn-outline-primary",
            labelCheckedClassName="active",
            options=[
                {"label": "3m", "value": '3m'},
                {"label": "1y", "value": '1y'},
                {"label": "5y", "value": '5y'},
                {"label": "10y", "value": '10y'},
                {"label": "20y", "value": '20y'},
                {"label": "all", "value": 'all'},
            ],
            value='3m',
        ),
        html.Div(id="output"),
    ],
    className="radio-group",
)

dcc.Graph(
    id='yield-curve-graph',
    figure=None
),