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

# Inicialización de la navegación
if 'seccion_activa' not in st.session_state:
    st.session_state.seccion_activa = "Gestion"

def ir_a_matriz(): st.session_state.seccion_activa = "Matriz"
def ir_a_gestion(): st.session_state.seccion_activa = "Gestion"

# Estilos CSS Avanzados
st.markdown("""
    <style>
        .main { background-color: #f8fafc; }
        .stMetric { background-color: white; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .stButton > button { border-radius: 8px; font-weight: bold; height: 3.5em; width: 100%; transition: all 0.3s; }
        .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        [data-testid="stExpander"] { border: 1px solid #e2e8f0; border-radius: 10px; background-color: white; }
    </style>
""", unsafe_allow_html=True)

# ── 2. MARCA PERSONAL (ENCABEZADO) ──
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
            <h1 style="color: white; margin: 0; font-size: 2.2rem; font-weight: 800;">Purchasing Strategic Dashboard V4.5</h1>
            <p style="color: #94A3B8; margin: 5px 0 0 0; font-size: 1.1rem;">ESTRATEGIA DE COMPRAS 4.0 · POR <strong>ELYMAR ESTÉVEZ</strong></p>
        </div>
    </div>
""", unsafe_allow_html=True)

# ── 3. MOTOR DE INTELIGENCIA ESTRATÉGICA ──
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

# ── 4. NAVEGACIÓN SUPERIOR ──
c_nav1, c_nav2 = st.columns(2)
with c_nav1:
    if st.button("📥 1. GESTIÓN DE DATOS", type="primary" if st.session_state.seccion_activa == "Gestion" else "secondary"):
        ir_a_gestion()
        st.rerun()
with c_nav2:
    if st.button("📊 2. MATRIZ Y ESTRATEGIA", type="primary" if st.session_state.seccion_activa == "Matriz" else "secondary"):
        if 'data_final' in st.session_state:
            ir_a_matriz()
            st.rerun()
        else: st.warning("⚠️ Procesa los datos primero.")

st.divider()

# ── 5. SECCIÓN GESTIÓN DE DATOS ──
if st.session_state.seccion_activa == "Gestion":
    st.subheader("Carga y Validación")
    archivo = st.file_uploader("Sube tu archivo Excel o CSV", type=['xlsx', 'csv'])
    
    # Datos de ejemplo por si no hay carga
    df_temp = pd.DataFrame({'Subcategoría': ['Cacao', 'Cacao', 'Cartón'], 'Gasto Anual (€)': [500000, 700000, 200000]})
    df_input = pd.read_excel(archivo) if archivo and archivo.name.endswith('.xlsx') else (pd.read_csv(archivo) if archivo else df_temp)
    
    if 'Categoría' not in df_input.columns:
        df_input['Categoría'] = df_input['Subcategoría'].apply(sugerir_cat)
    
    st.info("💡 Puedes editar las categorías o gastos directamente en la tabla de abajo.")
    df_editor = st.data_editor(df_input, num_rows="dynamic", use_container_width=True)
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("🚀 PROCESAR Y CONSOLIDAR"):
            # Consolidación: Sumar gasto por subcategoría repetida
            df_consolidado = df_editor.groupby('Subcategoría').agg({'Gasto Anual (€)': 'sum', 'Categoría': 'first'}).reset_index()
            total_g = df_consolidado['Gasto Anual (€)'].sum()
            final_list = []
            
            for _, row in df_consolidado.iterrows():
                i_b, r_b = obtener_scores_base(row['Categoría'])
                g = row['Gasto Anual (€)']
                # Ajuste impacto si representa >15% del gasto
                impacto = min(10, i_b + 1) if (g/total_g) > 0.15 else i_b
                
                if impacto >= 6 and r_b >= 6: q = 'Estratégico'
                elif impacto >= 6 and r_b < 6: q = 'Apalancamiento'
                elif impacto < 6 and r_b >= 6: q = 'Cuello de Botella'
                else: q = 'No Crítico'
                
                final_list.append({'Categoría': row['Categoría'], 'Subcategoría': row['Subcategoría'], 'Gasto': g, 'Impacto': impacto, 'Riesgo': r_b, 'Cuadrante': q})
            
            st.session_state['data_final'] = pd.DataFrame(final_list)
            st.success("✅ Datos consolidados correctamente.")
            
    with col_b2:
        if 'data_final' in st.session_state:
            st.button("📊 IR A RESULTADOS", on_click=ir_a_matriz, type="primary")

# ── 6. SECCIÓN MATRIZ Y ESTRATEGIA ──
elif st.session_state.seccion_activa == "Matriz":
    res = st.session_state['data_final']
    
    # KPIs Rápidos
    c1, c2, c3 = st.columns(3)
    c1.metric("Gasto Total Consolidado", f"{res['Gasto'].sum():,.0f} €")
    c2.metric("Subcategorías Analizadas", len(res))
    c3.metric("Riesgo Medio", round(res['Riesgo'].mean(), 1))

    st.divider()
    st.info("💡 **INTERACCIÓN:** La matriz es interactiva. Desplaza el ratón por los puntos para identificar las subcategorías.")

    m1, m2 = st.columns([2, 1])
    with m1:
        fig = go.Figure()
        
        # Fondos de Cuadrantes
        fig.add_shape(type="rect", x0=5.5, y0=0, x1=11, y1=5.5, fillcolor="rgba(16, 185, 129, 0.08)", line_width=0, layer="below") # Apalancamiento
        fig.add_shape(type="rect", x0=5.5, y0=5.5, x1=11, y1=11, fillcolor="rgba(239, 68, 68, 0.08)", line_width=0, layer="below") # Estratégico
        fig.add_shape(type="rect", x0=0, y0=5.5, x1=5.5, y1=11, fillcolor="rgba(245, 158, 11, 0.08)", line_width=0, layer="below") # Cuello Botella
        fig.add_shape(type="rect", x0=0, y0=0, x1=5.5, y1=5.5, fillcolor="rgba(100, 116, 139, 0.08)", line_width=0, layer="below") # No Crítico

        colores = {'Estratégico': '#EF4444', 'Apalancamiento': '#10B981', 'Cuello de Botella': '#F59E0B', 'No Crítico': '#64748B'}
        for quad, color in colores.items():
            d = res[res['Cuadrante'] == quad]
            if not d.empty:
                fig.add_trace(go.Scatter(
                    x=d['Impacto'], y=d['Riesgo'], mode='markers', name=quad,
                    hovertemplate="<b>%{customdata[0]}</b><br>Gasto: %{customdata[1]:,.0f}€<extra></extra>",
                    customdata=list(zip(d['Subcategoría'], d['Gasto'])),
                    marker=dict(size=d['Gasto']/res['Gasto'].max()*50 + 15, color=color, opacity=0.9, line=dict(width=1.5, color='white'))
                ))

        fig.update_layout(
            title="<b>MATRIZ DE KRALJIC CONSOLIDADA</b>",
            xaxis=dict(title="IMPACTO FINANCIERO", range=[0, 11], dtick=1, gridcolor='#f1f5f9'),
            yaxis=dict(title="RIESGO DE SUMINISTRO", range=[0, 11], dtick=1, gridcolor='#f1f5f9'),
            shapes=[
                dict(type="line", x0=5.5, y0=0, x1=5.5, y1=11, line=dict(color="#94a3b8", width=2, dash="dot")),
                dict(type="line", x0=0, y0=5.5, x1=11, y1=5.5, line=dict(color="#94a3b8", width=2, dash="dot"))
            ],
            annotations=[
                dict(x=2.75, y=10.3, text="⚠️ CUELLO DE BOTELLA", showarrow=False, font=dict(size=13, color="#B45309", family="Arial Black")),
                dict(x=8.25, y=10.3, text="🔥 ESTRATÉGICO", showarrow=False, font=dict(size=13, color="#B91C1C", family="Arial Black")),
                dict(x=2.75, y=0.7, text="⚙️ NO CRÍTICO", showarrow=False, font=dict(size=13, color="#475569", family="Arial Black")),
                dict(x=8.25, y=0.7, text="💰 APALANCAMIENTO", showarrow=False, font=dict(size=13, color="#047857", family="Arial Black"))
            ],
            plot_bgcolor='white', height=650, margin=dict(l=0, r=0, t=50, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)

    with m2:
        st.markdown("### Gasto por Categoría")
        gasto_cat = res.groupby('Categoría')['Gasto'].sum().sort_values(ascending=True)
        fig_bar = go.Figure(go.Bar(x=gasto_cat.values, y=gasto_cat.index, orientation='h', marker_color='#1E293B'))
        fig_bar.update_layout(height=400, plot_bgcolor='white', margin=dict(t=0, b=0), xaxis=dict(showticklabels=False))
        st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()
    st.subheader("📋 Recomendaciones y Detalle por Cuadrante")
    
    for q in ['Estratégico', 'Apalancamiento', 'Cuello de Botella', 'No Crítico']:
        items = res[res['Cuadrante'] == q]
        if not items.empty:
            with st.expander(f"🛒 Ver {q.upper()} ({len(items)} items)"):
                # TABLA CON AJUSTE AUTOMÁTICO DE COLUMNAS
                st.dataframe(
                    items[['Subcategoría', 'Gasto']].rename(columns={'Gasto': 'Gasto Total (€)'}),
                    hide_index=True,
                    use_container_width=False, # Esto fuerza a que no se estire innecesariamente
                    column_config={
                        "Subcategoría": st.column_config.TextColumn("Subcategoría", width="medium"),
                        "Gasto Total (€)": st.column_config.NumberColumn("Gasto Total (€)", format="%.2f €", width="small")
                    }
                )
                
                if q == 'Estratégico': st.error("🎯 Estrategia: Alianzas, integración de procesos y contratos a largo plazo.")
                elif q == 'Apalancamiento': st.success("🎯 Estrategia: Licitaciones competitivas y optimización de volumen.")
                elif q == 'Cuello de Botella': st.warning("🎯 Estrategia: Asegurar stock, rediseño o búsqueda de sustitutos.")
                else: st.info("🎯 Estrategia: Automatización, simplificación y tarjetas de compra.")
    
    st.write("")
    st.button("⬅️ VOLVER A GESTIÓN", on_click=ir_a_gestion)
