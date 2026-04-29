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

# ── 3. ENCABEZADO ──
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

# ── 4. MOTOR DE MAPEO (Sugerencia de Categorías) ──
MAPEO_CATEGORIAS = {
    "MATERIA PRIMA ALIMENTACIÓN": ['cacao', 'chocolate', 'frutos secos', 'aceite', 'grasa', 'cereales', 'harina', 'levadura', 'azucar', 'edulcorante', 'aditivo', 'ingrediente', 'ovoproducto'],
    "PACKAGING": ['cartonaje', 'estucheria', 'laminado', 'embalaje', 'pallet', 'etiqueta', 'envase', 'film', 'botella'],
    "LOGÍSTICA": ['flete', 'transporte', 'maritimo', 'terrestre', 'aduana', 'almacenaje'],
    "TECNOLOGÍA / IT": ['software', 'erp', 'cloud', 'saas', 'hardware', 'licencia'],
    "ENERGÍA & UTILITIES": ['electricidad', 'gas', 'luz', 'agua', 'fuel', 'combustible'],
    "INDIRECTOS / SERVICIOS": ['limpieza', 'seguridad', 'consultoria', 'oficina', 'mantenimiento', 'mro']
}

def sugerir_categoria(subcategoria):
    sub_low = str(subcategoria).lower()
    for cat, palabras in MAPEO_CATEGORIAS.items():
        if any(p in sub_low for p in palabras):
            return cat
    return "OTRAS CATEGORÍAS"

# ── 5. BARRA LATERAL ──
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/strategy.png", width=80)
    st.markdown("### Herramientas")
    
    # Plantilla minimalista (solo subcategoría y gasto)
    st.markdown("#### 📥 Descargar Plantilla")
    df_temp = pd.DataFrame({'Subcategoría': ['Cacao', 'Cartonaje', 'Gas Natural'], 'Gasto Anual (€)': [500000, 100000, 250000]})
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_temp.to_excel(writer, index=False)
    st.download_button("Descargar Excel", output.getvalue(), "plantilla_minimal.xlsx")

# ── 6. CUERPO PRINCIPAL ──
t1, t2 = st.tabs(["📥 Gestión de Datos", "📊 Matriz & Estrategia"])

with t1:
    st.subheader("Carga de Datos Inteligente")
    st.info("💡 Si subes solo subcategorías, el sistema sugerirá la categoría automáticamente.")
    
    up_file = st.file_uploader("Sube tu Excel/CSV", type=['xlsx', 'csv'])
    
    if up_file:
        df = pd.read_excel(up_file) if up_file.name.endswith('.xlsx') else pd.read_csv(up_file)
        
        # LÓGICA DE SUGERENCIA: Si no hay columna 'Categoría', la creamos
        if 'Categoría' not in df.columns:
            df['Categoría'] = df['Subcategoría'].apply(sugerir_categoria)
        else:
            # Si existe pero hay celdas vacías, las rellenamos
            df['Categoría'] = df.apply(lambda r: sugerir_categoria(r['Subcategoría']) if pd.isna(r['Categoría']) else r['Categoría'], axis=1)
    else:
        # Datos de ejemplo por defecto
        df = pd.DataFrame({
            'Categoría': ['Sugerida por Sistema...', 'Sugerida por Sistema...'],
            'Subcategoría': ['Aceites y Grasas', 'Laminado flexible'],
            'Gasto Anual (€)': [200000, 150000]
        })
        df['Categoría'] = df['Subcategoría'].apply(sugerir_categoria)

    st.markdown("##### Valida o edita las Categorías sugeridas:")
    # El usuario valida aquí los datos antes de procesar
    data_final = st.data_editor(df, num_rows="dynamic", use_container_width=True)

    if st.button("EJECUTAR ANÁLISIS 4.0", type="primary"):
        # Lógica de Kraljic (simplificada para velocidad)
        processed = []
        total_g = data_final['Gasto Anual (€)'].sum()
        
        for _, row in data_final.iterrows():
            # Asignación de impacto/riesgo basada en nuestra base de datos anterior
            # (Aquí iría tu lógica de puntuación de 1 a 10)
            processed.append({
                'Subcategoría': row['Subcategoría'],
                'Gasto': row['Gasto Anual (€)'],
                'Impacto': 8 if row['Categoría'] == "MATERIA PRIMA ALIMENTACIÓN" else 5,
                'Riesgo': 7 if row['Categoría'] == "MATERIA PRIMA ALIMENTACIÓN" else 4,
                'Cuadrante': 'Estratégico' # Ejemplo simplificado
            })
        st.session_state['data'] = pd.DataFrame(processed)
        st.success("Análisis completado. Categorías validadas.")

with t2:
    if 'data' in st.session_state:
        st.write("Visualización de la Matriz...")
        # Aquí va el código del gráfico Plotly que ya tenemos
    else:
        st.info("Sube datos para ver el análisis.")
