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

# ── 2. LÓGICA DE NEGOCIO (MATRIZ DE KRALJIC) ──
def calculate_kraljic(df):
    if df.empty: return df
    total_spend = df['Gasto (€)'].sum()
    # Segmentación basada en impacto económico
    df['Impacto'] = df['Gasto (€)'].apply(lambda x: 9 if x/total_spend > 0.15 else (6 if x/total_spend > 0.05 else 3))
    df['Riesgo'] = 5  # Riesgo base por defecto
    
    def get_quadrant(i, r):
        if i >= 6 and r >= 6: return 'Estratégico'
        if i >= 6 and r < 6: return 'Apalancamiento'
        if i < 6 and r >= 6: return 'Cuello de Botella'
        return 'No Crítico'
    
    df['Cuadrante'] = df.apply(lambda x: get_quadrant(x['Impacto'], x['Riesgo']), axis=1)
    return df

# ── 3. MOTOR DE GRÁFICOS (SIN DUPLICADOS EN LEYENDA) ──
def draw_matrix(df, label_col):
    fig = go.Figure()
    
    # Dibujar Cuadrantes de Kraljic
    fig.add_shape(type="rect", x0=0, y0=5.5, x1=5.5, y1=11, fillcolor="#FEF3C7", opacity=0.4, line_width=0, layer="below")
    fig.add_shape(type="rect", x0=5.5, y0=5.5, x1=11, y1=11, fillcolor="#FEE2E2", opacity=0.4, line_width=0, layer="below")
    fig.add_shape(type="rect", x0=0, y0=0, x1=5.5, y1=5.5, fillcolor="#F1F5F9", opacity=0.4, line_width=0, layer="below")
    fig.add_shape(type="rect", x0=5.5, y0=0, x1=11, y1=5.5, fillcolor="#D1FAE5", opacity=0.4, line_width=0, layer="below")

    # Paleta de colores profesional
    colors = px.colors.qualitative.Prism
    max_g = df['Gasto (€)'].max() if not df.empty else 1
    
    # SOLUCIÓN A ETIQUETAS REPETIDAS: 
    # Agrupamos por la columna de etiquetas para crear una sola traza por nombre único
    unique_labels = df[label_col].unique()
    
    for i, label in enumerate(unique_labels):
        temp_df = df[df[label_col] == label]
        
        fig.add_trace(go.Scatter(
            x=temp_df['Impacto'], 
            y=temp_df['Riesgo'],
            mode='markers',
            name=str(label),
            legendgroup=str(label), # Agrupa para evitar duplicados visuales
            showlegend=True,
            marker=dict(
                size=(temp_df['Gasto (€)']/max_g)*55 + 15,
                color=colors[i % len(colors)],
                line=dict(width=1.5, color='white')
            ),
            hovertemplate=f"<b>{label}</b><br>Gasto: %{{customdata:,.2f}} EUR<extra></extra>",
            customdata=temp_df['Gasto (€)']
        ))
    
    fig.update_layout(
        xaxis=dict(title="IMPACTO ESTRATÉGICO (Gasto)", range=[-0.5, 11.5], gridcolor='#E2E8F0'),
        yaxis=dict(title="RIESGO DE SUMINISTRO", range=[-0.5, 11.5], gridcolor='#E2E8F0'),
        template="plotly_white", height=600,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

# ── 4. GENERADOR DE PDF PROFESIONAL (FIX UNICODE) ──
def generate_safe_pdf(df_micro, category_name):
    pdf = FPDF()
    pdf.add_page()
    
    # Header Corporativo
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, "REPORTE ESTRATEGICO DE COMPRAS", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 10, f"Categoria: {category_name} | Analista: Elymar Estevez", ln=True, align='C')
    
    pdf.set_text_color(0, 0, 0)
    pdf.ln(25)
    
    # Encabezados de tabla (Usamos EUR en lugar de € para evitar error de codificación)
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(70, 10, "Subcategoria", 1, 0, 'C', True)
    pdf.cell(75, 10, "Proveedor", 1, 0, 'C', True)
    pdf.cell(40, 10, "Gasto (EUR)", 1, 1, 'C', True)
    
    # Contenido con limpieza Unicode (latin-1)
    pdf.set_font("Arial", '', 9)
    for _, row in df_micro.iterrows():
        sub = str(row['Subcategoría']).encode('latin-1', 'replace').decode('latin-1')
        prov = str(row['Proveedor']).encode('latin-1', 'replace').decode('latin-1')
        
        pdf.cell(70, 9, sub[:38], 1)
        pdf.cell(75, 9, prov[:42], 1)
        pdf.cell(40, 9, f"{row['Gasto (€)']:,.0f}", 1, 1, 'R')
        
    return bytes(pdf.output())

# ── 5. ESTRUCTURA DE LA APLICACIÓN ──
with st.sidebar:
    if os.path.exists("elymar.png"):
        st.image("elymar.png", use_container_width=True)
    st.markdown("<h3 style='text-align: center;'>Elymar Estévez</h3>", unsafe_allow_html=True)
    st.divider()
    app_mode = st.radio("Navegación:", ["📂 Carga de Datos", "📊 Cuadro de Mando"])

st.markdown('<div class="header-banner"><h1>Sourcing Intelligence Dashboard</h1><div class="author-tag">Decisión Táctica y Estratégica</div></div>', unsafe_allow_html=True)

if app_mode == "📂 Carga de Datos":
    st.header("Importación de Datos")
    file = st.file_uploader("Subir archivo Excel (.xlsx)", type=["xlsx"])
    if file:
        df = pd.read_excel(file)
        # Validación de columnas críticas
        required = ['Categoría', 'Subcategoría', 'Proveedor', 'Gasto (€)']
        if all(c in df.columns for c in required):
            st.session_state['data'] = df
            st.success("¡Base de datos cargada y sincronizada correctamente!")
            st.dataframe(df.head(10), use_container_width=True)
        else:
            st.error(f"Estructura inválida. El archivo debe contener: {', '.join(required)}")

elif app_mode == "📊 Cuadro de Mando":
    if 'data' not in st.session_state:
        st.info("👋 Por favor, carga un archivo en el módulo de 'Carga de Datos' para activar el dashboard.")
    else:
        df = st.session_state['data']
        
        # Procesamiento Nivel Macro
        df_macro = df.groupby('Categoría').agg({'Gasto (€)': 'sum'}).reset_index()
        df_macro = calculate_kraljic(df_macro)
        
        st.subheader("🌐 Análisis Macro (Categorías)")
        st.plotly_chart(draw_matrix(df_macro, 'Categoría'), use_container_width=True)
        
        st.divider()
        
        # Análisis Micro
        selected_cat = st.selectbox("Seleccione Categoría para desglose Micro:", df_macro['Categoría'].unique())
        df_micro = df[df['Categoría'] == selected_cat].groupby(['Subcategoría', 'Proveedor']).agg({'Gasto (€)': 'sum'}).reset_index()
        df_micro = calculate_kraljic(df_micro)
        
        st.subheader(f"🔍 Análisis Micro: {selected_cat}")
        
        # Layout para gráfico y acción de descarga
        col_viz, col_rpt = st.columns([4, 1])
        
        with col_viz:
            # Aquí el gráfico ya no tendrá etiquetas repetidas en la leyenda
            st.plotly_chart(draw_matrix(df_micro, 'Subcategoría'), use_container_width=True)
        
        with col_rpt:
            st.write("### Reporte")
            try:
                pdf_data = generate_safe_pdf(df_micro, selected_cat)
                st.download_button(
                    label="📥 Exportar PDF",
                    data=pdf_data,
                    file_name=f"Analisis_{selected_cat}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except:
                st.error("Error en codificación PDF")
        
        # Tabla detallada inferior
        st.dataframe(df_micro.sort_values('Gasto (€)', ascending=False), hide_index=True, use_container_width=True)
