import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
import os
from PIL import Image

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
        .strategy-box {
            padding: 15px; border-radius: 10px; border-left: 5px solid #10B981;
            background-color: #F8FAFC; margin-top: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# ── 2. BARRA LATERAL (BRANDING) ──
with st.sidebar:
    foto_path = "elymar.png"
    if os.path.exists(foto_path):
        st.image(Image.open(foto_path), use_container_width=True)
    
    st.markdown("<div style='text-align: center; font-weight: bold; font-size: 1.2rem;'>Elymar Estévez</div>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("Módulos:", ["📂 Gestión de Datos", "📊 Matriz de Kraljic"], index=1)
    
    # Plantilla de 4 columnas
    try:
        import xlsxwriter
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as w:
            pd.DataFrame(columns=['Proveedor', 'Categoría', 'Subcategoría', 'Gasto (€)']).to_excel(w, index=False)
        st.download_button("📥 Plantilla Excel", buf.getvalue(), "plantilla_compras.xlsx")
    except: pass

# ── 3. CABECERA ──
st.markdown("""
    <div class="header-banner">
        <h1>Sourcing Strategic Intelligence</h1>
        <p>Cuadro de Mando para Toma de Decisiones Estratégicas</p>
        <div class="author-tag">Desarrollado por Elymar Estévez</div>
    </div>
""", unsafe_allow_html=True)

# ── 4. MOTOR DE ESTRATEGIA POR CUADRANTE ──
def obtener_estrategia(cuadrante):
    estrategias = {
        'Estratégico': "🚀 **Estrategia:** Alianzas a largo plazo, co-diseño y gestión estrecha de la relación con el proveedor (SRM).",
        'Apalancamiento': "💰 **Estrategia:** Licitaciones competitivas, optimización de precios y consolidación de volúmenes.",
        'Cuello de Botella': "⚠️ **Estrategia:** Asegurar volumen, buscar sustitutos y reducir dependencia de proveedores únicos.",
        'No Crítico': "🛒 **Estrategia:** Automatización de compras, catálogos electrónicos y reducción de costes administrativos."
    }
    return estrategias.get(cuadrante, "")

# ── 5. FUNCIÓN DE MATRIZ MEJORADA (COLORES Y LEYENDA FUERA) ──
def draw_kraljic_interactive(df, label_col):
    fig = go.Figure()
    
    # Fondos (Colores imagen 8b1011.png)
    fig.add_shape(type="rect", x0=0, y0=5.5, x1=5.5, y1=11, fillcolor="#FEF3C7", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=5.5, y0=5.5, x1=11, y1=11, fillcolor="#FEE2E2", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=0, y0=0, x1=5.5, y1=5.5, fillcolor="#F1F5F9", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=5.5, y0=0, x1=11, y1=5.5, fillcolor="#D1FAE5", line_width=0, layer="below")

    # Etiquetas de fondo
    for t, x, y in [("CUELLO BOTELLA", 2.75, 10.5), ("ESTRATÉGICO", 8.25, 10.5), ("NO CRÍTICO", 2.75, 0.5), ("APALANCAMIENTO", 8.25, 0.5)]:
        fig.add_annotation(x=x, y=y, text=t, showarrow=False, font=dict(size=18, color="#94A3B8", family="Arial Black"))

    # Burbujas: Se usa el label_col para el color (leyenda fuera automáticamente)
    for i, row in df.iterrows():
        fig.add_trace(go.Scatter(
            x=[row['Impacto']], y=[row['Riesgo']],
            mode='markers',
            name=str(row[label_col]), # Esto genera la leyenda fuera
            marker=dict(size=row['Gasto']/df['Gasto'].max()*45 + 25, line=dict(width=1, color='white')),
            hovertemplate=f"<b>{row[label_col]}</b><br>Gasto: {row['Gasto']:,.2f} €<br>Cuadrante: {row['Cuadrante']}<extra></extra>"
        ))
    
    fig.update_layout(
        xaxis=dict(title="IMPACTO FINANCIERO", range=[-0.2, 11.2]),
        yaxis=dict(title="RIESGO DE SUMINISTRO", range=[-0.2, 11.2]),
        height=650, template="plotly_white",
        legend=dict(title=f"Leyenda de {label_col}", orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
    )
    return fig

# ── 6. LÓGICA DE PROCESAMIENTO ──
if menu == "📂 Gestión de Datos":
    st.subheader("📥 Carga de Datos")
    file = st.file_uploader("Sube tu Excel", type=['xlsx'])
    if file:
        df = pd.read_excel(file)
        df['Gasto (€)'] = pd.to_numeric(df['Gasto (€)'], errors='coerce').fillna(0)
        total = df['Gasto (€)'].sum()
        
        def asignar_q(i, r):
            if i >= 6 and r >= 6: return 'Estratégico'
            if i >= 6: return 'Apalancamiento'
            if r >= 6: return 'Cuello de Botella'
            return 'No Crítico'

        # Nivel 1
        n1 = df.groupby('Categoría').agg({'Gasto (€)': 'sum'}).reset_index()
        n1['Impacto'] = n1['Gasto (€)'].apply(lambda x: 9 if x/total > 0.15 else (6 if x/total > 0.05 else 3))
        n1['Riesgo'] = n1['Categoría'].apply(lambda x: 8 if any(k in str(x).upper() for k in ["ALIM", "ENER", "QUIM"]) else 4)
        n1['Cuadrante'] = n1.apply(lambda x: asignar_q(x['Impacto'], x['Riesgo']), axis=1)
        st.session_state['n1'] = n1.rename(columns={'Gasto (€)': 'Gasto'})

        # Nivel 2
        n2 = df.groupby(['Categoría', 'Subcategoría']).agg({'Gasto (€)': 'sum', 'Proveedor': 'first'}).reset_index()
        n2['Impacto'] = n2['Gasto (€)'].apply(lambda x: 9 if x/total > 0.08 else (6 if x/total > 0.02 else 3))
        n2['Riesgo'] = n2['Categoría'].apply(lambda x: 8 if any(k in str(x).upper() for k in ["ALIM", "ENER", "QUIM"]) else 4)
        n2['Cuadrante'] = n2.apply(lambda x: asignar_q(x['Impacto'], x['Riesgo']), axis=1)
        st.session_state['n2'] = n2.rename(columns={'Gasto (€)': 'Gasto'})
        st.success("¡Datos listos!")

# ── 7. DASHBOARD ──
elif menu == "📊 Matriz de Kraljic":
    if 'n1' in st.session_state:
        t1, t2 = st.tabs(["🏛️ Nivel 1: Categorías", "🔍 Nivel 2: Subcategorías"])
        
        with t1:
            col_g, col_s = st.columns([3, 1])
            df_n1 = st.session_state['n1']
            with col_g:
                st.plotly_chart(draw_kraljic_interactive(df_n1, 'Categoría'), use_container_width=True)
            with col_s:
                st.markdown("### 💡 Estrategia Sugerida")
                for q in df_n1['Cuadrante'].unique():
                    st.markdown(f"<div class='strategy-box'>{obtener_estrategia(q)}</div>", unsafe_allow_html=True)

            st.dataframe(df_n1.sort_values('Gasto', ascending=False), hide_index=True, column_config={"Gasto": st.column_config.NumberColumn(format="%.2f €", width=200)})

        with t2:
            sel_cat = st.selectbox("Selecciona Categoría:", st.session_state['n2']['Categoría'].unique())
            df_f = st.session_state['n2'][st.session_state['n2']['Categoría'] == sel_cat]
            
            col_g2, col_s2 = st.columns([3, 1])
            with col_g2:
                st.plotly_chart(draw_kraljic_interactive(df_f, 'Subcategoría'), use_container_width=True)
            with col_s2:
                st.markdown("### 💡 Estrategia del Grupo")
                for q in df_f['Cuadrante'].unique():
                    st.markdown(f"<div class='strategy-box'>{obtener_estrategia(q)}</div>", unsafe_allow_html=True)
            
            st.dataframe(df_f[['Subcategoría', 'Proveedor', 'Gasto', 'Cuadrante']], hide_index=True, column_config={"Gasto": st.column_config.NumberColumn(format="%.2f €", width=200)})
    else:
        st.warning("⚠️ Carga datos primero.")
