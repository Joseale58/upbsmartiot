import psycopg2
from crate import client
from datetime import datetime
import sys

# Configuraciones de la conexión
# CrateDB
CRATE_URL = "db-crate"

# PostgreSQL
POSTGRES_HOST = "postgres"
POSTGRES_PORT = "5432"
POSTGRES_DB = "postgres"
POSTGRES_USER = "root"
POSTGRES_PASSWORD = "password"
POSTGRES_TABLE_TEMPERATURE = "temperature"
POSTGRES_TABLE_HUMIDITY = "humidity"

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

    # Obtener la última fecha de los datos en PostgreSQL
    
    cursor_pg = postgres_conn.cursor()
    last_date_temp_query = f"SELECT MAX(timestamp) FROM {POSTGRES_TABLE_TEMPERATURE};"
    cursor_pg.execute(last_date_temp_query)
    last_date_temp = cursor_pg.fetchone()[0]

    last_date_humidity_query = f"SELECT MAX(timestamp) FROM {POSTGRES_TABLE_HUMIDITY};"
    cursor_pg.execute(last_date_humidity_query)
    last_date_humidity = cursor_pg.fetchone()[0]

    if last_date_temp < last_date_humidity:
        last_date = last_date_temp
    else:
        last_date = last_date_humidity


    # Conexión a CrateDB
    print("Conectando a CrateDB...")
    crate_conn = client.connect(CRATE_URL, error_trace=True)
    cursor_crate = crate_conn.cursor()
    crate_query = crate_query = f""" SELECT time_index, temp, humedad  FROM doc.etvariables WHERE entity_id = 'Joselito' AND time_index >= '{last_date}' LIMIT 10000; """
    cursor_crate.execute(crate_query)
    crate_data = cursor_crate.fetchall()
    
    print(f"Datos capturados de CrateDB: {len(crate_data)} filas")

    

    # Inserción de los datos en la tabla PostgreSQL
    print("Insertando datos en PostgreSQL...")
    for row in crate_data:
        time_index, temp, humedad = row
        # Convertir el timestamp de milisegundos a un objeto datetime
        timestamp = datetime.fromtimestamp(time_index / 1000.0)
        insert_temp_query = f"INSERT INTO {POSTGRES_TABLE_TEMPERATURE} (value, timestamp) VALUES (%s,%s)"
        insert_humidity_query = f"INSERT INTO {POSTGRES_TABLE_HUMIDITY} (value, timestamp) VALUES (%s,%s)"
        cursor_pg.execute(insert_temp_query, (temp,timestamp))
        cursor_pg.execute(insert_humidity_query, (humedad,timestamp))
    # Guardar los cambios definitivamente
    postgres_conn.commit()
    
    print("Datos insertados en PostgreSQL con éxito.")

except Exception as e:
    print(f"Ha ocurrido un error: {e}")
    sys.exit(1)

finally:
    # Cerrar cursores y conexiones
    if cursor_crate:
        cursor_crate.close()
    if crate_conn:
        crate_conn.close()
    if cursor_pg:
        cursor_pg.close()
    if postgres_conn:
        postgres_conn.close()
    print("Conexiones cerradas.")
