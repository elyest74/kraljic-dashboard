import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
import os
import base64

# ── 1. CONFIGURACIÓN PROFESIONAL ──
st.set_page_config(
    page_title="Purchasing Strategic Dashboard | Elymar Estévez",
    page_icon="https://img.icons8.com/fluency/96/strategy.png",
    layout="wide"
)

# ── 2. LÓGICA PARA CARGAR TU FOTO ──
def get_base64_img(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    return "https://img.icons8.com/fluency/96/businesswoman.png"

foto_base64 = get_base64_img("elymar.png")

# ── 3. ENCABEZADO PREMIUM ──
st.markdown(f"""
    <div style="background-color: #0F172A; padding: 25px; border-radius: 15px; margin-bottom: 25px; border-left: 8px solid #3B82F6; display: flex; align-items: center;">
        <div style="flex-shrink: 0; margin-right: 25px;">
            <img src="{foto_base64}" style="width: 100px; height: 100px; border-radius: 50%; border: 3px solid #3B82F6; object-fit: cover;">
        </div>
        <div style="flex-grow: 1;">
            <h1 style="color: white; margin: 0; font-size: 2.2rem; font-weight: 800;">Purchasing Strategic Dashboard V4.0</h1>
            <p style="color: #94A3B8; margin: 5px 0 0 0; font-size: 1.1rem;">ACOMPAÑANTE DIGITAL: <strong>COMPRAS 4.0</strong> · POR ELYMAR ESTÉVEZ</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# ── 4. DICCIONARIO MAESTRO DE CATEGORIZACIÓN ──
# Impacto (I) y Riesgo (R) base por subcategoría
DATABASE_INTEL = {
    "MATERIA PRIMA ALIMENTACIÓN": {
        'keywords': ['cacao', 'chocolate', 'frutos secos', 'aceite', 'grasa', 'cereales', 'harina', 'levadura', 'azucar', 'edulcorante', 'aditivo', 'ingrediente', 'ovoproducto'],
        'i': 9, 'r': 8
    },
    "PACKAGING": {
        'keywords': ['cartonaje', 'estucheria', 'laminado', 'embalaje', 'pallet', 'etiqueta', 'envase', 'film', 'botella'],
        'i': 7, 'r': 7
    },
    "LOGÍSTICA": {
        'keywords': ['flete', 'transporte', 'maritimo', 'terrestre', 'aduana', 'almacenaje'],
        'i': 8, 'r': 7
    },
    "ENERGÍA & UTILITIES": {
        'keywords': ['electricidad', 'gas', 'luz', 'agua', 'fuel', 'combustible'],
        'i': 10, 'r': 9
    },
    "TECNOLOGÍA / IT": {
        'keywords': ['software', 'erp', 'cloud', 'saas', 'hardware'],
        'i': 8, 'r': 6
    }
}

def sugerir_categoria_y_scores(subcategoria):
    sub_low = str(subcategoria).lower()
    for cat, data in DATABASE_INTEL.items():
        if any(k in sub_low for k in data['keywords']):
            return cat, data['i'], data['r']
    return "OTRAS CATEGORÍAS", 5, 5

# ── 5. BARRA LATERAL ──
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/strategy.png", width=80)
    st.markdown("### Herramientas de Datos")
    st.divider()
    
    # Plantilla de ejemplo
    df_temp = pd.DataFrame({
        'Subcategoría': ['Cacao', 'Cartonaje', 'Fletes Marítimos'],
        'Gasto Anual (€)': [500000, 120000, 300000]
    })
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_temp.to_excel(writer, index=False)
    
    st.download_button("📥 Descargar Plantilla", output.getvalue(), "plantilla_compras.xlsx")
    st.divider()
    st.caption("Compras 4.0 - Elymar Estévez")

# ── 6. CUERPO PRINCIPAL ──
tab1, tab2 = st.tabs(["📥 Gestión de Datos", "📊 Matriz & Estrategia"])

with tab1:
    st.subheader("Configuración del Portfolio de Compra")
    up_file = st.file_uploader("Sube tu archivo (Excel o CSV)", type=['xlsx', 'csv'])
    
    if up_file:
        df_raw = pd.read_excel(up_file) if up_file.name.endswith('.xlsx') else pd.read_csv(up_file)
    else:
        df_raw = df_temp.copy()

    # Si no tiene columna Categoría, la sugerimos
    if 'Categoría' not in df_raw.columns:
        df_raw['Categoría'] = df_raw['Subcategoría'].apply(lambda x: sugerir_categoria_y_scores(x)[0])

    st.write("Edita las categorías sugeridas si es necesario:")
    data_editor = st.data_editor(df_raw, num_rows="dynamic", use_container_width=True)

    if st.button("🚀 PROCESAR MATRIZ 4.0", type="primary"):
        processed = []
        total_gasto = data_editor['Gasto Anual (€)'].sum()
        
        for _, row in data_editor.iterrows():
            cat_sug, i_base, r_base = sugerir_categoria_y_scores(row['Subcategoría'])
            
            # Usar la categoría que el usuario dejó en el editor
            cat_final = row['Categoría']
            
            # Ajuste de Impacto por Pareto (Gasto relativo)
            gasto = row['Gasto Anual (€)']
            if total_gasto > 0 and (gasto / total_gasto) > 0.15:
                i_base = min(10, i_base + 1)
            
            # Determinación de Cuadrante
            if i_base >= 6 and r_base >= 6: q = 'Estratégico'
            elif i_base >= 6 and r_base < 6: q = 'Apalancamiento'
            elif i_base < 6 and r_base >= 6: q = 'Cuello de Botella'
            else: q = 'No Crítico'
            
            processed.append({
                'Proveedor': row.get('Proveedor', 'N/A'),
                'Categoría': cat_final,
                'Subcategoría': row['Subcategoría'],
                'Gasto': gasto,
                'Impacto': i_base,
                'Riesgo': r_base,
                'Cuadrante': q
            })
        
        st.session_state['results'] = pd.DataFrame(processed)
        st.success("¡Datos procesados! Haz clic en la pestaña 'Matriz & Estrategia'.")

with tab2:
    if 'results' in st.session_state:
        results = st.session_state['results']
        
        # ── KPI'S RÁPIDOS ──
        c1, c2, c3 = st.columns(3)
        c1.metric("Gasto Total", f"{results['Gasto'].sum():,.0f} €")
        c2.metric("Nº Subcategorías", len(results))
        c3.metric("Riesgo Promedio", round(results['Riesgo'].mean(), 1))
        
        st.divider()
        
        # ── MATRIZ DE KRALJIC ──
        col_map, col_list = st.columns([2, 1])
        
        with col_map:
            fig = go.Figure()
            colors = {'Estratégico': '#EF4444', 'Apalancamiento': '#10B981', 'Cuello de Botella': '#F59E0B', 'No Crítico': '#64748B'}
            
            for quad, color in colors.items():
                dff = results[results['Cuadrante'] == quad]
                if not dff.empty:
                    fig.add_trace(go.Scatter(
                        x=dff['Impacto'], y=dff['Riesgo'],
                        mode='markers+text',
                        name=quad,
                        text=dff['Subcategoría'],
                        textposition="top center",
                        marker=dict(size=dff['Gasto']/results['Gasto'].max()*50 + 20, color=color, opacity=0.7)
                    ))

            fig.update_layout(
                title="Matriz de Kraljic Automatizada",
                xaxis=dict(title="Impacto Financiero", range=[0, 11], gridcolor='#E2E8F0'),
                yaxis=dict(title="Riesgo de Suministro", range=[0, 11], gridcolor='#E2E8F0'),
                shapes=[
                    dict(type="line", x0=5.5, y0=0, x1=5.5, y1=11, line=dict(color="#CBD5E1", dash="dash")),
                    dict(type="line", x0=0, y0=5.5, x1=11, y1=5.5, line=dict(color="#CBD5E1", dash="dash"))
                ],
                plot_bgcolor='white', height=600
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col_list:
            st.write("### Gasto por Categoría")
            gasto_cat = results.groupby('Categoría')['Gasto'].sum().sort_values(ascending=False)
            st.bar_chart(gasto_cat)

        st.divider()
        
        # ── ESTRATEGIAS ──
        st.subheader("📋 Recomendaciones Estratégicas 4.0")
        for q in ['Estratégico', 'Apalancamiento', 'Cuello de Botella', 'No Crítico']:
            items = results[results['Cuadrante'] == q]
            if not items.empty:
                with st.expander(f"Ver Estrategia para {q.upper()} ({len(items)} items)"):
                    st.dataframe(items[['Subcategoría', 'Gasto', 'Categoría']])
                    if q == 'Estratégico':
                        st.error("Desarrollar alianzas a largo plazo e integración digital con proveedores clave.")
                    elif q == 'Apalancamiento':
                        st.success("Maximizar poder de compra: Licitaciones agresivas y consolidación de volumen.")
                    elif q == 'Cuello de Botella':
                        st.warning("Asegurar suministro: Búsqueda de sustitutos y creación de stocks de seguridad.")
                    else:
                        st.info("Eficiencia: Automatización de pedidos y reducción de carga administrativa.")
    else:
        st.warning("⚠️ Por favor, carga datos y haz clic en 'PROCESAR ANÁLISIS 4.0' en la pestaña anterior.")
