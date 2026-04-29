import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
import numpy as np

# ── 1. CONFIGURACIÓN DE PÁGINA ──
st.set_page_config(page_title="Sourcing Intelligence Hub | Elymar Estévez", layout="wide", page_icon="📊")

# ── 2. ESTILOS CSS (BANNER Y TABLAS) ──
st.markdown("""
    <style>
        /* Estilo del Banner de Cabecera */
        .header-banner {
            background-color: #1E293B;
            padding: 30px;
            border-radius: 15px;
            color: white;
            text-align: center;
            margin-bottom: 25px;
            border-bottom: 5px solid #10B981;
        }
        .header-banner h1 { margin: 0; font-size: 2.5rem; font-weight: 800; color: white; }
        .header-banner p { margin: 5px 0 0 0; font-size: 1.1rem; opacity: 0.8; }
        
        /* Estilo general */
        .main-header { color: #0F172A; font-size: 1.8rem; font-weight: 700; margin-top: 20px; }
        .stDataFrame { border: 1px solid #e2e8f0; }
    </style>
""", unsafe_allow_html=True)

# ── 3. CABECERA (BANNER INICIAL) ──
st.markdown("""
    <div class="header-banner">
        <h1>📊 Sourcing Strategic Intelligence</h1>
        <p>Dashboard Interactivo para la Toma de Decisiones en Compra de Materias Primas</p>
    </div>
""", unsafe_allow_html=True)

# ── 4. BARRA LATERAL Y PLANTILLA EXCEL ──
with st.sidebar:
    st.title("⚙️ Configuración")
    
    # Generador de Plantilla con las 4 columnas exactas
    try:
        import xlsxwriter
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            pd.DataFrame(columns=['Proveedor', 'Categoría', 'Subcategoría', 'Gasto (€)']).to_excel(writer, index=False)
        st.download_button(
            label="📥 Descargar Plantilla Excel",
            data=buffer.getvalue(),
            file_name="plantilla_compras_v13.xlsx",
            mime="application/vnd.ms-excel"
        )
    except ImportError:
        st.error("Instala 'xlsxwriter' para habilitar la descarga de Excel")
    
    st.divider()
    menu = st.radio("Navegación:", ["1. Gestión de Datos", "2. Análisis de Matriz"])
    st.divider()
    st.caption("Desarrollado por Elymar Estévez")

# ── 5. FUNCION PARA CREAR MATRICES (ESTILO REFERENCIA) ──
def draw_kraljic(df, label_col, title):
    fig = go.Figure()
    # Cuadrantes con colores pastel de la imagen enviada anteriormente
    fig.add_shape(type="rect", x0=0, y0=5.5, x1=5.5, y1=11.5, fillcolor="#FEF3C7", line_width=0, layer="below") # Cuello Botella
    fig.add_shape(type="rect", x0=5.5, y0=5.5, x1=11.5, y1=11.5, fillcolor="#FEE2E2", line_width=0, layer="below") # Estratégico
    fig.add_shape(type="rect", x0=0, y0=0, x1=5.5, y1=5.5, fillcolor="#F1F5F9", line_width=0, layer="below") # No Crítico
    fig.add_shape(type="rect", x0=5.5, y0=0, x1=11.5, y1=5.5, fillcolor="#D1FAE5", line_width=0, layer="below") # Apalancamiento

    # Etiquetas de texto de cuadrantes
    for txt, x, y in [("CUELLO BOTELLA", 2.75, 10.8), ("ESTRATÉGICO", 8.25, 10.8), ("NO CRÍTICO", 2.75, 0.5), ("APALANCAMIENTO", 8.25, 0.5)]:
        fig.add_annotation(x=x, y=y, text=txt, showarrow=False, font=dict(size=18, color="#94A3B8", family="Arial Black"))

    # Burbujas
    fig.add_trace(go.Scatter(
        x=df['Impacto'], y=df['Riesgo'], mode='markers+text',
        text=df[label_col], textposition="top center",
        marker=dict(size=df['Gasto']/df['Gasto'].max()*45 + 25, color='#334155', line=dict(width=1.5, color='white')),
        hovertemplate="<b>%{text}</b><br>Gasto: %{customdata:,.2f} €<extra></extra>",
        customdata=df['Gasto']
    ))
    
    fig.update_layout(
        title=title, xaxis=dict(title="IMPACTO FINANCIERO", range=[-0.5, 11.5]),
        yaxis=dict(title="RIESGO DE SUMINISTRO", range=[-0.5, 11.5]),
        height=650, template="plotly_white"
    )
    return fig

# ── 6. LÓGICA DE CARGA ──
if menu == "1. Gestión de Datos":
    st.markdown("<h2 class='main-header'>📥 Carga de Gastos Anuales</h2>", unsafe_allow_html=True)
    archivo = st.file_uploader("Sube el archivo Excel completado", type=['xlsx'])
    
    if archivo:
        df_raw = pd.read_excel(archivo)
        df_raw['Gasto (€)'] = pd.to_numeric(df_raw['Gasto (€)'], errors='coerce').fillna(0)
        
        # Consolidación para Nivel 1 (Categoría)
        res_cat = df_raw.groupby('Categoría').agg({'Gasto (€)': 'sum'}).reset_index()
        total_g = res_cat['Gasto (€)'].sum()
        res_cat['Impacto'] = res_cat['Gasto (€)'].apply(lambda x: 9 if x/total_g > 0.15 else (6 if x/total_g > 0.05 else 3))
        res_cat['Riesgo'] = res_cat['Categoría'].apply(lambda x: 8 if "ALIM" in str(x).upper() else 4)
        st.session_state['df_nivel1'] = res_cat.rename(columns={'Gasto (€)': 'Gasto'})

        # Consolidación para Nivel 2 (Subcategoría)
        res_sub = df_raw.groupby(['Categoría', 'Subcategoría']).agg({'Gasto (€)': 'sum', 'Proveedor': 'first'}).reset_index()
        res_sub['Impacto'] = res_sub['Gasto (€)'].apply(lambda x: 9 if x/total_g > 0.10 else (6 if x/total_g > 0.02 else 3))
        res_sub['Riesgo'] = res_sub['Categoría'].apply(lambda x: 8 if "ALIM" in str(x).upper() else 4)
        st.session_state['df_nivel2'] = res_sub.rename(columns={'Gasto (€)': 'Gasto'})

        st.success("✅ Datos procesados con éxito. Dirígete a 'Análisis de Matriz'.")
        st.dataframe(df_raw, use_container_width=True, hide_index=True)

# ── 7. LÓGICA DE MATRIZ DOS NIVELES ──
elif menu == "2. Análisis de Matriz":
    if 'df_nivel1' not in st.session_state:
        st.warning("⚠️ Por favor, carga los datos en la sección 1.")
    else:
        tab_cat, tab_sub = st.tabs(["🏛️ NIVEL 1: Categorías", "🔍 NIVEL 2: Zoom Subcategorías"])
        
        with tab_cat:
            st.plotly_chart(draw_kraljic(st.session_state['df_nivel1'], 'Categoría', "Visión Global por Macro-Categoría"), use_container_width=True)
            st.dataframe(st.session_state['df_nivel1'], hide_index=True, column_config={"Gasto": st.column_config.NumberColumn(format="%.2f €", width=200)})

        with tab_sub:
            df_s = st.session_state['df_nivel2']
            cat_list = df_s['Categoría'].unique()
            seleccion = st.selectbox("🎯 Selecciona una Categoría para ver sus detalles:", cat_list)
            
            df_filtrado = df_s[df_s['Categoría'] == seleccion]
            
            st.plotly_chart(draw_kraljic(df_filtrado, 'Subcategoría', f"Desglose de {seleccion}"), use_container_width=True)
            st.dataframe(df_filtrado[['Subcategoría', 'Proveedor', 'Gasto']], hide_index=True, 
                         column_config={"Gasto": st.column_config.NumberColumn(format="%.2f €", width=200)})
