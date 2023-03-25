# import dash
# import dash_html_components as html
from dash import Dash, dcc, html

url = 'https://financepress.com/wp-content/uploads/2016/06/Lewis.Vol2_.TOC_.pdf'

app = Dash(__name__)

# app.layout = html.Iframe(src='/path/to/your/pdf/file.pdf', style={'width': '100%', 'height': '800px'})

# app.layout = html.Iframe(src=url, style={'width': '100%', 'height': '800px'})

app.layout = html.Div(
    [
        html.H1('Testing the display of PDFs in Dash'),
        html.ObjectEl(
            # To my recollection you need to put your static files in the 'assets' folder
            # data="assets/ChatGPT.pdf",  # local file: works
            data = url,   # remote file: works
            type="application/pdf",
            style={"width": "800px", "height": "600px"}
        ),
    ])

if __name__ == '__main__':
    app.run_server(debug=True)
