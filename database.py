import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

COLS_REGISTROS = ["ID_Registro", "Fecha", "Año", "Mes", "Coordinador", "Cedula", "Empleado", "Labor", "Tipo_Parametro", "Observaciones", "Hora_Registro"]
COLS_EMPLEADOS = ["Cedula", "Nombre", "Coordinador", "Cargo_Area", "Estado"]
COLS_LABORES = ["Nombre_Labor", "Tipo_Parametro", "Estado"]

@st.cache_resource
def conectar_sheets():
    scope = ["https://google.com", "https://googleapis.com"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open("Reporte_Labores_DB")

def leer_pestana(nombre_pestana, columnas_default):
    try:
        sheet = conectar_sheets()
        ws = sheet.worksheet(nombre_pestana)
        datos = ws.get_all_records()
        if not datos:
            return pd.DataFrame(columns=columnas_default)
        df = pd.DataFrame(datos)
        for col in columnas_default:
            if col not in df.columns:
                df[col] = ""
        return df[columnas_default]
    except Exception as e:
        st.error(f"Error leyendo '{nombre_pestana}': {e}")
        return pd.DataFrame(columns=columnas_default)

def sobrescribir_pestana(nombre_pestana, df):
    try:
        sheet = conectar_sheets()
        ws = sheet.worksheet(nombre_pestana)
        ws.clear()
        df_clean = df.fillna("").astype(str)
        ws.update([df_clean.columns.values.tolist()] + df_clean.values.tolist())
        return True
    except Exception as e:
        st.error(f"Error guardando en '{nombre_pestana}': {e}")
        return False

def agregar_filas(nombre_pestana, filas):
    try:
        sheet = conectar_sheets()
        ws = sheet.worksheet(nombre_pestana)
        for fila in filas:
            ws.append_row([str(x) for x in fila])
        return True
    except Exception as e:
        st.error(f"Error agregando registros: {e}")
        return False
