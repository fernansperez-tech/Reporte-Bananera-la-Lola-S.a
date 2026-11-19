import streamlit as st
import pandas as pd
from datetime import datetime, date
import io
import uuid
from database import COLS_REGISTROS, COLS_EMPLEADOS, agregar_filas

def vista_coordinadores(df_registros, df_empleados, df_labores):
    st.title("👷 Reporte Diario de Labores")

    empleados_activos = df_empleados[df_empleados["Estado"] == "Activo"] if not df_empleados.empty else pd.DataFrame()
    labores_activas = df_labores[df_labores["Estado"] == "Activa"] if not df_labores.empty else pd.DataFrame()

    if empleados_activos.empty or labores_activas.empty:
        st.warning("⚠️ El Administrador aún no ha creado empleados activos o labores en el sistema.")
        return

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
                "cedula": ced,
                "nombre": nom,
                "labor": labor_sel,
                "parametro": mapa_parametros.get(labor_sel, "Laborado"),
                "obs": obs_sel
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

def vista_secretaria(df_registros, df_empleados):
    st.title("🗂️ Control Diario y Consolidado Excel")
    
    fecha_consulta = st.date_input("Seleccione fecha a revisar:", value=date.today())
    fecha_str = fecha_consulta.strftime("%Y-%m-%d")

    df_todos = df_empleados[df_empleados["Estado"] == "Activo"].copy() if not df_empleados.empty else pd.DataFrame(columns=COLS_EMPLEADOS)
    df_todos["Cedula"] = df_todos["Cedula"].astype(str)

    if not df_registros.empty:
        df_dia = df_registros[df_registros["Fecha"] == fecha_str].copy()
        df_dia["Cedula"] = df_dia["Cedula"].astype(str)
    else:
        df_dia = pd.DataFrame(columns=COLS_REGISTROS)

    cedulas_reportadas = df_dia["Cedula"].tolist()
    df_faltantes = df_todos[~df_todos["Cedula"].isin(cedulas_reportadas)]

    m1, m2, m3 = st.columns(3)
    m1.metric("Personal Activo Total", len(df_todos))
    m2.metric("Reportados Hoy", len(df_dia))
    m3.metric("⚠️ Faltan por Reportar", len(df_faltantes))

    st.divider()

    if not df_faltantes.empty:
        st.error("🚨 Empleados pendientes por reporte:")
        st.dataframe(df_faltantes[["Coordinador", "Cedula", "Nombre", "Cargo_Area"]], use_container_width=True, hide_index=True)
    else:
        st.success("✅ Todo el personal activo ha sido reportado hoy.")

    st.subheader("📄 Formato Consolidado del Día")
    df_export = df_dia.drop(columns=["ID_Registro"], errors="ignore")
    st.dataframe(df_export, use_container_width=True, hide_index=True)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_export.to_excel(writer, index=False, sheet_name='Reporte_Diario')
    
    st.download_button(
        label="📥 Descargar Formato en Excel (.xlsx)",
        data=buffer.getvalue(),
        file_name=f"Reporte_Labores_{fecha_str}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )
