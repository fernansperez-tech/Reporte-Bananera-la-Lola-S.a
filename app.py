import streamlit as st
from database import COLS_REGISTROS, COLS_EMPLEADOS, COLS_LABORES, leer_pestana
from mod_operativo import vista_coordinadores, vista_secretaria
from mod_admin import vista_rrhh, vista_admin

st.set_page_config(page_title="Sistema de Gestión de Labores", layout="wide", page_icon="📋")

ADMIN_PASSWORD = st.secrets.get("admin_password", "Admin2026*")

# Cargar datos desde Google Sheets
df_registros = leer_pestana("Registros", COLS_REGISTROS)
df_empleados = leer_pestana("Empleados", COLS_EMPLEADOS)
df_labores = leer_pestana("Labores", COLS_LABORES)

# Menú lateral
st.sidebar.title("🏢 Gestión Operativa")
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
    vista_coordinadores(df_registros, df_empleados, df_labores)
elif perfil == "🗂️ 2. Control Secretaría":
    vista_secretaria(df_registros, df_empleados)
elif perfil == "📊 3. Recursos Humanos":
    vista_rrhh(df_registros)
elif perfil == "⚙️ 4. Administración (Admin)":
    vista_admin(df_registros, df_empleados, df_labores, ADMIN_PASSWORD)
