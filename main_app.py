import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
import os
from PIL import Image
from fpdf import FPDF

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

# ── 2. FUNCIONES DE APOYO CORREGIDAS ──
def get_strategy_text(cuadrante):
    data = {
        'Estratégico': "Alianzas a largo plazo, co-diseño y gestión estrecha de la relación (SRM).",
        'Apalancamiento': "Licitaciones competitivas, optimización de precios y consolidación de volúmenes.",
        'Cuello de Botella': "Asegurar volumen, buscar sustitutos y reducir dependencia de proveedores.",
        'No Crítico': "Automatización de compras, catálogos e-procurement y reducción de burocracia."
    }
    return data.get(cuadrante, "")

def create_pdf_report(df_n1, df_n2, categoria_sel):
    # Inicializar PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Encabezado Corporativo
    pdf.set_fill_color(30, 41, 59) 
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, "INFORME ESTRATÉGICO DE COMPRAS", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Desarrollado por: Elymar Estévez", ln=True, align='C')
    
    pdf.set_text_color(0, 0, 0)
    pdf.ln(25)
    
    # Bloque 1: Resumen Macro
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "1. Resumen Global por Categorías", ln=True)
    pdf.set_font("Arial", '', 11)
    gasto_total = df_n1['Gasto'].sum()
    pdf.cell(0, 10, f"Gasto Total Analizado: {gasto_total:,.2f} EUR", ln=True)
    pdf.ln(5)
    
    # Tabla Nivel 1
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(80, 10, "Categoría", 1, 0, 'C', True)
    pdf.cell(50, 10, "Gasto", 1, 0, 'C', True)
    pdf.cell(50, 10, "Cuadrante", 1, 1, 'C', True)
    
    pdf.set_font("Arial", '', 10)
    for _, row in df_n1.iterrows():
        pdf.cell(80, 10, str(row['Categoría'])[:40], 1)
        pdf.cell(50, 10, f"{row['Gasto']:,.2f}", 1, 0, 'R')
        pdf.cell(50, 10, str(row['Cuadrante']), 1, 1, 'C')
    
    # Bloque 2: Detalle por Categoría
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"2. Análisis Detallado: {categoria_sel}", ln=True)
    pdf.ln(5)
    
    df_f = df_n2[df_n2['Categoría'] == categoria_sel]
    
    # Estrategias
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, "Estrategias de Compra Aplicables:", ln=True)
    pdf.set_font("Arial", '', 10)
    for q in df_f['Cuadrante'].unique():
        pdf.multi_cell(0, 7, f"- {q.upper()}: {get_strategy_text(q)}", border=0)
    
    pdf.ln(10)
    # Tabla Nivel 2
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(70, 10, "Subcategoría", 1, 0, 'C', True)
    pdf.cell(60, 10, "Proveedor", 1, 0, 'C', True)
    pdf.cell(50, 10, "Gasto (EUR)", 1, 1, 'C', True)
    
    pdf.set_font("Arial", '', 8)
    for _, row in df_f.sort_values('Gasto', ascending=False).iterrows():
        pdf.cell(70, 10, str(row['Subcategoría'])[:38], 1)
        pdf.cell(60, 10, str(row['Proveedor'])[:33], 1)
        pdf.cell(50, 10, f"{row['Gasto']:,.2f}", 1, 1, 'R')

    # CORRECCIÓN CLAVE: Devolver bytes reales
    return bytes(pdf.output())

# ── 3. BARRA LATERAL (BRANDING) ──
with st.sidebar:
    if os.path.exists("elymar.png"):
        st.image(Image.open("elymar.png"), use_container_width=True)
    st.markdown(f"<div style='text-align: center; font-weight: bold; font-size: 1.2rem;'>Elymar Estévez</div>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("Navegación:", ["📂 Gestión de Datos", "📊 Matriz de Kraljic"], index=1)
    
    # Plantilla Excel
    try:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as w:
            pd.DataFrame(columns=['Proveedor', 'Categoría', 'Subcategoría', 'Gasto (€)']).to_excel(w, index=False)
        st.download_button("📥 Descargar Plantilla", buf.getvalue(), "plantilla_elymar.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except: pass

# ── 4. CABECERA ──
st.markdown("""
    <div class="header-banner">
        <h1>Sourcing Strategic Intelligence</h1>
        <p>Dashboard Interactivo para Decisiones de Compra</p>
        <div class="author-tag">Desarrollado por Elymar Estévez</div>
    </div>
""", unsafe_allow_html=True)

# ── 5. FUNCIÓN DE MATRIZ ──
def draw_kraljic_interactive(df, label_col):
    fig = go.Figure()
    # Fondos
    fig.add_shape(type="rect", x0=0, y0=5.5, x1=5.5, y1=11, fillcolor="#FEF3C7", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=5.5, y0=5.5, x1=11, y1=11, fillcolor="#FEE2E2", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=0, y0=0, x1=5.5, y1=5.5, fillcolor="#F1F5F9", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=5.5, y0=0, x1=11, y1=5.5, fillcolor="#D1FAE5", line_width=0, layer="below")

    # Anotaciones
    quads = [("CUELLO BOTELLA", 2.75, 10.5), ("ESTRATÉGICO", 8.25, 10.5), ("NO CRÍTICO", 2.75, 0.5), ("APALANCAMIENTO", 8.25, 0.5)]
    for t, x, y in quads:
        fig.add_annotation(x=x, y=y, text=t, showarrow=False, font=dict(size=18, color="#94A3B8", family="Arial Black"))

    # Puntos
    for i, row in df.iterrows():
        fig.add_trace(go.Scatter(
            x=[row['Impacto']], y=[row['Riesgo']], mode='markers',
            name=str(row[label_col]),
            marker=dict(size=row['Gasto']/df['Gasto'].max()*45 + 25, line=dict(width=1, color='white')),
            hovertemplate=f"<b>{row[label_col]}</b><br>Gasto: {row['Gasto']:,.2f} €<br>Cuadrante: {row['Cuadrante']}<extra></extra>"
        ))
    
    fig.update_layout(
        xaxis=dict(title="IMPACTO FINANCIERO", range=[-0.2, 11.2]),
        yaxis=dict(title="RIESGO DE SUMINISTRO", range=[-0.2, 11.2]),
        height=650, template="plotly_white",
        legend=dict(title=f"Leyenda: {label_col}", orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
    )
    return fig

# ── 6. LÓGICA DE DATOS ──
if menu == "📂 Gestión de Datos":
    archivo = st.file_uploader("Sube el archivo Excel de compras", type=['xlsx'])
    if archivo:
        df = pd.read_excel(archivo)
        df['Gasto (€)'] = pd.to_numeric(df['Gasto (€)'], errors='coerce').fillna(0)
        total = df['Gasto (€)'].sum()
        
        def asignar_q(i, r):
            if i >= 6 and r >= 6: return 'Estratégico'
            elif i >= 6: return 'Apalancamiento'
            elif r >= 6: return 'Cuello de Botella'
            return 'No Crítico'

        # Nivel 1
        n1 = df.groupby('Categoría').agg({'Gasto (€)': 'sum'}).reset_index()
        n1['Impacto'] = n1['Gasto (€)'].apply(lambda x: 9 if x/total > 0.15 else (6 if x/total > 0.05 else 3))
        n1['Riesgo'] = n1['Categoría'].apply(lambda x: 8 if any(k in str(x).upper() for k in ["ALIM", "ENER", "QUIM"]) else 4)
        n1['Cuadrante'] = n1.apply(lambda x: asignar_q(x['Impacto'], x['Riesgo']), axis=1)
        st.session_state['n1'] = n1.rename(columns={'Gasto (€)': 'Gasto'})

        # Nivel 2
        n2 = df.groupby(['Categoría', 'Subcategoría']).agg({'Gasto (€)': 'sum', 'Proveedor': 'first'}).reset_index()
        n2['Impacto'] = n2['Gasto (€)'].apply(lambda x: 9 if x/total > 0.08 else (6 if x/total > 0.02 else 3))
        n2['Riesgo'] = n2['Categoría'].apply(lambda x: 8 if any(k in str(x).upper() for k in ["ALIM", "ENER", "QUIM"]) else 4)
        n2['Cuadrante'] = n2.apply(lambda x: asignar_q(x['Impacto'], x['Riesgo']), axis=1)
        st.session_state['n2'] = n2.rename(columns={'Gasto (€)': 'Gasto'})
        st.success("✅ Datos procesados con éxito.")

# ── 7. DASHBOARD MATRIZ ──
elif menu == "📊 Matriz de Kraljic":
    if 'n1' in st.session_state:
        # Selección de categoría para el reporte
        sel_cat = st.selectbox("Categoría para el análisis detallado:", st.session_state['n2']['Categoría'].unique())
        
        # Botón de Descarga PDF con corrección de bytes
        try:
            pdf_bytes = create_pdf_report(st.session_state['n1'], st.session_state['n2'], sel_cat)
            st.download_button(
                label="📄 Descargar Informe PDF de " + sel_cat,
                data=pdf_bytes,
                file_name=f"Reporte_Kraljic_{sel_cat.replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error preparando el PDF: {e}")

        tab1, tab2 = st.tabs(["🏛️ Visión Macro", "🔍 Visión Micro"])
        
        with tab1:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.plotly_chart(draw_kraljic_interactive(st.session_state['n1'], 'Categoría'), use_container_width=True)
            with col2:
                st.markdown("### 💡 Estrategia Global")
                for q in ['Estratégico', 'Apalancamiento', 'Cuello de Botella', 'No Crítico']:
                    if q in st.session_state['n1']['Cuadrante'].values:
                        clase = q.lower().replace(" ", "").replace("é", "e")
                        st.markdown(f"<div class='strategy-container est-{clase}'><strong>{q.upper()}</strong><br>{get_strategy_text(q)}</div>", unsafe_allow_html=True)
            st.dataframe(st.session_state['n1'].sort_values('Gasto', ascending=False), hide_index=True, column_config={"Gasto": st.column_config.NumberColumn(format="%.2f €", width=200)})

        with tab2:
            df_f = st.session_state['n2'][st.session_state['n2']['Categoría'] == sel_cat]
            col3, col4 = st.columns([3, 1])
            with col3:
                st.plotly_chart(draw_kraljic_interactive(df_f, 'Subcategoría'), use_container_width=True)
            with col4:
                st.markdown("### 💡 Estrategia del Grupo")
                for q in df_f['Cuadrante'].unique():
                    clase = q.lower().replace(" ", "").replace("é", "e")
                    st.markdown(f"<div class='strategy-container est-{clase}'><strong>{q.upper()}</strong><br>{get_strategy_text(q)}</div>", unsafe_allow_html=True)
            st.dataframe(df_f[['Subcategoría', 'Proveedor', 'Gasto', 'Cuadrante']].sort_values('Gasto', ascending=False), hide_index=True, column_config={"Gasto": st.column_config.NumberColumn(format="%.2f €", width=200)})
    else:
        st.warning("⚠️ Sube primero los datos en la pestaña 'Gestión de Datos'.")
