
from common import *
from dash import Dash, html, dcc

app = Dash(__name__)
app.layout = html.Div(children=[ html.H1(children='Hello Dash') ])

app.run_server(debug=True)