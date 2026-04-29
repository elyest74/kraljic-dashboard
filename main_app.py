import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
import numpy as np # Para la dispersión de etiquetas

# Intentamos importar xlsxwriter para la plantilla Excel
try:
    import xlsxwriter
    XLSX_AVAILABLE = True
except ImportError:
    XLSX_AVAILABLE = False

# ── 1. CONFIGURACIÓN DE PÁGINA ──
st.set_page_config(page_title="Sourcing Strategy Hub | Elymar", page_icon="📈", layout="wide")

# Estilos CSS
st.markdown("""
    <style>
        .stDownloadButton>button { width: 100%; background-color: #059669 !important; color: white !important; border: none !important; }
        .main-header { color: #0F172A; font-size: 2rem; font-weight: 800; border-bottom: 3px solid #10B981; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

# ── 2. BARRA LATERAL ──
with st.sidebar:
    st.title("⚙️ Configuración")
    
    if XLSX_AVAILABLE:
        columns = ['Proveedor', 'Categoría', 'Subcategoría', 'Gasto (€)']
        df_template = pd.DataFrame(columns=columns)
        df_template.loc[0] = ['Proveedor de Prueba', 'ALIMENTACIÓN', 'Cacao', 1000000.00]
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_template.to_excel(writer, index=False, sheet_name='Datos')
        
        st.download_button(
            label="📥 Descargar Plantilla Excel (.xlsx)",
            data=output.getvalue(),
            file_name="Plantilla_Kraljic.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    st.divider()
    menu = st.radio("2. Navegación:", ["Carga de Datos", "Análisis de Matriz"])

# ── 3. PANTALLA 1: GESTIÓN DE DATOS ──
if menu == "Carga de Datos":
    st.markdown("<h1 class='main-header'>📥 Gestión de Sourcing</h1>", unsafe_allow_html=True)
    archivo = st.file_uploader("Sube tu archivo (Excel o CSV)", type=['xlsx', 'csv'])
    
    if archivo:
        df_input = pd.read_excel(archivo) if archivo.name.endswith('.xlsx') else pd.read_csv(archivo)
    else:
        df_input = pd.DataFrame(columns=['Proveedor', 'Categoría', 'Subcategoría', 'Gasto (€)'])
        df_input.loc[0] = ['Proveedor Ejemplo', 'LOGÍSTICA', 'Fletes', 250000.00]

    df_editor = st.data_editor(df_input, num_rows="dynamic", use_container_width=True)

    if st.button("🚀 PROCESAR DASHBOARD"):
        if not df_editor.empty:
            df_proc = df_editor.copy()
            df_proc['Gasto (€)'] = pd.to_numeric(df_proc['Gasto (€)'], errors='coerce').fillna(0)
            
            res_agrupado = df_proc.groupby('Subcategoría').agg({
                'Gasto (€)': 'sum',
                'Categoría': 'first',
                'Proveedor': lambda x: ', '.join(x.dropna().unique().astype(str))
            }).reset_index()
            
            total_g = res_agrupado['Gasto (€)'].sum()
            
            final_data = []
            for _, row in res_agrupado.iterrows():
                g = row['Gasto (€)']
                # Lógica de impacto y riesgo
                impacto = 9 if (g/total_g) > 0.15 else (6 if (g/total_g) > 0.05 else 3)
                cat = str(row['Categoría']).upper()
                riesgo = 8 if "ALIMENTACIÓN" in cat or "ENERGÍA" in cat else 4
                
                q = 'Estratégico' if impacto >= 6 and riesgo >= 6 else ('Apalancamiento' if impacto >= 6 else ('Cuello de Botella' if riesgo >= 6 else 'No Crítico'))
                
                final_data.append({
                    'Subcategoría': row['Subcategoría'], 'Proveedores': row['Proveedor'],
                    'Gasto': g, 'Impacto': impacto, 'Riesgo': riesgo, 'Cuadrante': q
                })
            
            st.session_state['data_final'] = pd.DataFrame(final_data)
            st.success("✅ Datos procesados. Cambia a la pestaña de Análisis.")
        else:
            st.error("La tabla está vacía.")

# ── 4. PANTALLA 2: ANÁLISIS DE MATRIZ ──
elif menu == "Análisis de Matriz":
    st.markdown("<h1 class='main-header'>📊 Dashboard de Decisiones</h1>", unsafe_allow_html=True)
    
    if 'data_final' in st.session_state:
        res = st.session_state['data_final']
        
        fig = go.Figure()

        # AÑADIR CUADRANTES (FONDO)
        # 1. Apalancamiento (Verde)
        fig.add_shape(type="rect", x0=5.5, y0=0, x1=11, y1=5.5, fillcolor="rgba(16, 185, 129, 0.15)", line_width=0, layer="below")
        # 2. Estratégico (Rojo)
        fig.add_shape(type="rect", x0=5.5, y0=5.5, x1=11, y1=11, fillcolor="rgba(239, 68, 68, 0.15)", line_width=0, layer="below")
        # 3. Cuello de Botella (Naranja)
        fig.add_shape(type="rect", x0=0, y0=5.5, x1=5.5, y1=11, fillcolor="rgba(245, 158, 11, 0.15)", line_width=0, layer="below")
        # 4. No Crítico (Gris)
        fig.add_shape(type="rect", x0=0, y0=0, x1=5.5, y1=5.5, fillcolor="rgba(100, 116, 139, 0.15)", line_width=0, layer="below")

        # LÍNEAS DIVISORIAS
        fig.add_hline(y=5.5, line_width=2, line_dash="dash", line_color="black", opacity=0.3)
        fig.add_vline(x=5.5, line_width=2, line_dash="dash", line_color="black", opacity=0.3)

        # TEXTO DE CUADRANTES
        fig.add_annotation(x=2.75, y=10.5, text="CUELLO DE BOTELLA", showarrow=False, font=dict(color="#B45309", size=14, family="Arial Black"))
        fig.add_annotation(x=8.25, y=10.5, text="ESTRATÉGICO", showarrow=False, font=dict(color="#B91C1C", size=14, family="Arial Black"))
        fig.add_annotation(x=2.75, y=0.5, text="NO CRÍTICO", showarrow=False, font=dict(color="#475569", size=14, family="Arial Black"))
        fig.add_annotation(x=8.25, y=0.5, text="APALANCAMIENTO", showarrow=False, font=dict(color="#047857", size=14, family="Arial Black"))

        # DISPERSIÓN (Jittering) para que las etiquetas no se pisen
        # Añadimos un pequeño valor aleatorio solo a la posición del texto, no al punto real
        res['Impacto_Jitter'] = res['Impacto'] + np.random.uniform(-0.2, 0.2, len(res))
        res['Riesgo_Jitter'] = res['Riesgo'] + np.random.uniform(0.2, 0.5, len(res)) # Siempre un poco arriba

        # PUNTOS DE DATOS
        fig.add_trace(go.Scatter(
            x=res['Impacto'], 
            y=res['Riesgo'], 
            mode='markers',
            marker=dict(size=res['Gasto']/res['Gasto'].max()*50 + 20, color='#0F172A', line=dict(width=2, color='white')),
            name="Materias Primas",
            customdata=np.stack((res['Subcategoría'], res['Gasto'], res['Proveedores']), axis=-1),
            hovertemplate="<b>%{customdata[0]}</b><br>Gasto: %{customdata[1]:,.2f} €<br>Proveedores: %{customdata[2]}<extra></extra>"
        ))

        # ETIQUETAS SEPARADAS
        fig.add_trace(go.Scatter(
            x=res['Impacto_Jitter'],
            y=res['Riesgo_Jitter'],
            mode='text',
            text=res['Subcategoría'],
            textfont=dict(size=11, color="#1E293B"),
            showlegend=False
        ))

        fig.update_layout(
            xaxis=dict(title="<b>IMPACTO FINANCIERO</b>", range=[0, 11], gridcolor="#e2e8f0"),
            yaxis=dict(title="<b>RIESGO DE SUMINISTRO</b>", range=[0, 11], gridcolor="#e2e8f0"),
            template="plotly_white", height=700, margin=dict(l=40, r=40, t=40, b=40)
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # Tablas detalladas
        for q in ['Estratégico', 'Apalancamiento', 'Cuello de Botella', 'No Crítico']:
            subset = res[res['Cuadrante'] == q]
            if not subset.empty:
                with st.expander(f"📋 Ver detalle de items: {q.upper()}"):
                    st.dataframe(
                        subset[['Subcategoría', 'Proveedores', 'Gasto']].rename(columns={'Gasto': 'Gasto Anual (€)'}),
                        hide_index=True,
                        column_config={"Gasto Anual (€)": st.column_config.NumberColumn(format="%.2f €", width=200)}
                    )
    else:
        st.warning("⚠️ No hay datos cargados. Por favor, ve a 'Carga de Datos'.")
