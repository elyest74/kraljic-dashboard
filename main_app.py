import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date
import io

# ── 1. CONFIGURACIÓN DE NIVEL PROFESIONAL ──
st.set_page_config(
    page_title="Purchasing Strategic Dashboard | Elymar Estévez",
    page_icon="https://img.icons8.com/fluency/96/strategy.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── 2. ESTILOS CSS PERSONALIZADOS ──
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .main { background-color: #f8fafc; }
        .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

# ── 3. ENCABEZADO PREMIUM ──
st.markdown("""
    <div style="background-color: #0F172A; padding: 25px; border-radius: 15px; margin-bottom: 25px; border-left: 8px solid #3B82F6;">
        <h1 style="color: white; margin: 0; font-size: 2.2rem; font-weight: 800;">
            Purchasing Strategic Dashboard <span style="font-size: 0.9rem; color: #3B82F6; vertical-align: middle; border: 1px solid #3B82F6; padding: 2px 8px; border-radius: 10px; margin-left: 10px;">V4.0</span>
        </h1>
        <p style="color: #94A3B8; margin: 8px 0 0 0; font-size: 1.1rem;">
            ACOMPAÑANTE DIGITAL: <strong>COMPRAS 4.0</strong> · ELYMAR ESTÉVEZ
        </p>
    </div>
""", unsafe_allow_html=True)

# ── 4. LÓGICA DE NEGOCIO Y REGLAS ──
RULES = [
    (['acero', 'hierro', 'aluminio', 'cobre', 'metal'], 9, 8, 'Metales y Commodities'),
    (['gas', 'electricidad', 'energia', 'fuel'], 10, 9, 'Energía y Utilities'),
    (['resina', 'quimico', 'plastico'], 7, 7, 'Químicos y Resinas'),
    (['logistica', 'flete', 'transporte'], 6, 6, 'Servicios Logísticos'),
    (['software', 'it', 'nube', 'cloud'], 8, 7, 'Tecnología 4.0'),
    (['oficina', 'limpieza', 'papel'], 2, 2, 'Suministros No Críticos')
]

def analyze_item(name, spend, total_spend):
    name_low = str(name).lower()
    imp, risk, cat = 5, 5, "General"
    for keywords, score_i, score_r, category_name in RULES:
        if any(k in name_low for k in keywords):
            imp, risk, cat = score_i, score_r, category_name
            break
    if total_spend > 0 and (spend / total_spend) > 0.15:
        imp = min(10, imp + 1)
    
    if imp >= 6 and risk >= 6: q = 'Estratégico'
    elif imp >= 6 and risk < 6: q = 'Apalancamiento'
    elif imp < 6 and risk >= 6: q = 'Cuello de Botella'
    else: q = 'No Crítico'
    return imp, risk, cat, q

# ── 5. BARRA LATERAL ──
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/strategy.png", width=100)
    st.markdown("### Configuración")
    sector = st.selectbox("Sector", ["Manufactura", "Energía", "Tecnología", "Salud"])
    st.divider()
    
    # --- SECCIÓN DE DESCARGA DE PLANTILLA ---
    st.markdown("#### 📥 Plantilla")
    template_df = pd.DataFrame({'Nombre': ['Acero', 'Logistica'], 'Gasto': [100000, 5000]})
    csv = template_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Descargar Plantilla CSV",
        data=csv,
        file_name='plantilla_compras_40.csv',
        mime='text/csv',
    )
    st.divider()
    st.caption("Compras 4.0 - Elymar Estévez")

# ── 6. INTERFAZ PRINCIPAL ──
tab1, tab2 = st.tabs(["📥 Datos y Carga", "📊 Análisis y Estrategia"])

with tab1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Subir Archivo")
        uploaded_file = st.file_uploader("Carga tu Excel o CSV", type=['csv', 'xlsx'])
    
    with col2:
        st.subheader("Entrada Manual")
        st.info("Puedes editar los datos directamente en la tabla de abajo.")

    # Lógica para determinar qué datos mostrar
    if uploaded_file is not None:
        if uploaded_file.name.endswith('.csv'):
            df_initial = pd.read_csv(uploaded_file)
        else:
            df_initial = pd.read_excel(uploaded_file)
    else:
        df_initial = pd.DataFrame({'Nombre': ['Ejemplo 1', 'Ejemplo 2'], 'Gasto': [10000, 5000]})

    data_df = st.data_editor(df_initial, num_rows="dynamic", use_container_width=True)

    if st.button("EJECUTAR ANÁLISIS ESTRATÉGICO", type="primary"):
        total = data_df.iloc[:, 1].sum()
        processed = []
        for _, row in data_df.iterrows():
            i, r, c, q = analyze_item(row[0], row[1], total)
            processed.append({'Nombre': row[0], 'Gasto': row[1], 'Impacto': i, 'Riesgo': r, 'Tipo': c, 'Cuadrante': q})
        st.session_state['results'] = pd.DataFrame(processed)
        st.success("¡Análisis Generado!")

with tab2:
    if 'results' in st.session_state:
        df = st.session_state['results']
        
        # Gráfico Plotly
        fig = go.Figure()
        colors = {'Estratégico': '#EF4444', 'Apalancamiento': '#10B981', 'Cuello de Botella': '#F59E0B', 'No Crítico': '#64748B'}
        
        for q_name, color in colors.items():
            dff = df[df['Cuadrante'] == q_name]
            if not dff.empty:
                fig.add_trace(go.Scatter(
                    x=dff['Impacto'], y=dff['Riesgo'],
                    mode='markers+text',
                    name=q_name,
                    text=dff['Nombre'],
                    marker=dict(size=dff['Gasto']/df['Gasto'].max()*50 + 20, color=color)
                ))
        
        fig.update_layout(title="Matriz de Kraljic", xaxis_title="Impacto", yaxis_title="Riesgo")
        st.plotly_chart(fig, use_container_width=True)
        
        # Botón para descargar el resultado final
        res_csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Informe Final (CSV)", res_csv, "informe_kraljic_40.csv", "text/csv")
    else:
        st.info("Carga datos para ver la matriz.")
