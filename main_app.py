import streamlit as st
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
            padding: 2rem; border-radius: 12px; color: white; text-align: center;
            margin-bottom: 2rem; border-bottom: 5px solid #10B981;
        }
        .strategy-card {
            background-color: #FFFFFF; border-radius: 8px; padding: 15px;
            border-left: 5px solid #10B981; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            height: 100%;
        }
        .metric-card {
            background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 15px;
            border-radius: 10px; text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

# ── 2. INTELIGENCIA DE COMPRAS: MATRIZ DE ESTRATEGIAS ──
ESTRATEGIAS_MATRIZ = {
    'Estratégico': {
        'objetivo': "Garantizar suministro y ventaja competitiva.",
        'tactica': "Alianzas a largo plazo, desarrollo de proveedores compartidos y gestión de riesgos.",
        'color': "#FEE2E2"
    },
    'Apalancamiento': {
        'objetivo': "Maximizar rentabilidad y ahorro.",
        'tactica': "Licitaciones competitivas, negociación por volumen y búsqueda de sustitutos.",
        'color': "#D1FAE5"
    },
    'Cuello de Botella': {
        'objetivo': "Garantizar continuidad del suministro.",
        'tactica': "Asegurar stock de seguridad, contratos de capacidad y búsqueda de alternativas.",
        'color': "#FEF3C7"
    },
    'No Crítico': {
        'objetivo': "Reducir carga administrativa.",
        'tactica': "E-procurement, catálogos estándar y automatización de pedidos.",
        'color': "#F1F5F9"
    }
}

# ── 3. LÓGICA DE PROCESAMIENTO ──
def segmentacion_kraljic(df):
    if df.empty: return df
    total_gasto = df['Gasto (€)'].sum()
    
    df['Impacto'] = df['Gasto (€)'].apply(lambda x: 9 if x/total_gasto > 0.15 else (6 if x/total_gasto > 0.05 else 3))
    df['Riesgo'] = 5 
    
    def clasificar(row):
        if row['Impacto'] >= 6 and row['Riesgo'] >= 6: return 'Estratégico'
        if row['Impacto'] >= 6: return 'Apalancamiento'
        if row['Riesgo'] >= 6: return 'Cuello de Botella'
        return 'No Crítico'
    
    df['Cuadrante'] = df.apply(clasificar, axis=1)
    df['% Peso'] = (df['Gasto (€)'] / total_gasto) * 100
    return df

# ── 4. MOTOR DE VISUALIZACIÓN PROFESIONAL (CORREGIDO SOLAPAMIENTO) ──
def render_kraljic(df, label_col):
    fig = go.Figure()

    # Cuadrantes de fondo
    rects = [
        (0, 5.5, 5.5, 11, ESTRATEGIAS_MATRIZ['Cuello de Botella']['color'], "CUELLO DE BOTELLA"),
        (5.5, 5.5, 11, 11, ESTRATEGIAS_MATRIZ['Estratégico']['color'], "ESTRATÉGICO"),
        (0, 0, 5.5, 5.5, ESTRATEGIAS_MATRIZ['No Crítico']['color'], "NO CRÍTICO"),
        (5.5, 0, 11, 5.5, ESTRATEGIAS_MATRIZ['Apalancamiento']['color'], "APALANCAMIENTO")
    ]
    for x0, y0, x1, y1, color, name in rects:
        fig.add_shape(type="rect", x0=x0, y0=y0, x1=x1, y1=y1, fillcolor=color, opacity=0.4, line_width=0, layer="below")
        fig.add_annotation(x=x0+2.7, y=y0+5, text=name, showarrow=False, font=dict(color="grey", size=10), opacity=0.3)

    max_bubble = df['Gasto (€)'].max() if not df.empty else 1
    colors = px.colors.qualitative.Bold
    
    for i, label in enumerate(df[label_col].unique()):
        sub_df = df[df[label_col] == label]
        fig.add_trace(go.Scatter(
            x=sub_df['Impacto'], y=sub_df['Riesgo'],
            mode='markers', name=str(label),
            marker=dict(size=(sub_df['Gasto (€)']/max_bubble)*55 + 15, color=colors[i % len(colors)], line=dict(width=1, color='white')),
            hovertemplate=f"<b>{label}</b><br>Gasto: %{{customdata:,.2f}} €<br>Cuadrante: %{{text}}<extra></extra>",
            customdata=sub_df['Gasto (€)'], text=sub_df['Cuadrante']
        ))

    # AJUSTE DE LEYENDA Y MÁRGENES PARA EVITAR SOLAPAMIENTO
    fig.update_layout(
        xaxis=dict(title="IMPACTO ECONÓMICO (Gasto)", range=[-0.5, 11.5]),
        yaxis=dict(title="RIESGO DE SUMINISTRO", range=[-0.5, 11.5]),
        template="plotly_white", 
        height=650, # Aumentado ligeramente para dar aire
        margin=dict(b=120), # Aumentado margen inferior para la leyenda
        showlegend=True,
        legend=dict(
            orientation="h", 
            yanchor="top", 
            y=-0.25, # Movida más hacia abajo para no tocar el título del eje X
            xanchor="center", 
            x=0.5
        )
    )
    return fig

# ── 5. GENERADOR DE REPORTES PDF ──
def generate_pdf_report(df_table, title_cat):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 15, f"Reporte de Sourcing Intelligence: {title_cat}", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(80, 10, "Item", 1, 0, 'C', True)
    pdf.cell(50, 10, "Gasto (EUR)", 1, 0, 'C', True)
    pdf.cell(60, 10, "Estrategia", 1, 1, 'C', True)
    
    pdf.set_font("Arial", '', 9)
    for _, row in df_table.iterrows():
        name = str(row.iloc[0]).encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(80, 10, name[:40], 1)
        pdf.cell(50, 10, f"{row['Gasto (€)']:,.2f}", 1, 0, 'R')
        pdf.cell(60, 10, row['Cuadrante'], 1, 1, 'C')
        
    return bytes(pdf.output())

# ── 6. ESTRUCTURA DE LA APLICACIÓN ──
st.markdown('<div class="header-banner"><h1>Dashboard de Compra Estratégica</h1><p>Análisis de Materias Primas | Elymar Estévez</p></div>', unsafe_allow_html=True)

with st.sidebar:
    if os.path.exists("elymar.png"): st.image("elymar.png")
    st.header("Gestión de Datos")
    uploaded_file = st.file_uploader("Subir Excel", type=["xlsx"])
    menu = st.radio("Sección:", ["📊 Vista Macro", "🔍 Detalle de Categoría"])

if uploaded_file:
    data = pd.read_excel(uploaded_file)
    
    if menu == "📊 Vista Macro":
        st.subheader("Análisis de Gasto por Categoría")
        df_macro = data.groupby('Categoría').agg({'Gasto (€)': 'sum'}).reset_index()
        df_macro = segmentacion_kraljic(df_macro).sort_values('Gasto (€)', ascending=False)
        
        col_map, col_table = st.columns([2, 1])
        with col_map:
            st.plotly_chart(render_kraljic(df_macro, 'Categoría'), use_container_width=True)
        with col_table:
            st.markdown("### 📋 Tabla de Gasto")
            st.dataframe(df_macro[['Categoría', 'Gasto (€)', '% Peso', 'Cuadrante']], 
                         hide_index=True, use_container_width=True,
                         column_config={"Gasto (€)": st.column_config.NumberColumn(format="%.2f €"),
                                        "% Peso": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100)})

    elif menu == "🔍 Detalle de Categoría":
        sel_cat = st.selectbox("Seleccione Categoría:", data['Categoría'].unique())
        df_micro = data[data['Categoría'] == sel_cat].groupby(['Subcategoría', 'Proveedor']).agg({'Gasto (€)': 'sum'}).reset_index()
        df_micro = segmentacion_kraljic(df_micro).sort_values('Gasto (€)', ascending=False)
        
        st.plotly_chart(render_kraljic(df_micro, 'Subcategoría'), use_container_width=True)
        
        st.markdown(f"### 📋 Gasto Detallado en {sel_cat}")
        st.dataframe(df_micro[['Subcategoría', 'Proveedor', 'Gasto (€)', 'Cuadrante']], 
                     hide_index=True, use_container_width=True,
                     column_config={"Gasto (€)": st.column_config.NumberColumn(format="%.2f €")})
        
        st.markdown("### 💡 Tácticas Recomendadas")
        present_q = df_micro['Cuadrante'].unique()
        cols = st.columns(len(present_q))
        for idx, q in enumerate(present_q):
            with cols[idx]:
                st.markdown(f"""<div class="strategy-card"><b>{q.upper()}</b><br>
                            <small><b>Objetivo:</b> {ESTRATEGIAS_MATRIZ[q]['objetivo']}</small><br>
                            <small><b>Táctica:</b> {ESTRATEGIAS_MATRIZ[q]['tactica']}</small></div>""", unsafe_allow_html=True)
        
        st.divider()
        report_bytes = generate_pdf_report(df_micro, sel_cat)
        st.download_button("📥 Descargar Reporte Estratégico (PDF)", report_bytes, f"Estrategia_{sel_cat}.pdf")

else:
    st.info("👋 Por favor, carga tu base de datos en Excel para activar los cuadros de mando.")
