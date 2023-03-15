import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc

dash.register_page(__name__, path='/rates')

# the style arguments for the sidebar. We use position:fixed and a fixed width
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": "56px",
    "left": 0,
    "bottom": 0,
    "width": "20rem",
    "padding": "1rem 1rem",
    "background-color": "#f8f9fa",
}

# the styles for the main content position it to the right of the sidebar and
# add some padding.
CONTENT_STYLE = {
    "margin-left": "22rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

first_date = '2000-01-01'
last_date = '2022-12-31'

date_input = html.Div(
    dcc.DatePickerSingle(
        id='date-picker-single',
        min_date_allowed=first_date,
        max_date_allowed=last_date,
        initial_visible_month=last_date,
        disabled_days=[],
        first_day_of_week=1,
        day_size=32,
        date=last_date,
    ),
    className='text-center mt-3'
)
    
rate_type_input = html.Div(
    [
        dbc.Select(
            [
                "Par Rates", 
                "Zero Curve", 
                "Discount Curve",
                "Forward Curve"
            ],
            "Par Rates",
            id="rate-type-select",
            class_name='mt-3 mb-3'
        ),
    ]
)

tenors_input = html.Div(
    [
        dbc.Label("Tenors:", class_name='mt-3'),
        dbc.Select(
            ["Treasury", "Monthly", "Quarterly", "Yearly"],
            "Treasury",
            id="tenor-select",
        ),
    ]
)


interpolation_type_input = html.Div(
    [
        dbc.Label("Interpolation method:", class_name='mt-3'),
        dbc.Select(
            [
                "Natural Cubic Spline",
                "Linear"
            ],
            "Natural Cubic Spline",
            id="interpolation-type-select",
        ),
    ]
)

period_input = html.Div(
    [
        dbc.Label("Historical period:"),
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
            value=1,
        ),
        html.Div(id="output"),
    ],
    className="radio-group",
)


tab1_content = html.Div(
        [
            date_input,
            tenors_input,
            interpolation_type_input,
        ]
)

tab2_content = html.Div(
        [
            period_input,
            html.P("todo: Checkboxes to select tenors like 3M, 2Y", className="card-text"),
        ],
    className="mt-3"
)


tabs = dbc.Tabs(
    [
        dbc.Tab(tab1_content, label="PIT"),
        dbc.Tab(tab2_content, label="Hist"),
    ]
)

sidebar = html.Div(
    [
        html.H3("Treasury Rates", className="display-6"),
        rate_type_input,
        tabs,
    ],
    style=SIDEBAR_STYLE,
)

content = html.Div(id="page-content", style=CONTENT_STYLE)

layout = html.Div([dcc.Location(id="url"), sidebar, content])

