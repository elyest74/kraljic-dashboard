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
    </style>
""", unsafe_allow_html=True)

# ── 2. FUNCIONES ESTRATÉGICAS ──
def draw_kraljic_interactive(df, label_col):
    if df.empty: return go.Figure()
    
    fig = go.Figure()

    # REINSTALACIÓN DE CUADRANTES (Fondo coloreado)
    # Cuello de Botella (Amarillo)
    fig.add_shape(type="rect", x0=0, y0=5.5, x1=5.5, y1=11, fillcolor="#FEF3C7", opacity=0.5, line_width=0, layer="below")
    # Estratégico (Rojo)
    fig.add_shape(type="rect", x0=5.5, y0=5.5, x1=11, y1=11, fillcolor="#FEE2E2", opacity=0.5, line_width=0, layer="below")
    # No Crítico (Gris)
    fig.add_shape(type="rect", x0=0, y0=0, x1=5.5, y1=5.5, fillcolor="#F1F5F9", opacity=0.5, line_width=0, layer="below")
    # Apalancamiento (Verde)
    fig.add_shape(type="rect", x0=5.5, y0=0, x1=11, y1=5.5, fillcolor="#D1FAE5", opacity=0.5, line_width=0, layer="below")
    
    max_gasto = df['Gasto'].max() if not df.empty else 1
    
    for i, row in df.iterrows():
        # CAMBIO CLAVE: mode='markers' para evitar etiquetas solapadas
        fig.add_trace(go.Scatter(
            x=[row['Impacto']], 
            y=[row['Riesgo']], 
            mode='markers',
            name=str(row[label_col]),
            marker=dict(
                size=(row['Gasto']/max_gasto)*40 + 20, 
                line=dict(width=1.5, color='white'),
                color='#1E293B'
            ),
            # Personalización de la leyenda flotante (Hover)
            hovertemplate=(
                f"<b>{row[label_col]}</b><br>" +
                f"Gasto: {row['Gasto']:,.2f} €<br>" +
                f"Impacto: {row['Impacto']}<br>" +
                f"Riesgo: {row['Riesgo']}" +
                "<extra></extra>"
            )
        ))

    fig.update_layout(
        xaxis=dict(title="IMPACTO ESTRATÉGICO", range=[-0.5, 11.5], gridcolor='white'),
        yaxis=dict(title="RIESGO DE SUMINISTRO", range=[-0.5, 11.5], gridcolor='white'),
        height=600,
        showlegend=True,
        template="plotly_white"
    )
    return fig

def create_pdf_report(df_n1, df_micro, cat_sel):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Encabezado
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, "CUADRO DE MANDO ESTRATÉGICO", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, f"Analista: Elymar Estévez", ln=True, align='C')
    
    # Tabla Macro
    pdf.set_text_color(0, 0, 0)
    pdf.ln(30)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "1. Resumen de Posicionamiento Macro", ln=True)
    
    pdf.set_font("Arial", 'B', 9)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(90, 8, "Categoría", 1, 0, 'C', True)
    pdf.cell(45, 8, "Gasto (€)", 1, 0, 'C', True)
    pdf.cell(45, 8, "Cuadrante", 1, 1, 'C', True)
    
    pdf.set_font("Arial", '', 8)
    for _, row in df_n1.iterrows():
        pdf.cell(90, 8, str(row['Categoría'])[:50], 1)
        pdf.cell(45, 8, f"{row['Gasto']:,.0f}", 1, 0, 'R')
        pdf.cell(45, 8, str(row['Cuadrante']), 1, 1, 'C')

    # Sección Micro
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"2. Detalle de Subcategorías y Proveedores: {cat_sel}", ln=True)
    
    pdf.set_font("Arial", 'B', 9)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(65, 8, "Subcategoría", 1, 0, 'C', True)
    pdf.cell(75, 8, "Proveedor", 1, 0, 'C', True)
    pdf.cell(40, 8, "Gasto (€)", 1, 1, 'C', True)
    
    pdf.set_font("Arial", '', 8)
    for _, row in df_micro.iterrows():
        sub = str(row['Subcategoría']).encode('latin-1', 'replace').decode('latin-1')
        prov = str(row['Proveedor']).encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(65, 8, sub[:40], 1)
        pdf.cell(75, 8, prov[:45], 1)
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
        st.success("¡Datos sincronizados!")

# ── 6. DASHBOARD ──
elif menu == "📊 Matriz de Kraljic":
    if 'n1' in st.session_state:
        # Fila superior de selectores y descarga
        col_sel, col_btn = st.columns([3, 1])
        
        with col_sel:
            sel_cat = st.selectbox("Seleccione Categoría para desglose Micro:", st.session_state['n2']['Categoría'].unique())
            df_micro_f = st.session_state['n2'][st.session_state['n2']['Categoría'] == sel_cat]
        
        with col_btn:
            try:
                pdf_data = create_pdf_report(st.session_state['n1'], df_micro_f, sel_cat)
                st.download_button(
                    label="📥 Descargar PDF",
                    data=pdf_data,
                    file_name=f"Reporte_{sel_cat}.pdf",
                    mime="application/pdf"
                )
            except:
                st.info("Preparando PDF...")

        # Visualizaciones
        tab_macro, tab_micro = st.tabs(["📊 Análisis Macro (Categorías)", "🔍 Análisis Micro (Proveedores)"])
        
        with tab_macro:
            st.plotly_chart(draw_kraljic_interactive(st.session_state['n1'], 'Categoría'), use_container_width=True)
            st.dataframe(st.session_state['n1'], hide_index=True)

        with tab_micro:
            st.plotly_chart(draw_kraljic_interactive(df_micro_f, 'Subcategoría'), use_container_width=True)
            st.dataframe(df_micro_f, hide_index=True)
    else:
        st.warning("Por favor, sube el archivo Excel en el módulo 'Gestión de Datos'.")
