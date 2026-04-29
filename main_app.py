import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
import os
from PIL import Image
from fpdf import FPDF

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Sourcing Intelligence | Elymar Estévez", layout="wide")

# --- 2. MOTOR DE RENDERIZADO DE GRÁFICOS ---
def draw_kraljic(df, label_col):
    fig = go.Figure()
    # Cuadrantes
    fig.add_shape(type="rect", x0=0, y0=5.5, x1=5.5, y1=11, fillcolor="#FEF3C7", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=5.5, y0=5.5, x1=11, y1=11, fillcolor="#FEE2E2", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=0, y0=0, x1=5.5, y1=5.5, fillcolor="#F1F5F9", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=5.5, y0=0, x1=11, y1=5.5, fillcolor="#D1FAE5", line_width=0, layer="below")

    # Burbujas: Ajuste de escala para asegurar visibilidad
    max_gasto = df['Gasto'].max() if not df.empty else 1
    
    for i, row in df.iterrows():
        fig.add_trace(go.Scatter(
            x=[row['Impacto']], y=[row['Riesgo']],
            mode='markers+text',
            name=str(row[label_col]),
            text=[str(row[label_col]) if df.shape[0] < 10 else ""], # Texto solo si hay pocos puntos
            textposition="top center",
            marker=dict(
                size=(row['Gasto']/max_gasto)*40 + 20,
                color='#1E293B',
                line=dict(width=2, color='white')
            ),
            hovertemplate=f"<b>{row[label_col]}</b><br>Gasto: {row['Gasto']:,.2f} €<extra></extra>"
        ))

    fig.update_layout(
        xaxis=dict(title="IMPACTO", range=[-0.5, 11.5], gridcolor="#E2E8F0"),
        yaxis=dict(title="RIESGO", range=[-0.5, 11.5], gridcolor="#E2E8F0"),
        margin=dict(l=20, r=20, t=20, b=20),
        height=500,
        template="plotly_white",
        showlegend=True
    )
    return fig

# --- 3. GENERADOR DE PDF (CORREGIDO PARA MICRO) ---
def create_pdf_report(df_n1, df_micro, cat_name, fig_macro, fig_micro):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Portada
    pdf.add_page()
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 210, 50, 'F')
    pdf.set_font("Arial", 'B', 22)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 20, "REPORTE ESTRATÉGICO DE COMPRAS", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Categoría Analizada: {cat_name}", ln=True, align='C')
    
    # Gráfico Macro
    pdf.set_text_color(0, 0, 0)
    pdf.ln(25)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "1. Matriz de Posicionamiento Global (Nivel 1)", ln=True)
    
    try:
        # Intentamos capturar imagen; si falla por Kaleido, el PDF sigue
        img_bytes = fig_macro.to_image(format="png", engine="kaleido")
        pdf.image(io.BytesIO(img_bytes), x=15, y=75, w=180)
    except:
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(0, 10, "[Gráfico Macro: Vista previa no disponible en servidor - Ver tablas abajo]", ln=True)

    # Segunda Página: Análisis Micro
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"2. Análisis Detallado (Micro): {cat_name}", ln=True)
    
    try:
        img_bytes_m = fig_micro.to_image(format="png", engine="kaleido")
        pdf.image(io.BytesIO(img_bytes_m), x=15, y=30, w=180)
    except:
        pdf.ln(5)
        pdf.cell(0, 10, "[Gráfico Micro: Vista previa no disponible]", ln=True)

    pdf.set_y(140)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, "Desglose de Subcategorías y Proveedores:", ln=True)
    
    # Tabla de datos Micro
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(70, 8, "Subcategoría", 1, 0, 'C', True)
    pdf.cell(70, 8, "Proveedor", 1, 0, 'C', True)
    pdf.cell(40, 8, "Gasto (€)", 1, 1, 'C', True)
    
    pdf.set_font("Arial", '', 8)
    for _, row in df_micro.sort_values('Gasto', ascending=False).iterrows():
        pdf.cell(70, 8, str(row['Subcategoría'])[:35], 1)
        pdf.cell(70, 8, str(row['Proveedor'])[:35], 1)
        pdf.cell(40, 8, f"{row['Gasto']:,.2f}", 1, 1, 'R')

    return pdf.output(dest='S').encode('latin-1', errors='replace')

# --- 4. LÓGICA DE LA APP ---
if 'n1' not in st.session_state:
    st.info("👋 Por favor, carga tus datos en la pestaña 'Gestión de Datos'.")
else:
    # Selector de Categoría (Eje del análisis Micro)
    categorias_disponibles = st.session_state['n2']['Categoría'].unique()
    cat_seleccionada = st.selectbox("Seleccione Categoría para Análisis Detallado:", categorias_disponibles)
    
    # Filtrado dinámico
    df_micro_actual = st.session_state['n2'][st.session_state['n2']['Categoría'] == cat_seleccionada]
    
    # Generación de figuras
    fig_macro = draw_kraljic(st.session_state['n1'], 'Categoría')
    fig_micro = draw_kraljic(df_micro_actual, 'Subcategoría')
    
    # Mostrar en pantalla
    col1, col2 = st.tabs(["📊 Vista Global", "🔍 Vista Micro (Detalle)"])
    
    with col1:
        st.plotly_chart(fig_macro, use_container_width=True)
    
    with col2:
        st.plotly_chart(fig_micro, use_container_width=True)
        st.dataframe(df_micro_actual, hide_index=True)

    # BOTÓN DE REPORTE (Aquí estaba el error)
    st.divider()
    try:
        reporte_pdf = create_pdf_report(
            st.session_state['n1'], 
            df_micro_actual, 
            cat_seleccionada, 
            fig_macro, 
            fig_micro
        )
        
        st.download_button(
            label="📥 Descargar Reporte PDF (Macro + Micro)",
            data=reporte_pdf,
            file_name=f"Analisis_Kraljic_{cat_seleccionada}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Error técnico al preparar el PDF: {e}")
