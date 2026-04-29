import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
import os
import base64
from datetime import date

# ── 1. CONFIGURACIÓN DE PÁGINA ──
st.set_page_config(
    page_title="Purchasing Strategic Dashboard | Elymar Estévez",
    page_icon="📊",
    layout="wide"
)

# Inicializamos el estado de la pestaña si no existe
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0

# Estilos CSS Profesionales
st.markdown("""
    <style>
        .main { background-color: #f8fafc; }
        .stMetric { background-color: white; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; }
        /* Estilo para botones en paralelo */
        div.stButton > button { border-radius: 8px; font-weight: bold; height: 3.5em; }
    </style>
""", unsafe_allow_html=True)

# ── 2. MARCA PERSONAL ──
def get_base64_img(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    return "https://img.icons8.com/fluency/96/businesswoman.png"

foto_base64 = get_base64_img("elymar.png")

st.markdown(f"""
    <div id="top" style="background-color: #0F172A; padding: 25px; border-radius: 15px; margin-bottom: 25px; border-left: 8px solid #3B82F6; display: flex; align-items: center;">
        <div style="flex-shrink: 0; margin-right: 25px;">
            <img src="{foto_base64}" style="width: 100px; height: 100px; border-radius: 50%; border: 3px solid #3B82F6; object-fit: cover;">
        </div>
        <div style="flex-grow: 1;">
            <h1 style="color: white; margin: 0; font-size: 2.2rem; font-weight: 800;">Purchasing Strategic Dashboard V4.0</h1>
            <p style="color: #94A3B8; margin: 5px 0 0 0; font-size: 1.1rem;">ACOMPAÑANTE DIGITAL: <strong>COMPRAS 4.0</strong> · POR ELYMAR ESTÉVEZ</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# ── 3. INTELIGENCIA DE NEGOCIO ──
DATABASE_INTEL = {
    "MATERIA PRIMA ALIMENTACIÓN": ['cacao', 'chocolate', 'aceite', 'grasa', 'cereales', 'harina', 'azucar', 'leche', 'cafe'],
    "PACKAGING": ['carton', 'estucheria', 'laminado', 'embalaje', 'pallet', 'etiqueta', 'envase', 'film'],
    "LOGÍSTICA": ['flete', 'transporte', 'maritimo', 'terrestre', 'aduana', 'almacen'],
    "ENERGÍA & UTILITIES": ['electricidad', 'gas', 'luz', 'agua', 'fuel'],
    "IT & TECNOLOGÍA": ['software', 'erp', 'cloud', 'saas', 'hardware'],
    "INDIRECTOS": ['limpieza', 'seguridad', 'consultoria', 'mantenimiento', 'oficina']
}

def sugerir_cat(subcat):
    sub_low = str(subcat).lower()
    for cat, keywords in DATABASE_INTEL.items():
        if any(k in sub_low for k in keywords): return cat
    return "OTRAS CATEGORÍAS"

def obtener_scores_base(cat):
    scores = {
        "MATERIA PRIMA ALIMENTACIÓN": (9, 8), "PACKAGING": (7, 7), "LOGÍSTICA": (8, 7),
        "ENERGÍA & UTILITIES": (10, 9), "IT & TECNOLOGÍA": (8, 6), "INDIRECTOS": (3, 3), "OTRAS CATEGORÍAS": (5, 5)
    }
    return scores.get(cat, (5, 5))

# ── 4. CONTROL DE PESTAÑAS DINÁMICO ──
# Usamos un contenedor para las pestañas y el session state para controlar cuál está activa
tabs = st.tabs(["📥 Gestión de Datos", "📊 Matriz & Estrategia"])

with tabs[0]:
    st.subheader("Carga y Consolidación de Información")
    archivo = st.file_uploader("Sube tu Excel/CSV", type=['xlsx', 'csv'])
    
    # Datos por defecto/ejemplo
    df_temp = pd.DataFrame({'Subcategoría': ['Cacao', 'Cacao', 'Cartón'], 'Gasto Anual (€)': [500000, 700000, 200000]})
    df_input = pd.read_excel(archivo) if archivo and archivo.name.endswith('.xlsx') else (pd.read_csv(archivo) if archivo else df_temp)

    if 'Categoría' not in df_input.columns:
        df_input['Categoría'] = df_input['Subcategoría'].apply(sugerir_cat)

    df_editor = st.data_editor(df_input, num_rows="dynamic", use_container_width=True)

    st.write("---")
    
    # ── BOTONES EN PARALELO ──
    col_btn1, col_btn2, col_spacer = st.columns([1, 1, 1.5])
    
    with col_btn1:
        if st.button("🚀 PROCESAR Y CONSOLIDAR", use_container_width=True):
            df_consolidado = df_editor.groupby('Subcategoría').agg({
                'Gasto Anual (€)': 'sum',
                'Categoría': 'first'
            }).reset_index()

            total_gasto = df_consolidado['Gasto Anual (€)'].sum()
            final_list = []

            for _, row in df_consolidado.iterrows():
                i_base, r_base = obtener_scores_base(row['Categoría'])
                gasto = row['Gasto Anual (€)']
                impacto = min(10, i_base + 1) if (gasto / total_gasto) > 0.15 else i_base
                
                if impacto >= 6 and r_base >= 6: q = 'Estratégico'
                elif impacto >= 6 and r_base < 6: q = 'Apalancamiento'
                elif impacto < 6 and r_base >= 6: q = 'Cuello de Botella'
                else: q = 'No Crítico'
                
                final_list.append({
                    'Categoría': row['Categoría'], 'Subcategoría': row['Subcategoría'], 
                    'Gasto': gasto, 'Impacto': impacto, 'Riesgo': r_base, 'Cuadrante': q
                })
            
            st.session_state['data_final'] = pd.DataFrame(final_list)
            st.success("¡Datos consolidados con éxito!")

    with col_btn2:
        # Este botón solo aparece si ya hay datos procesados
        if 'data_final' in st.session_state:
            if st.button("📊 VER RESULTADOS AHORA", type="primary", use_container_width=True):
                # El truco: Streamlit recarga y al tener el anclaje en el link o la lógica de tabs, sube.
                # Para un salto limpio, usamos este componente de JS invisible:
                st.markdown('<script>window.parent.document.querySelector(".stTabs [id^=\'tabs-bui\'][id$=' + "'-tab-1']\").click();</script>", unsafe_allow_html=True)
                st.info("Desplazando a Matriz...")

with tabs[1]:
    if 'data_final' in st.session_state:
        res = st.session_state['data_final']
        
        # KPIs de Cabecera
        c1, c2, c3 = st.columns(3)
        c1.metric("Gasto Consolidado", f"{res['Gasto'].sum():,.0f} €")
        c2.metric("Subcategorías Únicas", len(res))
        c3.metric("Riesgo Promedio", round(res['Riesgo'].mean(), 1))

        st.divider()
        
        # MATRIZ INTERACTIVA
        m1, m2 = st.columns([2, 1])
        with m1:
            fig = go.Figure()
            colores = {'Estratégico': '#EF4444', 'Apalancamiento': '#10B981', 'Cuello de Botella': '#F59E0B', 'No Crítico': '#64748B'}
            for quad, color in colores.items():
                d = res[res['Cuadrante'] == quad]
                if not d.empty:
                    fig.add_trace(go.Scatter(
                        x=d['Impacto'], y=d['Riesgo'], mode='markers', name=quad,
                        hovertemplate="<b>%{customdata[0]}</b><br>Gasto: %{customdata[1]:,.0f}€<extra></extra>",
                        customdata=list(zip(d['Subcategoría'], d['Gasto'])),
                        marker=dict(size=d['Gasto']/res['Gasto'].max()*60 + 20, color=color, opacity=0.7, line=dict(width=2, color='white'))
                    ))
            fig.update_layout(
                title="<b>Matriz de Kraljic (Consolidada)</b>",
                xaxis=dict(title="IMPACTO", range=[-0.5, 11]),
                yaxis=dict(title="RIESGO", range=[-0.5, 11]),
                plot_bgcolor='white', height=550
            )
            st.plotly_chart(fig, use_container_width=True)

        with m2:
            st.markdown("### Gasto por Categoría")
            gasto_cat = res.groupby('Categoría')['Gasto'].sum().sort_values(ascending=True)
            fig_bar = go.Figure(go.Bar(x=gasto_cat.values, y=gasto_cat.index, orientation='h', marker_color='#1E293B'))
            fig_bar.update_layout(height=400, plot_bgcolor='white')
            st.plotly_chart(fig_bar, use_container_width=True)

        # RECOMENDACIONES
        st.divider()
        st.subheader("📋 Recomendaciones Estratégicas Únicas")
        for q in ['Estratégico', 'Apalancamiento', 'Cuello de Botella', 'No Crítico']:
            items = res[res['Cuadrante'] == q]
            if not items.empty:
                with st.expander(f"Ver Estrategias para: {q.upper()}"):
                    st.table(items[['Subcategoría', 'Gasto']].rename(columns={'Gasto': 'Gasto Total (€)'}))
                    if q == 'Estratégico': st.error("Foco: Alianzas Estratégicas y SRM.")
                    elif q == 'Apalancamiento': st.success("Foco: Licitaciones y Agregación de Volumen.")
                    elif q == 'Cuello de Botella': st.warning("Foco: Garantía de Suministro y Sustitutos.")
                    else: st.info("Foco: Automatización y Transaccionalidad.")
    else:
        st.warning("⚠️ Los resultados aparecerán aquí una vez proceses los datos en la pestaña anterior.")
