import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
import os
from PIL import Image

# ── 1. CONFIGURACIÓN DE PÁGINA ──
st.set_page_config(page_title="Sourcing Hub | Elymar Estévez", layout="wide", page_icon="📈")

# ── 2. ESTILOS CSS (DISEÑO PREMIUM) ──
st.markdown("""
    <style>
        /* Banner Principal */
        .header-banner {
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            padding: 45px;
            border-radius: 20px;
            color: white;
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 6px solid #10B981;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }
        .header-banner h1 { margin: 0; font-size: 3rem; font-weight: 800; letter-spacing: -1px; }
        .header-banner p { font-size: 1.3rem; opacity: 0.8; margin-top: 10px; }
        
        /* Badge de Autor */
        .author-tag {
            display: inline-block;
            background-color: #10B981;
            color: white;
            padding: 6px 18px;
            border-radius: 50px;
            font-weight: 700;
            font-size: 1rem;
            margin-top: 15px;
            text-transform: uppercase;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #F8FAFC;
            border-right: 1px solid #E2E8F0;
        }
    </style>
""", unsafe_allow_html=True)

# ── 3. BARRA LATERAL: PERFIL DE ELYMAR ──
with st.sidebar:
    # Carga de la foto específica: elymar.png
    foto_path = "elymar.png"
    if os.path.exists(foto_path):
        try:
            img = Image.open(foto_path)
            st.image(img, use_container_width=True)
        except Exception as e:
            st.error(f"Error al cargar la imagen: {e}")
    else:
        st.warning(f"⚠️ No se encontró el archivo '{foto_path}' en la raíz.")
    
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    st.title("Elymar Estévez")
    st.markdown("*Supply Chain & Data Expert*")
    st.markdown("</div>", unsafe_allow_html=True)
    st.divider()

    # Navegación
    menu = st.radio("Módulos de Decisión:", ["📂 Gestión de Datos", "📊 Matriz de Kraljic"], index=1)
    
    st.divider()
    # Plantilla de 4 columnas
    try:
        import xlsxwriter
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as w:
            pd.DataFrame(columns=['Proveedor', 'Categoría', 'Subcategoría', 'Gasto (€)']).to_excel(w, index=False)
        st.download_button("📥 Bajar Plantilla Operativa", buf.getvalue(), "formato_compras.xlsx")
    except:
        pass

# ── 4. CUERPO PRINCIPAL Y BANNER ──
st.markdown(f"""
    <div class="header-banner">
        <h1>Sourcing Strategic Intelligence</h1>
        <p>Cuadro de Mando Interactivo para Decisiones de Suministro</p>
        <div class="author-tag">Desarrollado por Elymar Estévez</div>
    </div>
""", unsafe_allow_html=True)

# ── 5. FUNCIÓN MOTOR DE LA MATRIZ ──
def draw_kraljic_pro(df, label_col, title):
    fig = go.Figure()
    
    # Cuadrantes basados en tu imagen de referencia
    fig.add_shape(type="rect", x0=0, y0=5.5, x1=5.5, y1=11, fillcolor="#FEF3C7", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=5.5, y0=5.5, x1=11, y1=11, fillcolor="#FEE2E2", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=0, y0=0, x1=5.5, y1=5.5, fillcolor="#F1F5F9", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=5.5, y0=0, x1=11, y1=5.5, fillcolor="#D1FAE5", line_width=0, layer="below")

    # Etiquetas de Cuadrante
    quads = [("CUELLO BOTELLA", 2.75, 10.5), ("ESTRATÉGICO", 8.25, 10.5), 
             ("NO CRÍTICO", 2.75, 0.5), ("APALANCAMIENTO", 8.25, 0.5)]
    for t, x, y in quads:
        fig.add_annotation(x=x, y=y, text=t, showarrow=False, font=dict(size=16, color="#94A3B8", family="Arial Black"))

    # Puntos de Datos (Burbujas)
    fig.add_trace(go.Scatter(
        x=df['Impacto'], y=df['Riesgo'], mode='markers+text',
        text=df[label_col], textposition="top center",
        marker=dict(size=df['Gasto']/df['Gasto'].max()*40 + 25, color='#334155', line=dict(width=2, color='white')),
        customdata=df['Gasto'],
        hovertemplate="<b>%{text}</b><br>Gasto: %{customdata:,.2f} €<extra></extra>"
    ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=20)),
        xaxis=dict(title="IMPACTO FINANCIERO", range=[-0.5, 11.5]),
        yaxis=dict(title="RIESGO DE SUMINISTRO", range=[-0.5, 11.5]),
        template="plotly_white", height=700
    )
    return fig

# ── 6. LÓGICA DE APLICACIÓN ──
if menu == "📂 Gestión de Datos":
    st.subheader("📥 Carga de Datos")
    file = st.file_uploader("Sube el archivo Excel (Proveedor, Categoría, Subcategoría, Gasto)", type=['xlsx'])
    
    if file:
        df = pd.read_excel(file)
        df['Gasto (€)'] = pd.to_numeric(df['Gasto (€)'], errors='coerce').fillna(0)
        total = df['Gasto (€)'].sum()
        
        # Procesar Nivel 1 (Categoría)
        n1 = df.groupby('Categoría').agg({'Gasto (€)': 'sum'}).reset_index()
        n1['Impacto'] = n1['Gasto (€)'].apply(lambda x: 9 if x/total > 0.15 else (6 if x/total > 0.05 else 3))
        n1['Riesgo'] = n1['Categoría'].apply(lambda x: 8 if any(k in str(x).upper() for k in ["ALIM", "ENER", "QUIM"]) else 4)
        st.session_state['n1'] = n1.rename(columns={'Gasto (€)': 'Gasto'})

        # Procesar Nivel 2 (Subcategoría)
        n2 = df.groupby(['Categoría', 'Subcategoría']).agg({'Gasto (€)': 'sum', 'Proveedor': 'first'}).reset_index()
        n2['Impacto'] = n2['Gasto (€)'].apply(lambda x: 9 if x/total > 0.08 else (6 if x/total > 0.02 else 3))
        n2['Riesgo'] = n2['Categoría'].apply(lambda x: 8 if any(k in str(x).upper() for k in ["ALIM", "ENER", "QUIM"]) else 4)
        st.session_state['n2'] = n2.rename(columns={'Gasto (€)': 'Gasto'})
        st.success("✅ Estructura procesada correctamente.")

elif menu == "📊 Matriz de Kraljic":
    if 'n1' in st.session_state:
        tab_macro, tab_micro = st.tabs(["🏛️ Visión Macro (Categorías)", "🔍 Visión Detallada (Subcategorías)"])
        
        with tab_macro:
            st.plotly_chart(draw_kraljic_pro(st.session_state['n1'], 'Categoría', "Posicionamiento por Macro-Categoría"), use_container_width=True)
            st.dataframe(st.session_state['n1'].sort_values('Gasto', ascending=False), hide_index=True, 
                         column_config={"Gasto": st.column_config.NumberColumn(format="%.2f €", width=200)})

        with tab_micro:
            sel_cat = st.selectbox("Selecciona Categoría para auditar:", st.session_state['n2']['Categoría'].unique())
            df_filtered = st.session_state['n2'][st.session_state['n2']['Categoría'] == sel_cat]
            
            st.plotly_chart(draw_kraljic_pro(df_filtered, 'Subcategoría', f"Desglose Estratégico: {sel_cat}"), use_container_width=True)
            st.dataframe(df_filtered[['Subcategoría', 'Proveedor', 'Gasto']].sort_values('Gasto', ascending=False), hide_index=True,
                         column_config={"Gasto": st.column_config.NumberColumn(format="%.2f €", width=200)})
    else:
        st.warning("⚠️ Sube los datos en el módulo de 'Gestión de Datos' para activar la matriz.")
