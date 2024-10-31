import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import pandas as pd
import datetime
import numpy as np
import psycopg2
import sys

# Inicializar la aplicación con un tema de Bootstrap
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Planta Dashboard"

# PostgreSQL
POSTGRES_HOST = "localhost"
POSTGRES_PORT = "5432"
POSTGRES_DB = "postgres"
POSTGRES_USER = "root"
POSTGRES_PASSWORD = "password"
POSTGRES_TABLE_TEMPERATURE = "temperature_dummy"
POSTGRES_TABLE_HUMIDITY = "humidity_dummy"


# Consulta a PostgreSQL
try:
    
    # Conexión a PostgreSQL
    print("Conectando a PostgreSQL...")
    postgres_conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )

    cursor_pg = postgres_conn.cursor()

    # Datos de temperatura y humedad
    query_humidity = f"SELECT date_trunc('hour', timestamp) AS hour_interval, AVG(value) AS avg_value FROM {POSTGRES_TABLE_HUMIDITY} GROUP BY hour_interval ORDER BY hour_interval;"

    query_temperature = f"SELECT date_trunc('hour', timestamp) AS hour_interval, AVG(value) AS avg_value FROM {POSTGRES_TABLE_TEMPERATURE} GROUP BY hour_interval ORDER BY hour_interval;"

    query_last_temperature = f"SELECT date_trunc('hour', timestamp) AS hour_interval, value FROM {POSTGRES_TABLE_TEMPERATURE} ORDER BY hour_interval DESC LIMIT 1;"

    query_last_humidity = f"SELECT date_trunc('hour', timestamp) AS hour_interval, value FROM {POSTGRES_TABLE_HUMIDITY} ORDER BY hour_interval DESC LIMIT 1;"

    cursor_pg.execute(query_humidity)
    humedad = cursor_pg.fetchall()

    cursor_pg.execute(query_temperature)
    temperatura = cursor_pg.fetchall()

    cursor_pg.execute(query_last_temperature)
    last_temperature = cursor_pg.fetchall()

    cursor_pg.execute(query_last_humidity)
    last_humidity = cursor_pg.fetchall()

    # Cerrar el cursor y la conexión
    cursor_pg.close()
    postgres_conn.close()

except Exception as e:
    print(f"Ha ocurrido un error: {e}")
    sys.exit(1)

finally:
    # Cerrar cursores y conexiones
    if cursor_pg:
        cursor_pg.close()
    if postgres_conn:
        postgres_conn.close()
    print("Conexiones cerradas.")

# Seleccionar datos por fecha de calendario
def datos_fecha(fecha):

    # Convertirmo a objeto fecha
    fecha_obj = pd.to_datetime(fecha).date()

    horas = pd.date_range(start=fecha, periods=24, freq='h')

    # Filtrar datos de temperatura y humedad por la fecha seleccionada y convertir a Series (para que quede indexado por hora)
    temperatura_series = pd.Series(
        {temp[0]: temp[1] for temp in temperatura if temp[0].date() == fecha_obj}, 
        index=horas
    )
    humedad_series = pd.Series(
        {hum[0]: hum[1] for hum in humedad if hum[0].date() == fecha_obj}, 
        index=horas
    )

    # Interpolar valores nulos
    temperatura_dia = temperatura_series.interpolate(method='linear').to_list()
    humedad_dia = humedad_series.interpolate(method='linear').to_list()


    return pd.DataFrame({'Hora': horas, 'Temperatura': temperatura_dia, 'Humedad': humedad_dia})

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
            html.Hr(),
            html.H4("Últimas medidas registras para temperatura: " + last_temperature[0][0].strftime("%Y-%m-%d %H") + " horas y humedad: " + last_humidity[0][0].strftime("%Y-%m-%d %H") + " horas", className="mt-4"),
            html.Div(id='output-gauges', className='mt-4'),
            dcc.DatePickerSingle(
                id='date-picker',
                date=datetime.date.today(),
                className='mt-3'
            ),
            dcc.Graph(id='time-series-graph-temperatura', className='mt-4'),
            dcc.Graph(id='time-series-graph-humedad', className='mt-4')
        ])
    ]),

    # Pestaña 3: Vacía por ahora
    dbc.Tab(label='Predicciones futuras', children=[
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
    datos = datos_fecha(fecha_seleccionada)

    temperatura_media = datos['Temperatura'].mean()
    humedad_media = datos['Humedad'].mean()

    # Definir color del indicador de temperatura basado en el valor
    if temperatura_media < 15:
        color_temperatura = "blue"  # Temperatura baja
    elif 15 <= temperatura_media < 25:
        color_temperatura = "green"  # Temperatura óptima
    elif 25 <= temperatura_media < 35:
        color_temperatura = "yellow"  # Temperatura alta
    else:
        color_temperatura = "red"  # Temperatura muy alta

    # Definir color del indicador de humedad basado en el valor
    if humedad_media < 30:
        color_humedad = "lightblue"  # Humedad muy baja
    elif 30 <= humedad_media < 60:
        color_humedad = "green"  # Humedad óptima
    elif 60 <= humedad_media < 80:
        color_humedad = "yellow"  # Humedad alta
    else:
        color_humedad = "red"  # Humedad muy alta


    # Crear gráficos de gauge para temperatura y humedad
    gauge_temperatura = dcc.Graph(
        figure=go.Figure(go.Indicator(
            mode="gauge+number",
            value=last_temperature[0][1],
            title={'text': "Temperatura (°C)"},
            gauge={
            'axis': {'range': [0, 50]},
            'bar': {'color': color_temperatura}  # Color dinámico del indicador
            }
        )), style={'display': 'inline-block', 'width': '45%'}
    )

    gauge_humedad = dcc.Graph(
        figure=go.Figure(go.Indicator(
            mode="gauge+number",
            value=last_humidity[0][1],
            title={'text': "Humedad (%)"},
            gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': color_humedad}  # Color dinámico del indicador
            }
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
