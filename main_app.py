import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
import os
from PIL import Image
from fpdf import FPDF
import tempfile

# ── 1. CONFIGURACIÓN Y ESTILOS ──
st.set_page_config(page_title="Sourcing Intelligence | Elymar Estévez", layout="wide", page_icon="📈")

st.markdown("""
    <style>
        .header-banner {
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            padding: 40px; border-radius: 15px; color: white; text-align: center;
            margin-bottom: 30px; border-bottom: 6px solid #10B981;
        }
        .author-tag {
            background-color: #10B981; color: white; padding: 5px 15px;
            border-radius: 50px; font-weight: bold; font-size: 0.9rem;
        }
        .strategy-container { margin-bottom: 15px; padding: 15px; border-radius: 8px; border-left: 8px solid; }
        .est-estrategico { background-color: #FEE2E2; border-color: #EF4444; color: #991B1B; }
        .est-apalancamiento { background-color: #D1FAE5; border-color: #10B981; color: #065F46; }
        .est-cuello { background-color: #FEF3C7; border-color: #F59E0B; color: #92400E; }
        .est-nocritico { background-color: #F1F5F9; border-color: #64748B; color: #1E293B; }
    </style>
""", unsafe_allow_html=True)

# ── 2. FUNCIONES DE APOYO ──
def get_strategy_text(cuadrante):
    data = {
        'Estratégico': "Alianzas a largo plazo, co-diseño y gestión estrecha de la relación (SRM).",
        'Apalancamiento': "Licitaciones competitivas, optimización de precios y consolidación de volúmenes.",
        'Cuello de Botella': "Asegurar volumen, buscar sustitutos y reducir dependencia de proveedores.",
        'No Crítico': "Automatización de compras, catálogos e-procurement y reducción de burocracia."
    }
    return data.get(cuadrante, "")

def create_pdf_report(df_n1, df_n2, cat_sel, fig1, fig2):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- PÁGINA 1: RESUMEN GLOBAL ---
    pdf.add_page()
    pdf.set_fill_color(30, 41, 59) 
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, "INFORME ESTRATÉGICO DE COMPRAS", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Analista Senior: Elymar Estévez", ln=True, align='C')
    
    pdf.set_text_color(0, 0, 0)
    pdf.ln(25)
    
    # Exportar e insertar Gráfica Macro
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp1:
        fig1.write_image(tmp1.name, width=800, height=500, scale=2)
        pdf.image(tmp1.name, x=15, y=60, w=180)
        os.unlink(tmp1.name)
    
    pdf.set_y(160)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "1. Matriz de Posicionamiento Global", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 7, "La gráfica anterior muestra la distribución de las categorías principales basadas en riesgo e impacto financiero.")
    
    # --- PÁGINA 2: DETALLE CATEGORÍA ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"2. Análisis Detallado: {cat_sel}", ln=True)
    
    # Exportar e insertar Gráfica Micro
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp2:
        fig2.write_image(tmp2.name, width=800, height=500, scale=2)
        pdf.image(tmp2.name, x=15, y=30, w=180)
        os.unlink(tmp2.name)
        
    pdf.set_y(135)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, "Estrategias de Suministro Sugeridas:", ln=True)
    pdf.set_font("Arial", '', 10)
    df_f = df_n2[df_n2['Categoría'] == cat_sel]
    for q in df_f['Cuadrante'].unique():
        pdf.multi_cell(0, 7, f"- {q.upper()}: {get_strategy_text(q)}", border=0)

    pdf.ln(5)
    # Tabla de Datos Detallada
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(75, 8, "Subcategoría", 1, 0, 'C', True)
    pdf.cell(65, 8, "Proveedor", 1, 0, 'C', True)
    pdf.cell(40, 8, "Gasto (EUR)", 1, 1, 'C', True)
    
    pdf.set_font("Arial", '', 8)
    for _, row in df_f.sort_values('Gasto', ascending=False).iterrows():
        pdf.cell(75, 8, str(row['Subcategoría'])[:40], 1)
        pdf.cell(65, 8, str(row['Proveedor'])[:35], 1)
        pdf.cell(40, 8, f"{row['Gasto']:,.2f}", 1, 1, 'R')

    return bytes(pdf.output())

# ── 3. BARRA LATERAL (BRANDING) ──
with st.sidebar:
    if os.path.exists("elymar.png"):
        st.image(Image.open("elymar.png"), use_container_width=True)
    st.markdown(f"<div style='text-align: center; font-weight: bold; font-size: 1.2rem;'>Elymar Estévez</div>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("Módulos:", ["📂 Gestión de Datos", "📊 Matriz de Kraljic"], index=1)

# ── 4. CABECERA ──
st.markdown("""
    <div class="header-banner">
        <h1>Sourcing Strategic Intelligence</h1>
        <p>Cuadro de Mando Interactivo para Decisiones de Suministro</p>
        <div class="author-tag">Desarrollado por Elymar Estévez</div>
    </div>
""", unsafe_allow_html=True)

# ── 5. FUNCIÓN DE MATRIZ (MEJORADA CON EJES AMPLIADOS) ──
def draw_kraljic_interactive(df, label_col):
    fig = go.Figure()
    # Fondos Cuadrantes
    fig.add_shape(type="rect", x0=0, y0=5.5, x1=5.5, y1=11, fillcolor="#FEF3C7", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=5.5, y0=5.5, x1=11, y1=11, fillcolor="#FEE2E2", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=0, y0=0, x1=5.5, y1=5.5, fillcolor="#F1F5F9", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=5.5, y0=0, x1=11, y1=5.5, fillcolor="#D1FAE5", line_width=0, layer="below")

    # Texto de cuadrantes
    for t, x, y in [("CUELLO BOTELLA", 2.75, 10.5), ("ESTRATÉGICO", 8.25, 10.5), ("NO CRÍTICO", 2.75, 0.5), ("APALANCAMIENTO", 8.25, 0.5)]:
        fig.add_annotation(x=x, y=y, text=t, showarrow=False, font=dict(size=16, color="#94A3B8", family="Arial Black"))

    # Burbujas
    for i, row in df.iterrows():
        fig.add_trace(go.Scatter(
            x=[row['Impacto']], y=[row['Riesgo']], mode='markers',
            name=str(row[label_col]),
            marker=dict(size=row['Gasto']/df['Gasto'].max()*45 + 25, line=dict(width=1.5, color='white')),
            hovertemplate=f"<b>{row[label_col]}</b><br>Gasto: {row['Gasto']:,.2f} €<extra></extra>"
        ))
    
    # CORRECCIÓN DE VISIBILIDAD: Ejes amplios para que no se pierdan puntos
    fig.update_layout(
        xaxis=dict(title="IMPACTO FINANCIERO", range=[-0.5, 11.5], gridcolor="#E2E8F0"),
        yaxis=dict(title="RIESGO DE SUMINISTRO", range=[-0.5, 11.5], gridcolor="#E2E8F0"),
        height=600, template="plotly_white",
        legend=dict(title=f"Categorías analizadas:", orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
    )
    return fig

# ── 6. LÓGICA DE DATOS ──
if menu == "📂 Gestión de Datos":
    archivo = st.file_uploader("Sube el archivo Excel", type=['xlsx'])
    if archivo:
        df = pd.read_excel(archivo)
        df['Gasto (€)'] = pd.to_numeric(df['Gasto (€)'], errors='coerce').fillna(0)
        total = df['Gasto (€)'].sum()
        
        def asignar_q(i, r):
            if i >= 6 and r >= 6: return 'Estratégico'
            elif i >= 6: return 'Apalancamiento'
            elif r >= 6: return 'Cuello de Botella'
            return 'No Crítico'

        # Agrupación Nivel 1
        n1 = df.groupby('Categoría').agg({'Gasto (€)': 'sum'}).reset_index()
        n1['Impacto'] = n1['Gasto (€)'].apply(lambda x: 9 if x/total > 0.15 else (6 if x/total > 0.05 else 3))
        n1['Riesgo'] = n1['Categoría'].apply(lambda x: 8 if any(k in str(x).upper() for k in ["ALIM", "ENER", "QUIM"]) else 4)
        n1['Cuadrante'] = n1.apply(lambda x: asignar_q(x['Impacto'], x['Riesgo']), axis=1)
        st.session_state['n1'] = n1.rename(columns={'Gasto (€)': 'Gasto'})

        # Agrupación Nivel 2
        n2 = df.groupby(['Categoría', 'Subcategoría']).agg({'Gasto (€)': 'sum', 'Proveedor': 'first'}).reset_index()
        n2['Impacto'] = n2['Gasto (€)'].apply(lambda x: 9 if x/total > 0.08 else (6 if x/total > 0.02 else 3))
        n2['Riesgo'] = n2['Categoría'].apply(lambda x: 8 if any(k in str(x).upper() for k in ["ALIM", "ENER", "QUIM"]) else 4)
        n2['Cuadrante'] = n2.apply(lambda x: asignar_q(x['Impacto'], x['Riesgo']), axis=1)
        st.session_state['n2'] = n2.rename(columns={'Gasto (€)': 'Gasto'})
        st.success("¡Datos procesados correctamente!")

# ── 7. DASHBOARD Y PDF ──
elif menu == "📊 Matriz de Kraljic":
    if 'n1' in st.session_state:
        sel_cat = st.selectbox("Selecciona Categoría para auditar:", st.session_state['n2']['Categoría'].unique())
        
        # Generamos las figuras para usarlas en pantalla y en PDF
        fig_macro = draw_kraljic_interactive(st.session_state['n1'], 'Categoría')
        df_micro = st.session_state['n2'][st.session_state['n2']['Categoría'] == sel_cat]
        fig_micro = draw_kraljic_interactive(df_micro, 'Subcategoría')

        # Botón PDF
        try:
            with st.spinner('Generando reporte con gráficas...'):
                pdf_bytes = create_pdf_report(st.session_state['n1'], st.session_state['n2'], sel_cat, fig_macro, fig_micro)
                st.download_button(
                    label="📥 Descargar Informe Completo (PDF con Gráficas)",
                    data=pdf_bytes,
                    file_name=f"Reporte_Sourcing_{sel_cat}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        except Exception as e:
            st.error(f"Error al generar imágenes para el PDF. Asegúrate de tener 'kaleido' instalado. Detalles: {e}")

        tab1, tab2 = st.tabs(["🏛️ Nivel 1: Macro-Categorías", "🔍 Nivel 2: Detalle Subcategorías"])
        
        with tab1:
            c1, c2 = st.columns([3, 1])
            with c1: st.plotly_chart(fig_macro, use_container_width=True)
            with c2:
                st.markdown("### Estrategias")
                for q in ['Estratégico', 'Apalancamiento', 'Cuello de Botella', 'No Crítico']:
                    if q in st.session_state['n1']['Cuadrante'].values:
                        clase = q.lower().replace(" ", "").replace("é", "e")
                        st.markdown(f"<div class='strategy-container est-{clase}'><strong>{q.upper()}</strong><br>{get_strategy_text(q)}</div>", unsafe_allow_html=True)
            st.dataframe(st.session_state['n1'].sort_values('Gasto', ascending=False), hide_index=True)

        with tab2:
            c3, c4 = st.columns([3, 1])
            with c3: st.plotly_chart(fig_micro, use_container_width=True)
            with c4:
                st.markdown("### Estrategia Grupo")
                for q in df_micro['Cuadrante'].unique():
                    clase = q.lower().replace(" ", "").replace("é", "e")
                    st.markdown(f"<div class='strategy-container est-{clase}'><strong>{q.upper()}</strong><br>{get_strategy_text(q)}</div>", unsafe_allow_html=True)
            st.dataframe(df_micro.sort_values('Gasto', ascending=False), hide_index=True)
    else:
        st.warning("⚠️ Carga datos primero.")
