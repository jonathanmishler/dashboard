import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd

import app_data

# Create the App
external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Create the Data
main_df = app_data.load()
chain_list = app_data.create_chain_list(main_df, ["Kroger", "HEB"])
# Create the Main Plot
fig = px.scatter_mapbox(
    chain_list,
    lat="lat",
    lon="lon",
    color="chain",
    custom_data=["Customer", "Address"],
    color_discrete_map={"Kroger": "#134b97", "HEB": "#ee3124"},
)

fig.update_traces(
    marker=dict(size=8),
    hovertemplate="<b>%{customdata[0]}</b><br><i>%{customdata[1]}</i>",
)

fig.update_layout(mapbox_style="stamen-toner", margin={"r": 0, "t": 0, "l": 0, "b": 0}, autosize=True, height='auto')

# Create the Layout
app.layout = html.Div(
    children=[
        html.H1(children="Chain Account Map"),
        dcc.Graph(id="chain_map", figure=fig)
    ]
)

if __name__ == "__main__":
    app.run_server(debug=True)
