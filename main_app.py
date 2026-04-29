import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import base64

# ── 1. CONFIGURACIÓN TÉCNICA ──
st.set_page_config(
    page_title="Purchasing Intelligence | Elymar Estévez",
    page_icon="📈",
    layout="wide"
)

# Inicialización forzada del estado de navegación
if 'seccion_activa' not in st.session_state:
    st.session_state.seccion_activa = "Gestion"

# Función para cambiar de pestaña
def cambiar_pestaña(nombre_pestaña):
    st.session_state.seccion_activa = nombre_pestaña

# CSS para que los botones de navegación se vean grandes y claros
st.markdown("""
    <style>
        .main { background-color: #f1f5f9; }
        .stButton > button { 
            border-radius: 10px; 
            font-weight: bold; 
            height: 4em; 
            border: 2px solid #e2e8f0;
        }
        .header-container { 
            background-color: #0F172A; 
            padding: 1.5rem; 
            border-radius: 1rem; 
            color: white; 
            display: flex; 
            align-items: center; 
            margin-bottom: 2rem; 
            border-left: 10px solid #3B82F6; 
        }
    </style>
""", unsafe_allow_html=True)

# ── 2. ENCABEZADO Y MARCA ──
def get_base64_img(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    return "https://img.icons8.com/fluency/96/businesswoman.png"

foto_base64 = get_base64_img("elymar.png")

st.markdown(f"""
    <div class="header-container">
        <img src="{foto_base64}" style="width: 80px; height: 80px; border-radius: 50%; border: 2px solid #3B82F6; margin-right: 20px; object-fit: cover;">
        <div>
            <h1 style="margin:0; font-size: 1.8rem;">Purchasing Strategic Dashboard</h1>
            <p style="margin:0; opacity: 0.8;">POR ELYMAR ESTÉVEZ</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# ── 3. BOTONES DE NAVEGACIÓN (SIEMPRE VISIBLES) ──
col_nav1, col_nav2 = st.columns(2)
with col_nav1:
    # Botón para ir a la CARGA
    if st.button("📥 PASO 1: CARGAR Y EDITAR DATOS", use_container_width=True, 
                 type="primary" if st.session_state.seccion_activa == "Gestion" else "secondary"):
        st.session_state.seccion_activa = "Gestion"
        st.rerun()

with col_nav2:
    # Botón para ir a la MATRIZ
    if st.button("📊 PASO 2: VER MATRIZ Y ESTRATEGIA", use_container_width=True, 
                 type="primary" if st.session_state.seccion_activa == "Matriz" else "secondary"):
        if 'data_final' in st.session_state:
            st.session_state.seccion_activa = "Matriz"
            st.rerun()
        else:
            st.error("⚠️ Primero debes procesar los datos en el Paso 1.")

st.write("---")

# ── 4. LÓGICA DE CATEGORIZACIÓN ──
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

# ── 5. PANTALLA DE GESTIÓN (AQUÍ ESTÁ EL BOTÓN QUE BUSCAS) ──
if st.session_state.seccion_activa == "Gestion":
    st.subheader("📥 Carga de Archivos y Preparación")
    
    archivo = st.file_uploader("Sube tu archivo (Excel o CSV)", type=['xlsx', 'csv'])
    
    # Datos semilla para que la tabla no esté vacía
    df_base = pd.DataFrame({'Subcategoría': ['Cacao', 'Packaging'], 'Gasto Anual (€)': [1250000.0, 450000.0]})
    
    if archivo:
        if archivo.name.endswith('.xlsx'): df_input = pd.read_excel(archivo)
        else: df_input = pd.read_csv(archivo)
    else:
        df_input = df_base

    if 'Categoría' not in df_input.columns:
        df_input['Categoría'] = df_input['Subcategoría'].apply(sugerir_cat)

    st.info("💡 Edita directamente en la tabla si necesitas ajustar alguna categoría o gasto.")
    df_editor = st.data_editor(df_input, num_rows="dynamic", use_container_width=True)

    # ESTE ES EL BOTÓN CLAVE PARA AVANZAR
    if st.button("🚀 PROCESAR DATOS Y GENERAR MATRIZ", size="large"):
        # Consolidación
        df_cons = df_editor.groupby('Subcategoría').agg({'Gasto Anual (€)': 'sum', 'Categoría': 'first'}).reset_index()
        total_g = df_cons['Gasto Anual (€)'].sum()
        
        final_data = []
        for _, row in df_cons.iterrows():
            # Lógica simple de Kraljic para el ejemplo
            g = row['Gasto Anual (€)']
            # Asignamos impacto/riesgo ficticio basado en categoría o aleatorio para el dashboard
            impacto = 8 if (g/total_g) > 0.1 else 4
            riesgo = 7 if "ALIMENTACIÓN" in row['Categoría'] else 3
            
            if impacto >= 6 and riesgo >= 6: q = 'Estratégico'
            elif impacto >= 6: q = 'Apalancamiento'
            elif riesgo >= 6: q = 'Cuello de Botella'
            else: q = 'No Crítico'
            
            final_data.append({
                'Categoría': row['Categoría'], 'Subcategoría': row['Subcategoría'], 
                'Gasto': g, 'Impacto': impacto, 'Riesgo': riesgo, 'Cuadrante': q
            })
        
        st.session_state['data_final'] = pd.DataFrame(final_data)
        st.success("✅ Datos procesados. Haz clic en el botón superior 'VER MATRIZ' para continuar.")
        st.balloons()

# ── 6. PANTALLA DE MATRIZ ──
elif st.session_state.seccion_activa == "Matriz":
    res = st.session_state['data_final']
    
    st.subheader("📊 Análisis de Posicionamiento Estratégico")
    
    # Gráfico Kraljic (Sección visual)
    fig = go.Figure()
    # Cuadrantes... (se mantiene la lógica de colores de la v5.2)
    fig.add_shape(type="rect", x0=5.5, y0=0, x1=11, y1=5.5, fillcolor="rgba(16, 185, 129, 0.1)", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=5.5, y0=5.5, x1=11, y1=11, fillcolor="rgba(239, 68, 68, 0.1)", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=0, y0=5.5, x1=5.5, y1=11, fillcolor="rgba(245, 158, 11, 0.1)", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=0, y0=0, x1=5.5, y1=5.5, fillcolor="rgba(100, 116, 139, 0.1)", line_width=0, layer="below")

    fig.add_trace(go.Scatter(
        x=res['Impacto'], y=res['Riesgo'], mode='markers+text',
        text=res['Subcategoría'], textposition="top center",
        marker=dict(size=res['Gasto']/res['Gasto'].max()*40 + 20, color='#1E293B'),
        hovertemplate="Gasto: %{customdata:,.2f}€", customdata=res['Gasto']
    ))
    
    fig.update_layout(xaxis=dict(title="Impacto", range=[0, 11]), yaxis=dict(title="Riesgo", range=[0, 11]), height=500)
    st.plotly_chart(fig, use_container_width=True)

    # Detalle de Tablas (Con el formato de miles y ancho corregido)
    st.write("### Detalle por Cuadrante")
    for q in ['Estratégico', 'Apalancamiento', 'Cuello de Botella', 'No Crítico']:
        items = res[res['Cuadrante'] == q]
        if not items.empty:
            with st.expander(f"Ver {q.upper()}"):
                st.dataframe(
                    items[['Subcategoría', 'Gasto']].rename(columns={'Gasto': 'Gasto Anual (€)'}),
                    hide_index=True,
                    column_config={
                        "Subcategoría": st.column_config.TextColumn("Subcategoría", width=300),
                        "Gasto Anual (€)": st.column_config.NumberColumn(
                            "Gasto Anual (€)",
                            format="%.2f €", # Esto pone el símbolo y decimales, Streamlit pone el punto de miles
                            width=200
                        )
                    }
                )
