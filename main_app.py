import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date

# ── 1. CONFIGURACIÓN DE NIVEL PROFESIONAL (Obligatorio al inicio) ──
st.set_page_config(
    page_title="Purchasing Strategic Dashboard | Elymar Estévez",
    page_icon="https://img.icons8.com/fluency/96/strategy.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── 2. ESTILOS CSS PERSONALIZADOS (Look & Feel 4.0) ──
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .main { background-color: #f8fafc; }
        .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-weight: 600; }
        .stTabs [data-baseweb="tab"] { font-weight: 700; color: #1e293b; }
    </style>
""", unsafe_allow_html=True)

# ── 3. ENCABEZADO PREMIUM (Identidad Visual del Libro) ──
st.markdown("""
    <div style="background-color: #0F172A; padding: 25px; border-radius: 15px; margin-bottom: 25px; border-left: 8px solid #3B82F6;">
        <h1 style="color: white; margin: 0; font-size: 2.2rem; font-weight: 800;">
            Purchasing Strategic Dashboard <span style="font-size: 0.9rem; color: #3B82F6; vertical-align: middle; border: 1px solid #3B82F6; padding: 2px 8px; border-radius: 10px; margin-left: 10px;">V4.0</span>
        </h1>
        <p style="color: #94A3B8; margin: 8px 0 0 0; font-size: 1.1rem; letter-spacing: 0.5px;">
            ACOMPAÑANTE DIGITAL: <strong>COMPRAS 4.0</strong> · ELYMAR ESTÉVEZ
        </p>
    </div>
""", unsafe_allow_html=True)

# ── 4. BARRA LATERAL (Panel de Control) ──
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/strategy.png", width=100)
    st.markdown("### Control Estratégico")
    st.info("Algoritmo de categorización automática basado en sector e impacto de gasto.")
    
    st.divider()
    sector = st.selectbox("Sector de la Empresa", 
                          ["Manufactura / Metalmecánica", "Energía / Utilities", "Alimentación / Agro", "Tecnología / IT", "Salud / Pharma"])
    analista = st.text_input("Analista Responsable", "Elymar Estévez")
    fecha_analisis = st.date_input("Fecha de Análisis", date.today())
    
    st.divider()
    st.caption("© 2024 - Gestión de Categorías y Futuro Digital")

# ── 5. MOTOR DE INTELIGENCIA DE CATEGORIZACIÓN ──
RULES = [
    (['acero', 'hierro', 'aluminio', 'cobre', 'metal', 'niquel'], 9, 8, 'Metales y Commodities'),
    (['gas', 'electricidad', 'energia', 'fuel', 'diesel'], 10, 9, 'Energía y Utilities'),
    (['resina', 'quimico', 'plastico', 'polimero'], 7, 7, 'Químicos y Resinas'),
    (['logistica', 'flete', 'transporte', 'puerto', 'aduana'], 6, 6, 'Servicios Logísticos'),
    (['software', 'it', 'licencia', 'nube', 'cloud', 'saas'], 8, 7, 'Tecnología 4.0'),
    (['mantenimiento', 'repuesto', 'mro', 'herramienta'], 5, 7, 'Mantenimiento / MRO'),
    (['oficina', 'limpieza', 'papel', 'suministro'], 2, 2, 'Suministros No Críticos')
]

def analyze_item(name, spend, total_spend):
    name_low = name.lower()
    imp, risk, cat = 5, 5, "General / No Clasificado"
    
    for keywords, score_i, score_r, category_name in RULES:
        if any(k in name_low for k in keywords):
            imp, risk, cat = score_i, score_r, category_name
            break
            
    # Ajuste por Pareto (Si representa más del 15% del gasto, el impacto sube)
    if total_spend > 0 and (spend / total_spend) > 0.15:
        imp = min(10, imp + 1)
        
    # Lógica de Cuadrantes
    if imp >= 6 and risk >= 6: q = 'Estratégico'
    elif imp >= 6 and risk < 6: q = 'Apalancamiento'
    elif imp < 6 and risk >= 6: q = 'Cuello de Botella'
    else: q = 'No Crítico'
    
    return imp, risk, cat, q

# ── 6. INTERFAZ DE USUARIO (TABS) ──
tab1, tab2, tab3 = st.tabs(["📥 Gestión de Datos", "📊 Matriz de Kraljic", "📋 Estrategias de Negociación"])

with tab1:
    st.subheader("Carga y Categorización de Proveedores")
    st.markdown("Introduce los datos de tus categorías. El sistema aplicará la lógica 4.0 para el scoring.")
    
    data_df = st.data_editor(
        pd.DataFrame({
            'Categoría / Proveedor': ['Bobinas de Acero', 'Suministro Gas Natural', 'Mantenimiento Planta', 'Servicios Cloud ERP'],
            'Gasto Anual (€)': [850000, 420000, 65000, 110000]
        }),
        num_rows="dynamic",
        use_container_width=True
    )

    if st.button("EJECUTAR ANÁLISIS ESTRATÉGICO", type="primary"):
        total = data_df['Gasto Anual (€)'].sum()
        processed_data = []
        
        for _, row in data_df.iterrows():
            i, r, c, q = analyze_item(row['Categoría / Proveedor'], row['Gasto Anual (€)'], total)
            processed_data.append({
                'Nombre': row['Categoría / Proveedor'],
                'Gasto': row['Gasto Anual (€)'],
                'Impacto': i,
                'Riesgo': r,
                'Tipo': c,
                'Cuadrante': q
            })
        
        st.session_state['results'] = pd.DataFrame(processed_data)
        st.success(f"Análisis finalizado para {len(processed_data)} elementos.")

with tab2:
    if 'results' in st.session_state:
        df = st.session_state['results']
        
        # Dashboard de KPIs rápidos
        c1, c2, c3 = st.columns(3)
        c1.metric("Gasto Total", f"{df['Gasto'].sum():,.0f} €")
        c2.metric("Categoría Principal", df.loc[df['Gasto'].idxmax(), 'Nombre'])
        c3.metric("Riesgo Promedio", f"{df['Riesgo'].mean():.1f} / 10")

        # Matriz de Kraljic Interactiva con Plotly
        fig = go.Figure()
        
        # Cuadrantes (Zonas de fondo)
        colors = {'Estratégico': '#EF4444', 'Apalancamiento': '#10B981', 'Cuello de Botella': '#F59E0B', 'No Crítico': '#64748B'}
        
        for q_name, color in colors.items():
            dff = df[df['Cuadrante'] == q_name]
            if not dff.empty:
                fig.add_trace(go.Scatter(
                    x=dff['Impacto'], y=dff['Riesgo'],
                    mode='markers+text',
                    name=q_name,
                    text=dff['Nombre'],
                    textposition="top center",
                    marker=dict(size=dff['Gasto']/df['Gasto'].max()*60 + 20, color=color, opacity=0.8, line=dict(width=2, color='white')),
                    hovertemplate="<b>%{text}</b><br>Gasto: %{customdata}€<br>Impacto: %{x}<br>Riesgo: %{y}<extra></extra>",
                    customdata=dff['Gasto']
                ))

        fig.update_layout(
            title="Visualización Estratégica de Kraljic (Burbuja = Volumen de Gasto)",
            xaxis=dict(title="IMPACTO ECONÓMICO", range=[0, 11], tickvals=[2, 4, 6, 8, 10]),
            yaxis=dict(title="RIESGO DE SUMINISTRO", range=[0, 11], tickvals=[2, 4, 6, 8, 10]),
            shapes=[
                dict(type="line", x0=5.5, y0=0, x1=5.5, y1=11, line=dict(color="gray", dash="dash")),
                dict(type="line", x0=0, y0=5.5, x1=11, y1=5.5, line=dict(color="gray", dash="dash"))
            ],
            height=600,
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ Sin datos. Por favor, procesa la información en la pestaña anterior.")

with tab3:
    if 'results' in st.session_state:
        df = st.session_state['results']
        st.subheader("Guía de Negociación según Cuadrante")
        
        for quad in ['Estratégico', 'Apalancamiento', 'Cuello de Botella', 'No Crítico']:
            items = df[df['Cuadrante'] == quad]
            if not items.empty:
                with st.expander(f"📌 {quad.upper()} - ({len(items)} categorías)"):
                    if quad == 'Estratégico':
                        st.error("**ENFOQUE:** Alianzas de largo plazo y desarrollo mutuo.")
                        st.markdown("- **Estrategia:** Contratos colaborativos, compartir riesgos y beneficios, integración de procesos.")
                    elif quad == 'Apalancamiento':
                        st.success("**ENFOQUE:** Maximización del poder de compra.")
                        st.markdown("- **Estrategia:** Licitaciones competitivas, optimización de volúmenes, contratos marco globales.")
                    elif quad == 'Cuello de Botella':
                        st.warning("**ENFOQUE:** Asegurar la continuidad del suministro.")
                        st.markdown("- **Estrategia:** Aumentar stock de seguridad, buscar sustitutos técnicos, contratos con reserva de capacidad.")
                    else:
                        st.info("**ENFOQUE:** Eficiencia administrativa y reducción de transacciones.")
                        st.markdown("- **Estrategia:** Automatización de pedidos (e-procurement), consolidación de proveedores.")
                    
                    st.table(items[['Nombre', 'Gasto', 'Tipo']])
    else:
        st.info("Genera el análisis para visualizar las estrategias recomendadas.")
