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

# CSS Avanzado para mejorar la UI
st.markdown("""
    <style>
        .main { background-color: #F8FAFC; }
        .header-banner {
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            padding: 3rem; border-radius: 15px; color: white; text-align: center;
            margin-bottom: 2rem; border-bottom: 6px solid #10B981;
        }
        .author-tag {
            background-color: #10B981; color: white; padding: 0.4rem 1.2rem;
            border-radius: 50px; font-weight: bold; font-size: 0.9rem; display: inline-block;
        }
        .stMetric { background-color: white; padding: 1rem; border-radius: 10px; border: 1px solid #E2E8F0; }
    </style>
""", unsafe_allow_html=True)

# ── 2. LÓGICA DE NEGOCIO (MATRIZ DE KRALJIC) ──
def calculate_kraljic_logic(df):
    """Calcula dimensiones de impacto y riesgo basadas en el gasto y parámetros de Sourcing."""
    total_spend = df['Gasto (€)'].sum()
    
    # Impacto en Resultados (Eje X): Basado en Pareto de gasto
    # Riesgo de Suministro (Eje Y): Por defecto 5 (ajustable en versiones futuras)
    df['Impacto'] = df['Gasto (€)'].apply(lambda x: 9 if x/total_spend > 0.15 else (6 if x/total_spend > 0.05 else 3))
    df['Riesgo'] = 5  
    
    def get_quadrant(i, r):
        if i >= 6 and r >= 6: return 'Estratégico'
        if i >= 6 and r < 6: return 'Apalancamiento'
        if i < 6 and r >= 6: return 'Cuello de Botella'
        return 'No Crítico'
    
    df['Cuadrante'] = df.apply(lambda x: get_quadrant(x['Impacto'], x['Riesgo']), axis=1)
    return df

# ── 3. MOTOR DE VISUALIZACIÓN (PLOTLY) ──
def draw_kraljic_matrix(df, label_col):
    fig = go.Figure()

    # Dibujar áreas de la matriz (Cuadrantes)
    areas = [
        dict(x0=0, y0=5.5, x1=5.5, y1=11, color="#FEF3C7", name="Cuello de Botella"),
        dict(x0=5.5, y0=5.5, x1=11, y1=11, color="#FEE2E2", name="Estratégico"),
        dict(x0=0, y0=0, x1=5.5, y1=5.5, color="#F1F5F9", name="No Crítico"),
        dict(x0=5.5, y0=0, x1=11, y1=5.5, color="#D1FAE5", name="Apalancamiento")
    ]
    
    for area in areas:
        fig.add_shape(type="rect", x0=area['x0'], y0=area['y0'], x1=area['x1'], y1=area['y1'],
                      fillcolor=area['color'], opacity=0.4, line_width=0, layer="below")

    # Burbujas dinámicas
    max_bubble = df['Gasto (€)'].max() if not df.empty else 1
    colors = px.colors.qualitative.Prism

    for i, (_, row) in enumerate(df.iterrows()):
        fig.add_trace(go.Scatter(
            x=[row['Impacto']], y=[row['Riesgo']],
            mode='markers',
            name=str(row[label_col]),
            marker=dict(
                size=(row['Gasto (€)']/max_bubble)*50 + 15,
                color=colors[i % len(colors)],
                line=dict(width=2, color='white'),
                opacity=0.85
            ),
            hovertemplate=f"<b>{row[label_col]}</b><br>Gasto: {row['Gasto (€)']:,.2f} €<br>Cuadrante: {row['Cuadrante']}<extra></extra>"
        ))

    fig.update_layout(
        xaxis=dict(title="IMPACTO (Económico)", range=[-0.5, 11.5], gridcolor='white'),
        yaxis=dict(title="RIESGO (Suministro)", range=[-0.5, 11.5], gridcolor='white'),
        height=600, template="plotly_white", margin=dict(t=50, b=50, l=50, r=50)
    )
    return fig

# ── 4. GENERADOR DE REPORTES (FPDF2) ──
def generate_pdf(df_macro, df_micro, selected_cat):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Estilo de página
    pdf.add_page()
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 210, 45, 'F')
    
    pdf.set_font("Arial", 'B', 18)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, "SOURCING INTELLIGENCE REPORT", ln=True, align='C')
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 5, f"Analista: Elymar Estévez | Categoría: {selected_cat}", ln=True, align='C')
    
    # Tabla de datos
    pdf.set_text_color(0, 0, 0)
    pdf.ln(35)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"Detalle de Subcategorías y Proveedores", ln=True)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(70, 10, "Subcategoría", 1, 0, 'C', True)
    pdf.cell(70, 10, "Proveedor", 1, 0, 'C', True)
    pdf.cell(40, 10, "Gasto (€)", 1, 1, 'C', True)
    
    pdf.set_font("Arial", '', 9)
    for _, row in df_micro.iterrows():
        pdf.cell(70, 10, str(row['Subcategoría'])[:35], 1)
        pdf.cell(70, 10, str(row['Proveedor'])[:35], 1)
        pdf.cell(40, 10, f"{row['Gasto (€)']:,.0f}", 1, 1, 'R')
        
    return bytes(pdf.output())

# ── 5. ESTRUCTURA DE LA APP (BARRA LATERAL Y NAVEGACIÓN) ──
with st.sidebar:
    if os.path.exists("elymar.png"):
        st.image("elymar.png", use_container_width=True)
    st.markdown("<h3 style='text-align: center;'>Elymar Estévez</h3>", unsafe_allow_html=True)
    st.divider()
    app_mode = st.radio("Módulos del Sistema:", ["📂 Carga de Datos", "📊 Matriz de Kraljic", "📋 Reportes Detallados"])

# ── 6. MÓDULOS ──
if app_mode == "📂 Carga de Datos":
    st.header("Gestión de Datos de Compras")
    uploaded_file = st.file_uploader("Subir archivo Excel de Sourcing", type=["xlsx"])
    
    if uploaded_file:
        df_raw = pd.read_excel(uploaded_file)
        # Validación de columnas
        required_cols = ['Categoría', 'Subcategoría', 'Proveedor', 'Gasto (€)']
        if all(col in df_raw.columns for col in required_cols):
            st.session_state['data'] = df_raw
            st.success("Base de datos cargada y validada con éxito.")
            st.dataframe(df_raw.head(10), use_container_width=True)
        else:
            st.error(f"El archivo debe contener las columnas: {', '.join(required_cols)}")

elif app_mode == "📊 Matriz de Kraljic":
    if 'data' not in st.session_state:
        st.warning("Por favor, carga datos en el módulo correspondiente.")
    else:
        df = st.session_state['data']
        
        # Procesamiento Macro
        df_macro = df.groupby('Categoría').agg({'Gasto (€)': 'sum'}).reset_index()
        df_macro = calculate_kraljic_logic(df_macro)
        
        st.markdown('<div class="header-banner"><h1>Matriz de Kraljic Macro</h1><div class="author-tag">Análisis por Categoría</div></div>', unsafe_allow_html=True)
        
        # KPIs rápidos
        c1, c2, c3 = st.columns(3)
        c1.metric("Gasto Total", f"{df['Gasto (€)'].sum():,.0f} €")
        c2.metric("Categorías", len(df_macro))
        c3.metric("Proveedores", df['Proveedor'].nunique())
        
        # Gráfico Macro
        st.plotly_chart(draw_kraljic_matrix(df_macro, 'Categoría'), use_container_width=True)
        
        # Selección para análisis Micro
        st.divider()
        selected_cat = st.selectbox("Profundizar en Categoría:", df_macro['Categoría'].unique())
        
        df_micro = df[df['Categoría'] == selected_cat].groupby(['Subcategoría', 'Proveedor']).agg({'Gasto (€)': 'sum'}).reset_index()
        df_micro = calculate_kraljic_logic(df_micro)
        
        st.subheader(f"Análisis Micro: {selected_cat}")
        st.plotly_chart(draw_kraljic_matrix(df_micro, 'Subcategoría'), use_container_width=True)

        # Botón de Reporte
        pdf_data = generate_pdf(df_macro, df_micro, selected_cat)
        st.download_button(label="📥 Descargar Reporte Estratégico", data=pdf_data, file_name=f"Reporte_{selected_cat}.pdf", mime="application/pdf")

elif app_mode == "📋 Reportes Detallados":
    if 'data' in st.session_state:
        st.subheader("Explorador de Datos Estratégicos")
        st.dataframe(st.session_state['data'], use_container_width=True)
    else:
        st.info("No hay datos para mostrar.")
