import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
from fpdf import FPDF

# ── 1. CONFIGURACIÓN E IDENTIDAD VISUAL ──
st.set_page_config(page_title="Sourcing Intelligence | Elymar Estévez", layout="wide", page_icon="📈")

st.markdown("""
    <style>
        .header-banner {
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            padding: 2.5rem; border-radius: 15px; color: white; text-align: center;
            margin-bottom: 2rem; border-bottom: 6px solid #10B981;
        }
        .strategy-card {
            background-color: #FFFFFF; border-radius: 10px; padding: 20px;
            border-top: 5px solid #10B981; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
    </style>
""", unsafe_allow_html=True)

# ── 2. INTELIGENCIA DE COMPRAS: ESTRATEGIAS ──
DATOS_ESTRATEGICOS = {
    'Estratégico': {
        'tactica': "Alianzas a largo plazo, contratos de colaboración y gestión de riesgos conjunta.",
        'color': "#FEE2E2", 'label': "ESTRATÉGICO"
    },
    'Apalancamiento': {
        'tactica': "Licitaciones competitivas, optimización de precios y consolidación de volúmenes.",
        'color': "#D1FAE5", 'label': "APALANCAMIENTO"
    },
    'Cuello de Botella': {
        'tactica': "Asegurar volumen de stock, buscar sustitutos y contratos de reserva de capacidad.",
        'color': "#FEF3C7", 'label': "CUELLO DE BOTELLA"
    },
    'No Crítico': {
        'tactica': "Estandarización de productos y automatización de procesos administrativos.",
        'color': "#F1F5F9", 'label': "NO CRÍTICO"
    }
}

# ── 3. LÓGICA DE PROCESAMIENTO ──
def aplicar_logica_kraljic(df):
    if df.empty: return df
    total_gasto = df['Gasto (€)'].sum()
    
    # Impacto (Eje X): Basado en Pareto de gasto (ejemplo: >15% es impacto alto)
    df['Impacto'] = df['Gasto (€)'].apply(lambda x: 9 if x/total_gasto > 0.15 else (6 if x/total_gasto > 0.05 else 3))
    # Riesgo (Eje Y): Valor estático 5 para demostración (personalizable en Excel)
    df['Riesgo'] = 5 

    def clasificar(row):
        if row['Impacto'] >= 6 and row['Riesgo'] >= 6: return 'Estratégico'
        if row['Impacto'] >= 6: return 'Apalancamiento'
        if row['Riesgo'] >= 6: return 'Cuello de Botella'
        return 'No Crítico'

    df['Cuadrante'] = df.apply(clasificar, axis=1)
    return df

# ── 4. MOTOR DE GRÁFICOS (SIN DUPLICADOS Y CON CUADRANTES) ──
def renderizar_matriz(df, columna_nombre):
    fig = go.Figure()

    # Dibujar áreas de fondo (Cuadrantes)
    rectas = [
        (0, 5.5, 5.5, 11, DATOS_ESTRATEGICOS['Cuello de Botella']['color'], "CUELLO DE BOTELLA"),
        (5.5, 5.5, 11, 11, DATOS_ESTRATEGICOS['Estratégico']['color'], "ESTRATÉGICO"),
        (0, 0, 5.5, 5.5, DATOS_ESTRATEGICOS['No Crítico']['color'], "NO CRÍTICO"),
        (5.5, 0, 11, 5.5, DATOS_ESTRATEGICOS['Apalancamiento']['color'], "APALANCAMIENTO")
    ]
    for x0, y0, x1, y1, color, nombre in rectas:
        fig.add_shape(type="rect", x0=x0, y0=y0, x1=x1, y1=y1, fillcolor=color, opacity=0.4, line_width=0, layer="below")
        fig.add_annotation(x=x0+2.7, y=y0+5, text=nombre, showarrow=False, font=dict(color="rgba(0,0,0,0.2)", size=12))

    # Burbujas: Una traza por nombre único para evitar duplicados en leyenda
    nombres_unicos = df[columna_nombre].unique()
    paleta = px.colors.qualitative.Bold
    gasto_max = df['Gasto (€)'].max() if not df.empty else 1

    for i, nombre in enumerate(nombres_unicos):
        sub_df = df[df[columna_nombre] == nombre]
        fig.add_trace(go.Scatter(
            x=sub_df['Impacto'], y=sub_df['Riesgo'],
            mode='markers', name=str(nombre),
            marker=dict(size=(sub_df['Gasto (€)']/gasto_max)*60 + 15, color=paleta[i % len(paleta)], line=dict(width=1, color='white')),
            hovertemplate=f"<b>{nombre}</b><br>Gasto: %{{customdata:,.2f}} EUR<br>Cuadrante: %{{text}}<extra></extra>",
            customdata=sub_df['Gasto (€)'], text=sub_df['Cuadrante']
        ))

    fig.update_layout(
        xaxis=dict(title="IMPACTO EN RESULTADOS", range=[-0.5, 11.5]),
        yaxis=dict(title="RIESGO DE SUMINISTRO", range=[-0.5, 11.5]),
        template="plotly_white", height=650, legend=dict(orientation="h", y=-0.15)
    )
    return fig

# ── 5. GENERACIÓN DE REPORTE PDF SEGURO ──
def crear_pdf_estratego(df_micro, cat_nombre):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, "CUADRO DE MANDO ESTRATEGICO", ln=True, align='C')
    
    pdf.set_text_color(0, 0, 0)
    pdf.ln(30)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"Categoria de Analisis: {cat_nombre}", ln=True)
    
    for _, fila in df_micro.iterrows():
        cuad = fila['Cuadrante']
        pdf.set_font("Arial", 'B', 10)
        pdf.set_fill_color(245, 245, 245)
        txt_sub = str(fila['Subcategoría']).encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(0, 8, f"Subcategoria: {txt_sub} | Cuadrante: {cuad}", 1, 1, 'L', True)
        pdf.set_font("Arial", '', 9)
        pdf.multi_cell(0, 6, f"Recomendacion: {DATOS_ESTRATEGICOS[cuad]['tactica']}")
        pdf.ln(3)
        
    return bytes(pdf.output())

# ── 6. ESTRUCTURA DE LA APP ──
st.markdown('<div class="header-banner"><h1>Sourcing Intelligence Dashboard</h1><p>Elymar Estévez | Cuadro de Mando de Compras</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("Control de Datos")
    if os.path.exists("elymar.png"): st.image("elymar.png")
    uploaded_file = st.file_uploader("Subir base de datos (Excel)", type=["xlsx"])
    app_mode = st.radio("Sección:", ["Carga", "Análisis Estratégico"])

if app_mode == "Carga":
    if uploaded_file:
        df_init = pd.read_excel(uploaded_file)
        if all(col in df_init.columns for col in ['Categoría', 'Subcategoría', 'Proveedor', 'Gasto (€)']):
            st.session_state['data_raw'] = df_init
            st.success("✅ Datos cargados correctamente.")
            st.dataframe(df_init.head(10), use_container_width=True)
        else:
            st.error("❌ El Excel no tiene las columnas requeridas.")
    else:
        st.info("Sube un archivo Excel para comenzar el análisis.")

elif app_mode == "Análisis Estratégico":
    if 'data_raw' in st.session_state:
        df = st.session_state['data_raw']
        
        # Análisis Macro
        df_macro = df.groupby('Categoría').agg({'Gasto (€)': 'sum'}).reset_index()
        df_macro = aplicar_logica_kraljic(df_macro)
        
        st.subheader("🌐 Matriz de Posicionamiento Macro")
        st.plotly_chart(renderizar_matriz(df_macro, 'Categoría'), use_container_width=True)
        
        st.divider()
        
        # Análisis Micro
        cat_seleccionada = st.selectbox("Seleccione categoría para nivel de detalle:", df_macro['Categoría'].unique())
        df_micro = df[df['Categoría'] == cat_seleccionada].groupby(['Subcategoría', 'Proveedor']).agg({'Gasto (€)': 'sum'}).reset_index()
        df_micro = aplicar_logica_kraljic(df_micro)
        
        st.subheader(f"🔍 Detalle Táctico: {cat_seleccionada}")
        st.plotly_chart(renderizar_matriz(df_micro, 'Subcategoría'), use_container_width=True)
        
        # Renderizado de Tarjetas de Estrategia
        st.markdown("### 💡 Estrategias Recomendadas")
        cuadrantes_presentes = df_micro['Cuadrante'].unique()
        cols = st.columns(len(cuadrantes_presentes))
        for idx, c in enumerate(cuadrantes_presentes):
            with cols[idx]:
                st.markdown(f"""<div class="strategy-card"><b>{c}</b><br><small>{DATOS_ESTRATEGICOS[c]['tactica']}</small></div>""", unsafe_allow_html=True)
        
        st.divider()
        # Exportación
        pdf_bytes = crear_pdf_estratego(df_micro, cat_seleccionada)
        st.download_button("📥 Descargar Reporte en PDF", pdf_bytes, f"Estrategia_{cat_seleccionada}.pdf", "application/pdf")
    else:
        st.warning("Cargue un archivo en la sección 'Carga' antes de analizar.")
