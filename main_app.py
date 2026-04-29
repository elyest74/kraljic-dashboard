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

# Lógica de navegación
if 'seccion_activa' not in st.session_state:
    st.session_state.seccion_activa = "Gestion"

def ir_a_matriz(): st.session_state.seccion_activa = "Matriz"
def ir_a_gestion(): st.session_state.seccion_activa = "Gestion"

# Estilos CSS
st.markdown("""
    <style>
        .main { background-color: #f8fafc; }
        .stMetric { background-color: white; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; }
        .stButton > button { border-radius: 8px; font-weight: bold; height: 3.5em; width: 100%; }
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
    <div style="background-color: #0F172A; padding: 25px; border-radius: 15px; margin-bottom: 25px; border-left: 8px solid #3B82F6; display: flex; align-items: center;">
        <div style="flex-shrink: 0; margin-right: 25px;">
            <img src="{foto_base64}" style="width: 100px; height: 100px; border-radius: 50%; border: 3px solid #3B82F6; object-fit: cover;">
        </div>
        <div style="flex-grow: 1;">
            <h1 style="color: white; margin: 0; font-size: 2.2rem; font-weight: 800;">Purchasing Strategic Dashboard V4.0</h1>
            <p style="color: #94A3B8; margin: 5px 0 0 0; font-size: 1.1rem;">ESTRATEGIA DE COMPRAS 4.0 · POR ELYMAR ESTÉVEZ</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# ── 3. LÓGICA DE NEGOCIO ──
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

# ── 4. NAVEGACIÓN ──
c_nav1, c_nav2 = st.columns(2)
with c_nav1:
    if st.button("📥 GESTIÓN DE DATOS", type="primary" if st.session_state.seccion_activa == "Gestion" else "secondary"):
        st.session_state.seccion_activa = "Gestion"
        st.rerun()
with c_nav2:
    if st.button("📊 MATRIZ Y ESTRATEGIA", type="primary" if st.session_state.seccion_activa == "Matriz" else "secondary"):
        if 'data_final' in st.session_state:
            st.session_state.seccion_activa = "Matriz"
            st.rerun()
        else: st.warning("Procesa los datos primero.")

st.divider()

# ── 5. SECCIÓN GESTIÓN ──
if st.session_state.seccion_activa == "Gestion":
    archivo = st.file_uploader("Sube tu Excel/CSV", type=['xlsx', 'csv'])
    df_temp = pd.DataFrame({'Subcategoría': ['Cacao', 'Cacao', 'Cartón'], 'Gasto Anual (€)': [500000, 700000, 200000]})
    df_input = pd.read_excel(archivo) if archivo and archivo.name.endswith('.xlsx') else (pd.read_csv(archivo) if archivo else df_temp)
    if 'Categoría' not in df_input.columns:
        df_input['Categoría'] = df_input['Subcategoría'].apply(sugerir_cat)
    
    df_editor = st.data_editor(df_input, num_rows="dynamic", use_container_width=True)
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("🚀 PROCESAR Y CONSOLIDAR"):
            df_consolidado = df_editor.groupby('Subcategoría').agg({'Gasto Anual (€)': 'sum', 'Categoría': 'first'}).reset_index()
            total_g = df_consolidado['Gasto Anual (€)'].sum()
            final_list = []
            for _, row in df_consolidado.iterrows():
                i_b, r_b = obtener_scores_base(row['Categoría'])
                g = row['Gasto Anual (€)']
                impacto = min(10, i_b + 1) if (g/total_g) > 0.15 else i_b
                if impacto >= 6 and r_b >= 6: q = 'Estratégico'
                elif impacto >= 6 and r_b < 6: q = 'Apalancamiento'
                elif impacto < 6 and r_b >= 6: q = 'Cuello de Botella'
                else: q = 'No Crítico'
                final_list.append({'Categoría': row['Categoría'], 'Subcategoría': row['Subcategoría'], 'Gasto': g, 'Impacto': impacto, 'Riesgo': r_b, 'Cuadrante': q})
            st.session_state['data_final'] = pd.DataFrame(final_list)
            st.success("¡Datos procesados!")
    with col_b2:
        if 'data_final' in st.session_state:
            st.button("📊 VER RESULTADOS AHORA", on_click=ir_a_matriz, type="primary")

# ── 6. SECCIÓN MATRIZ (DEFINICIÓN VISUAL DE CUADRANTES) ──
elif st.session_state.seccion_activa == "Matriz":
    res = st.session_state['data_final']
    st.info("💡 Desplaza el ratón sobre los puntos para ver el detalle.")
    
    m1, m2 = st.columns([2, 1])
    with m1:
        fig = go.Figure()
        
        # ── DIBUJAR CUADRANTES CON COLORES DE FONDO ──
        # Apalancamiento (Verde claro) - Abajo Derecha
        fig.add_shape(type="rect", x0=5.5, y0=0, x1=11, y1=5.5, fillcolor="rgba(16, 185, 129, 0.1)", line_width=0, layer="below")
        # Estratégico (Rojo claro) - Arriba Derecha
        fig.add_shape(type="rect", x0=5.5, y0=5.5, x1=11, y1=11, fillcolor="rgba(239, 68, 68, 0.1)", line_width=0, layer="below")
        # Cuello de Botella (Naranja claro) - Arriba Izquierda
        fig.add_shape(type="rect", x0=0, y0=5.5, x1=5.5, y1=11, fillcolor="rgba(245, 158, 11, 0.1)", line_width=0, layer="below")
        # No Crítico (Gris claro) - Abajo Izquierda
        fig.add_shape(type="rect", x0=0, y0=0, x1=5.5, y1=5.5, fillcolor="rgba(100, 116, 139, 0.1)", line_width=0, layer="below")

        # Puntos de datos
        colores = {'Estratégico': '#EF4444', 'Apalancamiento': '#10B981', 'Cuello de Botella': '#F59E0B', 'No Crítico': '#64748B'}
        for quad, color in colores.items():
            d = res[res['Cuadrante'] == quad]
            if not d.empty:
                fig.add_trace(go.Scatter(
                    x=d['Impacto'], y=d['Riesgo'], mode='markers', name=quad,
                    hovertemplate="<b>%{customdata[0]}</b><br>Gasto: %{customdata[1]:,.0f}€<extra></extra>",
                    customdata=list(zip(d['Subcategoría'], d['Gasto'])),
                    marker=dict(size=d['Gasto']/res['Gasto'].max()*50 + 20, color=color, opacity=0.9, line=dict(width=2, color='white'))
                ))

        # Líneas de división y anotaciones
        fig.update_layout(
            title="<b>MATRIZ DE KRALJIC ESTRATÉGICA</b>",
            xaxis=dict(title="IMPACTO FINANCIERO", range=[0, 11], dtick=1, gridcolor='white'),
            yaxis=dict(title="RIESGO DE SUMINISTRO", range=[0, 11], dtick=1, gridcolor='white'),
            shapes=[
                dict(type="line", x0=5.5, y0=0, x1=5.5, y1=11, line=dict(color="black", width=2, dash="dot")),
                dict(type="line", x0=0, y0=5.5, x1=11, y1=5.5, line=dict(color="black", width=2, dash="dot"))
            ],
            annotations=[
                dict(x=2.75, y=10.5, text="⚠️ CUELLO DE BOTELLA", showarrow=False, font=dict(size=14, color="#B45309", family="Arial Black")),
                dict(x=8.25, y=10.5, text="🔥 ESTRATÉGICO", showarrow=False, font=dict(size=14, color="#B91C1C", family="Arial Black")),
                dict(x=2.75, y=0.5, text="⚙️ NO CRÍTICO", showarrow=False, font=dict(size=14, color="#475569", family="Arial Black")),
                dict(x=8.25, y=0.5, text="💰 APALANCAMIENTO", showarrow=False, font=dict(size=14, color="#047857", family="Arial Black"))
            ],
            plot_bgcolor='white', height=700, margin=dict(l=0, r=0, t=50, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)

    with m2:
        st.markdown("### Gasto por Categoría")
        gasto_cat = res.groupby('Categoría')['Gasto'].sum().sort_values(ascending=True)
        fig_bar = go.Figure(go.Bar(x=gasto_cat.values, y=gasto_cat.index, orientation='h', marker_color='#1E293B'))
        fig_bar.update_layout(height=400, plot_bgcolor='white', margin=dict(t=0, b=0))
        st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()
    st.subheader("📋 Estrategias por Cuadrante")
    for q in ['Estratégico', 'Apalancamiento', 'Cuello de Botella', 'No Crítico']:
        items = res[res['Cuadrante'] == q]
        if not items.empty:
            with st.expander(f"Ver {q.upper()}"):
                st.table(items[['Subcategoría', 'Gasto']].rename(columns={'Gasto': 'Gasto Total (€)'}))
    
    st.button("⬅️ VOLVER A GESTIÓN", on_click=ir_a_gestion)
