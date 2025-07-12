import dash
import os
import sys
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import numpy as np
import webbrowser
import threading
from src.Car_buying_plot_functions import price_vs_age_plot_scatter
from src.Car_buying_plot_functions import custom_boxplot_no_whiskers
from src.paths import PARENT_DIR
import hopsworks
from dotenv import load_dotenv

# Load data from Hopsworks

#--------------------------------------
#sys.path.append(os.path.abspath("../src"))
load_dotenv(PARENT_DIR/'.env')

HOPSWORKS_PROJECT_NAME='Cars_project'
HOPSWORKS_API_KEY=os.environ['HOPSWORKS_API_KEY']

project = hopsworks.login(
    project=HOPSWORKS_PROJECT_NAME,
    api_key_value=HOPSWORKS_API_KEY
)

feature_store = project.get_feature_store()
# Retrieve your feature group
feature_group = feature_store.get_feature_group(
    name="batch_data_cars",  # must match the name used during creation
    version=3
)

# Read it into a DataFrame
df_from_fg = feature_group.read()  # this returns a Pandas DataFrame
df_from_fg.rename(columns={
    'url': 'URL',
    'power_hp': 'power_HP'
}, inplace=True)

#--------------------------------------
df=df_from_fg
#df.info()
#df = pd.read_csv('data/autoscout_data_with_predictions.csv')


# Dashboard code

#--------------------------------------
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server=app.server

app.layout = dbc.Container([
    dcc.Store(id='redirect-store'),

    dbc.Row([
        dbc.Col([
            html.Div([
                html.H4("Filter Vehicle Data", className="mb-3"),

                dbc.Row([
                    dbc.Col([
                        html.H5("Brand"),
                        dcc.Dropdown(
                            id='brand-dropdown',
                            options=[{'label': b, 'value': b} for b in df['brand'].unique()],
                            value=df['brand'].unique()[0]
                        ),
                    ], width=6),

                    dbc.Col([
                        html.H5("Model"),
                        dcc.Dropdown(id='model-dropdown'),
                    ], width=6)
                ]),

                html.Br(),
                html.H5("Vehicle Age (months)"),
                dcc.RangeSlider(
                    id='age-slider', step=1,
                    tooltip={"placement": "bottom", "always_visible": True},
                    marks=None
                ),
                html.Br(),
                html.H5("Mileage (kms)"),
                dcc.RangeSlider(
                    id='mileage-slider', step=1000,
                    tooltip={"placement": "bottom", "always_visible": True},
                    marks=None
                ),
                html.Br(),
                html.H5("Power (HP)"),
                dcc.RangeSlider(
                    id='power-slider', step=1,
                    tooltip={"placement": "bottom", "always_visible": True},
                    marks=None
                ),
            ],
            style={
                "border": "1px solid #ddd",
                "padding": "20px",
                "borderRadius": "10px",
                "backgroundColor": "#f9f9f9"
            })
        ], width=6),

        dbc.Col([
            html.Img(id='car-image',
                     style={
                         'width': '100%',
                         "padding": "40px",
                         'object-fit': 'contain',
                         'maxHeight': '450px'
                     })
        ], width=6)
    ]),

    dbc.Row([
        dbc.Col([
            dcc.Graph(id='price-age-plot', style={'height': '600px'})
        ], width=6),

        dbc.Col([
            dcc.Graph(id='deviation-plot', style={'height': '600px'})
        ], width=6)
    ])
], fluid=True, style={"padding": "30px"})

@app.callback(
    Output('model-dropdown', 'options'),
    Output('model-dropdown', 'value'),
    Input('brand-dropdown', 'value')
)
def update_models(brand):
    models = df[df['brand'] == brand]['model'].unique()
    return [{'label': m, 'value': m} for m in models], models[0]

@app.callback(
    Output('age-slider', 'min'), Output('age-slider', 'max'), Output('age-slider', 'value'),
    Output('mileage-slider', 'min'), Output('mileage-slider', 'max'), Output('mileage-slider', 'value'),
    Output('power-slider', 'min'), Output('power-slider', 'max'), Output('power-slider', 'value'),
    Input('brand-dropdown', 'value'),
    Input('model-dropdown', 'value')
)
def update_slider_bounds(brand, model):
    filtered = df[(df['brand'] == brand) & (df['model'] == model)]

    age_min, age_max = int(filtered['vehicle_age'].min()), int(filtered['vehicle_age'].max())
    mileage_min, mileage_max = int(filtered['mileage'].min()), int(filtered['mileage'].max())

    df_filtered_by_age_mileage = df[
        (df['vehicle_age'] >= age_min) & (df['vehicle_age'] <= age_max) &
        (df['mileage'] >= mileage_min) & (df['mileage'] <= mileage_max)
    ]
    power_min = int(df_filtered_by_age_mileage['power_HP'].min())
    power_max = int(df_filtered_by_age_mileage['power_HP'].max())

    return (
        age_min, age_max, [age_min, age_max],
        mileage_min, mileage_max, [mileage_min, mileage_max],
        power_min, power_max, [power_min, power_max]
    )

@app.callback(
    Output('price-age-plot', 'figure'),
    Output('deviation-plot', 'figure'),
    Input('brand-dropdown', 'value'),
    Input('model-dropdown', 'value'),
    Input('age-slider', 'value'),
    Input('mileage-slider', 'value'),
    Input('power-slider', 'value')
)
def update_plots(brand, model, age, mileage, power):
    age_min, age_max = age
    mileage_min, mileage_max = mileage
    power_min, power_max = power

    filtered_df = df[
        (df['brand'] == brand) &
        (df['model'] == model) &
        (df['vehicle_age'] >= age_min) & (df['vehicle_age'] <= age_max) &
        (df['mileage'] >= mileage_min) & (df['mileage'] <= mileage_max) &
        (df['power_HP'] >= power_min) & (df['power_HP'] <= power_max)
    ].copy()

    df_filtered_by_sliders = df[
        (df['vehicle_age'] >= age_min) & (df['vehicle_age'] <= age_max) &
        (df['mileage'] >= mileage_min) & (df['mileage'] <= mileage_max) &
        (df['power_HP'] >= power_min) & (df['power_HP'] <= power_max)
    ].copy()

    fig1 = price_vs_age_plot_scatter(filtered_df, brand, model)
    fig2 = custom_boxplot_no_whiskers(df_filtered_by_sliders, selected_model=model)
    return fig1, fig2

# 🔁 New Callback: Update image based on model selection
@app.callback(
    Output('car-image', 'src'),
    Input('model-dropdown', 'value')
)
def update_car_image(model):
    if model:
        return f"/assets/{model.lower()}.png"
    return "/assets/default.png"

@app.callback(
    Output('redirect-store', 'data'),
    Input('price-age-plot', 'clickData'),
    prevent_initial_call=True
)
def open_listing(clickData):
    if clickData and 'customdata' in clickData['points'][0]:
        relative_url = clickData['points'][0]['customdata'][0]
        full_url = f'https://www.autoscout24.nl/{relative_url}'
        threading.Thread(target=lambda: webbrowser.open_new_tab(full_url)).start()
    return dash.no_update

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8050)
