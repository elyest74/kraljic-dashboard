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

# ── 2. LÓGICA DE NEGOCIO (KRALJIC) ──
def calculate_kraljic(df):
    if df.empty: return df
    total_spend = df['Gasto (€)'].sum()
    # Impacto en resultados (Eje X) y Riesgo (Eje Y)
    df['Impacto'] = df['Gasto (€)'].apply(lambda x: 9 if x/total_spend > 0.15 else (6 if x/total_spend > 0.05 else 3))
    df['Riesgo'] = 5  # Valor base para la matriz
    
    def get_quadrant(i, r):
        if i >= 6 and r >= 6: return 'Estratégico'
        if i >= 6 and r < 6: return 'Apalancamiento'
        if i < 6 and r >= 6: return 'Cuello de Botella'
        return 'No Crítico'
    
    df['Cuadrante'] = df.apply(lambda x: get_quadrant(x['Impacto'], x['Riesgo']), axis=1)
    return df

# ── 3. MOTOR DE GRÁFICOS (RESTAURACIÓN DE CUADRANTES) ──
def draw_matrix(df, label_col):
    fig = go.Figure()
    
    # Dibujar los 4 cuadrantes con sus colores estándar de Sourcing
    fig.add_shape(type="rect", x0=0, y0=5.5, x1=5.5, y1=11, fillcolor="#FEF3C7", opacity=0.4, line_width=0, layer="below") # Cuello Botella
    fig.add_shape(type="rect", x0=5.5, y0=5.5, x1=11, y1=11, fillcolor="#FEE2E2", opacity=0.4, line_width=0, layer="below") # Estratégico
    fig.add_shape(type="rect", x0=0, y0=0, x1=5.5, y1=5.5, fillcolor="#F1F5F9", opacity=0.4, line_width=0, layer="below") # No Crítico
    fig.add_shape(type="rect", x0=5.5, y0=0, x1=11, y1=5.5, fillcolor="#D1FAE5", opacity=0.4, line_width=0, layer="below") # Apalancamiento

    colors = px.colors.qualitative.Prism
    max_g = df['Gasto (€)'].max() if not df.empty else 1
    
    for i, (_, row) in enumerate(df.iterrows()):
        fig.add_trace(go.Scatter(
            x=[row['Impacto']], y=[row['Riesgo']],
            mode='markers',
            name=str(row[label_col]),
            marker=dict(
                size=(row['Gasto (€)']/max_g)*55 + 15,
                color=colors[i % len(colors)],
                line=dict(width=1.5, color='white')
            ),
            hovertemplate=f"<b>{row[label_col]}</b><br>Gasto: {row['Gasto (€)']:,.2f} EUR<br>Cuadrante: {row['Cuadrante']}<extra></extra>"
        ))
    
    fig.update_layout(
        xaxis=dict(title="IMPACTO ESTRATÉGICO", range=[-0.5, 11.5]),
        yaxis=dict(title="RIESGO DE SUMINISTRO", range=[-0.5, 11.5]),
        template="plotly_white", height=600, showlegend=True
    )
    return fig

# ── 4. GENERADOR DE PDF (PROTEGIDO CONTRA ERRORES) ──
def generate_safe_pdf(df_micro, category_name):
    pdf = FPDF()
    pdf.add_page()
    
    # Header Corporativo
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, "INFORME ESTRATEGICO DE COMPRAS", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 10, f"Analisis de Categoria: {category_name} | Por: Elymar Estevez", ln=True, align='C')
    
    pdf.set_text_color(0, 0, 0)
    pdf.ln(25)
    
    # Encabezados de tabla
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(70, 10, "Subcategoria", 1, 0, 'C', True)
    pdf.cell(75, 10, "Proveedor", 1, 0, 'C', True)
    pdf.cell(40, 10, "Gasto (EUR)", 1, 1, 'C', True)
    
    # Contenido de la tabla con limpieza de caracteres
    pdf.set_font("Arial", '', 9)
    for _, row in df_micro.iterrows():
        # Limpieza Unicode para evitar FPDFUnicodeEncodingException
        sub = str(row['Subcategoría']).encode('latin-1', 'replace').decode('latin-1')
        prov = str(row['Proveedor']).encode('latin-1', 'replace').decode('latin-1')
        
        pdf.cell(70, 9, sub[:38], 1)
        pdf.cell(75, 9, prov[:42], 1)
        pdf.cell(40, 9, f"{row['Gasto (€)']:,.0f}", 1, 1, 'R')
        
    return bytes(pdf.output())

# ── 5. ESTRUCTURA DE NAVEGACIÓN ──
with st.sidebar:
    if os.path.exists("elymar.png"):
        st.image("elymar.png", use_container_width=True)
    st.markdown("<h3 style='text-align: center;'>Elymar Estévez</h3>", unsafe_allow_html=True)
    st.divider()
    app_mode = st.radio("Módulos:", ["📂 Carga de Datos", "📊 Cuadro de Mando"])

# Banner Principal
st.markdown('<div class="header-banner"><h1>Sourcing Intelligence Dashboard</h1><div class="author-tag">Decisión Estratégica en Materias Primas</div></div>', unsafe_allow_html=True)

if app_mode == "📂 Carga de Datos":
    st.header("Gestión de Base de Datos")
    file = st.file_uploader("Subir Excel de Compras", type=["xlsx"])
    if file:
        df = pd.read_excel(file)
        # Validación de columnas mínima
        if all(c in df.columns for c in ['Categoría', 'Subcategoría', 'Proveedor', 'Gasto (€)']):
            st.session_state['data'] = df
            st.success("¡Datos cargados y validados correctamente!")
            st.dataframe(df.head(10), use_container_width=True)
        else:
            st.error("El archivo no tiene el formato correcto (Faltan columnas clave).")

elif app_mode == "📊 Cuadro de Mando":
    if 'data' not in st.session_state:
        st.info("💡 Por favor, ve al módulo de 'Carga de Datos' para empezar.")
    else:
        df = st.session_state['data']
        
        # Procesamiento Macro
        df_macro = df.groupby('Categoría').agg({'Gasto (€)': 'sum'}).reset_index()
        df_macro = calculate_kraljic(df_macro)
        
        # Visualización Macro
        st.subheader("🌐 Visión Global de Categorías (Macro)")
        st.plotly_chart(draw_matrix(df_macro, 'Categoría'), use_container_width=True)
        
        st.divider()
        
        # Selección Micro
        selected_cat = st.selectbox("Profundizar en una Categoría:", df_macro['Categoría'].unique())
        df_micro = df[df['Categoría'] == selected_cat].groupby(['Subcategoría', 'Proveedor']).agg({'Gasto (€)': 'sum'}).reset_index()
        df_micro = calculate_kraljic(df_micro)
        
        st.subheader(f"🔍 Detalle Táctico: {selected_cat}")
        
        # Columnas para Gráfico Micro y Botón PDF
        col_graph, col_pdf = st.columns([4, 1])
        
        with col_graph:
            st.plotly_chart(draw_matrix(df_micro, 'Subcategoría'), use_container_width=True)
        
        with col_pdf:
            st.markdown("### Reporte")
            try:
                pdf_bytes = generate_safe_pdf(df_micro, selected_cat)
                st.download_button(
                    label="📥 Descargar PDF",
                    data=pdf_bytes,
                    file_name=f"Reporte_{selected_cat.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error("Error al preparar el PDF.")
        
        st.dataframe(df_micro.sort_values('Gasto (€)', ascending=False), hide_index=True)
