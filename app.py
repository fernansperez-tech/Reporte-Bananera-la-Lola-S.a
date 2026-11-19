import streamlit as st
import pandas as pd
from datetime import datetime, date
import io
import uuid
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Bananera La Lola S.A. - Labores", layout="wide", page_icon="🍌")

ADMIN_PASSWORD = st.secrets.get("admin_password", "Admin2026*")

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

df_registros = leer_pestana("Registros", COLS_REGISTROS)
df_empleados = leer_pestana("Empleados", COLS_EMPLEADOS)
df_labores = leer_pestana("Labores", COLS_LABORES)

st.sidebar.title("🍌 Bananera La Lola S.A.")
perfil = st.sidebar.radio(
    "Seleccione su módulo:",
    [
        "👷 1. Reporte Coordinadores",
        "🗂️ 2. Control Secretaría",
        "📊 3. Recursos Humanos",
        "⚙️ 4. Administración (Admin)"
    ]
)

if perfil == "👷 1. Reporte Coordinadores":
    st.title("👷 Reporte Diario de Labores")
    empleados_activos = df_empleados[df_empleados["Estado"] == "Activo"] if not df_empleados.empty else pd.DataFrame()
    labores_activas = df_labores[df_labores["Estado"] == "Activa"] if not df_labores.empty else pd.DataFrame()

    if empleados_activos.empty or labores_activas.empty:
        st.warning("⚠️ El Administrador aún no ha creado empleados activos o labores en el sistema.")
    else:
        lista_coordinadores = sorted(empleados_activos["Coordinador"].unique().tolist())
        col1, col2 = st.columns(2)
        with col1:
            coordinador = st.selectbox("Seleccione Coordinador:", lista_coordinadores)
        with col2:
            fecha_reporte = st.date_input("Fecha de la labor:", value=date.today())

        fecha_str = fecha_reporte.strftime("%Y-%m-%d")
        ya_reportados = []
        if not df_registros.empty:
            filtro_hoy = df_registros[(df_registros["Fecha"] == fecha_str) & (df_registros["Coordinador"] == coordinador)]
            ya_reportados = filtro_hoy["Cedula"].astype(str).tolist()

        st.subheader(f"Personal activo a cargo de {coordinador}")
        mis_empleados = empleados_activos[empleados_activos["Coordinador"] == coordinador]
        opciones_labores = labores_activas["Nombre_Labor"].tolist()
        mapa_parametros = dict(zip(labores_activas["Nombre_Labor"], labores_activas["Tipo_Parametro"]))

        with st.form("form_reporte_diario"):
            registros_pendientes = []
            for _, emp in mis_empleados.iterrows():
                ced = str(emp["Cedula"])
                nom = emp["Nombre"]
                cargo = emp["Cargo_Area"]
                c1, c2, c3 = st.columns([2.2, 2, 2])
                estado_previo = "✅ Ya reportado" if ced in ya_reportados else "⏳ Pendiente"
                with c1:
                    st.markdown(f"**{nom}** (`{ced}`)  \n*{cargo}* | {estado_previo}")
                with c2:
                    labor_sel = st.selectbox(f"Labor {ced}", opciones_labores, key=f"lab_{ced}", label_visibility="collapsed")
                with c3:
                    obs_sel = st.text_input("Observación", placeholder="Novedad opcional...", key=f"obs_{ced}", label_visibility="collapsed")
                registros_pendientes.append({
                    "cedula": ced, "nombre": nom, "labor": labor_sel,
                    "parametro": mapa_parametros.get(labor_sel, "Laborado"), "obs": obs_sel
                })
                st.divider()

            if st.form_submit_button("💾 Guardar Reporte del Día", type="primary"):
                nuevas_filas = []
                hora_actual = datetime.now().strftime("%H:%M:%S")
                for item in registros_pendientes:
                    if item["cedula"] not in ya_reportados:
                        id_unico = str(uuid.uuid4())[:8].upper()
                        nuevas_filas.append([
                            id_unico, fecha_str, fecha_reporte.year, fecha_reporte.month,
                            coordinador, item["cedula"], item["nombre"], item["labor"],
                            item["parametro"], item["obs"], hora_actual
                        ])
                if nuevas_filas:
                    if agregar_filas("Registros", nuevas_filas):
                        st.success(f"✅ Se guardaron {len(nuevas_filas)} registros correctamente.")
                        st.rerun()
                else:
                    st.warning("Todos los empleados de esta lista ya fueron reportados en esta fecha.")
