import psycopg2
import sys
import pandas as pd
from datetime import datetime, timedelta
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from skforecast.ForecasterAutoreg import ForecasterAutoreg
from skforecast.model_selection import grid_search_forecaster

# PostgreSQL
POSTGRES_HOST = "localhost"
POSTGRES_PORT = "5432"
POSTGRES_DB = "postgres"
POSTGRES_USER = "root"
POSTGRES_PASSWORD = "password"
POSTGRES_TABLE_TEMPERATURE = "temperature_dummy"
POSTGRES_TABLE_HUMIDITY = "humidity_dummy"
POSTGRES_TABLE_PREDICTION = "predictions"

try:
    # Conexión a PostgreSQL
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

    cursor_pg.execute(query_humidity)
    humedad = cursor_pg.fetchall()

    cursor_pg.execute(query_temperature)
    temperatura = cursor_pg.fetchall()

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

# --- Preprocesamiento de datos ---

#Temperatura

df_temperatura = pd.DataFrame(temperatura, columns=["hour", "temperature"])

# Crear una columna de 'fecha' para agrupar por día
df_temperatura['fecha'] = df_temperatura['hour'].dt.date

# Crear un rango de horas completo para cada día que esté presente en los datos
fechas_unicas = df_temperatura['fecha'].unique()

# Crear un DataFrame vacío para almacenar todas las fechas y horas
rango_completo = []
for fecha in fechas_unicas:
    horas = pd.date_range(start=pd.to_datetime(fecha), periods=24, freq='h')
    rango_completo.append(pd.DataFrame({'hour': horas}))

# Concatenar todos los DataFrames de rangos de horas en un solo DataFrame
rango_completo_df = pd.concat(rango_completo, ignore_index=True)

# Hacer un merge (unir) entre el DataFrame completo de horas y el DataFrame de temperatura
# Esto permitirá identificar las horas que no tienen registros de temperatura
df_completo_temp = pd.merge(rango_completo_df, df_temperatura, on="hour", how="left")

df_completo_temp = df_completo_temp.drop(columns=["fecha"])

# Realizar la interpolación lineal para rellenar los valores faltantes de temperatura
df_completo_temp['temperature'] = df_completo_temp['temperature'].interpolate(method='linear')

# Si quedan valores nulos al principio o al final, se pueden rellenar con ffill o bfill
df_completo_temp['temperature'] = df_completo_temp['temperature'].ffill().bfill()

# --- Predicción de valores futuros con Skforecast ---

# Crear y entrenar el modelo ForecasterAutoreg con RandomForestRegressor
# Ajustar el valor de lags para que sea menor que el tamaño de la serie
total_observations = len(df_completo_temp)
lags = min(24, total_observations - 1)  # Ajustar el valor de lags para que no supere el número de observaciones

forecaster = ForecasterAutoreg(
                regressor=RandomForestRegressor(random_state=123),
                lags=lags
             )

forecaster.fit(y=df_completo_temp['temperature'])
print(forecaster)

# Definir el número de pasos para predecir
steps = 24

# Realizar predicciones con el modelo entrenado
predictions = forecaster.predict(steps=steps)

# Mostrar las predicciones futuras
ultima_hora = df_completo_temp['hour'].max()
horas_futuras = pd.date_range(start=ultima_hora + timedelta(hours=1), periods=steps, freq='h')
df_futuro_temp = pd.DataFrame({'hour': horas_futuras, 'predicted_temperature': predictions})
print(df_futuro_temp)


# Calcular y mostrar el Error Cuadrático Medio (MSE) para las predicciones
mse = mean_squared_error(df_completo_temp['temperature'].iloc[-steps:], predictions)
print(f"Error Cuadrático Medio (MSE): {mse}")
print("Fin del modelo")


# Humedad

# Suponiendo que ya tienes los datos de la variable `humedad`
df_humedad = pd.DataFrame(humedad, columns=["hour", "humidity"])

# Crear una columna de 'fecha' para agrupar por día
df_humedad['fecha'] = df_humedad['hour'].dt.date

# Crear un rango de horas completo para cada día que esté presente en los datos
fechas_unicas = df_humedad['fecha'].unique()

# Crear un DataFrame vacío para almacenar todas las fechas y horas
rango_completo = []
for fecha in fechas_unicas:
    horas = pd.date_range(start=pd.to_datetime(fecha), periods=24, freq='h')
    rango_completo.append(pd.DataFrame({'hour': horas}))

# Concatenar todos los DataFrames de rangos de horas en un solo DataFrame
rango_completo_df = pd.concat(rango_completo, ignore_index=True)

# Hacer un merge (unir) entre el DataFrame completo de horas y el DataFrame de humedad
# Esto permitirá identificar las horas que no tienen registros de humedad
df_completo_hum = pd.merge(rango_completo_df, df_humedad, on="hour", how="left")

df_completo_hum = df_completo_hum.drop(columns=["fecha"])

# Realizar la interpolación lineal para rellenar los valores faltantes de humedad
df_completo_hum['humidity'] = df_completo_hum['humidity'].interpolate(method='linear')

# Si quedan valores nulos al principio o al final, se pueden rellenar con ffill o bfill
df_completo_hum['humidity'] = df_completo_hum['humidity'].ffill().bfill()

# --- Predicción de valores futuros ---
# --- Predicción de valores futuros con Skforecast ---

# Crear y entrenar el modelo ForecasterAutoreg con RandomForestRegressor
# Ajustar el valor de lags para que sea menor que el tamaño de la serie
total_observations = len(df_completo_hum)
lags = min(24, total_observations - 1)  # Ajustar el valor de lags para que no supere el número de observaciones

forecaster = ForecasterAutoreg(
                regressor=RandomForestRegressor(random_state=123),
                lags=lags
             )

forecaster.fit(y=df_completo_hum['humidity'])
print(forecaster)

# Definir el número de pasos para predecir
steps = 24

# Realizar predicciones con el modelo entrenado
predictions = forecaster.predict(steps=steps)

# Mostrar las predicciones futuras
ultima_hora = df_completo_hum['hour'].max()
horas_futuras = pd.date_range(start=ultima_hora + timedelta(hours=1), periods=steps, freq='h')
df_futuro_hum = pd.DataFrame({'hour': horas_futuras, 'predicted_humidity': predictions})
print(df_futuro_hum)

# Calcular y mostrar el Error Cuadrático Medio (MSE) para las predicciones
mse = mean_squared_error(df_completo_hum['humidity'].iloc[-steps:], predictions)
print(f"Error Cuadrático Medio (MSE): {mse}")
print("Fin del modelo")


df_futuro_completo = pd.merge(df_futuro_temp, df_futuro_hum, on="hour", how="inner")

print(df_futuro_completo)

try:

    postgres_conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )
    
    cursor_pg = postgres_conn.cursor()

    for _, row in df_futuro_completo.iterrows():
        time_index = row['hour']
        temp = row['predicted_temperature']
        hum = row['predicted_humidity']

        insert_temp_query = f"INSERT INTO {POSTGRES_TABLE_PREDICTION} (temperature, humidity, timestamp) VALUES (%s,%s,%s)"
        cursor_pg.execute(insert_temp_query, (temp, hum, time_index))

        # Guardar los cambios definitivamente
        postgres_conn.commit()


except Exception as e:
    print(f"Ha ocurrido un error: {e}")
    sys.exit(1)

finally:
    if cursor_pg:
        cursor_pg.close()
    if postgres_conn:
        postgres_conn.close()
    print("Conexiones cerradas.")