import streamlit as st
import pandas as pd
import plotly.graph_objects as go
impoimport streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
from fpdf import FPDF

# ── 1. CONFIGURACIÓN E IDENTIDAD VISUAL ──
st.set_page_config(page_title="Sourcing Intelligence | Elymar Estévez", layout="wide", page_icon="📈")

st.markdown("""
    <style>
        .header-banner {
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            padding: 2.5rem; border-radius: 15px; color: white; text-align: center;
            margin-bottom: 2rem; border-bottom: 6px solid #10B981;
        }
        .strategy-box {
            background-color: #F1F5F9; border-left: 5px solid #10B981;
            padding: 15px; border-radius: 5px; margin-top: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# ── 2. DICCIONARIO DE ESTRATEGIAS (INTELIGENCIA DE COMPRAS) ──
ESTRATEGIAS = {
    'Estratégico': {
        'objetivo': "Garantizar suministro y ventaja competitiva.",
        'tactica': "Alianzas a largo plazo, desarrollo de proveedores, gestión de riesgos compartida.",
        'color': "#FEE2E2"
    },
    'Apalancamiento': {
        'objetivo': "Maximizar rentabilidad y ahorro.",
        'tactica': "Licitaciones competitivas, pooling de compras, búsqueda de sustitutos.",
        'color': "#D1FAE5"
    },
    'Cuello de Botella': {
        'objetivo': "Garantizar continuidad del suministro.",
        'tactica': "Aumento de stock de seguridad, contratos de reserva de capacidad, búsqueda de proveedores alternativos.",
        'color': "#FEF3C7"
    },
    'No Crítico': {
        'objetivo': "Reducir carga administrativa.",
        'tactica': "E-procurement, catálogos estándar, consolidación de pedidos.",
        'color': "#F1F5F9"
    }
}

# ── 3. LÓGICA DE NEGOCIO ──
def process_data(df):
    if df.empty: return df
    total_spend = df['Gasto (€)'].sum()
    # Segmentación basada en impacto (Pareto)
    df['Impacto'] = df['Gasto (€)'].apply(lambda x: 9 if x/total_spend > 0.15 else (6 if x/total_spend > 0.05 else 3))
    df['Riesgo'] = 5 # Valor base
    
    def get_quadrant(i, r):
        if i >= 6 and r >= 6: return 'Estratégico'
        if i >= 6: return 'Apalancamiento'
        if r >= 6: return 'Cuello de Botella'
        return 'No Crítico'
    
    df['Cuadrante'] = df.apply(lambda x: get_quadrant(x['Impacto'], x['Riesgo']), axis=1)
    return df

# ── 4. MOTOR DE GRÁFICOS (REVISADO) ──
def draw_kraljic_matrix(df, label_col):
    fig = go.Figure()
    
    # Cuadrantes con etiquetas de texto en el fondo
    rects = [
        (0, 5.5, 5.5, 11, ESTRATEGIAS['Cuello de Botella']['color'], "CUELLO DE BOTELLA"),
        (5.5, 5.5, 11, 11, ESTRATEGIAS['Estratégico']['color'], "ESTRATÉGICO"),
        (0, 0, 5.5, 5.5, ESTRATEGIAS['No Crítico']['color'], "NO CRÍTICO"),
        (5.5, 0, 11, 5.5, ESTRATEGIAS['Apalancamiento']['color'], "APALANCAMIENTO")
    ]
    for x0, y0, x1, y1, color, name in rects:
        fig.add_shape(type="rect", x0=x0, y0=y0, x1=x1, y1=y1, fillcolor=color, opacity=0.4, line_width=0, layer="below")
        fig.add_annotation(x=x0+2.7, y=y0+5, text=name, showarrow=False, font=dict(color="grey", size=10), opacity=0.3)

    # Burbujas sin duplicados en leyenda
    colors = px.colors.qualitative.Bold
    max_g = df['Gasto (€)'].max() if not df.empty else 1
    
    for i, label in enumerate(df[label_col].unique()):
        temp = df[df[label_col] == label]
        fig.add_trace(go.Scatter(
            x=temp['Impacto'], y=temp['Riesgo'],
            mode='markers', name=str(label),
            marker=dict(size=(temp['Gasto (€)']/max_g)*50 + 15, color=colors[i % len(colors)], line=dict(width=1, color='white')),
            hovertemplate=f"<b>{label}</b><br>Gasto: %{{customdata:,.2f}} EUR<br>Cuadrante: %{{text}}<extra></extra>",
            customdata=temp['Gasto (€)'], text=temp['Cuadrante']
        ))
    
    fig.update_layout(xaxis=dict(title="IMPACTO", range=[-0.5, 11.5]), yaxis=dict(title="RIESGO", range=[-0.5, 11.5]),
                      template="plotly_white", height=600, legend=dict(orientation="h", y=-0.2))
    return fig

# ── 5. EXPORTACIÓN PDF (CON ESTRATEGIAS) ──
def create_pdf(df_micro, category):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, "INFORME ESTRATEGICO DE COMPRAS", ln=True, align='C')
    
    pdf.set_text_color(0, 0, 0)
    pdf.ln(30)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"Analisis de Categoria: {category}", ln=True)
    
    for _, row in df_micro.iterrows():
        quad = row['Cuadrante']
        pdf.set_font("Arial", 'B', 10)
        pdf.set_fill_color(240, 240, 240)
        sub = str(row['Subcategoría']).encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(0, 8, f"Subcategoria: {sub} - [{quad}]", 1, 1, 'L', True)
        pdf.set_font("Arial", '', 9)
        pdf.multi_cell(0, 6, f"Estrategia: {ESTRATEGIAS[quad]['tactica']}")
        pdf.ln(2)
        
    return bytes(pdf.output())

# ── 6. INTERFAZ STREAMLIT ──
with st.sidebar:
    if os.path.exists("elymar.png"): st.image("elymar.png")
    st.title("Elymar Estévez")
    menu = st.radio("Menú:", ["📁 Carga", "📊 Dashboard"])

st.markdown('<div class="header-banner"><h1>Sourcing Intelligence System</h1></div>', unsafe_allow_html=True)

if menu == "📁 Carga":
    file = st.file_uploader("Subir Excel (.xlsx)", type=["xlsx"])
    if file:
        df = pd.read_excel(file)
        if all(c in df.columns for c in ['Categoría', 'Subcategoría', 'Proveedor', 'Gasto (€)']):
            st.session_state['data'] = df
            st.success("Datos listos.")
        else: st.error("Faltan columnas.")

elif menu == "📊 Dashboard":
    if 'data' in st.session_state:
        df = st.session_state['data']
        df_macro = process_data(df.groupby('Categoría').agg({'Gasto (€)': 'sum'}).reset_index())
        
        st.plotly_chart(draw_kraljic_matrix(df_macro, 'Categoría'), use_container_width=True)
        
        sel_cat = st.selectbox("Detalle por Categoría:", df_macro['Categoría'].unique())
        df_micro = process_data(df[df['Categoría'] == sel_cat].groupby(['Subcategoría', 'Proveedor']).agg({'Gasto (€)': 'sum'}).reset_index())
        
        st.plotly_chart(draw_kraljic_matrix(df_micro, 'Subcategoría'), use_container_width=True)
        
        # MOSTRAR ESTRATEGIAS EN PANTALLA
        st.subheader("💡 Recomendaciones Estratégicas")
        cols = st.columns(len(df_micro['Cuadrante'].unique()))
        for i, q in enumerate(df_micro['Cuadrante'].unique()):
            with cols[i]:
                st.markdown(f"""<div class="strategy-box"><b>{q}</b><br><small>{ESTRATEGIAS[q]['tactica']}</small></div>""", unsafe_allow_html=True)
        
        pdf_btn = st.download_button("📥 Descargar Reporte PDF", create_pdf(df_micro, sel_cat), f"Estrategia_{sel_cat}.pdf")
    else:
        st.info("Carga datos primero.")
