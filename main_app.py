import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date
import io

# ── 1. CONFIGURACIÓN DE NIVEL PROFESIONAL ──
st.set_page_config(
    page_title="Purchasing Strategic Dashboard | Elymar Estévez",
    page_icon="https://img.icons8.com/fluency/96/strategy.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── 2. ESTILOS CSS PERSONALIZADOS (Look & Feel Compras 4.0) ──
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .main { background-color: #f8fafc; }
        .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; background-color: #1E293B; color: white; border: none; height: 3em; }
        .stTabs [data-baseweb="tab"] { font-weight: 700; font-size: 1.1rem; }
    </style>
""", unsafe_allow_html=True)

# ── 3. ENCABEZADO ──
st.markdown("""
    <div style="background-color: #0F172A; padding: 25px; border-radius: 15px; margin-bottom: 25px; border-left: 8px solid #3B82F6;">
        <h1 style="color: white; margin: 0; font-size: 2.2rem; font-weight: 800;">
            Purchasing Strategic Dashboard <span style="font-size: 0.9rem; color: #3B82F6; vertical-align: middle; border: 1px solid #3B82F6; padding: 2px 8px; border-radius: 10px; margin-left: 10px;">V4.0</span>
        </h1>
        <p style="color: #94A3B8; margin: 8px 0 0 0; font-size: 1.1rem;">
            ACOMPAÑANTE DIGITAL: <strong>COMPRAS 4.0</strong> · ELYMAR ESTÉVEZ
        </p>
    </div>
""", unsafe_allow_html=True)

# ── 4. BASE DE DATOS DE REGLAS MAESTRA (TODAS LAS CATEGORÍAS) ──
# Formato: [Lista de palabras clave], Impacto Base, Riesgo Base
RULES_DB = {
    "MATERIA PRIMA ALIMENTACIÓN": [
        (['cacao', 'chocolate', 'frutos secos', 'aceites', 'grasas', 'edulcorantes', 'azucar'], 9, 8),
        (['cereales', 'harinas', 'levaduras', 'aditivos', 'ingredientes', 'ovoproductos'], 8, 7)
    ],
    "PACKAGING": [
        (['laminado', 'flexible', 'envases', 'etiquetas', 'estucheria'], 7, 7),
        (['cartonaje', 'embalaje'], 6, 5),
        (['pallets', 'madera'], 4, 3)
    ],
    "DIRECTOS / INDUSTRIALES": [
        (['acero', 'hierro', 'metales', 'quimicos', 'resinas', 'componentes'], 9, 8),
        (['repuestos', 'mantenimiento', 'mro', 'herramientas'], 5, 6)
    ],
    "SERVICIOS / INDIRECTOS": [
        (['consultoria', 'auditoria', 'legal'], 6, 4),
        (['limpieza', 'seguridad', 'oficina', 'papeleria'], 2, 2),
        (['marketing', 'publicidad', 'viajes'], 5, 3)
    ],
    "LOGÍSTICA": [
        (['fletes', 'transporte', 'maritimo', 'puerto', 'aduana'], 8, 7),
        (['ultima milla', 'paqueteria'], 5, 5)
    ],
    "TECNOLOGÍA (IT)": [
        (['software', 'saas', 'erp', 'cloud', 'servidores'], 8, 7),
        (['hardware', 'laptops', 'telefonia'], 6, 5)
    ],
    "ENERGÍA & UTILITIES": [
        (['electricidad', 'gas', 'agua', 'fuel'], 10, 9)
    ]
}

def get_kraljic_scores(categoria, subcategoria):
    text = f"{categoria} {subcategoria}".lower()
    imp, risk = 5, 5 # Valores neutros por defecto
    
    for cat_name, sub_rules in RULES_DB.items():
        for keywords, i_score, r_score in sub_rules:
            if any(k in text for k in keywords):
                return i_score, r_score
    return imp, risk

# ── 5. BARRA LATERAL ──
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/strategy.png", width=90)
    st.markdown("### Navegación")
    st.divider()
    
    # PLANTILLA COMPLETA
    st.markdown("#### 📥 Plantilla de Categorías")
    example_data = {
        'Proveedor': ['Steel Co', 'Cocoa Global', 'Pack Solution', 'Logistics Pro', 'Soft Systems', 'Power Supply'],
        'Categoría': ['Directos', 'Materia prima Alimentación', 'Packaging', 'Logística', 'Tecnología', 'Energía'],
        'Subcategoría': ['Acero Inox', 'Cacao y chocolate', 'Laminado flexible', 'Fletes Marítimos', 'Software ERP', 'Electricidad'],
        'Gasto Anual (€)': [800000, 450000, 120000, 300000, 150000, 500000]
    }
    df_template = pd.DataFrame(example_data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_template.to_excel(writer, index=False)
    
    st.download_button(
        label="Descargar Plantilla Excel",
        data=output.getvalue(),
        file_name="plantilla_compras_40_completa.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.divider()
    st.caption("Compras 4.0 - El Futuro Digital")

# ── 6. CUERPO DE LA APP ──
t1, t2, t3 = st.tabs(["📥 Gestión de Categorías", "📊 Matriz Interactiva", "💡 Estrategia Digital"])

with t1:
    st.subheader("Entrada de Datos del Portfolio")
    uploaded_file = st.file_uploader("Sube tu archivo (Excel/CSV)", type=['xlsx', 'csv'])
    
    if uploaded_file:
        df_input = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    else:
        df_input = df_template

    data_df = st.data_editor(df_input, num_rows="dynamic", use_container_width=True)

    if st.button("PROCESAR CATEGORÍAS 4.0", type="primary"):
        total_gasto = data_df['Gasto Anual (€)'].sum()
        processed_list = []
        
        for _, row in data_df.iterrows():
            i_base, r_base = get_kraljic_scores(row['Categoría'], row['Subcategoría'])
            
            # Factor de Impacto por Gasto (Pareto 4.0)
            if total_gasto > 0 and (row['Gasto Anual (€)'] / total_gasto) > 0.10:
                i_base = min(10, i_base + 1)
            
            # Cuadrante
            if i_base >= 6 and r_base >= 6: q = 'Estratégico'
            elif i_base >= 6 and r_base < 6: q = 'Apalancamiento'
            elif i_base < 6 and r_base >= 6: q = 'Cuello de Botella'
            else: q = 'No Crítico'
            
            processed_list.append({**row, 'Impacto': i_base, 'Riesgo': r_base, 'Cuadrante': q})
        
        st.session_state['data'] = pd.DataFrame(processed_list)
        st.success("Análisis omnicategoría finalizado.")

with t2:
    if 'data' in st.session_state:
        df = st.session_state['data']
        
        fig = go.Figure()
        colors = {'Estratégico': '#EF4444', 'Apalancamiento': '#10B981', 'Cuello de Botella': '#F59E0B', 'No Crítico': '#64748B'}
        
        for quad, color in colors.items():
            dff = df[df['Cuadrante'] == quad]
            if not dff.empty:
                fig.add_trace(go.Scatter(
                    x=dff['Impacto'], y=dff['Riesgo'],
                    mode='markers+text',
                    name=quad,
                    text=dff['Subcategoría'],
                    marker=dict(size=dff['Gasto Anual (€)']/df['Gasto Anual (€)'].max()*50 + 20, color=color, opacity=0.8),
                    textposition="top center"
                ))

        fig.update_layout(
            title="Matriz de Kraljic Omnicategoría",
            xaxis=dict(title="Impacto Financiero", range=[0, 11]),
            yaxis=dict(title="Riesgo de Suministro", range=[0, 11]),
            shapes=[
                dict(type="line", x0=5.5, y0=0, x1=5.5, y1=11, line=dict(color="gray", dash="dash")),
                dict(type="line", x0=0, y0=5.5, x1=11, y1=5.5, line=dict(color="gray", dash="dash"))
            ],
            template="plotly_white", height=700
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Carga datos para generar la matriz.")

with t3:
    if 'data' in st.session_state:
        df = st.session_state['data']
        for q in ['Estratégico', 'Apalancamiento', 'Cuello de Botella', 'No Crítico']:
            items = df[df['Cuadrante'] == q]
            if not items.empty:
                with st.expander(f"Estrategia 4.0 para {q.upper()}"):
                    st.table(items[['Proveedor', 'Subcategoría', 'Gasto Anual (€)']])
                    if q == 'Estratégico': st.error("Foco: Relaciones asociativas, gestión de la demanda y planes de contingencia.")
                    elif q == 'Apalancamiento': st.success("Foco: Búsqueda de escala, licitaciones digitales y optimización de precios.")
                    elif q == 'Cuello de Botella': st.warning("Foco: Asegurar volumen, rediseñar especificaciones y diversificar proveedores.")
                    else: st.info("Foco: Automatización logística (E-procurement) y reducción de burocracia.")
