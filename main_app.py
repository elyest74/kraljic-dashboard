import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
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

    # 1. CUADRANTES DE FONDO (Matriz de Kraljic)
    fig.add_shape(type="rect", x0=0, y0=5.5, x1=5.5, y1=11, fillcolor="#FEF3C7", opacity=0.5, line_width=0, layer="below") # Cuello de Botella
    fig.add_shape(type="rect", x0=5.5, y0=5.5, x1=11, y1=11, fillcolor="#FEE2E2", opacity=0.5, line_width=0, layer="below") # Estratégico
    fig.add_shape(type="rect", x0=0, y0=0, x1=5.5, y1=5.5, fillcolor="#F1F5F9", opacity=0.5, line_width=0, layer="below") # No Crítico
    fig.add_shape(type="rect", x0=5.5, y0=0, x1=11, y1=5.5, fillcolor="#D1FAE5", opacity=0.5, line_width=0, layer="below") # Apalancamiento
    
    max_gasto = df['Gasto'].max() if not df.empty else 1
    
    # 2. GENERACIÓN DE COLORES DINÁMICOS
    # Usamos una paleta cualitativa para que cada punto tenga un color diferente
    colors = px.colors.qualitative.Bold 

    for i, (idx, row) in enumerate(df.iterrows()):
        color_index = i % len(colors) # Ciclar colores si hay más puntos que colores en la paleta
        
        fig.add_trace(go.Scatter(
            x=[row['Impacto']], 
            y=[row['Riesgo']], 
            mode='markers', # Solo marcadores, sin etiquetas de texto solapadas
            name=str(row[label_col]),
            marker=dict(
                size=(row['Gasto']/max_gasto)*45 + 15, 
                line=dict(width=1.5, color='white'),
                color=colors[color_index], # Color dinámico por punto
                opacity=0.9,
                shadow=dict(color="black", dx=2, dy=2) # Efecto de profundidad
            ),
            hovertemplate=(
                f"<b>{row[label_col]}</b><br>" +
                f"Gasto: {row['Gasto']:,.2f} €<br>" +
                f"Impacto (X): {row['Impacto']}<br>" +
                f"Riesgo (Y): {row['Riesgo']}" +
                "<extra></extra>"
            )
        ))

    fig.update_layout(
        xaxis=dict(title="IMPACTO EN RESULTADOS (0-11)", range=[-0.5, 11.5], gridcolor='#E2E8F0', zeroline=False),
        yaxis=dict(title="RIESGO DE SUMINISTRO (0-11)", range=[-0.5, 11.5], gridcolor='#E2E8F0', zeroline=False),
        height=650,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_white",
        margin=dict(l=20, r=20, t=100, b=20)
    )
    return fig

def create_pdf_report(df_n1, df_micro, cat_sel):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Header Estilizado
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, "REPORTE ESTRATÉGICO DE COMPRAS", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, "Sourcing Intelligence | Dashboard Elymar Estévez", ln=True, align='C')
    
    # Tabla Macro
    pdf.set_text_color(0, 0, 0)
    pdf.ln(30)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "1. Análisis Macro por Categoría", ln=True)
    
    pdf.set_font("Arial", 'B', 9)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(90, 8, "Categoría", 1, 0, 'C', True)
    pdf.cell(45, 8, "Gasto Total (€)", 1, 0, 'C', True)
    pdf.cell(45, 8, "Cuadrante", 1, 1, 'C', True)
    
    pdf.set_font("Arial", '', 8)
    for _, row in df_n1.sort_values('Gasto', ascending=False).iterrows():
        pdf.cell(90, 8, str(row['Categoría'])[:50], 1)
        pdf.cell(45, 8, f"{row['Gasto']:,.0f}", 1, 0, 'R')
        pdf.cell(45, 8, str(row['Cuadrante']), 1, 1, 'C')

    # Sección Micro
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"2. Análisis Detallado: {cat_sel}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 9)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(65, 8, "Subcategoría", 1, 0, 'C', True)
    pdf.cell(75, 8, "Proveedor de Referencia", 1, 0, 'C', True)
    pdf.cell(40, 8, "Gasto (€)", 1, 1, 'C', True)
    
    pdf.set_font("Arial", '', 8)
    for _, row in df_micro.sort_values('Gasto', ascending=False).iterrows():
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
    st.markdown("<div style='text-align: center; font-weight: bold; font-size: 1.1rem;'>Elymar Estévez</div>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("Navegación:", ["📂 Gestión de Datos", "📊 Matriz de Kraljic"], index=1)

# ── 4. CABECERA ──
st.markdown("""
    <div class="header-banner">
        <h1>Sourcing Intelligence</h1>
        <div class="author-tag">Business Decision Support</div>
    </div>
""", unsafe_allow_html=True)

# ── 5. LÓGICA DE DATOS ──
if menu == "📂 Gestión de Datos":
    archivo = st.file_uploader("Cargar Base de Datos de Compras (Excel)", type=['xlsx'])
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
        st.success("¡Base de datos procesada y lista para análisis!")

# ── 6. DASHBOARD INTERACTIVO ──
elif menu == "📊 Matriz de Kraljic":
    if 'n1' in st.session_state:
        col_sel, col_btn = st.columns([3, 1])
        
        with col_sel:
            sel_cat = st.selectbox("Filtrar por Categoría:", st.session_state['n2']['Categoría'].unique())
            df_micro_f = st.session_state['n2'][st.session_state['n2']['Categoría'] == sel_cat]
        
        with col_btn:
            try:
                pdf_data = create_pdf_report(st.session_state['n1'], df_micro_f, sel_cat)
                st.download_button(
                    label="📥 Exportar Reporte PDF",
                    data=pdf_data,
                    file_name=f"Analisis_Kraljic_{sel_cat}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except:
                st.info("Generando reporte...")

        tab_macro, tab_micro = st.tabs(["🌎 Matriz Macro (Categorías)", "🔍 Detalle Micro (Proveedores)"])
        
        with tab_macro:
            st.plotly_chart(draw_kraljic_interactive(st.session_state['n1'], 'Categoría'), use_container_width=True)
            st.dataframe(st.session_state['n1'].sort_values('Gasto', ascending=False), hide_index=True)

        with tab_micro:
            st.plotly_chart(draw_kraljic_interactive(df_micro_f, 'Subcategoría'), use_container_width=True)
            st.dataframe(df_micro_f.sort_values('Gasto', ascending=False), hide_index=True)
    else:
        st.info("💡 Pendiente: Carga un archivo Excel en el módulo 'Gestión de Datos' para iniciar el análisis.")
