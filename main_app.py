import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
from datetime import date
import io

# ── CONFIGURACIÓN DE PÁGINA ──────────────────────────────────────────
st.set_page_config(
    page_title="Kraljic AI – Cuadro de Mando de Compras",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── ESTILOS CSS PERSONALIZADOS ───────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background-color: #f8fafc; }
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        border-left: 5px solid #2563eb;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ── DICCIONARIOS Y LÓGICA DE NEGOCIO ────────────────────────────────
LANG = {
    'es': {
        'title': 'Matriz de Kraljic Inteligente',
        'subtitle': 'Análisis Estratégico de Materias Primas y Proveedores',
        'setup': 'Configuración del Análisis',
        'data_tab': '1. Datos y Categorización',
        'matrix_tab': '2. Matriz y Estrategias',
        'sector_lbl': 'Sector Industrial',
        'spend_total': 'Gasto Total Analizado',
        'download_report': 'Descargar Informe',
        'strategic': 'Estratégico',
        'leverage': 'Apalancamiento',
        'bottleneck': 'Cuello de Botella',
        'noncritical': 'No Crítico',
        'provider': 'Proveedor/Categoría',
        'spend': 'Gasto (€)',
        'impact_axis': 'Impacto en el Negocio (Económico)',
        'risk_axis': 'Riesgo de Suministro (Complejidad)',
        'strategy_title': 'Estrategias de Negociación por Cuadrante'
    }
}

RULES = [
    (['acero', 'aluminio', 'cobre', 'litio', 'gas', 'petroleo', 'energia', 'resina'], 9, 8, 'Materia Prima Crítica'),
    (['software', 'it', 'nube', 'licencia'], 7, 7, 'Tecnología'),
    (['logistica', 'transporte', 'flete'], 6, 5, 'Servicios Logísticos'),
    (['papeleria', 'limpieza', 'oficina'], 2, 2, 'Mantenimiento General'),
    (['repuestos', 'mro', 'valvulas', 'motores'], 5, 7, 'Recambios Técnicos'),
]

def calculate_kraljic(df, sector):
    results = []
    total_spend = df['spend'].sum()
    
    for _, row in df.iterrows():
        name = str(row['name']).lower()
        spend = row['spend']
        
        # Scoring base
        impact, risk, cat = 5, 5, 'General'
        for kws, si, sr, sc in RULES:
            if any(k in name for k in kws):
                impact, risk, cat = si, sr, sc
                break
        
        # Ajuste por volumen de gasto (Pareto)
        if total_spend > 0:
            share = spend / total_spend
            if share > 0.15: impact = min(10, impact + 2)
        
        # Determinar Cuadrante
        if impact >= 6 and risk >= 6: q = 'strategic'
        elif impact >= 6 and risk < 6: q = 'leverage'
        elif impact < 6 and risk >= 6: q = 'bottleneck'
        else: q = 'noncritical'
            
        results.append({
            'name': row['name'],
            'spend': spend,
            'impact': impact,
            'risk': risk,
            'category': cat,
            'quadrant': q
        })
    return pd.DataFrame(results)

# ── APP PRINCIPAL ───────────────────────────────────────────────────
def main():
    L = LANG['es']
    
    with st.sidebar:
        st.title("⚙️ " + L['setup'])
        client = st.text_input("Empresa", "Mi Empresa S.L.")
        sector = st.selectbox(L['sector_lbl'], ["Manufactura", "Energía", "Alimentación", "Tecnología"])
        st.divider()
        st.info("Esta herramienta categoriza automáticamente tus proveedores basándose en el nombre y volumen de compra.")

    st.title("⬡ " + L['title'])
    st.caption(L['subtitle'] + " | Cliente: " + client)

    tab1, tab2 = st.tabs([L['data_tab'], L['matrix_tab']])

    with tab1:
        st.subheader("Entrada de Datos")
        col_input, col_info = st.columns([2, 1])
        
        with col_input:
            data_editor = st.data_editor(
                pd.DataFrame({'name': ['Acero Inox', 'Servicios Cloud', 'Limpieza Oficina', 'Logística Marítima'], 
                              'spend': [500000, 120000, 15000, 85000]}),
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "name": st.column_config.TextColumn(L['provider']),
                    "spend": st.column_config.NumberColumn(L['spend'], format="%d €")
                }
            )
        
        with col_info:
            st.markdown("""
            **Instrucciones:**
            1. Introduce el nombre del proveedor o materia prima.
            2. Indica el gasto anual.
            3. La IA asignará el cuadrante en la siguiente pestaña.
            """)
            if st.button("Procesar Análisis", type="primary", use_container_width=True):
                st.session_state['df_results'] = calculate_kraljic(data_editor, sector)
                st.success("Análisis completado.")

    with tab2:
        if 'df_results' not in st.session_state:
            st.warning("Por favor, procesa los datos en la pestaña anterior.")
        else:
            df = st.session_state['df_results']
            
            # KPIs
            c1, c2, c3 = st.columns(3)
            c1.metric(L['spend_total'], f"{df['spend'].sum():,.0f} €")
            c2.metric("Proveedores", len(df))
            c3.metric("Categoría Top", df.loc[df['spend'].idxmax(), 'name'])

            # Plotly Matrix
            fig = go.Figure()
            
            # Dibujar cuadrantes (colores de fondo)
            fig.add_hrect(y0=6, y1=10, x0=0, x1=6, fillcolor="orange", opacity=0.1, annotation_text="C. Botella")
            fig.add_hrect(y0=6, y1=10, x0=6, x1=10, fillcolor="red", opacity=0.1, annotation_text="ESTRATÉGICO")
            fig.add_hrect(y0=0, y1=6, x0=0, x1=6, fillcolor="gray", opacity=0.1, annotation_text="No Crítico")
            fig.add_hrect(y0=0, y1=6, x0=6, x1=10, fillcolor="green", opacity=0.1, annotation_text="APALANCAMIENTO")

            for q in df['quadrant'].unique():
                dff = df[df['quadrant'] == q]
                fig.add_trace(go.Scatter(
                    x=dff['impact'], y=dff['risk'],
                    mode='markers+text',
                    name=L[q],
                    text=dff['name'],
                    textposition="top center",
                    marker=dict(size=dff['spend']/df['spend'].max()*50 + 20, sizemode='area')
                ))

            fig.update_layout(
                title="Distribución en Matriz de Kraljic (Burbuja = Gasto)",
                xaxis_title=L['impact_axis'],
                yaxis_title=L['risk_axis'],
                xaxis=dict(range=[0, 10.5]), yaxis=dict(range=[0, 10.5]),
                height=600
            )
            st.plotly_chart(fig, use_container_width=True)

            # Estrategias Detalladas
            st.header("💡 " + L['strategy_title'])
            
            for q_type in ['strategic', 'leverage', 'bottleneck', 'noncritical']:
                items = df[df['quadrant'] == q_type]
                if not items.empty:
                    with st.expander(f"{L[q_type]} - Proveedores: {', '.join(items['name'].tolist())}"):
                        if q_type == 'strategic':
                            st.error("**Estrategia:** Alianzas a largo plazo, co-diseño y previsión conjunta.")
                        elif q_type == 'leverage':
                            st.success("**Estrategia:** Licitaciones competitivas, optimización de volumen y precios.")
                        elif q_type == 'bottleneck':
                            st.warning("**Estrategia:** Asegurar suministro, buscar sustitutos y aumentar stocks.")
                        else:
                            st.info("**Estrategia:** Simplificación administrativa y automatización de pedidos.")
                        st.table(items[['name', 'spend', 'category']])

            # Botón de descarga
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Reporte Final (CSV)", csv, "kraljic_report.csv", "text/csv")

if __name__ == "__main__":
    main()
