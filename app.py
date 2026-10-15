import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import io
import re

st.set_page_config(page_title="Calculadora Flete Lácteo", layout="wide", page_icon="🚚")

st.title("🚚 Calculadora de Flete Lácteo vs. Tarifa de Referencia")
st.markdown("Herramienta interactiva para evaluar el punto de equilibrio y la conveniencia económica del flete lácteo.")

# --- ID PRECARGADO POR DEFECTO ---
DEFAULT_DRIVE_ID = "1X4SRt1MRDAhv5Xn2D-wucQJnVKZn6KDE"

# --- DATOS EMBEBIDOS DE RESPALDO (EN CASO DE FALTA DE CONEXIÓN O ERROR) ---
RAW_RATES = [
    9636.69, 9636.69, 9636.69, 9636.69, 9636.69, 9636.69, 9636.69, 9636.69, 9636.69, 9636.69,
    9864.22, 10096.67, 10329.15, 10566.63, 10811.61, 11061.60, 11311.57, 11571.55, 11836.52, 12104.00,
    12376.48, 12653.95, 12933.93, 13218.91, 13508.88, 13801.36, 14098.84, 14398.81, 14703.79, 15011.27,
    15321.25, 15636.22, 15953.70, 16273.68, 16596.15, 16923.63, 17253.61, 17586.08, 17921.06, 18258.54,
    18598.51, 18941.00, 19285.97, 19633.45, 19983.43, 20335.90, 20690.88, 21048.36, 21408.33, 21770.81,
    22135.79, 22503.26, 22873.24, 23245.72, 23620.69, 23998.17, 24378.15, 24760.62, 25145.60, 25533.08,
    25923.05, 26315.53, 26710.51, 27107.98, 27507.96, 27910.44, 28315.41, 28722.89, 29132.87, 29545.34,
    29960.32, 30377.80, 30797.77, 31220.25, 31645.23, 32072.70, 32502.68, 32935.16, 33370.13, 33807.61,
    34247.59, 34690.06, 35135.04, 35582.52, 36032.49, 36484.97, 36939.95, 37397.42, 37857.40, 38319.88,
    38784.85, 39252.33, 39722.31, 40194.78, 40669.76, 41147.24, 41627.21, 42109.69, 42594.67, 43082.14,
    43572.12, 44064.60, 44559.57, 45057.05, 45557.03, 46059.50, 46564.48, 47071.96, 47581.93, 48094.41,
    48609.39, 49126.86, 49646.84, 50169.32, 50694.29, 51221.77, 51751.75, 52284.22, 52819.20, 53356.68,
    53896.65, 54439.13, 54984.11, 55531.58, 56081.56, 56633.54, 57188.01, 57744.99, 58304.46, 58866.44,
    59430.92, 59997.89, 60567.37, 61139.35, 61713.82, 62290.80, 62870.28, 63452.25, 64036.73, 64623.71,
    65213.18, 65805.16, 66399.64, 66996.61, 67596.09, 68198.07, 68802.54, 69409.52, 70018.99, 70630.97,
    71245.45, 71862.42, 72481.90, 73103.88, 73728.35, 74355.33, 74984.81, 75616.78, 76251.26, 76888.24,
    77527.71, 78169.69, 78814.17, 79461.14, 80110.62, 80762.60, 81417.07, 82074.05, 82733.53, 83395.50,
    84059.98, 84726.96, 85396.43, 86068.41, 86742.89, 87419.86, 88099.34, 88781.32, 89465.79, 90152.77,
    90842.25, 91534.22, 92228.70, 92925.68, 93625.15, 94327.13, 95031.61, 95738.58, 96448.06, 97160.04,
    97874.51, 98591.49, 99310.97, 100032.94, 100757.42, 101484.40, 102213.87, 102945.85, 103680.33, 104417.30
]

DEFAULT_DF = pd.DataFrame({
    'KM': list(range(1, len(RAW_RATES[:300]) + 1)),
    'Tarifa_Tn': RAW_RATES[:300]
})

# --- EXTRAER ID DESDE TEXTO O URL ---
def extract_file_id(url_or_id):
    if not url_or_id:
        return ""
    url_or_id = url_or_id.strip()
    match = re.search(r'/(?:d|file/d)/([a-zA-Z0-9_-]+)', url_or_id)
    if match:
        return match.group(1)
    match_param = re.search(r'id=([a-zA-Z0-9_-]+)', url_or_id)
    if match_param:
        return match_param.group(1)
    return url_or_id

# --- CARGA AUTOMÁTICA DESDE GOOGLE DRIVE ---
@st.cache_data(ttl=600)
def load_from_drive(file_id_input):
    clean_id = extract_file_id(file_id_input)
    if not clean_id:
        return DEFAULT_DF, "Cargado con datos por defecto."
    
    urls_to_try = [
        f"https://drive.google.com/uc?export=download&id={clean_id}",
        f"https://docs.google.com/spreadsheets/d/{clean_id}/export?format=xlsx"
    ]
    
    for url in urls_to_try:
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200 and len(res.content) > 500:
                excel_buffer = io.BytesIO(res.content)
                df = pd.read_excel(excel_buffer)
                df = df.iloc[:, :2] # Toma las dos primeras columnas (KM y Tarifa)
                df.columns = ['KM', 'Tarifa_Tn']
                return df, "✅ Planilla cargada exitosamente desde Google Drive"
        except Exception:
            continue
            
    return DEFAULT_DF, "⚠️ No se pudo descargar desde Drive. Verificá que el archivo tenga acceso público ('Cualquier persona con el enlace')."

# --- SIDEBAR ---
st.sidebar.header("⚙️ Configuración")

drive_input = st.sidebar.text_input(
    "ID o Enlace de Google Drive", 
    value=DEFAULT_DRIVE_ID, 
    placeholder="Pegá el ID o enlace del archivo"
)

aforo_tn = st.sidebar.number_input(
    "Aforo del Camión (Toneladas)", 
    min_value=1.0, 
    max_value=60.0, 
    value=30.0, 
    step=1.0
)
litros_totales = aforo_tn * 1000

precio_fijo_litro = st.sidebar.number_input(
    "Precio Fijo Actual ($/Litro)", 
    min_value=1.0, 
    max_value=200.0, 
    value=30.0, 
    step=0.50
)

# Cargar y notificar estado
df, status_msg = load_from_drive(drive_input)

if "✅" in status_msg:
    st.sidebar.success(status_msg)
elif "⚠️" in status_msg:
    st.sidebar.warning(status_msg)

# --- CÁLCULOS ---
df['Costo_L_Tabla'] = df['Tarifa_Tn'] / 1000.0
df['Costo_Viaje_Tabla'] = df['Tarifa_Tn'] * aforo_tn
df['Costo_Viaje_Fijo'] = precio_fijo_litro * litros_totales
df['Diferencia_Viaje'] = df['Costo_Viaje_Fijo'] - df['Costo_Viaje_Tabla']

# Punto de Equilibrio
be_row = df[df['Costo_L_Tabla'] >= precio_fijo_litro].head(1)
if not be_row.empty:
    km_be = be_row.iloc[0]['KM']
    costo_be = be_row.iloc[0]['Costo_L_Tabla']
else:
    km_be = "> 300"
    costo_be = 0.0

# --- METRICAS DE CABECERA ---
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Punto de Equilibrio", f"{km_be} KM", f"${costo_be:.2f} / Litro")
kpi2.metric("Volumen por Viaje", f"{litros_totales:,.0f} Lts", f"{aforo_tn:.0f} Toneladas")
kpi3.metric("Costo Fijo / Viaje", f"${precio_fijo_litro * litros_totales:,.2f}", f"${precio_fijo_litro:.2f} / Litro")
kpi4.metric("Tarifa Máxima (300 km)", f"${df['Costo_L_Tabla'].max():.2f} / L", f"${df['Costo_Viaje_Tabla'].max():,.2f} / viaje")

st.divider()

# --- SIMULADOR DE KILOMETRAJE ---
st.subheader("📍 Simulación por Recorrido")
km_sim = st.slider("Seleccionar distancia recorrida (KM)", min_value=int(df['KM'].min()), max_value=int(df['KM'].max()), value=50)

row_km = df[df['KM'] == km_sim].iloc[0]
costo_tabla_l = row_km['Costo_L_Tabla']
costo_tabla_v = row_km['Costo_Viaje_Tabla']
costo_fijo_v = row_km['Costo_Viaje_Fijo']
dif_v = row_km['Diferencia_Viaje']

c1, c2, c3, c4 = st.columns(4)
c1.metric("Tarifa Tabla ($/L)", f"${costo_tabla_l:.2f}")
c2.metric("Costo Viaje (Tabla)", f"${costo_tabla_v:,.2f}")
c3.metric("Costo Viaje (Fijo Actual)", f"${costo_fijo_v:,.2f}")

if dif_v > 0:
    pct = (dif_v / costo_tabla_v) * 100
    c4.metric("Estado Operativo", f"Sobrepago de ${dif_v:,.2f}", f"+{pct:.1f}% vs Tabla", delta_color="inverse")
else:
    pct = (abs(dif_v) / costo_tabla_v) * 100
    c4.metric("Estado Operativo", f"Ahorro de ${abs(dif_v):,.2f}", f"-{pct:.1f}% vs Tabla", delta_color="normal")

# --- GRÁFICO INTERACTIVO ---
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df['KM'], 
    y=df['Costo_L_Tabla'], 
    mode='lines', 
    name='Tarifa Referencia ($/L)', 
    line=dict(color='#1f77b4', width=3)
))

fig.add_trace(go.Scatter(
    x=df['KM'], 
    y=[precio_fijo_litro]*len(df), 
    mode='lines', 
    name=f'Tarifa Fija Actual (${precio_fijo_litro:.2f}/L)', 
    line=dict(color='#e377c2', width=2, dash='dash')
))

if isinstance(km_be, (int, float)):
    fig.add_vline(x=km_be, line_dash="dot", line_color="red", annotation_text=f"Equilibrio: {km_be} KM", annotation_position="top right")

fig.update_layout(
    title="Curva de Costo por Litro según Distancia Recorrida",
    xaxis_title="Distancia (KM)",
    yaxis_title="Costo ($ / Litro)",
    hovermode="x unified",
    template="plotly_white",
    height=450
)

st.plotly_chart(fig, use_container_width=True)

# --- TABLA DE DATOS ---
with st.expander("📋 Ver Tabla Completa de Tarifas y Comparativa"):
    st.dataframe(
        df[['KM', 'Tarifa_Tn', 'Costo_L_Tabla', 'Costo_Viaje_Tabla', 'Costo_Viaje_Fijo', 'Diferencia_Viaje']].rename(columns={
            'Tarifa_Tn': 'Tarifa ($/Tn)',
            'Costo_L_Tabla': 'Tarifa Tabla ($/L)',
            'Costo_Viaje_Tabla': 'Costo Viaje Tabla ($)',
            'Costo_Viaje_Fijo': 'Costo Viaje Fijo ($)',
            'Diferencia_Viaje': 'Diferencia ($)'
        }),
        use_container_width=True
    )
