import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# ── 1. CONFIGURACIÓN DE PÁGINA ──
st.set_page_config(
    page_title="Purchasing Dashboard | Elymar Estévez",
    page_icon="📊",
    layout="wide"
)

# Estilos CSS para asegurar que todo sea legible
st.markdown("""
    <style>
        .stDataFrame { background-color: white; }
        .stMetric { background-color: #ffffff; border-radius: 10px; padding: 15px; border: 1px solid #e6e9ef; }
        .main-header { color: #1E293B; font-size: 2rem; font-weight: 800; margin-bottom: 1rem; }
    </style>
""", unsafe_allow_html=True)

# ── 2. NAVEGACIÓN LATERAL (SEGURA) ──
with st.sidebar:
    st.title("🛡️ Panel de Control")
    st.info("Configura aquí tu análisis")
    menu = st.radio(
        "Selecciona una fase:",
        ["1. Carga y Gestión", "2. Matriz de Kraljic"],
        index=0
    )
    st.divider()
    st.markdown("👨‍💼 **Desarrollado por:**\nElymar Estévez")

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

# ── 4. PANTALLA 1: CARGA Y GESTIÓN ──
if menu == "1. Carga y Gestión":
    st.markdown("<h1 class='main-header'>📥 Gestión de Datos de Compra</h1>", unsafe_allow_html=True)
    
    # --- AQUÍ ESTÁ EL CARGADOR DE DATOS ---
    st.write("### 1. Sube tu archivo")
    archivo = st.file_uploader("Arrastra aquí tu Excel o CSV", type=['xlsx', 'csv'], help="Sube el listado de subcategorías y gastos anuales")
    
    # Si no hay archivo, usamos datos de ejemplo para que la tabla sea visible
    if archivo:
        if archivo.name.endswith('.xlsx'):
            df_input = pd.read_excel(archivo)
        else:
            df_input = pd.read_csv(archivo)
    else:
        st.warning("⚠️ No has subido ningún archivo. Se muestran datos de ejemplo:")
        df_input = pd.DataFrame({
            'Subcategoría': ['Masa de Cacao', 'Mantequilla Cacao', 'Cajas Cartón'],
            'Gasto Anual (€)': [2500000.0, 1800000.0, 450000.0]
        })

    # Autocompletar categorías si no existen
    if 'Categoría' not in df_input.columns:
        df_input['Categoría'] = df_input['Subcategoría'].apply(sugerir_cat)

    st.write("### 2. Valida y Edita los datos")
    df_editor = st.data_editor(df_input, num_rows="dynamic", use_container_width=True)

    # --- BOTÓN DE PROCESADO (CLAVE) ---
    st.divider()
    if st.button("🚀 PROCESAR DATOS Y GENERAR ESTRATEGIA", type="primary", use_container_width=True):
        # Consolidación: Sumamos gastos de subcategorías iguales
        df_cons = df_editor.groupby('Subcategoría').agg({
            'Gasto Anual (€)': 'sum', 
            'Categoría': 'first'
        }).reset_index()
        
        total_g = df_cons['Gasto Anual (€)'].sum()
        
        # Generación de matriz
        final_list = []
        for _, row in df_cons.iterrows():
            g = row['Gasto Anual (€)']
            # Lógica automática: Si es > 10% del gasto, es alto impacto
            impacto = 8 if (g/total_g) > 0.10 else 4
            # Riesgo basado en categoría
            riesgo = 8 if "ALIMENTACIÓN" in row['Categoría'] else 4
            
            # Cuadrante
            if impacto >= 6 and riesgo >= 6: q = 'Estratégico'
            elif impacto >= 6: q = 'Apalancamiento'
            elif riesgo >= 6: q = 'Cuello de Botella'
            else: q = 'No Crítico'
            
            final_list.append({
                'Categoría': row['Categoría'],
                'Subcategoría': row['Subcategoría'],
                'Gasto': g,
                'Impacto': impacto,
                'Riesgo': riesgo,
                'Cuadrante': q
            })
        
        st.session_state['data_final'] = pd.DataFrame(final_list)
        st.success("✅ ¡Datos procesados con éxito! Ahora puedes ir a la sección 'Matriz de Kraljic' en el menú de la izquierda.")
        st.balloons()

# ── 5. PANTALLA 2: MATRIZ Y ESTRATEGIA ──
elif menu == "2. Matriz de Kraljic":
    st.markdown("<h1 class='main-header'>📊 Análisis Estratégico</h1>", unsafe_allow_html=True)
    
    if 'data_final' not in st.session_state:
        st.error("❌ No hay datos procesados. Por favor, vuelve a la sección 'Carga y Gestión'.")
    else:
        res = st.session_state['data_final']
        
        # KPIs
        c1, c2, c3 = st.columns(3)
        c1.metric("Gasto Consolidado", f"{res['Gasto'].sum():,.2f} €")
        c2.metric("Nº Subcategorías", len(res))
        c3.metric("Riesgo Promedio", f"{res['Riesgo'].mean():.1f}")

        st.divider()

        # Gráfico
        fig = go.Figure()
        # Fondos de cuadrantes
        fig.add_shape(type="rect", x0=5.5, y0=0, x1=11, y1=5.5, fillcolor="rgba(16, 185, 129, 0.1)", line_width=0)
        fig.add_shape(type="rect", x0=5.5, y0=5.5, x1=11, y1=11, fillcolor="rgba(239, 68, 68, 0.1)", line_width=0)
        fig.add_shape(type="rect", x0=0, y0=5.5, x1=5.5, y1=11, fillcolor="rgba(245, 158, 11, 0.1)", line_width=0)
        fig.add_shape(type="rect", x0=0, y0=0, x1=5.5, y1=5.5, fillcolor="rgba(100, 116, 139, 0.1)", line_width=0)

        fig.add_trace(go.Scatter(
            x=res['Impacto'], y=res['Riesgo'], mode='markers+text',
            text=res['Subcategoría'], textposition="top center",
            marker=dict(size=res['Gasto']/res['Gasto'].max()*50 + 20, color='#0F172A'),
            hovertemplate="Subcategoría: %{text}<br>Gasto: %{customdata:,.2f}€",
            customdata=res['Gasto']
        ))
        
        fig.update_layout(
            xaxis=dict(title="Impacto Financiero", range=[0, 11]),
            yaxis=dict(title="Riesgo de Suministro", range=[0, 11]),
            height=600, template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.write("### 📋 Recomendaciones por Cuadrante")
        for q in ['Estratégico', 'Apalancamiento', 'Cuello de Botella', 'No Crítico']:
            items = res[res['Cuadrante'] == q]
            if not items.empty:
                with st.expander(f"Items en Cuadrante {q.upper()} ({len(items)})"):
                    st.dataframe(
                        items[['Subcategoría', 'Gasto']].rename(columns={'Gasto': 'Gasto Anual (€)'}),
                        hide_index=True,
                        column_config={
                            "Subcategoría": st.column_config.TextColumn("Subcategoría", width=300),
                            "Gasto Anual (€)": st.column_config.NumberColumn(
                                "Gasto Anual (€)", 
                                format="%.2f €", 
                                width=200 # Ancho ajustado para leer bien los miles
                            )
                        }
                    )
