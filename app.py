import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Calculadora Flete Lácteo", layout="wide", page_icon="🚚")

st.title("🚚 Calculadora de Flete Lácteo vs. Tarifa de Referencia")
st.markdown("Herramienta interactiva para evaluar el punto de equilibrio y la conveniencia económica del flete lácteo.")

# --- SIDEBAR ---
st.sidebar.header("⚙️ Parámetros de Carga y Tarifa")

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

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_tarifas():
    df = pd.read_excel('Tarifa camiones.xlsx')
    df.columns = ['KM', 'Tarifa_Tn']
    return df

try:
    df = cargar_tarifas()
except Exception as e:
    st.error(f"Error al cargar 'Tarifa camiones.xlsx': {e}")
    st.stop()

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

# --- GRÁFICO INTERACTIVO PLOTLY ---
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
