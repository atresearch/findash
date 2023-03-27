from dash import Dash, html, dcc
import dash
import dash_bootstrap_components as dbc
import data

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("US Treasury Rates", href="/rates")),
        dbc.NavItem(dbc.NavLink("About", href="/about")),
    ],
    brand="Our Tool Name",
    brand_href="/",
    color="primary",
    dark=True,
)
from calc.rates import par_curve_to_spot

t, r = par_curve_to_spot('2023-02-19', [12, 24], [4.25, 4.50], [3, 6, 12, 18, 24])
print(t, r)


print('reading rates')
rates_source = data.storage_backend.LocalTextStream('rates.csv')
rates_df = data.rates.load_rates(rates_source)
print(rates_df)


app = Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    navbar,
	dash.page_container
])

if __name__ == '__main__':
	app.run_server(debug=True)
