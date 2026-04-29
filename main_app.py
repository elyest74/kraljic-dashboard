import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
import os
import base64
from datetime import date

# ── 1. CONFIGURACIÓN DE PÁGINA (UI/UX) ──
st.set_page_config(
    page_title="Purchasing Strategic Dashboard | Elymar Estévez",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS para mejorar la estética profesional
st.markdown("""
    <style>
        .main { background-color: #f8fafc; }
        .stTabs [data-baseweb="tab"] { font-weight: 700; font-size: 1.1rem; color: #1e293b; }
        .stMetric { background-color: white; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; }
        div.stButton > button:first-child { background-color: #3B82F6; color: white; border-radius: 8px; border: none; font-weight: bold; width: 100%; }
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
            <img src="{foto_base64}" style="width: 100px; height: 100px; border-radius: 50%; border: 3px solid #3B82F6; object-fit: cover; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
        </div>
        <div style="flex-grow: 1;">
            <h1 style="color: white; margin: 0; font-size: 2.4rem; font-weight: 800;">Purchasing Strategic Dashboard V4.0</h1>
            <p style="color: #94A3B8; margin: 5px 0 0 0; font-size: 1.2rem;">ACOMPAÑANTE DIGITAL: <strong>COMPRAS 4.0</strong> · POR ELYMAR ESTÉVEZ</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# ── 3. MOTOR DE INTELIGENCIA DE CATEGORÍAS ──
DATABASE_INTEL = {
    "MATERIA PRIMA ALIMENTACIÓN": {
        'keywords': ['cacao', 'chocolate', 'aceite', 'grasa', 'cereales', 'harina', 'azucar', 'edulcorante', 'aditivo', 'ingrediente', 'leche', 'cafe'],
        'i': 9, 'r': 8
    },
    "PACKAGING": {
        'keywords': ['carton', 'estucheria', 'laminado', 'embalaje', 'pallet', 'etiqueta', 'envase', 'film', 'botella', 'vidrio', 'plastico'],
        'i': 7, 'r': 7
    },
    "LOGÍSTICA": {
        'keywords': ['flete', 'transporte', 'maritimo', 'terrestre', 'aduana', 'almacen', 'distribucion'],
        'i': 8, 'r': 7
    },
    "ENERGÍA & UTILITIES": {
        'keywords': ['electricidad', 'gas', 'luz', 'agua', 'fuel', 'vapor'],
        'i': 10, 'r': 9
    },
    "IT & TECNOLOGÍA": {
        'keywords': ['software', 'erp', 'cloud', 'saas', 'hardware', 'licencia', 'it'],
        'i': 8, 'r': 6
    },
    "INDIRECTOS": {
        'keywords': ['limpieza', 'seguridad', 'consultoria', 'mantenimiento', 'mro', 'oficina'],
        'i': 3, 'r': 3
    }
}

def sugerir_data(subcat):
    sub_low = str(subcat).lower()
    for cat, data in DATABASE_INTEL.items():
        if any(k in sub_low for k in data['keywords']):
            return cat, data['i'], data['r']
    return "OTRAS CATEGORÍAS", 5, 5

# ── 4. BARRA LATERAL ──
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/strategy.png", width=80)
    st.markdown("### Centro de Gestión")
    st.divider()
    
    st.markdown("#### 📥 Plantilla")
    df_temp = pd.DataFrame({
        'Subcategoría': ['Cacao', 'Cajas de cartón', 'Electricidad'],
        'Gasto Anual (€)': [1200000, 450000, 800000]
    })
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_temp.to_excel(writer, index=False)
    
    st.download_button("Descargar Excel Ejemplo", output.getvalue(), "plantilla_compras.xlsx")
    st.divider()
    st.info(f"Fecha de análisis: {date.today().strftime('%d/%m/%Y')}")

# ── 5. PESTAÑAS DE TRABAJO ──
tab1, tab2 = st.tabs(["📥 Gestión de Datos", "📊 Matriz de Kraljic & Estrategia"])

with tab1:
    st.subheader("Carga y Validación de Datos")
    st.markdown("""
    Carga tu archivo Excel o CSV. **No es necesario incluir el nombre del proveedor** si deseas mantener la privacidad. 
    Si solo incluyes la 'Subcategoría', el sistema sugerirá la categoría y los niveles de riesgo automáticamente.
    """)
    
    archivo = st.file_uploader("Subir Fichero", type=['xlsx', 'csv'])
    
    if archivo:
        df = pd.read_excel(archivo) if archivo.name.endswith('.xlsx') else pd.read_csv(archivo)
        
        # Inyectar categorías si no existen
        if 'Categoría' not in df.columns:
            df['Categoría'] = df['Subcategoría'].apply(lambda x: sugerir_data(x)[0])
    else:
        df = df_temp.copy()
        df['Categoría'] = df['Subcategoría'].apply(lambda x: sugerir_data(x)[0])

    st.write("---")
    st.markdown("##### ✏️ Valida y edita la información en la tabla:")
    df_editado = st.data_editor(df, num_rows="dynamic", use_container_width=True)

    if st.button("🚀 PROCESAR Y GENERAR ESTRATEGIA"):
        total_g = df_editado['Gasto Anual (€)'].sum()
        final_list = []
        
        for _, row in df_editado.iterrows():
            # Obtener scores base de la IA
            _, i_base, r_base = sugerir_data(row['Subcategoría'])
            
            # Factor Pareto: Si la subcategoría es >15% del gasto, sube impacto
            gasto = row['Gasto Anual (€)']
            impacto = min(10, i_base + 1) if (gasto/total_g) > 0.15 else i_base
            
            # Clasificación de Cuadrante
            if impacto >= 6 and r_base >= 6: q = 'Estratégico'
            elif impacto >= 6 and r_base < 6: q = 'Apalancamiento'
            elif impacto < 6 and r_base >= 6: q = 'Cuello de Botella'
            else: q = 'No Crítico'
            
            final_list.append({
                'Categoría': row['Categoría'],
                'Subcategoría': row['Subcategoría'],
                'Gasto': gasto,
                'Impacto': impacto,
                'Riesgo': r_base,
                'Cuadrante': q,
                'Proveedor': row.get('Proveedor', 'Confidencial')
            })
        
        st.session_state['data_final'] = pd.DataFrame(final_list)
        st.success("¡Análisis listo! Ve a la siguiente pestaña para ver la matriz.")

with tab2:
    if 'data_final' in st.session_state:
        res = st.session_state['data_final']
        
        # KPIs
        c1, c2, c3 = st.columns(3)
        c1.metric("Gasto Analizado", f"{res['Gasto'].sum():,.0f} €")
        c2.metric("Subcategorías", len(res))
        c3.metric("Cuadrante Dominante", res['Cuadrante'].mode()[0])

        st.divider()
        
        # MENSAJE DE AYUDA UX
        st.info("💡 **INTERACCIÓN:** La matriz es dinámica. **Desplaza el ratón (hover) sobre los puntos** para ver los nombres y detalles de cada subcategoría. Esto permite que el gráfico se mantenga limpio incluso con muchos datos.")

        # CUERPO VISUAL
        m1, m2 = st.columns([2, 1])
        
        with m1:
            fig = go.Figure()
            colores = {'Estratégico': '#EF4444', 'Apalancamiento': '#10B981', 'Cuello de Botella': '#F59E0B', 'No Crítico': '#64748B'}
            
            for quad, color in colores.items():
                d = res[res['Cuadrante'] == quad]
                if not d.empty:
                    fig.add_trace(go.Scatter(
                        x=d['Impacto'], y=d['Riesgo'],
                        mode='markers',
                        name=quad,
                        hovertemplate="<b>Subcategoría:</b> %{customdata[0]}<br><b>Gasto:</b> %{customdata[1]:,.0f}€<br><b>Impacto:</b> %{x}<br><b>Riesgo:</b> %{y}<extra></extra>",
                        customdata=list(zip(d['Subcategoría'], d['Gasto'])),
                        marker=dict(size=d['Gasto']/res['Gasto'].max()*60 + 20, color=color, opacity=0.7, line=dict(width=2, color='white'))
                    ))

            fig.update_layout(
                title="<b>Matriz de Kraljic Automatizada</b>",
                xaxis=dict(title="IMPACTO FINANCIERO", range=[-0.5, 11], gridcolor='#f1f5f9'),
                yaxis=dict(title="RIESGO DE SUMINISTRO", range=[-0.5, 11], gridcolor='#f1f5f9'),
                shapes=[
                    dict(type="line", x0=5.5, y0=-0.5, x1=5.5, y1=11, line=dict(color="#cbd5e1", dash="dash")),
                    dict(type="line", x0=-0.5, y0=5.5, x1=11, y1=5.5, line=dict(color="#cbd5e1", dash="dash"))
                ],
                annotations=[
                    dict(x=2, y=10.5, text="⚠️ CUELLO DE BOTELLA", showarrow=False, font=dict(color="#F59E0B", size=12)),
                    dict(x=9, y=10.5, text="🔥 ESTRATÉGICO", showarrow=False, font=dict(color="#EF4444", size=12)),
                    dict(x=2, y=0.5, text="⚙️ NO CRÍTICO", showarrow=False, font=dict(color="#64748B", size=12)),
                    dict(x=9, y=0.5, text="💰 APALANCAMIENTO", showarrow=False, font=dict(color="#10B981", size=12))
                ],
                plot_bgcolor='white', height=600, hovermode='closest'
            )
            st.plotly_chart(fig, use_container_width=True)

        with m2:
            st.markdown("### Reparto de Gasto")
            gasto_cat = res.groupby('Categoría')['Gasto'].sum().sort_values(ascending=True)
            fig_bar = go.Figure(go.Bar(x=gasto_cat.values, y=gasto_cat.index, orientation='h', marker_color='#1E293B'))
            fig_bar.update_layout(height=400, plot_bgcolor='white', margin=dict(t=10, b=10))
            st.plotly_chart(fig_bar, use_container_width=True)

        st.divider()
        
        # RECOMENDACIONES
        st.subheader("📋 Recomendaciones Estratégicas 4.0")
        for q in ['Estratégico', 'Apalancamiento', 'Cuello de Botella', 'No Crítico']:
            items = res[res['Cuadrante'] == q]
            if not items.empty:
                with st.expander(f"Estrategias para: {q.upper()} ({len(items)} items)"):
                    st.dataframe(items[['Subcategoría', 'Gasto', 'Categoría']], use_container_width=True)
                    if q == 'Estratégico': st.error("FOCO: Alianzas, integración de sistemas y contratos a largo plazo.")
                    elif q == 'Apalancamiento': st.success("FOCO: Licitaciones competitivas, e-auctions y negociación de precio.")
                    elif q == 'Cuello de Botella': st.warning("FOCO: Rediseño de producto, stock de seguridad o búsqueda de sustitutos.")
                    else: st.info("FOCO: Simplificación de pedidos, tarjetas de compra y reducción de burocracia.")
    else:
        st.warning("⚠️ Primero carga datos y pulsa el botón 'Procesar' en la pestaña anterior.")
