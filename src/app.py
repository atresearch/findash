from dash import Dash, html, dcc
import dash
import dash_bootstrap_components as dbc


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

app = Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    navbar,
	dash.page_container
])

if __name__ == '__main__':
	app.run_server(debug=True)
