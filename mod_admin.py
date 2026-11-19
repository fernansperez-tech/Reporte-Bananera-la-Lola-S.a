import streamlit as st
import pandas as pd
from datetime import date
import io
from database import agregar_filas, sobrescribir_pestana

def vista_rrhh(df_registros):
    st.title("📊 Analítica de Recursos Humanos y Ausentismo")

    if df_registros.empty:
        st.warning("Aún no hay datos registrados en el sistema.")
        return

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        años = ["Todos"] + sorted(df_registros["Año"].astype(str).unique().tolist(), reverse=True)
        sel_año = st.selectbox("Año:", años)
    with f2:
        meses = ["Todos"] + sorted(df_registros["Mes"].astype(str).unique().tolist())
        sel_mes = st.selectbox("Mes:", meses)
    with f3:
        coords = ["Todos"] + sorted(df_registros["Coordinador"].unique().tolist())
        sel_coord = st.selectbox("Coordinador:", coords)
    with f4:
        params = ["Todos"] + sorted(df_registros["Tipo_Parametro"].unique().tolist())
        sel_param = st.selectbox("Parámetro / Tipo:", params)

    f5, f6, f7 = st.columns(3)
    with f5:
        labores_list = ["Todas"] + sorted(df_registros["Labor"].unique().tolist())
        sel_labor = st.selectbox("Labor específica:", labores_list)
    with f6:
        buscar_emp = st.text_input("Buscar empleado (Nombre o Cédula):")
    with f7:
        usar_fecha = st.checkbox("Filtrar por día exacto")
        fecha_exacta = st.date_input("Día específico:", disabled=not usar_fecha)

    df_filtrado = df_registros.copy()
    if sel_año != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Año"].astype(str) == sel_año]
    if sel_mes != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Mes"].astype(str) == sel_mes]
    if sel_coord != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Coordinador"] == sel_coord]
    if sel_param != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Tipo_Parametro"] == sel_param]
    if sel_labor != "Todas":
        df_filtrado = df_filtrado[df_filtrado["Labor"] == sel_labor]
    if buscar_emp:
        df_filtrado = df_filtrado[
            df_filtrado["Empleado"].str.contains(buscar_emp, case=False, na=False) |
            df_filtrado["Cedula"].astype(str).str.contains(buscar_emp, na=False)
        ]
    if usar_fecha:
        df_filtrado = df_filtrado[df_filtrado["Fecha"] == fecha_exacta.strftime("%Y-%m-%d")]

    st.divider()
    k1, k2, k3 = st.columns(3)
    total_reg = len(df_filtrado)
    total_aus = len(df_filtrado[df_filtrado["Tipo_Parametro"].str.contains("Ausencia", case=False, na=False)])
    total_lab = len(df_filtrado[df_filtrado["Tipo_Parametro"] == "Laborado"])

    k1.metric("Total Registros", total_reg)
    k2.metric("Días Laborados", total_lab)
    k3.metric("Total Ausencias", total_aus)

    df_export = df_filtrado.drop(columns=["ID_Registro"], errors="ignore")
    st.dataframe(df_export, use_container_width=True, hide_index=True)

    buffer_rrhh = io.BytesIO()
    with pd.ExcelWriter(buffer_rrhh, engine='openpyxl') as writer:
        df_export.to_excel(writer, index=False, sheet_name='Historico_RRHH')

    st.download_button(
        label="📥 Exportar Consulta de RRHH a Excel",
        data=buffer_rrhh.getvalue(),
        file_name="Consulta_RRHH_Labores.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def vista_admin(df_registros, df_empleados, df_labores, admin_password):
    st.title("⚙️ Panel de Administración del Sistema")

    clave = st.text_input("Ingrese contraseña de administrador:", type="password")
    if clave != admin_password:
        st.info("🔒 Ingrese la contraseña para gestionar empleados, labores y registros.")
        return

    tab_emp, tab_lab, tab_reg = st.tabs(["👥 Gestión de Empleados", "🛠️ Gestión de Labores", "📝 Modificar / Eliminar Registros"])

    with tab_emp:
        st.subheader("➕ Agregar Nuevo Empleado")
        with st.form("form_nuevo_empleado"):
            c1, c2, c3, c4 = st.columns(4)
            nueva_ced = c1.text_input("Cédula / ID *")
            nuevo_nom = c2.text_input("Nombre Completo *")
            nuevo_coord = c3.text_input("Coordinador Asignado *")
            nuevo_cargo = c4.text_input("Cargo / Lote / Área")
            
            if st.form_submit_button("Agregar Empleado", type="primary"):
                if nueva_ced and nuevo_nom and nuevo_coord:
                    if not df_empleados.empty and nueva_ced in df_empleados["Cedula"].astype(str).values:
                        st.error("❌ Ya existe un empleado con esa cédula.")
                    else:
                        agregar_filas("Empleados", [[nueva_ced.strip(), nuevo_nom.strip(), nuevo_coord.strip(), nuevo_cargo.strip(), "Activo"]])
                        st.success("✅ Empleado creado exitosamente.")
                        st.rerun()
                else:
                    st.warning("Completa los campos obligatorios (*).")

        st.divider()
        st.subheader("✏️ Editar o Eliminar Empleados")
        df_emp_editado = st.data_editor(
            df_empleados, num_rows="dynamic", use_container_width=True,
            column_config={"Estado": st.column_config.SelectboxColumn("Estado", options=["Activo", "Inactivo"], required=True)},
            key="editor_empleados"
        )
        if st.button("💾 Guardar Cambios en Empleados", type="primary"):
            if sobrescribir_pestana("Empleados", df_emp_editado):
                st.success("✅ Base de datos de empleados actualizada.")
                st.rerun()

    with tab_lab:
        st.subheader("➕ Crear Nueva Labor y su Parámetro")
        with st.form("form_nueva_labor"):
            c1, c2 = st.columns(2)
            nombre_lab = c1.text_input("Nombre de la Labor o Novedad *")
            param_lab = c2.selectbox("Parámetro RRHH *", ["Laborado", "Ausencia Injustificada", "Ausencia Justificada", "Descanso / Vacaciones"])
            if st.form_submit_button("Crear Labor", type="primary"):
                if nombre_lab:
                    agregar_filas("Labores", [[nombre_lab.strip(), param_lab, "Activa"]])
                    st.success("✅ Labor agregada al catálogo.")
                    st.rerun()
                else:
                    st.warning("Escribe el nombre de la labor.")

        st.divider()
        st.subheader("✏️ Editar o Eliminar Labores")
        df_lab_editado = st.data_editor(
            df_labores, num_rows="dynamic", use_container_width=True,
            column_config={
                "Tipo_Parametro": st.column_config.SelectboxColumn("Tipo_Parametro", options=["Laborado", "Ausencia Injustificada", "Ausencia Justificada", "Descanso / Vacaciones"], required=True),
                "Estado": st.column_config.SelectboxColumn("Estado", options=["Activa", "Inactiva"], required=True)
            },
            key="editor_labores"
        )
        if st.button("💾 Guardar Cambios en Labores", type="primary"):
            if sobrescribir_pestana("Labores", df_lab_editado):
                st.success("✅ Catálogo de labores actualizado.")
                st.rerun()

    with tab_reg:
        st.subheader("📝 Corregir o Eliminar Registros Históricos")
        if df_registros.empty:
            st.info("No hay registros históricos para editar.")
        else:
            fecha_edicion = st.date_input("Filtrar registros por fecha:", value=date.today(), key="fecha_admin_reg")
            fecha_ed_str = fecha_edicion.strftime("%Y-%m-%d")
            ver_todos_reg = st.checkbox("Mostrar todos los registros históricos")

            df_vista_reg = df_registros.copy() if ver_todos_reg else df_registros[df_registros["Fecha"] == fecha_ed_str].copy()
            opciones_lab_admin = df_labores["Nombre_Labor"].tolist() if not df_labores.empty else []

            df_reg_editado = st.data_editor(
                df_vista_reg, num_rows="dynamic", use_container_width=True, disabled=["ID_Registro"],
                column_config={
                    "Labor": st.column_config.SelectboxColumn("Labor", options=opciones_lab_admin) if opciones_lab_admin else st.column_config.TextColumn("Labor"),
                    "Tipo_Parametro": st.column_config.SelectboxColumn("Tipo_Parametro", options=["Laborado", "Ausencia Injustificada", "Ausencia Justificada", "Descanso / Vacaciones"])
                },
                key="editor_registros"
            )

            if st.button("💾 Guardar Cambios en Registros", type="primary"):
                if ver_todos_reg:
                    df_final_guardar = df_reg_editado
                else:
                    df_otras_fechas = df_registros[df_registros["Fecha"] != fecha_ed_str]
                    df_final_guardar = pd.concat([df_otras_fechas, df_reg_editado], ignore_index=True)

                if sobrescribir_pestana("Registros", df_final_guardar):
                    st.success("✅ Registros actualizados permanentemente.")
                    st.rerun()
