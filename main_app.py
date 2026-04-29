import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
import numpy as np

# ── 1. CONFIGURACIÓN DE REQUISITOS ──
try:
    import xlsxwriter
    XLS_OK = True
except:
    XLS_OK = False

st.set_page_config(page_title="Sourcing Intelligence | Elymar", layout="wide")

# ── 2. ESTILOS Y NAVEGACIÓN ──
st.markdown("""
    <style>
        .main-header { color: #0F172A; font-size: 2.2rem; font-weight: 800; border-bottom: 3px solid #10B981; }
        .stDownloadButton>button { background-color: #059669 !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("⚙️ Configuración")
    if XLS_OK:
        cols = ['Proveedor', 'Categoría', 'Subcategoría', 'Gasto (€)']
        df_temp = pd.DataFrame(columns=cols)
        df_temp.loc[0] = ['Proveedor X', 'MATERIA PRIMA', 'Cacao', 1000000]
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as w:
            df_temp.to_excel(w, index=False)
        st.download_button("📥 Descargar Plantilla Excel", out.getvalue(), "Plantilla.xlsx")
    
    st.divider()
    menu = st.radio("Sección:", ["Carga de Datos", "Matriz de Decisiones"])

# ── 3. LÓGICA DE DATOS ──
if menu == "Carga de Datos":
    st.markdown("<h1 class='main-header'>📥 Gestión de Datos</h1>", unsafe_allow_html=True)
    archivo = st.file_uploader("Sube tu archivo", type=['xlsx', 'csv'])
    df_input = pd.read_excel(archivo) if archivo and archivo.name.endswith('.xlsx') else (pd.read_csv(archivo) if archivo else pd.DataFrame(columns=['Proveedor', 'Categoría', 'Subcategoría', 'Gasto (€)']))
    
    if df_input.empty:
        df_input = pd.DataFrame({'Proveedor':['Prov A', 'Prov B'], 'Categoría':['CAT1', 'CAT2'], 'Subcategoría':['Sub 1', 'Sub 2'], 'Gasto (€)':[500000, 150000]})

    df_ed = st.data_editor(df_input, num_rows="dynamic", use_container_width=True)

    if st.button("🚀 PROCESAR MATRIZ"):
        df_proc = df_ed.copy()
        df_proc['Gasto (€)'] = pd.to_numeric(df_proc['Gasto (€)'], errors='coerce').fillna(0)
        res = df_proc.groupby('Subcategoría').agg({'Gasto (€)':'sum', 'Categoría':'first', 'Proveedor': lambda x: ', '.join(x.unique().astype(str))}).reset_index()
        
        total = res['Gasto (€)'].sum()
        final = []
        for _, r in res.iterrows():
            g = r['Gasto (€)']
            imp = 9 if (g/total) > 0.15 else (6 if (g/total) > 0.05 else 3)
            riesgo = 8 if "ALIMENTACIÓN" in str(r['Categoría']).upper() else 4
            q = 'Estratégico' if imp >= 6 and riesgo >= 6 else ('Apalancamiento' if imp >= 6 else ('Cuello de Botella' if riesgo >= 6 else 'No Crítico'))
            final.append({'Subcategoría': r['Subcategoría'], 'Proveedores': r['Proveedor'], 'Gasto': g, 'Impacto': imp, 'Riesgo': riesgo, 'Cuadrante': q})
        
        st.session_state['df_kraljic'] = pd.DataFrame(final)
        st.success("¡Datos listos!")

# ── 4. DASHBOARD VISUAL (SOLUCIÓN A SUPERPOSICIÓN) ──
elif menu == "Matriz de Decisiones":
    st.markdown("<h1 class='main-header'>📊 Matriz de Kraljic</h1>", unsafe_allow_html=True)
    
    if 'df_kraljic' in st.session_state:
        df = st.session_state['df_kraljic'].copy()
        
        # --- ALGORITMO DE ANTI-SUPERPOSICIÓN ---
        # Si varios puntos tienen el mismo (Impacto, Riesgo), los separamos visualmente
        df['count'] = df.groupby(['Impacto', 'Riesgo']).cumcount()
        # Desplazamos las etiquetas en un círculo alrededor del punto real
        angle = df['count'] * (2 * np.pi / 8) # Distribuye hasta 8 etiquetas alrededor
        df['X_text'] = df['Impacto'] + np.cos(angle) * 0.4
        df['Y_text'] = df['Riesgo'] + np.sin(angle) * 0.4

        fig = go.Figure()

        # Cuadrantes de fondo
        fig.add_shape(type="rect", x0=5.5, y0=5.5, x1=11, y1=11, fillcolor="rgba(239, 68, 68, 0.2)", line_width=0) # Estratégico
        fig.add_shape(type="rect", x0=5.5, y0=0, x1=11, y1=5.5, fillcolor="rgba(16, 185, 129, 0.2)", line_width=0) # Apalancamiento
        fig.add_shape(type="rect", x0=0, y0=5.5, x1=5.5, y1=11, fillcolor="rgba(245, 158, 11, 0.2)", line_width=0) # Cuello Botella
        fig.add_shape(type="rect", x0=0, y0=0, x1=5.5, y1=5.5, fillcolor="rgba(100, 116, 139, 0.2)", line_width=0) # No Crítico

        # Etiquetas de cuadrantes
        quads = [("ESTRATÉGICO", 8.25, 10.5), ("APALANCAMIENTO", 8.25, 0.5), ("CUELLO BOTELLA", 2.75, 10.5), ("NO CRÍTICO", 2.75, 0.5)]
        for name, x, y in quads:
            fig.add_annotation(x=x, y=y, text=name, showarrow=False, font=dict(size=16, color="grey", family="Arial Black"), opacity=0.5)

        # Puntos reales (Burbujas)
        fig.add_trace(go.Scatter(
            x=df['Impacto'], y=df['Riesgo'], mode='markers',
            marker=dict(size=df['Gasto']/df['Gasto'].max()*40 + 20, color='#0F172A', line=dict(width=2, color='white')),
            text=df['Subcategoría'],
            hovertemplate="<b>%{text}</b><br>Gasto: %{customdata:,.2f}€<extra></extra>",
            customdata=df['Gasto']
        ))

        # Capa de Texto (Separada para evitar colisiones)
        fig.add_trace(go.Scatter(
            x=df['X_text'], y=df['Y_text'], mode='text',
            text=df['Subcategoría'],
            textfont=dict(size=12, color="#1E293B", family="Arial Black"),
            showlegend=False
        ))

        fig.update_layout(
            xaxis=dict(title="IMPACTO FINANCIERO", range=[-0.5, 11.5], gridcolor="#eee"),
            yaxis=dict(title="RIESGO DE SUMINISTRO", range=[-0.5, 11.5], gridcolor="#eee"),
            height=700, template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)

        # Tabla con formato de miles corregido (200px de ancho)
        st.write("### Detalle por Subcategoría")
        st.dataframe(
            df[['Subcategoría', 'Proveedores', 'Gasto', 'Cuadrante']],
            hide_index=True,
            column_config={
                "Subcategoría": st.column_config.TextColumn(width=300),
                "Gasto": st.column_config.NumberColumn("Gasto (€)", format="%.2f €", width=200)
            },
            use_container_width=True
        )
    else:
        st.warning("Carga datos en la pestaña anterior.")
