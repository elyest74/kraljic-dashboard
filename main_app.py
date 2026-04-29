import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
import os
from PIL import Image
from fpdf import FPDF

# ── 1. CONFIGURACIÓN Y ESTILOS ──
st.set_page_config(page_title="Sourcing Intelligence | Elymar Estévez", layout="wide", page_icon="📈")

st.markdown("""
    <style>
        .header-banner {
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            padding: 40px; border-radius: 15px; color: white; text-align: center;
            margin-bottom: 30px; border-bottom: 6px solid #10B981;
        }
        .author-tag {
            background-color: #10B981; color: white; padding: 5px 15px;
            border-radius: 50px; font-weight: bold; font-size: 0.9rem;
        }
        .strategy-container { margin-bottom: 15px; padding: 15px; border-radius: 8px; border-left: 8px solid; }
        .est-estrategico { background-color: #FEE2E2; border-color: #EF4444; color: #991B1B; }
        .est-apalancamiento { background-color: #D1FAE5; border-color: #10B981; color: #065F46; }
        .est-cuello { background-color: #FEF3C7; border-color: #F59E0B; color: #92400E; }
        .est-nocritico { background-color: #F1F5F9; border-color: #64748B; color: #1E293B; }
    </style>
""", unsafe_allow_html=True)

# ── 2. FUNCIONES ESTRATÉGICAS ──
def get_strategy_text(cuadrante):
    data = {
        'Estratégico': "Alianzas a largo plazo, co-diseño y SRM estrecho.",
        'Apalancamiento': "Licitaciones competitivas y optimización de precios.",
        'Cuello de Botella': "Asegurar volumen y reducir dependencia.",
        'No Crítico': "Automatización de compras y catálogos e-procurement."
    }
    return data.get(cuadrante, "")

def draw_kraljic_interactive(df, label_col):
    if df.empty: return go.Figure()
    fig = go.Figure()
    # Dibujo de cuadrantes
    fig.add_shape(type="rect", x0=0, y0=5.5, x1=5.5, y1=11, fillcolor="#FEF3C7", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=5.5, y0=5.5, x1=11, y1=11, fillcolor="#FEE2E2", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=0, y0=0, x1=5.5, y1=5.5, fillcolor="#F1F5F9", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=5.5, y0=0, x1=11, y1=5.5, fillcolor="#D1FAE5", line_width=0, layer="below")
    
    max_gasto = df['Gasto'].max() if not df.empty else 1
    for i, row in df.iterrows():
        fig.add_trace(go.Scatter(
            x=[row['Impacto']], y=[row['Riesgo']], mode='markers+text',
            name=str(row[label_col]),
            text=[str(row[label_col]) if len(df) < 12 else ""],
            textposition="top center",
            marker=dict(size=(row['Gasto']/max_gasto)*40 + 20, line=dict(width=1.5, color='white')),
            hovertemplate=f"<b>{row[label_col]}</b><br>Gasto: {row['Gasto']:,.2f} €<extra></extra>"
        ))
    fig.update_layout(xaxis=dict(title="IMPACTO (0-11)"), yaxis=dict(title="RIESGO (0-11)"), height=500, template="plotly_white")
    return fig

def create_pdf_report(df_n1, df_micro, cat_sel):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Portada
    pdf.add_page()
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 210, 45, 'F')
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 20, "INFORME ESTRATÉGICO DE COMPRAS", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Consultor: Elymar Estévez", ln=True, align='C')
    
    # Sección 1: Macro
    pdf.set_text_color(0, 0, 0)
    pdf.ln(25)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "1. Matriz de Posicionamiento Global (Macro)", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(80, 8, "Categoría", 1, 0, 'C', True)
    pdf.cell(50, 8, "Gasto (EUR)", 1, 0, 'C', True)
    pdf.cell(50, 8, "Segmentación", 1, 1, 'C', True)
    
    pdf.set_font("Arial", '', 9)
    for _, row in df_n1.sort_values('Gasto', ascending=False).iterrows():
        pdf.cell(80, 8, str(row['Categoría'])[:45], 1)
        pdf.cell(50, 8, f"{row['Gasto']:,.0f}", 1, 0, 'R')
        pdf.cell(50, 8, str(row['Cuadrante']), 1, 1, 'C')

    # Sección 2: Micro
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"2. Análisis Detallado: {cat_sel}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(70, 8, "Subcategoría", 1, 0, 'C', True)
    pdf.cell(70, 8, "Proveedor Principal", 1, 0, 'C', True)
    pdf.cell(40, 8, "Gasto (EUR)", 1, 1, 'C', True)
    
    pdf.set_font("Arial", '', 9)
    for _, row in df_micro.iterrows():
        sub = str(row['Subcategoría']).encode('latin-1', 'replace').decode('latin-1')
        prov = str(row['Proveedor']).encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(70, 8, sub[:35], 1)
        pdf.cell(70, 8, prov[:35], 1)
        pdf.cell(40, 8, f"{row['Gasto']:,.0f}", 1, 1, 'R')
    
    return bytes(pdf.output())

# ── 3. BARRA LATERAL ──
with st.sidebar:
    if os.path.exists("elymar.png"):
        st.image(Image.open("elymar.png"), use_container_width=True)
    st.markdown("<div style='text-align: center; font-weight: bold;'>Elymar Estévez</div>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("Módulos:", ["📂 Gestión de Datos", "📊 Matriz de Kraljic"], index=1)

# ── 4. CABECERA ──
st.markdown("""
    <div class="header-banner">
        <h1>Sourcing Intelligence</h1>
        <div class="author-tag">Elymar Estévez</div>
    </div>
""", unsafe_allow_html=True)

# ── 5. LÓGICA DE DATOS ──
if menu == "📂 Gestión de Datos":
    archivo = st.file_uploader("Subir Excel", type=['xlsx'])
    if archivo:
        df = pd.read_excel(archivo)
        df['Gasto (€)'] = pd.to_numeric(df['Gasto (€)'], errors='coerce').fillna(0)
        total = df['Gasto (€)'].sum()
        
        def asignar_q(i, r):
            if i >= 6 and r >= 6: return 'Estratégico'
            elif i >= 6: return 'Apalancamiento'
            elif r >= 6: return 'Cuello de Botella'
            return 'No Crítico'

        n1 = df.groupby('Categoría').agg({'Gasto (€)': 'sum'}).reset_index()
        n1['Impacto'] = n1['Gasto (€)'].apply(lambda x: 9 if x/total > 0.15 else (6 if x/total > 0.05 else 3))
        n1['Riesgo'] = 5 
        n1['Cuadrante'] = n1.apply(lambda x: asignar_q(x['Impacto'], x['Riesgo']), axis=1)
        st.session_state['n1'] = n1.rename(columns={'Gasto (€)': 'Gasto'})

        n2 = df.groupby(['Categoría', 'Subcategoría']).agg({'Gasto (€)': 'sum', 'Proveedor': 'first'}).reset_index()
        n2['Impacto'] = n2['Gasto (€)'].apply(lambda x: 9 if x/total > 0.05 else (6 if x/total > 0.01 else 3))
        n2['Riesgo'] = 5
        n2['Cuadrante'] = n2.apply(lambda x: asignar_q(x['Impacto'], x['Riesgo']), axis=1)
        st.session_state['n2'] = n2.rename(columns={'Gasto (€)': 'Gasto'})
        st.success("¡Datos cargados!")

# ── 6. DASHBOARD ──
elif menu == "📊 Matriz de Kraljic":
    if 'n1' in st.session_state:
        # Selector de Categoría (Crucial para el análisis Micro)
        sel_cat = st.selectbox("Seleccione Categoría para reporte:", st.session_state['n2']['Categoría'].unique())
        df_micro_f = st.session_state['n2'][st.session_state['n2']['Categoría'] == sel_cat]
        
        fig_macro = draw_kraljic_interactive(st.session_state['n1'], 'Categoría')
        fig_micro = draw_kraljic_interactive(df_micro_f, 'Subcategoría')

        # Botón PDF Seguro
        try:
            pdf_data = create_pdf_report(st.session_state['n1'], df_micro_f, sel_cat)
            st.download_button(
                label=f"📥 Informe PDF: {sel_cat}",
                data=pdf_data,
                file_name=f"Informe_{sel_cat}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error en reporte: {e}")

        tab1, tab2 = st.tabs(["📊 Visión Macro", "🔍 Análisis Micro"])
        with tab1:
            st.plotly_chart(fig_macro, use_container_width=True)
            st.dataframe(st.session_state['n1'], hide_index=True)
        with tab2:
            st.plotly_chart(fig_micro, use_container_width=True)
            st.dataframe(df_micro_f, hide_index=True)
    else:
        st.warning("Suba datos primero.")
