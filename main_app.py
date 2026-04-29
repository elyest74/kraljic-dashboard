import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date
import io
import os
import base64

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
        .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; background-color: #1E293B; color: white; border: none; height: 3.2em; }
        .stTabs [data-baseweb="tab"] { font-weight: 700; font-size: 1.05rem; }
        .stMetric { background-color: white; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; }
    </style>
""", unsafe_allow_html=True)

# ── 3. LÓGICA PARA CARGAR TU FOTO (elymar.png) ──
def get_base64_img(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            data = f.read()
        return f"data:image/png;base64,{base64.b64encode(data).decode()}"
    # Icono de respaldo si la foto no está
    return "https://img.icons8.com/fluency/96/businesswoman.png"

foto_base64 = get_base64_img("elymar.png")

# ── 4. ENCABEZADO PREMIUM CON TU MARCA PERSONAL ──
st.markdown(f"""
    <div style="background-color: #0F172A; padding: 25px; border-radius: 15px; margin-bottom: 25px; border-left: 8px solid #3B82F6; display: flex; align-items: center;">
        <div style="flex-shrink: 0; margin-right: 25px;">
            <img src="{foto_base64}" style="width: 100px; height: 100px; border-radius: 50%; border: 3px solid #3B82F6; object-fit: cover; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
        </div>
        <div style="flex-grow: 1;">
            <h1 style="color: white; margin: 0; font-size: 2.3rem; font-weight: 800; letter-spacing: -0.5px;">
                Purchasing Strategic Dashboard <span style="font-size: 0.85rem; color: #3B82F6; vertical-align: middle; border: 1px solid #3B82F6; padding: 3px 10px; border-radius: 12px; margin-left: 12px; font-weight: 400;">V4.0</span>
            </h1>
            <p style="color: #94A3B8; margin: 8px 0 0 0; font-size: 1.2rem; font-weight: 400;">
                ACOMPAÑANTE DIGITAL: <strong>COMPRAS 4.0</strong> · POR ELYMAR ESTÉVEZ
            </p>
        </div>
    </div>
""", unsafe_allow_html=True)

# ── 5. MOTOR DE INTELIGENCIA DE CATEGORIZACIÓN (Omnicategoría) ──
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
        (['repuestos', 'mantenimiento', 'mro'], 5, 6)
    ],
    "LOGÍSTICA / IT / OTROS": [
        (['fletes', 'transporte', 'maritimo', 'aduana'], 8, 7),
        (['software', 'saas', 'erp', 'cloud'], 8, 7),
        (['electricidad', 'gas', 'energia'], 10, 9),
        (['limpieza', 'seguridad', 'oficina'], 2, 2)
    ]
}

def analyze_entry(row, total_spend):
    text = f"{str(row['Categoría'])} {str(row['Subcategoría'])}".lower()
    imp, risk = 5, 5
    for _, sub_rules in RULES_DB.items():
        for keywords, i_s, r_s in sub_rules:
            if any(k in text for k in keywords):
                imp, risk = i_s, r_s
                break
    
    # Factor Pareto: Si gasto > 12% del total, el impacto es crítico
    if total_spend > 0 and (row['Gasto Anual (€)'] / total_spend) > 0.12:
        imp = max(imp, 8)

    if imp >= 6 and risk >= 6: q = 'Estratégico'
    elif imp >= 6 and risk < 6: q = 'Apalancamiento'
    elif imp < 6 and risk >= 6: q = 'Cuello de Botella'
    else: q = 'No Crítico'
    
    return imp, risk, q

# ── 6. BARRA LATERAL ──
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/strategy.png", width=80)
    st.markdown("### Centro de Control")
    st.divider()
    
    # PLANTILLA PARA EL USUARIO
    st.markdown("#### 📥 Preparar Datos")
    df_template = pd.DataFrame({
        'Proveedor': ['Ejemplo S.A.', 'Global Cocoa', 'Pack Center'],
        'Categoría': ['Directos', 'Materia prima Alimentación', 'Packaging'],
        'Subcategoría': ['Acero', 'Cacao', 'Estuchería'],
        'Gasto Anual (€)': [500000, 350000, 95000]
    })
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_template.to_excel(writer, index=False)
    
    st.download_button(
        label="Descargar Plantilla Excel",
        data=output.getvalue(),
        file_name="plantilla_compras40.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.divider()
    st.caption(f"Fecha: {date.today().strftime('%d/%m/%Y')}")

# ── 7. INTERFAZ PRINCIPAL ──
t1, t2, t3 = st.tabs(["📥 Gestión de Datos", "📊 Matriz de Kraljic", "💡 Guía Estratégica"])

with t1:
    st.subheader("Carga de Categorías y Gastos")
    uploaded_file = st.file_uploader("Sube tu archivo (Excel o CSV)", type=['xlsx', 'csv'])
    
    df_actual = pd.read_excel(uploaded_file) if uploaded_file and uploaded_file.name.endswith('.xlsx') else \
                (pd.read_csv(uploaded_file) if uploaded_file else df_template)

    data_df = st.data_editor(df_actual, num_rows="dynamic", use_container_width=True)

    if st.button("PROCESAR ANÁLISIS 4.0", type="primary"):
        total = data_df['Gasto Anual (€)'].sum()
        processed = []
        for _, row in data_df.iterrows():
            i, r, q = analyze_entry(row, total)
            processed.append({**row, 'Impacto': i, 'Riesgo': r, 'Cuadrante': q})
        st.session_state['data'] = pd.DataFrame(processed)
        st.success("¡Análisis omnicategoría listo!")

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
                    textposition="top center",
                    marker=dict(size=dff['Gasto Anual (€)']/df['Gasto Anual (€)'].max()*50 + 20, color=color, opacity=0.7)
                ))

        fig.update_layout(
            title="Matriz de Kraljic (Eje X: Impacto | Eje Y: Riesgo)",
            xaxis=dict(title="Impacto Financiero", range=[0, 11], gridcolor='#e2e8f0'),
            yaxis=dict(title="Riesgo de Suministro", range=[0, 11], gridcolor='#e2e8f0'),
            shapes=[
                dict(type="line", x0=5.5, y0=0, x1=5.5, y1=11, line=dict(color="gray", dash="dash")),
                dict(type="line", x0=0, y0=5.5, x1=11, y1=5.5, line=dict(color="gray", dash="dash"))
            ],
            plot_bgcolor='white'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Carga datos para visualizar la matriz.")

with t3:
    if 'data' in st.session_state:
        df = st.session_state['data']
        for q in ['Estratégico', 'Apalancamiento', 'Cuello de Botella', 'No Crítico']:
            subset = df[df['Cuadrante'] == q]
            if not subset.empty:
                with st.expander(f"Estrategia Digital para {q.upper()}"):
                    st.table(subset[['Proveedor', 'Subcategoría', 'Gasto Anual (€)']])
                    if q == 'Estratégico': st.error("Acción: Colaboración estrecha y gestión proactiva del riesgo.")
                    elif q == 'Apalancamiento': st.success("Acción: Licitaciones competitivas y gestión de volumen de gasto.")
                    elif q == 'Cuello de Botella': st.warning("Acción: Asegurar el suministro y buscar alternativas técnicas.")
                    else: st.info("Acción: Eficiencia administrativa y automatización de procesos.")
