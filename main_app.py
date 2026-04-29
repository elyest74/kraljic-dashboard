import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io

# ── 1. CONFIGURACIÓN DE PÁGINA ──
st.set_page_config(
    page_title="Sourcing Intelligence Hub | Elymar Estévez",
    page_icon="🏗️",
    layout="wide"
)

# CSS Personalizado para un look profesional
st.markdown("""
    <style>
        .stButton>button { width: 100%; border-radius: 5px; height: 3em; font-weight: bold; }
        .stDownloadButton>button { width: 100%; background-color: #3B82F6 !important; color: white !important; }
        .main-header { color: #1E293B; font-size: 2.2rem; font-weight: 800; margin-bottom: 1rem; border-bottom: 2px solid #3B82F6; padding-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# ── 2. BARRA LATERAL: CONFIGURACIÓN Y PLANTILLA ──
with st.sidebar:
    st.title("⚙️ Configuración")
    
    st.subheader("1. Plantilla de Datos")
    # Generamos el CSV de la plantilla en memoria
    template_df = pd.DataFrame(columns=['Subcategoría', 'Gasto Anual (€)', 'Categoría'])
    # Datos de ejemplo opcionales en la plantilla
    template_df.loc[0] = ['Ejemplo Materia Prima', 1500000.0, 'MATERIA PRIMA ALIMENTACIÓN']
    
    buffer = io.BytesIO()
    template_df.to_csv(buffer, index=False, encoding='utf-8-sig')
    
    st.download_button(
        label="📥 Descargar Plantilla Excel/CSV",
        data=buffer.getvalue(),
        file_name="plantilla_compras_kraljic.csv",
        mime="text/csv",
        help="Descarga este archivo, rellénalo y súbelo en la sección de gestión."
    )
    
    st.divider()
    
    menu = st.radio(
        "2. Navegación:",
        ["Gestión de Datos", "Análisis de Matriz"],
        index=0
    )
    
    st.divider()
    st.info("Desarrollado por Elymar Estévez para optimización de Sourcing Estratégico.")

# ── 3. LÓGICA DE CATEGORIZACIÓN ──
DATABASE_INTEL = {
    "MATERIA PRIMA ALIMENTACIÓN": ['cacao', 'chocolate', 'aceite', 'grasa', 'leche', 'azucar'],
    "PACKAGING": ['carton', 'film', 'etiqueta', 'envase', 'pallet'],
    "LOGÍSTICA": ['transporte', 'flete', 'almacen']
}

def sugerir_cat(subcat):
    sub_low = str(subcat).lower()
    for cat, keywords in DATABASE_INTEL.items():
        if any(k in sub_low for k in keywords): return cat
    return "OTRAS CATEGORÍAS"

# ── 4. PANTALLA 1: GESTIÓN DE DATOS ──
if menu == "Gestión de Datos":
    st.markdown("<h1 class='main-header'>📥 Gestión y Carga de Gastos</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        archivo = st.file_uploader("Sube tu archivo completado", type=['xlsx', 'csv'])
    with col2:
        st.write("") # Espaciador
        st.write("¿No tienes el archivo? Usa el botón azul de la izquierda para descargar la plantilla.")

    # Carga de datos
    if archivo:
        if archivo.name.endswith('.xlsx'):
            df_input = pd.read_excel(archivo)
        else:
            df_input = pd.read_csv(archivo)
    else:
        # Datos por defecto para que la app no se rompa
        df_input = pd.DataFrame({
            'Subcategoría': ['Masa de Cacao', 'Cajas Cartón'],
            'Gasto Anual (€)': [5000000.0, 850000.0],
            'Categoría': ['MATERIA PRIMA ALIMENTACIÓN', 'PACKAGING']
        })

    st.subheader("📝 Editor de Datos en Tiempo Real")
    df_editor = st.data_editor(df_input, num_rows="dynamic", use_container_width=True)

    if st.button("🚀 PROCESAR ANÁLISIS ESTRATÉGICO"):
        # Limpieza y Consolidación
        df_cons = df_editor.copy()
        df_cons['Gasto Anual (€)'] = pd.to_numeric(df_cons['Gasto Anual (€)'], errors='coerce').fillna(0)
        df_cons = df_cons.groupby('Subcategoría').agg({'Gasto Anual (€)': 'sum', 'Categoría': 'first'}).reset_index()
        
        total_g = df_cons['Gasto Anual (€)'].sum()
        
        final_list = []
        for _, row in df_cons.iterrows():
            g = row['Gasto Anual (€)']
            # Lógica de impacto: > 15% del gasto es estratégico
            impacto = 9 if (g/total_g) > 0.15 else (6 if (g/total_g) > 0.05 else 3)
            # Lógica de riesgo por categoría
            riesgo = 8 if "ALIMENTACIÓN" in str(row['Categoría']).upper() else 4
            
            if impacto >= 6 and riesgo >= 6: q = 'Estratégico'
            elif impacto >= 6: q = 'Apalancamiento'
            elif riesgo >= 6: q = 'Cuello de Botella'
            else: q = 'No Crítico'
            
            final_list.append({
                'Categoría': row['Categoría'], 'Subcategoría': row['Subcategoría'],
                'Gasto': g, 'Impacto': impacto, 'Riesgo': riesgo, 'Cuadrante': q
            })
        
        st.session_state['data_final'] = pd.DataFrame(final_list)
        st.success("✅ Análisis completado. Cambia a 'Análisis de Matriz' en el menú lateral.")
        st.balloons()

# ── 5. PANTALLA 2: ANÁLISIS DE MATRIZ ──
elif menu == "Análisis de Matriz":
    st.markdown("<h1 class='main-header'>📊 Dashboard de Toma de Decisiones</h1>", unsafe_allow_html=True)
    
    if 'data_final' not in st.session_state:
        st.error("⚠️ Por favor, procesa los datos en la sección 'Gestión de Datos' primero.")
    else:
        res = st.session_state['data_final']
        
        # Métricas Principales
        m1, m2, m3 = st.columns(3)
        m1.metric("Gasto Total Anual", f"{res['Gasto'].sum():,.2f} €")
        m2.metric("Items Analizados", len(res))
        m3.metric("Riesgo de Suministro", "Moderado" if res['Riesgo'].mean() < 6 else "Crítico")

        st.divider()

        # Matriz de Kraljic
        fig = go.Figure()
        # Zonas de color
        fig.add_shape(type="rect", x0=5.5, y0=0, x1=11, y1=5.5, fillcolor="#10B981", opacity=0.1, line_width=0)
        fig.add_shape(type="rect", x0=5.5, y0=5.5, x1=11, y1=11, fillcolor="#EF4444", opacity=0.1, line_width=0)
        fig.add_shape(type="rect", x0=0, y0=5.5, x1=5.5, y1=11, fillcolor="#F59E0B", opacity=0.1, line_width=0)
        fig.add_shape(type="rect", x0=0, y0=0, x1=5.5, y1=5.5, fillcolor="#64748B", opacity=0.1, line_width=0)

        fig.add_trace(go.Scatter(
            x=res['Impacto'], y=res['Riesgo'], mode='markers+text',
            text=res['Subcategoría'], textposition="top center",
            marker=dict(size=res['Gasto']/res['Gasto'].max()*60 + 20, color='#1E293B', line=dict(width=2, color='white')),
            hovertemplate="Sub: %{text}<br>Gasto: %{customdata:,.2f}€",
            customdata=res['Gasto']
        ))
        
        fig.update_layout(
            title="Posicionamiento de Categorías (Kraljic)",
            xaxis=dict(title="Impacto Financiero", range=[0, 11]),
            yaxis=dict(title="Riesgo de Suministro", range=[0, 11]),
            template="plotly_white", height=650
        )
        st.plotly_chart(fig, use_container_width=True)

        # Tablas Detalladas
        st.subheader("📋 Detalle de Gastos y Recomendaciones")
        for q in ['Estratégico', 'Apalancamiento', 'Cuello de Botella', 'No Crítico']:
            items = res[res['Cuadrante'] == q]
            if not items.empty:
                with st.expander(f"🛒 Ver detalle: {q.upper()}"):
                    st.dataframe(
                        items[['Subcategoría', 'Gasto']].rename(columns={'Gasto': 'Gasto (€)'}),
                        hide_index=True,
                        use_container_width=False,
                        column_config={
                            "Subcategoría": st.column_config.TextColumn("Subcategoría", width=350),
                            "Gasto (€)": st.column_config.NumberColumn(
                                "Gasto (€)", 
                                format="%.2f €", # Esto asegura decimales y símbolo
                                width=220        # Ancho para que los miles no se corten
                            )
                        }
                    )
