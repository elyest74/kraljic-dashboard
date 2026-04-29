import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import io
import os
from PIL import Image
from fpdf import FPDF

# ── 1. CONFIGURACIÓN E IDENTIDAD VISUAL ──
st.set_page_config(page_title="Sourcing Intelligence | Elymar Estévez", layout="wide", page_icon="📈")

st.markdown("""
    <style>
        .main { background-color: #F8FAFC; }
        .header-banner {
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            padding: 2.5rem; border-radius: 15px; color: white; text-align: center;
            margin-bottom: 2rem; border-bottom: 6px solid #10B981;
        }
        .author-tag {
            background-color: #10B981; color: white; padding: 0.4rem 1.2rem;
            border-radius: 50px; font-weight: bold; font-size: 0.9rem; display: inline-block;
        }
    </style>
""", unsafe_allow_html=True)

# ── 2. LÓGICA DE NEGOCIO ──
def calculate_kraljic(df):
    """Clasificación automática basada en Pareto de gasto"""
    if df.empty: return df
    total_spend = df['Gasto (€)'].sum()
    # Impacto: Alto si es >15% del total, Medio si es >5%, Bajo el resto
    df['Impacto'] = df['Gasto (€)'].apply(lambda x: 9 if x/total_spend > 0.15 else (6 if x/total_spend > 0.05 else 3))
    df['Riesgo'] = 5  # Valor base para visualización
    
    def get_quadrant(i, r):
        if i >= 6 and r >= 6: return 'Estratégico'
        if i >= 6 and r < 6: return 'Apalancamiento'
        if i < 6 and r >= 6: return 'Cuello de Botella'
        return 'No Crítico'
    
    df['Cuadrante'] = df.apply(lambda x: get_quadrant(x['Impacto'], x['Riesgo']), axis=1)
    return df

# ── 3. VISUALIZACIÓN INTERACTIVA ──
def draw_matrix(df, label_col):
    fig = go.Figure()
    # Cuadrantes
    rects = [
        (0, 5.5, 5.5, 11, "#FEF3C7", "Cuello de Botella"),
        (5.5, 5.5, 11, 11, "#FEE2E2", "Estratégico"),
        (0, 0, 5.5, 5.5, "#F1F5F9", "No Crítico"),
        (5.5, 0, 11, 5.5, "#D1FAE5", "Apalancamiento")
    ]
    for x0, y0, x1, y1, color, name in rects:
        fig.add_shape(type="rect", x0=x0, y0=y0, x1=x1, y1=y1, fillcolor=color, opacity=0.4, line_width=0, layer="below")

    colors = px.colors.qualitative.Safe
    max_g = df['Gasto (€)'].max() if not df.empty else 1
    
    for i, (idx, row) in enumerate(df.iterrows()):
        fig.add_trace(go.Scatter(
            x=[row['Impacto']], y=[row['Riesgo']],
            mode='markers',
            name=str(row[label_col]),
            marker=dict(
                size=(row['Gasto (€)']/max_g)*50 + 15,
                color=colors[i % len(colors)],
                line=dict(width=1, color='white')
            ),
            hovertemplate=f"<b>{row[label_col]}</b><br>Gasto: {row['Gasto (€)']:,.2f} EUR<extra></extra>"
        ))
    
    fig.update_layout(xaxis=dict(title="IMPACTO", range=[-0.5, 11.5]), yaxis=dict(title="RIESGO", range=[-0.5, 11.5]), 
                      template="plotly_white", height=550)
    return fig

# ── 4. REPORTE PDF (SOLUCIÓN AL ERROR UNICODE) ──
def generate_pdf_report(df_macro, df_micro, cat):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 210, 35, 'F')
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, "INFORME DE COMPRAS ESTRATEGICAS", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 10, f"Analisis: {cat} | Consultor: Elymar Estevez", ln=True, align='C')
    
    pdf.set_text_color(0, 0, 0)
    pdf.ln(25)
    pdf.set_font("Arial", 'B', 11)
    
    # Tabla: Sustituimos el símbolo de Euro por "EUR" para evitar el crash
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(75, 10, "Subcategoria", 1, 0, 'C', True)
    pdf.cell(75, 10, "Proveedor", 1, 0, 'C', True)
    pdf.cell(40, 10, "Gasto (EUR)", 1, 1, 'C', True)
    
    pdf.set_font("Arial", '', 9)
    for _, row in df_micro.iterrows():
        # Limpieza de texto para asegurar compatibilidad con Arial estándar
        sub = str(row['Subcategoría']).encode('latin-1', 'replace').decode('latin-1')
        prov = str(row['Proveedor']).encode('latin-1', 'replace').decode('latin-1')
        
        pdf.cell(75, 9, sub[:40], 1)
        pdf.cell(75, 9, prov[:40], 1)
        pdf.cell(40, 9, f"{row['Gasto (€)']:,.0f}", 1, 1, 'R')
        
    return bytes(pdf.output())

# ── 5. ESTRUCTURA PRINCIPAL ──
with st.sidebar:
    if os.path.exists("elymar.png"):
        st.image("elymar.png", use_container_width=True)
    st.markdown("<h3 style='text-align: center;'>Elymar Estévez</h3>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("Secciones:", ["Carga de Datos", "Cuadro de Mando"])

st.markdown('<div class="header-banner"><h1>Sourcing Intelligence Dashboard</h1><div class="author-tag">Strategic Procurement Support</div></div>', unsafe_allow_html=True)

if menu == "Carga de Datos":
    file = st.file_uploader("Subir base de datos (Excel)", type=["xlsx"])
    if file:
        df = pd.read_excel(file)
        if all(c in df.columns for c in ['Categoría', 'Subcategoría', 'Proveedor', 'Gasto (€)']):
            st.session_state['main_df'] = df
            st.success("¡Datos cargados correctamente!")
            st.dataframe(df.head())
        else:
            st.error("Error: Columnas faltantes.")

elif menu == "Cuadro de Mando":
    if 'main_df' in st.session_state:
        df = st.session_state['main_df']
        
        # Procesamiento
        df_macro = df.groupby('Categoría').agg({'Gasto (€)': 'sum'}).reset_index()
        df_macro = calculate_kraljic(df_macro)
        
        st.subheader("Análisis Global (Macro)")
        st.plotly_chart(draw_matrix(df_macro, 'Categoría'), use_container_width=True)
        
        st.divider()
        sel_cat = st.selectbox("Seleccione categoría para nivel Micro:", df_macro['Categoría'].unique())
        
        df_micro = df[df['Categoría'] == sel_cat].groupby(['Subcategoría', 'Proveedor']).agg({'Gasto (€)': 'sum'}).reset_index()
        df_micro = calculate_kraljic(df_micro)
        
        st.subheader(f"Análisis Detallado: {sel_cat}")
        st.plotly_chart(draw_matrix(df_micro, 'Subcategoría'), use_container_width=True)
        
        # Generar PDF seguro
        try:
            pdf_bytes = generate_pdf_report(df_macro, df_micro, sel_cat)
            st.download_button("📥 Descargar Reporte PDF", data=pdf_bytes, file_name=f"Reporte_{sel_cat}.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"Error al generar PDF: {e}")
            st.info("Sugerencia: Revisa que los nombres de proveedores no tengan caracteres extremadamente inusuales.")
    else:
        st.info("Por favor, sube un archivo Excel en la sección de 'Carga de Datos'.")
