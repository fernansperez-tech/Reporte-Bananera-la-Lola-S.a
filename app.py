import streamlit as st
import pandas as pd
from datetime import datetime, date
import io
import uuid
import gspread

st.set_page_config(page_title="Bananera La Lola S.A. - App Labores", layout="wide", page_icon="🍌")

# Estilos CSS estilo App Flutter (Material 3 Cards y Chips)
st.markdown("""
<style>
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: var(--secondary-background-color) !important;
        border-radius: 20px !important;
        border: 1px solid rgba(128, 128, 128, 0.22) !important;
        padding: 16px 18px !important;
        margin-bottom: 14px !important;
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08) !important;
        transition: transform 0.15s ease-in-out;
    }
    .flutter-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
        padding-bottom: 10px;
        border-bottom: 1px solid rgba(128, 128, 128, 0.18);
    }
    .flutter-user-box {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .flutter-avatar {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        background: linear-gradient(135deg, #16a34a, #22c55e);
        color: white;
        font-weight: 800;
        font-size: 1.05rem;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        box-shadow: 0 3px 8px rgba(22, 163, 74, 0.35);
    }
    .flutter-name {
        font-size: 1.08rem;
        font-weight: 700;
        color: var(--text-color);
        line-height: 1.2;
    }
    .flutter-chips {
        margin-top: 4px;
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
    }
    .flutter-chip {
        font-size: 0.74rem;
        font-weight: 600;
        padding: 2px 10px;
        border-radius: 12px;
        background-color: rgba(128, 128, 128, 0.14);
        color: var(--text-color);
    }
    .badge-ok {
        background-color: rgba(22, 163, 74, 0.18);
        color: #22c55e;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 700;
        border: 1px solid rgba(34, 197, 94, 0.35);
    }
    .badge-pend {
        background-color: rgba(245, 158, 11, 0.18);
        color: #f59e0b;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 700;
        border: 1px solid rgba(245, 158, 11, 0.35);
    }
    .stButton > button {
        border-radius: 14px !important;
        font-weight: 700 !important;
        height: 46px !important;
    }
</style>
""", unsafe_allow_html=True)

ADMIN_PASSWORD = st.secrets.get("admin_password", "Admin2026*")

COLS_REGISTROS = [
    "ID_Registro", "Fecha", "Año", "Mes", "Coordinador", "Cedula", "Empleado",
    "Lote", "Labor", "Cantidad", "Unidad", "Horas",
    "Tipo_Parametro", "Observaciones", "Hora_Registro"
]
COLS_EMPLEADOS = ["Cedula", "Nombre", "Coordinador", "Cargo_Area", "Estado"]
COLS_LABORES = ["Nombre_Labor", "Unidad_Medida", "Rendimiento_Estimado", "Tipo_Parametro", "Estado"]
COLS_COORDS = ["Usuario", "Nombre_Coordinador", "Password", "Estado"]

@st.cache_resource
def conectar_sheets():
    creds_dict = dict(st.secrets["gcp_service_account"])
    client = gspread.service_account_from_dict(creds_dict)
    return client.open_by_key("10rnbMgxL0L53tyqdF9klViPiLTxejQidd0rUmC2HqPQ")

@st.cache_data(ttl=120, show_spinner=False)
def leer_pestana(nombre_pestana, columnas_default):
    try:
        sheet = conectar_sheets()
        ws = sheet.worksheet(nombre_pestana)
        filas = ws.get("A1:Z2000")
        if not filas or len(filas) <= 1:
            return pd.DataFrame(columns=columnas_default)
        encabezados = [str(h).strip() for h in filas[0]]
        datos = filas[1:]
        datos_norm = [fila + [""] * (len(encabezados) - len(fila)) for fila in datos]
        df = pd.DataFrame(datos_norm, columns=encabezados)
        df = df.loc[:, ~df.columns.duplicated()].copy()
        for col in columnas_default:
            if col not in df.columns:
                df[col] = ""
        return df[columnas_default].astype(str)
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
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error guardando en '{nombre_pestana}': {e}")
        return False

def agregar_filas(nombre_pestana, filas):
    try:
        sheet = conectar_sheets()
        ws = sheet.worksheet(nombre_pestana)
        ws.append_rows([[str(x) for x in fila] for fila in filas])
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error agregando registros: {e}")
        return False

df_registros = leer_pestana("Registros", COLS_REGISTROS)
df_empleados = leer_pestana("Empleados", COLS_EMPLEADOS)
df_labores = leer_pestana("Labores", COLS_LABORES)
df_coords = leer_pestana("Coordinadores", COLS_COORDS)

if "coord_logueado" not in st.session_state:
    st.session_state.coord_logueado = None

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
    if st.session_state.coord_logueado is None:
        st.title("👷 Reporte Diario de Labores")
        st.subheader("🔐 Inicio de Sesión")
        with st.form("login_coord"):
            user_in = st.text_input("Usuario:")
            pass_in = st.text_input("Contraseña:", type="password")
            if st.form_submit_button("Ingresar a mi Equipo", type="primary", use_container_width=True):
                if not df_coords.empty:
                    match = df_coords[
                        (df_coords["Usuario"].str.strip().str.lower() == user_in.strip().lower()) &
                        (df_coords["Password"].astype(str).str.strip() == pass_in.strip()) &
                        (df_coords["Estado"] == "Activo")
                    ]
                    if not match.empty:
                        st.session_state.coord_logueado = match["Nombre_Coordinador"].values[0]
                        st.rerun()
                    else:
                        st.error("❌ Usuario o contraseña incorrectos, o coordinador inactivo.")
                else:
                    st.warning("⚠️ El administrador aún no ha creado coordinadores.")
    else:
        coordinador = st.session_state.coord_logueado
        h1, h2 = st.columns([3, 1])
        h1.title(f"👷 {coordinador}")
        if h2.button("🚪 Salir", use_container_width=True):
            st.session_state.coord_logueado = None
            st.rerun()

        empleados_activos = df_empleados[(df_empleados["Estado"] == "Activo") & (df_empleados["Coordinador"] == coordinador)] if not df_empleados.empty else pd.DataFrame()
        labores_activas = df_labores[df_labores["Estado"] == "Activa"] if not df_labores.empty else pd.DataFrame()

        if empleados_activos.empty:
            st.warning("⚠️ No tienes empleados activos asignados a tu nombre.")
        elif labores_activas.empty:
            st.warning("⚠️ No hay labores activas configuradas.")
        else:
            c_fecha, c_m1, c_m2, c_m3 = st.columns([1.6, 1, 1, 1])
            with c_fecha:
                fecha_reporte = st.date_input("📅 Fecha del reporte:", value=date.today())
            
            fecha_str = fecha_reporte.strftime("%Y-%m-%d")
            
            df_hoy = pd.DataFrame()
            ya_reportados = {}
            if not df_registros.empty:
                df_hoy = df_registros[(df_registros["Fecha"] == fecha_str) & (df_registros["Coordinador"] == coordinador)]
                for _, reg in df_hoy.iterrows():
                    ya_reportados[str(reg["Cedula"])] = reg

            total_equipo = len(empleados_activos)
            total_listos = sum(1 for c in empleados_activos["Cedula"].astype(str) if c in ya_reportados)
            total_pend = total_equipo - total_listos

            c_m1.metric("👥 Equipo", total_equipo)
            c_m2.metric("✅ Listos", total_listos)
            c_m3.metric("⏳ Faltan", total_pend)

            st.divider()

            opciones_labores = labores_activas["Nombre_Labor"].tolist()
            mapa_param = dict(zip(labores_activas["Nombre_Labor"], labores_activas["Tipo_Parametro"]))
            mapa_unid = dict(zip(labores_activas["Nombre_Labor"], labores_activas["Unidad_Medida"]))
            mapa_meta = {}
            for _, r in labores_activas.iterrows():
                try:
                    mapa_meta[r["Nombre_Labor"]] = float(r["Rendimiento_Estimado"])
                except ValueError:
                    mapa_meta[r["Nombre_Labor"]] = 0.0

            registros_pendientes = []
            lista_emp = list(empleados_activos.iterrows())

            # Cuadrícula de 2 columnas estilo App Flutter
            for i in range(0, len(lista_emp), 2):
                cols_grid = st.columns(2)
                for j in range(2):
                    if i + j < len(lista_emp):
                        _, emp = lista_emp[i + j]
                        ced = str(emp["Cedula"])
                        nom = str(emp["Nombre"]).strip()
                        cargo = str(emp["Cargo_Area"]).strip() if str(emp["Cargo_Area"]).strip() else "Operario"
                        esta_reportado = ced in ya_reportados

                        # Iniciales para el avatar circular
                        partes_nom = nom.split()
                        iniciales = (partes_nom[0][0] + partes_nom[1][0]).upper() if len(partes_nom) > 1 else nom[:2].upper()
                        badge_html = "<span class='badge-ok'>✓ Listo</span>" if esta_reportado else "<span class='badge-pend'>⏳ Pendiente</span>"

                        with cols_grid[j]:
                            with st.container(border=True):
                                st.markdown(f"""
                                <div class="flutter-header">
                                    <div class="flutter-user-box">
                                        <div class="flutter-avatar">{iniciales}</div>
                                        <div>
                                            <div class="flutter-name">{nom}</div>
                                            <div class="flutter-chips">
                                                <span class="flutter-chip">🪪 {ced}</span>
                                                <span class="flutter-chip">🌱 {cargo}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div>{badge_html}</div>
                                </div>
                                """, unsafe_allow_html=True)

                                if esta_reportado:
                                    reg_ant = ya_reportados[ced]
                                    st.success(f"📍 **Lote:** {reg_ant['Lote']}  \n🛠️ **Labor:** {reg_ant['Labor']}  \n📦 **Cant:** {reg_ant['Cantidad']} {reg_ant['Unidad']} | ⏱️ **{reg_ant['Horas']}h**")
                                else:
                                    k_lote = f"lote_{fecha_str}_{ced}"
                                    k_lab = f"lab_{fecha_str}_{ced}"
                                    k_cant = f"cant_{fecha_str}_{ced}"
                                    k_hrs = f"hrs_{fecha_str}_{ced}"
                                    k_obs = f"obs_{fecha_str}_{ced}"
                                    k_last = f"last_{fecha_str}_{ced}"

                                    r1_c1, r1_c2 = st.columns([1, 1.5])
                                    with r1_c1:
                                        lote_sel = st.text_input("📍 Lote", placeholder="Ej: Lote 4", key=k_lote)
                                    with r1_c2:
                                        labor_sel = st.selectbox("🛠️ Labor", opciones_labores, key=k_lab)

                                    if st.session_state.get(k_last) != labor_sel:
                                        st.session_state[k_cant] = mapa_meta.get(labor_sel, 0.0)
                                        st.session_state[k_last] = labor_sel

                                    unidad_auto = mapa_unid.get(labor_sel, "")
                                    r2_c1, r2_c2 = st.columns(2)
                                    with r2_c1:
                                        etiqueta_cant = f"📦 Cant. ({unidad_auto})" if unidad_auto else "📦 Cantidad"
                                        cant_sel = st.number_input(etiqueta_cant, min_value=0.0, step=1.0, key=k_cant)
                                    with r2_c2:
                                        horas_sel = st.number_input("⏱️ Horas", min_value=0.0, max_value=24.0, step=0.5, value=8.0, key=k_hrs)

                                    obs_sel = st.text_input("📝 Observación / Novedad", placeholder="Opcional...", key=k_obs)

                                    param_auto = mapa_param.get(labor_sel, "Laborado")
                                    horas_final = 0.0 if ("Ausencia" in param_auto or "Descanso" in param_auto) else horas_sel

                                    registros_pendientes.append({
                                        "cedula": ced, "nombre": nom, "lote": lote_sel, "labor": labor_sel,
                                        "cantidad": cant_sel, "unidad": unidad_auto, "horas": horas_final,
                                        "parametro": param_auto, "obs": obs_sel
                                    })

            st.write("")
            if total_pend > 0:
                if st.button("💾 Guardar Reporte de Pendientes", type="primary", use_container_width=True):
                    nuevas_filas = []
                    hora_actual = datetime.now().strftime("%H:%M:%S")
                    for item in registros_pendientes:
                        if item["cedula"] not in ya_reportados:
                            id_unico = str(uuid.uuid4())[:8].upper()
                            nuevas_filas.append([
                                id_unico, fecha_str, fecha_reporte.year, fecha_reporte.month,
                                coordinador, item["cedula"], item["nombre"], item["lote"],
                                item["labor"], item["cantidad"], item["unidad"],
                                item["horas"], item["parametro"], item["obs"], hora_actual
                            ])
                    if nuevas_filas:
                        if agregar_filas("Registros", nuevas_filas):
                            st.success(f"✅ Se guardaron {len(nuevas_filas)} registros correctamente.")
                            st.rerun()
            else:
                st.success("🎉 ¡Excelente! Ya completaste el reporte de todo tu personal para esta fecha.")

elif perfil == "🗂️ 2. Control Secretaría":
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

elif perfil == "📊 3. Recursos Humanos":
    st.title("📊 Analítica de Recursos Humanos, Rendimiento y Ausentismo")
    if df_registros.empty:
        st.warning("Aún no hay datos registrados en el sistema.")
    else:
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

        f5, f6, f7, f8 = st.columns(4)
        with f5:
            labores_list = ["Todas"] + sorted(df_registros["Labor"].unique().tolist())
            sel_labor = st.selectbox("Labor específica:", labores_list)
        with f6:
            lotes_list = ["Todos"] + sorted([x for x in df_registros["Lote"].unique().tolist() if str(x).strip() != ""])
            sel_lote = st.selectbox("Lote:", lotes_list)
        with f7:
            buscar_emp = st.text_input("Buscar empleado (Nombre/Cédula):")
        with f8:
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
        if sel_lote != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Lote"] == sel_lote]
        if buscar_emp:
            df_filtrado = df_filtrado[
                df_filtrado["Empleado"].str.contains(buscar_emp, case=False, na=False) |
                df_filtrado["Cedula"].astype(str).str.contains(buscar_emp, na=False)
            ]
        if usar_fecha:
            df_filtrado = df_filtrado[df_filtrado["Fecha"] == fecha_exacta.strftime("%Y-%m-%d")]

        df_filtrado["Cant_Num"] = pd.to_numeric(df_filtrado["Cantidad"], errors="coerce").fillna(0)
        df_filtrado["Horas_Num"] = pd.to_numeric(df_filtrado["Horas"], errors="coerce").fillna(0)

        st.divider()
        k1, k2, k3, k4 = st.columns(4)
        total_reg = len(df_filtrado)
        total_aus = len(df_filtrado[df_filtrado["Tipo_Parametro"].str.contains("Ausencia", case=False, na=False)])
        total_cant = df_filtrado["Cant_Num"].sum()
        total_hrs = df_filtrado["Horas_Num"].sum()

        k1.metric("Registros Filtrados", total_reg)
        k2.metric("Total Ausencias", total_aus)
        k3.metric("Suma Cantidad", f"{total_cant:,.1f}")
        k4.metric("Total Horas Laboradas", f"{total_hrs:,.1f} hrs")

        df_export = df_filtrado.drop(columns=["ID_Registro", "Cant_Num", "Horas_Num"], errors="ignore")
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
elif perfil == "⚙️ 4. Administración (Admin)":
    st.title("⚙️ Panel de Administración del Sistema")
    clave = st.text_input("Ingrese contraseña de administrador:", type="password")
    if clave != ADMIN_PASSWORD:
        st.info("🔒 Ingrese la contraseña para gestionar coordinadores, empleados, labores y registros.")
    else:
        tab_coord, tab_emp, tab_lab, tab_reg = st.tabs([
            "🧑‍💼 Coordinadores",
            "👥 Empleados",
            "🛠️ Labores y Metas",
            "📝 Modificar / Eliminar Registros"
        ])

        with tab_coord:
            st.subheader("➕ Crear Nuevo Coordinador (Acceso con Usuario y Clave)")
            with st.form("form_nuevo_coord"):
                c1, c2, c3 = st.columns(3)
                u_coord = c1.text_input("Usuario de ingreso *", placeholder="Ej: juanp")
                n_coord = c2.text_input("Nombre Completo Coordinador *", placeholder="Ej: Juan Pérez")
                p_coord = c3.text_input("Contraseña *", placeholder="Ej: Juan2026")
                if st.form_submit_button("Crear Coordinador", type="primary"):
                    if u_coord and n_coord and p_coord:
                        if not df_coords.empty and u_coord.strip().lower() in df_coords["Usuario"].str.lower().values:
                            st.error("❌ Ya existe un coordinador con ese usuario.")
                        else:
                            agregar_filas("Coordinadores", [[u_coord.strip(), n_coord.strip(), p_coord.strip(), "Activo"]])
                            st.success("✅ Coordinador creado exitosamente.")
                            st.rerun()
                    else:
                        st.warning("Completa todos los campos obligatorios (*).")

            st.divider()
            st.subheader("✏️ Editar o Eliminar Coordinadores")
            df_coord_editado = st.data_editor(
                df_coords.reset_index(drop=True),
                num_rows="dynamic",
                use_container_width=True,
                column_config={"Estado": st.column_config.SelectboxColumn("Estado", options=["Activo", "Inactivo"], required=True)},
                key="editor_coords"
            )
            if st.button("💾 Guardar Cambios en Coordinadores", type="primary"):
                if sobrescribir_pestana("Coordinadores", df_coord_editado):
                    st.success("✅ Lista de coordinadores actualizada.")
                    st.rerun()

        with tab_emp:
            st.subheader("➕ Agregar Nuevo Empleado")
            lista_coords_activos = [
                str(fila["Nombre_Coordinador"])
                for fila in df_coords.to_dict("records")
                if str(fila.get("Estado", "")).strip() == "Activo" and str(fila.get("Nombre_Coordinador", "")).strip() != ""
            ]
            
            if not lista_coords_activos:
                st.warning("⚠️ Primero crea al menos un Coordinador activo en la pestaña 'Coordinadores'.")
            else:
                with st.form("form_nuevo_empleado"):
                    c1, c2, c3, c4 = st.columns(4)
                    nueva_ced = c1.text_input("Cédula / ID *")
                    nuevo_nom = c2.text_input("Nombre Completo *")
                    nuevo_coord = c3.selectbox("Coordinador Asignado *", lista_coords_activos)
                    nuevo_cargo = c4.text_input("Cargo / Finca / Área")
                    if st.form_submit_button("Agregar Empleado", type="primary"):
                        if nueva_ced and nuevo_nom:
                            if not df_empleados.empty and nueva_ced.strip() in df_empleados["Cedula"].astype(str).values:
                                st.error("❌ Ya existe un empleado con esa cédula.")
                            else:
                                agregar_filas("Empleados", [[nueva_ced.strip(), nuevo_nom.strip(), nuevo_coord, nuevo_cargo.strip(), "Activo"]])
                                st.success("✅ Empleado creado exitosamente.")
                                st.rerun()
                        else:
                            st.warning("Completa Cédula y Nombre (*).")

            st.divider()
            st.subheader("✏️ Editar o Eliminar Empleados")
            col_cfg_emp = {
                "Estado": st.column_config.SelectboxColumn("Estado", options=["Activo", "Inactivo"], required=True)
            }
            if lista_coords_activos:
                col_cfg_emp["Coordinador"] = st.column_config.SelectboxColumn("Coordinador", options=lista_coords_activos)

            df_emp_editado = st.data_editor(
                df_empleados.reset_index(drop=True),
                num_rows="dynamic",
                use_container_width=True,
                column_config=col_cfg_emp,
                key="editor_empleados"
            )
            if st.button("💾 Guardar Cambios en Empleados", type="primary"):
                if sobrescribir_pestana("Empleados", df_emp_editado):
                    st.success("✅ Base de datos de empleados actualizada.")
                    st.rerun()

        with tab_lab:
            st.subheader("➕ Crear Labor con Unidad y Cantidad Estimada")
            with st.form("form_nueva_labor"):
                c1, c2, c3, c4 = st.columns(4)
                nombre_lab = c1.text_input("Nombre de la Labor *", placeholder="Ej: Embolse / Corte")
                unidad_lab = c2.text_input("Unidad de Medida *", placeholder="Ej: Fundas, Racimos, Ha")
                meta_lab = c3.number_input("Cantidad Estimada (Predefinida)", min_value=0.0, step=1.0, value=0.0)
                param_lab = c4.selectbox("Parámetro RRHH *", ["Laborado", "Ausencia Injustificada", "Ausencia Justificada", "Descanso / Vacaciones"])
                if st.form_submit_button("Crear Labor", type="primary"):
                    if nombre_lab:
                        agregar_filas("Labores", [[nombre_lab.strip(), unidad_lab.strip(), meta_lab, param_lab, "Activa"]])
                        st.success("✅ Labor agregada al catálogo.")
                        st.rerun()
                    else:
                        st.warning("Escribe el nombre de la labor.")

            st.divider()
            st.subheader("✏️ Editar o Eliminar Labores")
            df_lab_editado = st.data_editor(
                df_labores.reset_index(drop=True),
                num_rows="dynamic",
                use_container_width=True,
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
                opciones_lab_admin = [
                    str(fila["Nombre_Labor"])
                    for fila in df_labores.to_dict("records")
                    if str(fila.get("Nombre_Labor", "")).strip() != ""
                ]

                col_cfg_reg = {
                    "Tipo_Parametro": st.column_config.SelectboxColumn("Tipo_Parametro", options=["Laborado", "Ausencia Injustificada", "Ausencia Justificada", "Descanso / Vacaciones"])
                }
                if opciones_lab_admin:
                    col_cfg_reg["Labor"] = st.column_config.SelectboxColumn("Labor", options=opciones_lab_admin)

                df_reg_editado = st.data_editor(
                    df_vista_reg.reset_index(drop=True),
                    num_rows="dynamic",
                    use_container_width=True,
                    disabled=["ID_Registro"],
                    column_config=col_cfg_reg,
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
