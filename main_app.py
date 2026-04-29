import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io

# Intentamos importar xlsxwriter para evitar que la app se rompa si no está
try:
    import xlsxwriter
    XLSX_AVAILABLE = True
except ImportError:
    XLSX_AVAILABLE = False

# ── 1. CONFIGURACIÓN DE PÁGINA ──
st.set_page_config(
    page_title="Sourcing Strategy Hub | Elymar",
    page_icon="📈",
    layout="wide"
)

# Estilos CSS
st.markdown("""
    <style>
        .stDownloadButton>button { 
            width: 100%; background-color: #059669 !important; color: white !important; border: none !important;
        }
        .main-header { color: #0F172A; font-size: 2rem; font-weight: 800; border-bottom: 3px solid #10B981; }
    </style>
""", unsafe_allow_html=True)

# ── 2. BARRA LATERAL ──
with st.sidebar:
    st.title("⚙️ Configuración")
    st.subheader("1. Plantilla de Datos")
    
    # Lógica de descarga Excel
    if XLSX_AVAILABLE:
        columns = ['Proveedor', 'Categoría', 'Subcategoría', 'Gasto (€)']
        df_template = pd.DataFrame(columns=columns)
        df_template.loc[0] = ['Proveedor de Prueba', 'ALIMENTACIÓN', 'Cacao', 1000000.00]

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_template.to_excel(writer, index=False, sheet_name='Datos')
            workbook = writer.book
            worksheet = writer.sheets['Datos']
            header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1})
            for col_num, value in enumerate(df_template.columns.values):
                worksheet.write(0, col_num, value, header_fmt)
        
        st.download_button(
            label="📥 Descargar Plantilla Excel (.xlsx)",
            data=output.getvalue(),
            file_name="Plantilla_Kraljic.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("Error: Instala 'xlsxwriter' para descargar el Excel.")

    st.divider()
    menu = st.radio("2. Navegación:", ["Carga de Datos", "Análisis de Matriz"])

# ── 3. PANTALLA 1: GESTIÓN ──
if menu == "Carga de Datos":
    st.markdown("<h1 class='main-header'>📥 Gestión de Sourcing</h1>", unsafe_allow_html=True)
    
    archivo = st.file_uploader("Sube tu archivo (Excel o CSV)", type=['xlsx', 'csv'])
    
    if archivo:
        if archivo.name.endswith('.xlsx'):
            df_input = pd.read_excel(archivo)
        else:
            df_input = pd.read_csv(archivo)
    else:
        # Ejemplo para que no aparezca vacío
        df_input = pd.DataFrame(columns=['Proveedor', 'Categoría', 'Subcategoría', 'Gasto (€)'])
        df_input.loc[0] = ['Proveedor Ejemplo', 'LOGÍSTICA', 'Fletes', 250000.00]

    st.subheader("📝 Editor de Datos")
    df_editor = st.data_editor(df_input, num_rows="dynamic", use_container_width=True)

    if st.button("🚀 PROCESAR DASHBOARD"):
        if not df_editor.empty:
            df_proc = df_editor.copy()
            df_proc['Gasto (€)'] = pd.to_numeric(df_proc['Gasto (€)'], errors='coerce').fillna(0)
            
            # Agrupación por subcategoría para la matriz
            res_agrupado = df_proc.groupby('Subcategoría').agg({
                'Gasto (€)': 'sum',
                'Categoría': 'first',
                'Proveedor': lambda x: ', '.join(x.dropna().unique())
            }).reset_index()
            
            total_g = res_agrupado['Gasto (€)'].sum()
            
            final_data = []
            for _, row in res_agrupado.iterrows():
                g = row['Gasto (€)']
                impacto = 9 if (g/total_g) > 0.15 else (6 if (g/total_g) > 0.05 else 3)
                cat = str(row['Categoría']).upper()
                riesgo = 8 if "ALIMENTACIÓN" in cat or "ENERGÍA" in cat else 4
                
                q = 'Estratégico' if impacto >= 6 and riesgo >= 6 else ('Apalancamiento' if impacto >= 6 else ('Cuello de Botella' if riesgo >= 6 else 'No Crítico'))
                
                final_data.append({
                    'Subcategoría': row['Subcategoría'], 'Proveedores': row['Proveedor'],
                    'Gasto': g, 'Impacto': impacto, 'Riesgo': riesgo, 'Cuadrante': q
                })
            
            st.session_state['data_final'] = pd.DataFrame(final_data)
            st.success("✅ Datos procesados correctamente.")
        else:
            st.error("La tabla está vacía.")

# ── 4. PANTALLA 2: MATRIZ ──
elif menu == "Análisis de Matriz":
    st.markdown("<h1 class='main-header'>📊 Dashboard de Decisiones</h1>", unsafe_allow_html=True)
    
    if 'data_final' in st.session_state:
        res = st.session_state['data_final']
        
        # Gráfico
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=res['Impacto'], y=res['Riesgo'], mode='markers+text',
            text=res['Subcategoría'], textposition="top center",
            marker=dict(size=25, color='#0F172A'),
            hovertemplate="Gasto: %{customdata:,.2f} €", customdata=res['Gasto']
        ))
        fig.update_layout(xaxis=dict(title="Impacto", range=[0, 11]), yaxis=dict(title="Riesgo", range=[0, 11]), height=600)
        st.plotly_chart(fig, use_container_width=True)

        # Tablas de detalle
        for q in ['Estratégico', 'Apalancamiento', 'Cuello de Botella', 'No Crítico']:
            subset = res[res['Cuadrante'] == q]
            if not subset.empty:
                with st.expander(f"Ver {q.upper()}"):
                    st.dataframe(
                        subset[['Subcategoría', 'Proveedores', 'Gasto']].rename(columns={'Gasto': 'Gasto (€)'}),
                        hide_index=True,
                        column_config={"Gasto (€)": st.column_config.NumberColumn(format="%.2f €", width=200)}
                    )
    else:
        st.warning("Carga datos primero.")
