import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import pandas as pd
import datetime
import numpy as np

# Inicializar la aplicación con un tema de Bootstrap
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Planta Dashboard"

# Datos ficticios para temperatura y humedad
def generar_datos_ficticios(fecha):
    horas = pd.date_range(start=fecha, periods=24, freq='H')
    temperatura = np.random.uniform(15, 35, size=24)
    humedad = np.random.uniform(40, 90, size=24)
    return pd.DataFrame({'Hora': horas, 'Temperatura': temperatura, 'Humedad': humedad})

# Layout de la aplicación
tabs = dbc.Tabs([
    # Pestaña 1: Información de la planta
    dbc.Tab(label='Información de la Planta', children=[
    dbc.Container([
        html.H1("Información de la Planta", className="text-center mt-4"),  # Centrado del título
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardBody([
                        html.H2("Suculenta Echeverias", className="card-text text-center"),
                        html.P("Las suculentas son un tipo de planta muy popular debido a su resistencia y belleza.", className="text-center"),
                        html.Br(),
                        html.Img(src="/assets/plant.jpeg", className="img-fluid mx-auto d-block", style={"max-width": "50%"})
                    ])
                ], className="mx-auto"),  # Esto centra la tarjeta
                width="6"  # Hace que la columna se ajuste a la tarjeta y ayuda a centrarla
            ),
            dbc.Col(
                dbc.Card([
                    dbc.CardBody([
                        html.P([html.Strong("Origen: "),"Las suculentas provienen de áreas áridas y semiáridas de todo el mundo, especialmente de África, América y algunas partes de Asia. Su capacidad para almacenar agua en hojas, tallos o raíces les permite sobrevivir en condiciones de sequía extrema."], className="text-justify"),
                        html.Br(),
                        html.H2("Cuidados", className="card-text text-center"),
                        html.Br(),
                        html.P([html.Strong("Luz: "), "Las suculentas necesitan al menos 4 a 6 horas de luz indirecta o filtrada al día. Una ventana soleada es ideal para su crecimiento en interiores.La luz directa es buena, pero puede quemar sus hojas si es muy intensa o si la planta no está acostumbrada.", html.Br(), html.Br(), html.Strong("Riego")," La regla general es regarlas solo cuando el sustrato esté completamente seco, lo cual suele ser cada dos o tres semanas, dependiendo de las condiciones ambientales. Regar directamente el sustrato y evitar que el agua se acumule en las hojas o el centro de la planta, ya que esto puede causar pudrición. El exceso de riego es la causa más común de muerte en suculentas, ya que sus raíces se pudren fácilmente en sustratos encharcados.",html.Br(), html.Br(), html.Strong("Suelo:"), " Usar un sustrato especial para suculentas o cactus que drene bien, evitando mezclas que retengan demasiada agua. Se puede añadir arena gruesa o perlita al sustrato para mejorar el drenaje.",
                        html.Br(), html.Br(), html.Strong("Temperatura:")," Las suculentas prefieren temperaturas entre 15°C y 29°C durante el día, aunque pueden tolerar temperaturas más bajas durante la noche. Son sensibles al frío extremo, especialmente aquellas que no están adaptadas a climas fríos.",
                        html.Br(),], className="text-justify"),
                    ])
                ], className="mx-auto"),  # Esto centra la tarjeta
                width="6"  # Hace que la columna se ajuste a la tarjeta y ayuda a centrarla
            ),
        ], justify="center", className="mt-4"),  # Centra el contenido en la fila
    ])
]),

    # Pestaña 2: Visualización de Temperatura y Humedad
    dbc.Tab(label='Visualización de Datos', children=[
        dbc.Container([
            html.H1("Visualización de Temperatura y Humedad", className="mt-4"),
            dcc.DatePickerSingle(
                id='date-picker',
                date=datetime.date.today(),
                className='mt-3'
            ),
            html.Div(id='output-gauges', className='mt-4'),
            dcc.Graph(id='time-series-graph-temperatura', className='mt-4'),
            dcc.Graph(id='time-series-graph-humedad', className='mt-4')
        ])
    ]),

    # Pestaña 3: Vacía por ahora
    dbc.Tab(label='Pestaña Vacía', children=[
        dbc.Container([
            html.H1("Pestaña Vacía", className="mt-4"),
            html.P("Contenido próximamente...")
        ])
    ])
])

# Layout principal
app.layout = dbc.Container([
    html.H1("Dashboard de Planta", className="text-center mt-4 mb-4"),
    tabs
], fluid=True)

# Callback para actualizar los gauges y las series de tiempo
@app.callback(
    [Output('output-gauges', 'children'),
     Output('time-series-graph-temperatura', 'figure'),
     Output('time-series-graph-humedad', 'figure')],
    [Input('date-picker', 'date')]
)
def actualizar_visualizacion(fecha_seleccionada):
    # Generar datos ficticios para la fecha seleccionada
    datos = generar_datos_ficticios(fecha_seleccionada)

    # Crear gráficos de gauge para temperatura y humedad
    gauge_temperatura = dcc.Graph(
        figure=go.Figure(go.Indicator(
            mode="gauge+number",
            value=datos['Temperatura'].mean(),
            title={'text': "Temperatura Media (°C)"},
            gauge={'axis': {'range': [0, 50]}}
        )), style={'display': 'inline-block', 'width': '45%'}
    )

    gauge_humedad = dcc.Graph(
        figure=go.Figure(go.Indicator(
            mode="gauge+number",
            value=datos['Humedad'].mean(),
            title={'text': "Humedad Media (%)"},
            gauge={'axis': {'range': [0, 100]}}
        )), style={'display': 'inline-block', 'width': '45%'}
    )

    # Crear serie de tiempo para temperatura
    figura_serie_tiempo_temperatura = go.Figure()
    figura_serie_tiempo_temperatura.add_trace(go.Scatter(x=datos['Hora'], y=datos['Temperatura'], mode='lines', name='Temperatura (°C)'))
    figura_serie_tiempo_temperatura.update_layout(title="Series de Tiempo - Temperatura",
                                      xaxis_title="Hora",
                                      yaxis_title="Valores",
                                      template="plotly_white")

    # Crear serie de tiempo para humedad
    figura_serie_tiempo_humedad = go.Figure()
    figura_serie_tiempo_humedad.add_trace(go.Scatter(x=datos['Hora'], y=datos['Humedad'], mode='lines', name='Humedad (%)'))
    figura_serie_tiempo_humedad.update_layout(title="Series de Tiempo - Humedad",
                                      xaxis_title="Hora",
                                      yaxis_title="Valores",
                                      template="plotly_white")

    return [gauge_temperatura, gauge_humedad], figura_serie_tiempo_temperatura, figura_serie_tiempo_humedad

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
