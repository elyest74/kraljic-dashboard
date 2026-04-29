import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
import numpy as np

# ── 1. CONFIGURACIÓN ──
st.set_page_config(page_title="Sourcing Multi-Nivel | Elymar", layout="wide")

st.markdown("""
    <style>
        .main-header { color: #0F172A; font-size: 1.8rem; font-weight: 800; border-left: 5px solid #10B981; padding-left: 15px; margin-bottom: 20px; }
        .stTabs [data-baseweb="tab-list"] { gap: 24px; }
        .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ── 2. FUNCIONES DE APOYO ──
def crear_matriz_kraljic(df, etiqueta_col, titulo):
    fig = go.Figure()
    # Fondos (Colores exactos imagen 8b1011.png)
    fig.add_shape(type="rect", x0=0, y0=5.5, x1=5.5, y1=11, fillcolor="#FEF3C7", line_width=0, layer="below") # Cuello Botella
    fig.add_shape(type="rect", x0=5.5, y0=5.5, x1=11, y1=11, fillcolor="#FEE2E2", line_width=0, layer="below") # Estratégico
    fig.add_shape(type="rect", x0=0, y0=0, x1=5.5, y1=5.5, fillcolor="#F1F5F9", line_width=0, layer="below") # No Crítico
    fig.add_shape(type="rect", x0=5.5, y0=0, x1=11, y1=5.5, fillcolor="#D1FAE5", line_width=0, layer="below") # Apalancamiento

    # Etiquetas de Cuadrantes
    for txt, x, y in [("CUELLO BOTELLA", 2.75, 10.5), ("ESTRATÉGICO", 8.25, 10.5), ("NO CRÍTICO", 2.75, 0.5), ("APALANCAMIENTO", 8.25, 0.5)]:
        fig.add_annotation(x=x, y=y, text=txt, showarrow=False, font=dict(size=16, color="#94A3B8", family="Arial Black"))

    # Burbujas
    fig.add_trace(go.Scatter(
        x=df['Impacto'], y=df['Riesgo'], mode='markers+text',
        text=df[etiqueta_col], textposition="top center",
        marker=dict(size=df['Gasto']/df['Gasto'].max()*40 + 20, color='#334155', line=dict(width=1, color='white')),
        hovertemplate="<b>%{text}</b><br>Gasto: %{customdata:,.2f}€<extra></extra>",
        customdata=df['Gasto']
    ))
    
    fig.update_layout(
        title=titulo, xaxis=dict(title="IMPACTO FINANCIERO", range=[0, 11]),
        yaxis=dict(title="RIESGO DE SUMINISTRO", range=[0, 11]),
        height=600, template="plotly_white", margin=dict(t=50, b=50)
    )
    return fig

# ── 3. CARGA DE DATOS ──
with st.sidebar:
    st.title("📂 Datos")
    archivo = st.file_uploader("Subir Excel de Compras", type=['xlsx'])
    st.divider()
    if st.button("🔄 Resetear Análisis"):
        st.session_state.clear()

if archivo:
    df_raw = pd.read_excel(archivo)
    df_raw['Gasto (€)'] = pd.to_numeric(df_raw['Gasto (€)'], errors='coerce').fillna(0)
    
    # --- PROCESAMIENTO NIVEL 1 (CATEGORÍAS) ---
    df_cat = df_raw.groupby('Categoría').agg({'Gasto (€)': 'sum'}).reset_index()
    total_g = df_cat['Gasto (€)'].sum()
    df_cat['Impacto'] = df_cat['Gasto (€)'].apply(lambda x: 9 if x/total_g > 0.15 else (6 if x/total_g > 0.05 else 3))
    df_cat['Riesgo'] = df_cat['Categoría'].apply(lambda x: 8 if "ALIM" in str(x).upper() else 4)
    df_cat = df_cat.rename(columns={'Gasto (€)': 'Gasto'})

    # --- PROCESAMIENTO NIVEL 2 (SUBCATEGORÍAS) ---
    df_sub = df_raw.groupby(['Categoría', 'Subcategoría']).agg({'Gasto (€)': 'sum', 'Proveedor': 'first'}).reset_index()
    df_sub['Impacto'] = df_sub['Gasto (€)'].apply(lambda x: 9 if x/total_g > 0.10 else (6 if x/total_g > 0.02 else 3))
    df_sub['Riesgo'] = df_sub['Categoría'].apply(lambda x: 8 if "ALIM" in str(x).upper() else 4)
    df_sub = df_sub.rename(columns={'Gasto (€)': 'Gasto'})

    # ── 4. VISUALIZACIÓN MULTI-NIVEL ──
    tab1, tab2 = st.tabs(["🏛️ NIVEL 1: Visión por Categoría", "🔍 NIVEL 2: Detalle de Subcategorías"])

    with tab1:
        st.markdown("<h1 class='main-header'>Matriz Global de Categorías</h1>", unsafe_allow_html=True)
        st.plotly_chart(crear_matriz_kraljic(df_cat, 'Categoría', "Distribución Macro de Gasto"), use_container_width=True)
        
        st.write("### Resumen de Gastos por Categoría")
        st.dataframe(df_cat.sort_values('Gasto', ascending=False), hide_index=True, use_container_width=True,
                     column_config={"Gasto": st.column_config.NumberColumn(format="%.2f €", width=200)})

    with tab2:
        st.markdown("<h1 class='main-header'>Zoom Estratégico por Categoría</h1>", unsafe_allow_html=True)
        
        seleccion = st.selectbox("🎯 Selecciona una Categoría para analizar sus Subcategorías:", df_sub['Categoría'].unique())
        
        df_filtrado = df_sub[df_sub['Categoría'] == seleccion].copy()
        
        col_g, col_t = st.columns([2, 1])
        
        with col_g:
            st.plotly_chart(crear_matriz_kraljic(df_filtrado, 'Subcategoría', f"Análisis de {seleccion}"), use_container_width=True)
        
        with col_t:
            st.write(f"### Detalle: {seleccion}")
            st.dataframe(df_filtrado[['Subcategoría', 'Gasto']].sort_values('Gasto', ascending=False), 
                         hide_index=True, use_container_width=True,
                         column_config={"Gasto": st.column_config.NumberColumn(format="%.2f €", width=200)})

else:
    st.info("👋 ¡Hola! Por favor, sube tu archivo Excel en la barra lateral para generar las dos matrices de decisión.")
