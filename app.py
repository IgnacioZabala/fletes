import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
import io
import re

st.set_page_config(page_title="Gestión y Rentabilidad de Camión Lácteo", layout="wide", page_icon="🚛")

st.title("🚛 Control de Rentabilidad y Gestión de Camión Lácteo")
st.markdown("Calculadora de costos operativos, simulador de viajes y análisis de rentabilidad neta.")

DEFAULT_DRIVE_ID = "1X4SRt1MRDAhv5Xn2D-wucQJnVKZn6KDE"

# --- SIDEBAR: ESTRUCTURA DE COSTOS DEL CAMIÓN ---
st.sidebar.header("⚙️ 1. Costos Variables (por KM)")
gasoil_precio = st.sidebar.number_input("Precio Gasoil ($/L)", value=2000.0, step=10.0)
consumo_l_100km = st.sidebar.number_input("Consumo Camión (L / 100 km)", value=38.0, step=1.0)
costo_mantenimiento_km = st.sidebar.number_input("Mantenimiento y Repuestos ($/km)", value=400.0, step=10.0)
costo_neumaticos_km = st.sidebar.number_input("Desgaste de Cubiertas ($/km)", value=150.0, step=10.0)

# Cálculo Costo Variable por KM recorrido (ida + vuelta)
costo_gasoil_km = (consumo_l_100km / 100.0) * gasoil_precio
cv_total_km_recorrido = costo_gasoil_km + costo_mantenimiento_km + costo_neumaticos_km

st.sidebar.divider()
st.sidebar.header("🏢 2. Costos Fijos Mensuales")
sueldo_chofer = st.sidebar.number_input("Sueldo Chofer + Cargas Soc. ($)", value=2300000.0, step=50000.0)
seguros_patentes = st.sidebar.number_input("Seguro, Patente, VTV, Satelital ($)", value=450000.0, step=20000.0)
amortizacion_unidad = st.sidebar.number_input("Amortización / Depreciación ($)", value=2600000.0, step=50000.0)
gastos_admin = st.sidebar.number_input("Sueldo ($)", value=2000000.0, step=20000.0)
viajes_estimados_mes = st.sidebar.number_input("Viajes Estimados al Mes", value=20, min_value=1, step=1)

cf_total_mensual = sueldo_chofer + seguros_patentes + amortizacion_unidad + gastos_admin
cf_por_viaje = cf_total_mensual / viajes_estimados_mes

st.sidebar.divider()
st.sidebar.header("🔗 3. Planilla de Viajes (Drive)")
drive_input = st.sidebar.text_input("ID o Enlace de Google Drive", value=DEFAULT_DRIVE_ID)

# --- CARGA Y PROCESAMIENTO DESDE DRIVE ---
def extract_file_id(url_or_id):
    if not url_or_id: return ""
    url_or_id = url_or_id.strip()
    match = re.search(r'/(?:d|file/d)/([a-zA-Z0-9_-]+)', url_or_id)
    if match: return match.group(1)
    match_param = re.search(r'id=([a-zA-Z0-9_-]+)', url_or_id)
    if match_param: return match_param.group(1)
    return url_or_id

@st.cache_data(ttl=300)
def load_trips_data(file_id_input):
    clean_id = extract_file_id(file_id_input)
    if not clean_id:
        return None, "Sin ID configurado."
    
    urls = [
        f"https://drive.google.com/uc?export=download&id={clean_id}",
        f"https://docs.google.com/spreadsheets/d/{clean_id}/export?format=xlsx"
    ]
    for url in urls:
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200 and len(res.content) > 500:
                excel_buffer = io.BytesIO(res.content)
                # Intentar leer pestaña 'Viajes' o la primera
                xls = pd.ExcelFile(excel_buffer)
                sheet_name = 'Viajes' if 'Viajes' in xls.sheet_names else xls.sheet_names[0]
                df_trips = pd.read_excel(xls, sheet_name=sheet_name)
                return df_trips, "✅ Planilla vinculada con éxito desde Google Drive"
        except Exception:
            continue
    return None, "⚠️ No se pudo cargar la planilla. Verificá los permisos del archivo."

df_raw, status_msg = load_trips_data(drive_input)

# --- DATOS DE EJEMPLO SI NO HAY TABLA DE VIAJES ---
if df_raw is None or 'KM_Ida' not in df_raw.columns:
    df_trips = pd.DataFrame([
        {"Fecha": "2026-10-01", "Cliente_Ruta": "Tandil - Rauch", "KM_Ida": 75, "Litros_Carga": 30000, "Tipo_Cobro": "Por Litro", "Tarifa": 30.0},
        {"Fecha": "2026-10-03", "Cliente_Ruta": "Tandil - Azul", "KM_Ida": 100, "Litros_Carga": 28500, "Tipo_Cobro": "Por Litro", "Tarifa": 30.0},
        {"Fecha": "2026-10-05", "Cliente_Ruta": "Tandil - Olavarría", "KM_Ida": 130, "Litros_Carga": 30000, "Tipo_Cobro": "Global", "Tarifa": 1050000.0},
        {"Fecha": "2026-10-08", "Cliente_Ruta": "Tandil - Balcarce", "KM_Ida": 65, "Litros_Carga": 29000, "Tipo_Cobro": "Por Litro", "Tarifa": 30.0},
    ])
    st.sidebar.info("📌 Usando tabla de viajes de demostración.")
else:
    df_trips = df_raw.copy()
    st.sidebar.success(status_msg)

# --- PESTAÑAS DE LA APP ---
tab1, tab2, tab3 = st.tabs(["🧮 Simulador de Viaje Puntual", "📊 Bitácora & Rentabilidad Mensual", "⚙️ Resumen Estructura de Costos"])

# ==========================================
# TAB 1: SIMULADOR DE VIAJE PUNTUAL
# ==========================================
with tab1:
    st.subheader("📍 Cotizador / Evaluador de Viaje Individual")
    
    col_sim1, col_sim2, col_sim3, col_sim4 = st.columns(4)
    sim_km = col_sim1.number_input("Distancia de Ida (KM)", value=80, step=5)
    sim_litros = col_sim2.number_input("Litros a Transportar", value=30000, step=1000)
    sim_tipo_cobro = col_sim3.selectbox("Modalidad de Cobro", ["Por Litro ($/L)", "Monto Fijo Global ($)"])
    
    if sim_tipo_cobro == "Por Litro ($/L)":
        sim_tarifa = col_sim4.number_input("Precio Cobrado por Litro ($)", value=30.0, step=0.5)
        ingreso_sim = sim_litros * sim_tarifa
    else:
        sim_tarifa = col_sim4.number_input("Cobro Total del Flete ($)", value=900000.0, step=10000.0)
        ingreso_sim = sim_tarifa

    km_totales_sim = sim_km * 2
    costo_gasoil_sim = km_totales_sim * costo_gasoil_km
    costo_mantenimiento_sim = km_totales_sim * costo_mantenimiento_km
    costo_neumaticos_sim = km_totales_sim * costo_neumaticos_km
    costo_var_sim = km_totales_sim * cv_total_km_recorrido
    
    costo_total_sim = costo_var_sim + cf_por_viaje
    ganancia_neta_sim = ingreso_sim - costo_total_sim
    margen_neto_pct_sim = (ganancia_neta_sim / ingreso_sim) * 100 if ingreso_sim > 0 else 0

    st.markdown("#### Resultado Financiero del Viaje")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Ingreso Flete", f"${ingreso_sim:,.2f}")
    m2.metric("Costo Variable (Gasoil+Maint)", f"${costo_var_sim:,.2f}")
    m3.metric("Costo Fijo Asignado", f"${cf_por_viaje:,.2f}")
    m4.metric("Ganancia Neta", f"${ganancia_neta_sim:,.2f}", f"{margen_neto_pct_sim:.1f}% Margen")
    m5.metric("Costo por KM Recorrido", f"${costo_total_sim / km_totales_sim:,.2f} / km")

    # Desglose de costos del viaje
    fig_pie = go.Figure(data=[go.Pie(
        labels=['Gasoil', 'Mantenimiento', 'Cubiertas', 'Costo Fijo Prorrateado'],
        values=[costo_gasoil_sim, costo_mantenimiento_sim, costo_neumaticos_sim, cf_por_viaje],
        hole=.4
    )])
    fig_pie.update_layout(title="Distribución de Costos del Viaje", height=350)
    st.plotly_chart(fig_pie, use_container_width=True)

# ==========================================
# TAB 2: BITÁCORA Y RENTABILIDAD CONSOLIDADA
# ==========================================
with tab2:
    st.subheader("📈 Análisis de Rentabilidad Consolidada (Viajes Registrados)")

    # Procesamiento de la tabla de viajes
    df_trips['KM_Totales'] = df_trips['KM_Ida'] * 2
    df_trips['Costo_Combustible'] = df_trips['KM_Totales'] * costo_gasoil_km
    df_trips['Costo_Variable'] = df_trips['KM_Totales'] * cv_total_km_recorrido
    
    # Calcular ingreso según tipo de cobro
    if 'Tipo_Cobro' in df_trips.columns:
        df_trips['Ingreso_Total'] = df_trips.apply(
            lambda r: r['Litros_Carga'] * r['Tarifa'] if str(r['Tipo_Cobro']).lower() in ['por litro', 'por litro ($/l)'] else r['Tarifa'],
            axis=1
        )
    else:
        df_trips['Ingreso_Total'] = df_trips['Litros_Carga'] * 30.0

    df_trips['Costo_Fijo_Asignado'] = cf_por_viaje
    df_trips['Costo_Total'] = df_trips['Costo_Variable'] + df_trips['Costo_Fijo_Asignado']
    df_trips['Margen_Bruto'] = df_trips['Ingreso_Total'] - df_trips['Costo_Variable']
    df_trips['Ganancia_Neta'] = df_trips['Ingreso_Total'] - df_trips['Costo_Total']
    df_trips['Margen_Pct'] = (df_trips['Ganancia_Neta'] / df_trips['Ingreso_Total']) * 100

    # KPIs Generales
    tot_ingresos = df_trips['Ingreso_Total'].sum()
    tot_costo_var = df_trips['Costo_Variable'].sum()
    tot_km_recorridos = df_trips['KM_Totales'].sum()
    tot_litros = df_trips['Litros_Carga'].sum()
    
    # Resultado operacional del mes
    ganancia_operativa_real = tot_ingresos - tot_costo_var - cf_total_mensual
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Facturación Total", f"${tot_ingresos:,.2f}", f"{len(df_trips)} viajes")
    k2.metric("Litros Transportados", f"{tot_litros:,.0f} Lts", f"{tot_km_recorridos:,.0f} km recorridos")
    k3.metric("Costo Variable Acumulado", f"${tot_costo_var:,.2f}")
    k4.metric("Resultado Neto del Mes", f"${ganancia_operativa_real:,.2f}", f"{(ganancia_operativa_real/tot_ingresos)*100 if tot_ingresos>0 else 0:.1f}% Margen Global")

    st.divider()

    # Gráfico Comparativo por Viaje
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(x=df_trips['Cliente_Ruta'], y=df_trips['Ingreso_Total'], name='Ingreso Flete', marker_color='#2ca02c'))
    fig_bar.add_trace(go.Bar(x=df_trips['Cliente_Ruta'], y=df_trips['Costo_Variable'], name='Costo Variable', marker_color='#ff7f0e'))
    fig_bar.add_trace(go.Bar(x=df_trips['Cliente_Ruta'], y=df_trips['Ganancia_Neta'], name='Ganancia Neta (Post Costo Fijo)', marker_color='#1f77b4'))
    
    fig_bar.update_layout(title="Comparativo de Ingresos vs. Costos por Viaje", barmode='group', height=400, template='plotly_white')
    st.plotly_chart(fig_bar, use_container_width=True)

    # Detalle en Tabla
    st.subheader("📋 Detalle del Registro de Viajes")
    st.dataframe(
        df_trips[['Fecha', 'Cliente_Ruta', 'KM_Ida', 'Litros_Carga', 'Ingreso_Total', 'Costo_Variable', 'Costo_Total', 'Ganancia_Neta', 'Margen_Pct']].rename(columns={
            'KM_Ida': 'KM Ida',
            'Litros_Carga': 'Litros',
            'Ingreso_Total': 'Ingreso ($)',
            'Costo_Variable': 'Costo Var ($)',
            'Costo_Total': 'Costo Total ($)',
            'Ganancia_Neta': 'Ganancia ($)',
            'Margen_Pct': 'Margen (%)'
        }),
        use_container_width=True
    )

# ==========================================
# TAB 3: RESUMEN DE ESTRUCTURA DE COSTOS
# ==========================================
with tab3:
    st.subheader("⚙️ Estructura Completa de Costos de la Unidad")
    
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        st.markdown("### Costos Variables por KM Recorrido")
        st.write(f"* **Gasoil ({consumo_l_100km} L/100km @ ${gasoil_precio:.2f}/L):** ${costo_gasoil_km:.2f} / km")
        st.write(f"* **Mantenimiento, Filtros y Repuestos:** ${costo_mantenimiento_km:.2f} / km")
        st.write(f"* **Desgaste de Cubiertas / Neumáticos:** ${costo_neumaticos_km:.2f} / km")
        st.info(f"**Total Costo Variable por KM:** ${cv_total_km_recorrido:.2f} / km recorrido (${cv_total_km_recorrido*2:.2f} por KM de ida)")

    with col_c2:
        st.markdown("### Costos Fijos Mensuales")
        st.write(f"* **Sueldo Chofer y Cargas Sociales:** ${sueldo_chofer:,.2f}")
        st.write(f"* **Seguro, Patentes, VTV, Satelital:** ${seguros_patentes:,.2f}")
        st.write(f"* **Amortización / Depreciación:** ${amortizacion_unidad:,.2f}")
        st.write(f"* **Gastos Administrativos y Cochera:** ${gastos_admin:,.2f}")
        st.warning(f"**Total Costos Fijos Mensuales:** ${cf_total_mensual:,.2f} (${cf_por_viaje:,.2f} asignados por viaje sobre {viajes_estimados_mes} viajes/mes)")
