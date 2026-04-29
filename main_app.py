import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import base64

# ── 1. CONFIGURACIÓN TÉCNICA DEL DASHBOARD ──
st.set_page_config(
    page_title="Purchasing Intelligence Hub | Elymar Estévez",
    page_icon="📈",
    layout="wide"
)

# Persistencia de estado (Session State)
if 'seccion_activa' not in st.session_state:
    st.session_state.seccion_activa = "Gestion"

def navegar_a(seccion):
    st.session_state.seccion_activa = seccion

# Estilos de Interfaz de Usuario (UI)
st.markdown("""
    <style>
        .main { background-color: #f1f5f9; }
        .stMetric { background-color: white; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; }
        .stButton > button { border-radius: 8px; font-weight: bold; height: 3.5em; width: 100%; transition: all 0.2s; }
        .stButton > button:hover { border: 2px solid #3B82F6; color: #3B82F6; }
        .header-container { background-color: #0F172A; padding: 2rem; border-radius: 1rem; color: white; display: flex; align-items: center; margin-bottom: 2rem; border-left: 10px solid #3B82F6; }
    </style>
""", unsafe_allow_html=True)

# ── 2. BRANDING Y MARCA PERSONAL ──
def get_base64_img(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    return "https://img.icons8.com/fluency/96/businesswoman.png"

foto_base64 = get_base64_img("elymar.png")

st.markdown(f"""
    <div class="header-container">
        <img src="{foto_base64}" style="width: 90px; height: 90px; border-radius: 50%; border: 3px solid #3B82F6; margin-right: 20px; object-fit: cover;">
        <div>
            <h1 style="margin:0; font-size: 2rem;">Purchasing Strategic Dashboard V5.2</h1>
            <p style="margin:0; opacity: 0.8; font-size: 1.1rem;">ELYMAR ESTÉVEZ | Senior Strategy Lead</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# ── 3. LÓGICA DE NEGOCIO (ESTRATEGIA DE COMPRAS) ──
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

# ── 4. BARRA DE NAVEGACIÓN ──
col_n1, col_n2 = st.columns(2)
with col_n1:
    if st.button("📥 GESTIÓN Y CARGA", type="primary" if st.session_state.seccion_activa == "Gestion" else "secondary"):
        navegar_a("Gestion")
        st.rerun()
with col_n2:
    if st.button("📊 MATRIZ ESTRATÉGICA", type="primary" if st.session_state.seccion_activa == "Matriz" else "secondary"):
        if 'data_final' in st.session_state:
            navegar_a("Matriz")
            st.rerun()
        else: st.warning("Carga y procesa datos primero.")

st.write("---")

# ── 5. SECCIÓN 1: GESTIÓN DE DATOS ──
if st.session_state.seccion_activa == "Gestion":
    st.subheader("Entrada de Datos Consolidada")
    archivo = st.file_uploader("Sube tu Excel o CSV", type=['xlsx', 'csv'])
    
    # Datos por defecto (Placeholder)
    df_temp = pd.DataFrame({'Subcategoría': ['Cacao', 'Cacao', 'Packaging'], 'Gasto Anual (€)': [500000.0, 750000.0, 300000.0]})
    df_input = pd.read_excel(archivo) if archivo and archivo.name.endswith('.xlsx') else (pd.read_csv(archivo) if archivo else df_temp)
    
    if 'Categoría' not in df_input.columns:
        df_input['Categoría'] = df_input['Subcategoría'].apply(sugerir_cat)
    
    st.markdown("##### Editor de Datos (Ajusta categorías y gastos)")
    df_editor = st.data_editor(df_input, num_rows="dynamic", use_container_width=True)
    
    if st.button("🚀 PROCESAR Y GENERAR ESTRATEGIA"):
        # Consolidación de datos repetidos
        df_cons = df_editor.groupby('Subcategoría').agg({'Gasto Anual (€)': 'sum', 'Categoría': 'first'}).reset_index()
        total_g = df_cons['Gasto Anual (€)'].sum()
        final_rows = []
        
        for _, row in df_cons.iterrows():
            i_b, r_b = obtener_scores_base(row['Categoría'])
            g = row['Gasto Anual (€)']
            impacto = min(10, i_b + 1) if (g/total_g) > 0.15 else i_b
            
            # Determinación de Cuadrante
            if impacto >= 6 and r_b >= 6: q = 'Estratégico'
            elif impacto >= 6 and r_b < 6: q = 'Apalancamiento'
            elif impacto < 6 and r_b >= 6: q = 'Cuello de Botella'
            else: q = 'No Crítico'
            
            final_rows.append({'Categoría': row['Categoría'], 'Subcategoría': row['Subcategoría'], 'Gasto': g, 'Impacto': impacto, 'Riesgo': r_b, 'Cuadrante': q})
        
        st.session_state['data_final'] = pd.DataFrame(final_rows)
        st.success("Análisis completado. ¡Ve a la pestaña de Matriz!")
        st.balloons()

# ── 6. SECCIÓN 2: MATRIZ Y RESULTADOS ──
elif st.session_state.seccion_activa == "Matriz":
    res = st.session_state['data_final']
    
    # KPIs con formato de miles para visualización directa
    c1, c2, c3 = st.columns(3)
    c1.metric("Gasto Total", f"{res['Gasto'].sum():,.2f} €")
    c2.metric("Items Analizados", len(res))
    c3.metric("Riesgo Promedio", f"{res['Riesgo'].mean():.1f} / 10")

    st.divider()

    m1, m2 = st.columns([2, 1])
    
    with m1:
        fig = go.Figure()
        # Capas de fondo (Cuadrantes)
        fig.add_shape(type="rect", x0=5.5, y0=0, x1=11, y1=5.5, fillcolor="rgba(16, 185, 129, 0.1)", line_width=0, layer="below")
        fig.add_shape(type="rect", x0=5.5, y0=5.5, x1=11, y1=11, fillcolor="rgba(239, 68, 68, 0.1)", line_width=0, layer="below")
        fig.add_shape(type="rect", x0=0, y0=5.5, x1=5.5, y1=11, fillcolor="rgba(245, 158, 11, 0.1)", line_width=0, layer="below")
        fig.add_shape(type="rect", x0=0, y0=0, x1=5.5, y1=5.5, fillcolor="rgba(100, 116, 139, 0.1)", line_width=0, layer="below")

        colores = {'Estratégico': '#EF4444', 'Apalancamiento': '#10B981', 'Cuello de Botella': '#F59E0B', 'No Crítico': '#64748B'}
        for quad, color in colores.items():
            d = res[res['Cuadrante'] == quad]
            if not d.empty:
                fig.add_trace(go.Scatter(
                    x=d['Impacto'], y=d['Riesgo'], mode='markers', name=quad,
                    hovertemplate="<b>%{customdata[0]}</b><br>Gasto: %{customdata[1]:,.2f}€<extra></extra>",
                    customdata=list(zip(d['Subcategoría'], d['Gasto'])),
                    marker=dict(size=d['Gasto']/res['Gasto'].max()*50 + 20, color=color, opacity=0.9, line=dict(width=2, color='white'))
                ))
        
        fig.update_layout(
            title="MATRIZ DE KRALJIC ESTRATÉGICA",
            xaxis=dict(title="IMPACTO FINANCIERO", range=[0, 11], gridcolor="#e2e8f0"),
            yaxis=dict(title="RIESGO DE SUMINISTRO", range=[0, 11], gridcolor="#e2e8f0"),
            plot_bgcolor='white', height=600,
            shapes=[
                dict(type="line", x0=5.5, y0=0, x1=5.5, y1=11, line=dict(color="black", width=2, dash="dot")),
                dict(type="line", x0=0, y0=5.5, x1=11, y1=5.5, line=dict(color="black", width=2, dash="dot"))
            ]
        )
        st.plotly_chart(fig, use_container_width=True)

    with m2:
        st.markdown("### Mix de Gasto")
        gasto_cat = res.groupby('Categoría')['Gasto'].sum().sort_values()
        fig_bar = go.Figure(go.Bar(x=gasto_cat.values, y=gasto_cat.index, orientation='h', marker_color='#1E293B'))
        fig_bar.update_layout(height=400, plot_bgcolor='white', margin=dict(t=20, b=20, l=0, r=0))
        st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("📋 Recomendaciones Detalladas")
    for q in ['Estratégico', 'Apalancamiento', 'Cuello de Botella', 'No Crítico']:
        items = res[res['Cuadrante'] == q]
        if not items.empty:
            with st.expander(f"Items en {q.upper()}"):
                # TABLA AJUSTADA: Eliminamos el problema del formato raro
                st.dataframe(
                    items[['Subcategoría', 'Gasto']].rename(columns={'Gasto': 'Gasto Total (€)'}),
                    hide_index=True,
                    use_container_width=False,
                    column_config={
                        "Subcategoría": st.column_config.TextColumn("Subcategoría", width=300),
                        "Gasto Total (€)": st.column_config.NumberColumn(
                            "Gasto Total (€)",
                            format="%.2f €", # Esto permite decimales y símbolo
                            width=220        # Suficiente ancho para miles
                        )
                    }
                )
                if q == 'Estratégico': st.error("Estrategia: Alianzas y contratos a largo plazo.")
                elif q == 'Apalancamiento': st.success("Estrategia: Licitaciones y optimización de precio.")
                elif q == 'Cuello de Botella': st.warning("Estrategia: Asegurar stock y buscar sustitutos.")
                else: st.info("Estrategia: Simplificación y automatización de procesos.")

    st.button("⬅️ VOLVER A GESTIÓN", on_click=navegar_a, args=("Gestion",))
