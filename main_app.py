import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import base64

# ── 1. CONFIGURACIÓN INICIAL ──
st.set_page_config(
    page_title="Purchasing Strategy | Elymar Estévez",
    page_icon="📈",
    layout="wide"
)

# Inicializar navegación si no existe
if 'seccion_activa' not in st.session_state:
    st.session_state.seccion_activa = "Gestion"

# CSS Personalizado
st.markdown("""
    <style>
        .main { background-color: #f1f5f9; }
        .header-container { 
            background-color: #0F172A; 
            padding: 1.5rem; 
            border-radius: 1rem; 
            color: white; 
            border-left: 10px solid #3B82F6; 
            margin-bottom: 2rem;
        }
        .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3em; }
    </style>
""", unsafe_allow_html=True)

# ── 2. CABECERA ──
st.markdown(f"""
    <div class="header-container">
        <h1 style="margin:0; font-size: 1.8rem;">Purchasing Strategic Dashboard</h1>
        <p style="margin:0; opacity: 0.8;">POR ELYMAR ESTÉVEZ | Senior Strategy Lead</p>
    </div>
""", unsafe_allow_html=True)

# ── 3. NAVEGACIÓN SUPERIOR ──
c_nav1, c_nav2 = st.columns(2)
with c_nav1:
    if st.button("📥 1. GESTIÓN DE DATOS", type="primary" if st.session_state.seccion_activa == "Gestion" else "secondary"):
        st.session_state.seccion_activa = "Gestion"
        st.rerun()

with c_nav2:
    if st.button("📊 2. VER MATRIZ", type="primary" if st.session_state.seccion_activa == "Matriz" else "secondary"):
        if 'data_final' in st.session_state:
            st.session_state.seccion_activa = "Matriz"
            st.rerun()
        else:
            st.error("⚠️ Primero procesa los datos en la pestaña de Gestión.")

st.divider()

# ── 4. LÓGICA DE APOYO ──
DATABASE_INTEL = {
    "MATERIA PRIMA ALIMENTACIÓN": ['cacao', 'chocolate', 'aceite', 'grasa', 'cereales', 'harina', 'azucar', 'leche', 'cafe'],
    "PACKAGING": ['carton', 'estucheria', 'laminado', 'embalaje', 'pallet', 'etiqueta', 'envase', 'film'],
    "LOGÍSTICA": ['flete', 'transporte', 'maritimo', 'terrestre', 'aduana', 'almacen']
}

def sugerir_cat(subcat):
    sub_low = str(subcat).lower()
    for cat, keywords in DATABASE_INTEL.items():
        if any(k in sub_low for k in keywords): return cat
    return "OTRAS CATEGORÍAS"

# ── 5. SECCIÓN GESTIÓN (CARGA) ──
if st.session_state.seccion_activa == "Gestion":
    st.subheader("Carga y Edición de Datos")
    
    archivo = st.file_uploader("Sube tu archivo Excel o CSV", type=['xlsx', 'csv'])
    
    # Datos de ejemplo para que la app no nazca vacía
    if archivo:
        df_input = pd.read_excel(archivo) if archivo.name.endswith('.xlsx') else pd.read_csv(archivo)
    else:
        df_input = pd.DataFrame({'Subcategoría': ['Cacao', 'Cajas'], 'Gasto Anual (€)': [1000000.0, 250000.0]})

    if 'Categoría' not in df_input.columns:
        df_input['Categoría'] = df_input['Subcategoría'].apply(sugerir_cat)

    # Editor de datos
    df_editor = st.data_editor(df_input, num_rows="dynamic", use_container_width=True)

    if st.button("🚀 PROCESAR Y GUARDAR"):
        # Consolidación: Agrupar por subcategoría y sumar gasto
        df_cons = df_editor.groupby('Subcategoría').agg({'Gasto Anual (€)': 'sum', 'Categoría': 'first'}).reset_index()
        total_g = df_cons['Gasto Anual (€)'].sum()
        
        final_rows = []
        for _, row in df_cons.iterrows():
            g = row['Gasto Anual (€)']
            # Lógica Kraljic simplificada para asegurar funcionamiento
            impacto = 8 if (g/total_g) > 0.1 else 4
            riesgo = 7 if "ALIMENTACIÓN" in row['Categoría'] else 4
            
            q = 'Estratégico' if impacto >= 6 and riesgo >= 6 else ('Apalancamiento' if impacto >= 6 else ('Cuello de Botella' if riesgo >= 6 else 'No Crítico'))
            
            final_rows.append({
                'Categoría': row['Categoría'], 'Subcategoría': row['Subcategoría'], 
                'Gasto': g, 'Impacto': impacto, 'Riesgo': riesgo, 'Cuadrante': q
            })
        
        st.session_state['data_final'] = pd.DataFrame(final_rows)
        st.success("✅ Datos listos. Pulsa 'VER MATRIZ' arriba.")
        st.balloons()

# ── 6. SECCIÓN MATRIZ ──
elif st.session_state.seccion_activa == "Matriz":
    if 'data_final' in st.session_state:
        res = st.session_state['data_final']
        
        # Gráfico Plotly
        fig = go.Figure()
        
        # Dibujar cuadrantes (colores suaves)
        fig.add_shape(type="rect", x0=5.5, y0=0, x1=11, y1=5.5, fillcolor="rgba(16, 185, 129, 0.1)", line_width=0)
        fig.add_shape(type="rect", x0=5.5, y0=5.5, x1=11, y1=11, fillcolor="rgba(239, 68, 68, 0.1)", line_width=0)
        fig.add_shape(type="rect", x0=0, y0=5.5, x1=5.5, y1=11, fillcolor="rgba(245, 158, 11, 0.1)", line_width=0)
        fig.add_shape(type="rect", x0=0, y0=0, x1=5.5, y1=5.5, fillcolor="rgba(100, 116, 139, 0.1)", line_width=0)

        fig.add_trace(go.Scatter(
            x=res['Impacto'], y=res['Riesgo'], mode='markers+text',
            text=res['Subcategoría'], textposition="top center",
            marker=dict(size=25, color='#1E293B'),
            hovertemplate="Gasto: %{customdata:,.2f}€", customdata=res['Gasto']
        ))
        
        fig.update_layout(xaxis_title="Impacto", yaxis_title="Riesgo", height=600, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

        # Tablas de estrategia con el ancho que pediste
        st.write("### Estrategia por Cuadrante")
        for q in ['Estratégico', 'Apalancamiento', 'Cuello de Botella', 'No Crítico']:
            items = res[res['Cuadrante'] == q]
            if not items.empty:
                with st.expander(f"Items en {q.upper()}"):
                    st.dataframe(
                        items[['Subcategoría', 'Gasto']].rename(columns={'Gasto': 'Gasto (€)'}),
                        hide_index=True,
                        column_config={
                            "Subcategoría": st.column_config.TextColumn("Subcategoría", width=300),
                            "Gasto (€)": st.column_config.NumberColumn("Gasto (€)", format="%.2f €", width=200)
                        }
                    )
    else:
        st.warning("No hay datos cargados.")
