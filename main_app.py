import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io

# ── 1. CONFIGURACIÓN DE PÁGINA ──
st.set_page_config(
    page_title="Strategic Sourcing Hub | Elymar Estévez",
    page_icon="💼",
    layout="wide"
)

# Estilos CSS
st.markdown("""
    <style>
        .stButton>button { width: 100%; border-radius: 5px; font-weight: bold; }
        .stDownloadButton>button { 
            width: 100%; 
            background-color: #059669 !important; 
            color: white !important; 
            border: none !important;
        }
        .main-header { color: #0F172A; font-size: 2.2rem; font-weight: 800; border-bottom: 3px solid #10B981; padding-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# ── 2. BARRA LATERAL CON DESCARGA EXCEL ──
with st.sidebar:
    st.title("⚙️ Panel de Control")
    
    st.subheader("1. Plantilla de Datos")
    
    # --- LÓGICA PARA CREAR EXCEL EN MEMORIA ---
    # Creamos el dataframe con las 4 columnas solicitadas
    columns = ['Proveedor', 'Categoría', 'Subcategoría', 'Gasto (€)']
    template_df = pd.DataFrame(columns=columns)
    # Añadimos una fila de ejemplo
    template_df.loc[0] = ['Proveedor Global S.A.', 'MATERIA PRIMA ALIMENTACIÓN', 'Cacao en Polvo', 1500000.00]
    
    # Función para convertir dataframe a Excel
    def to_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Plantilla_Compras')
            # Ajuste de formato básico
            workbook  = writer.book
            worksheet = writer.sheets['Plantilla_Compras']
            header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1})
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
        return output.getvalue()

    excel_data = to_excel(template_df)
    
    st.download_button(
        label="📥 Descargar Plantilla Excel (.xlsx)",
        data=excel_data,
        file_name="Plantilla_Kraljic_Sourcing.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        help="Descarga este Excel, rellénalo con tus datos y súbelo después."
    )
    
    st.divider()
    
    menu = st.radio(
        "2. Fase del Análisis:",
        ["Gestión y Carga", "Dashboard Estratégico"],
        index=0
    )
    
    st.divider()
    st.caption("Desarrollado por Elymar Estévez")

# ── 3. PANTALLA 1: GESTIÓN DE DATOS ──
if menu == "Gestión y Carga":
    st.markdown("<h1 class='main-header'>📥 Carga de Datos de Materias Primas</h1>", unsafe_allow_html=True)
    
    archivo = st.file_uploader("Sube tu archivo Excel o CSV", type=['xlsx', 'csv'])
    
    if archivo:
        if archivo.name.endswith('.xlsx'):
            df_input = pd.read_excel(archivo)
        else:
            df_input = pd.read_csv(archivo)
    else:
        # Datos iniciales vacíos con las nuevas columnas
        df_input = pd.DataFrame(columns=['Proveedor', 'Categoría', 'Subcategoría', 'Gasto (€)'])
        # Ejemplo visual
        df_input.loc[0] = ['Ejemplo Prov', 'PACKAGING', 'Film Retráctil', 450000.00]

    st.subheader("📝 Editor de Datos")
    st.info("Puedes editar los valores directamente en la tabla de abajo antes de procesar.")
    df_editor = st.data_editor(df_input, num_rows="dynamic", use_container_width=True)

    if st.button("🚀 PROCESAR Y CONSOLIDAR COMPRAS"):
        if df_editor.empty or df_editor['Gasto (€)'].sum() == 0:
            st.error("Por favor, asegúrate de tener datos con importes de gasto válidos.")
        else:
            # Consolidación: Sumar gasto por subcategoría para la matriz
            df_cons = df_editor.copy()
            df_cons['Gasto (€)'] = pd.to_numeric(df_cons['Gasto (€)'], errors='coerce').fillna(0)
            
            # Agrupamos por Subcategoría para la Matriz
            res_agrupado = df_cons.groupby('Subcategoría').agg({
                'Gasto (€)': 'sum',
                'Categoría': 'first',
                'Proveedor': lambda x: ', '.join(x.unique())
            }).reset_index()
            
            total_g = res_agrupado['Gasto (€)'].sum()
            
            final_list = []
            for _, row in res_agrupado.iterrows():
                g = row['Gasto (€)']
                # Lógica de Impacto (Pareto)
                impacto = 9 if (g/total_g) > 0.15 else (6 if (g/total_g) > 0.05 else 3)
                # Lógica de Riesgo (Basada en complejidad de Categoría)
                cat = str(row['Categoría']).upper()
                riesgo = 8 if "ALIMENTACIÓN" in cat or "ENERGÍA" in cat else 4
                
                if impacto >= 6 and riesgo >= 6: q = 'Estratégico'
                elif impacto >= 6: q = 'Apalancamiento'
                elif riesgo >= 6: q = 'Cuello de Botella'
                else: q = 'No Crítico'
                
                final_list.append({
                    'Subcategoría': row['Subcategoría'],
                    'Proveedores': row['Proveedor'],
                    'Gasto': g,
                    'Impacto': impacto,
                    'Riesgo': riesgo,
                    'Cuadrante': q
                })
            
            st.session_state['data_final'] = pd.DataFrame(final_list)
            st.success("✅ Análisis realizado con éxito. Ve al Dashboard Estratégico.")
            st.balloons()

# ── 4. PANTALLA 2: DASHBOARD ──
elif menu == "Dashboard Estratégico":
    st.markdown("<h1 class='main-header'>📊 Cuadro de Mando: Matriz de Kraljic</h1>", unsafe_allow_html=True)
    
    if 'data_final' not in st.session_state:
        st.warning("⚠️ No hay datos. Sube un archivo en 'Gestión y Carga'.")
    else:
        res = st.session_state['data_final']
        
        # KPIs
        c1, c2, c3 = st.columns(3)
        c1.metric("Gasto Total", f"{res['Gasto'].sum():,.2f} €")
        c2.metric("Nº Subcategorías", len(res))
        c3.metric("Cuadrante Crítico", res.loc[res['Gasto'].idxmax(), 'Cuadrante'])

        st.divider()

        # Gráfico Interactivo
        fig = go.Figure()
        
        # Cuadrantes
        fig.add_shape(type="rect", x0=5.5, y0=0, x1=11, y1=5.5, fillcolor="#10B981", opacity=0.1, line_width=0) # Apalancamiento
        fig.add_shape(type="rect", x0=5.5, y0=5.5, x1=11, y1=11, fillcolor="#EF4444", opacity=0.1, line_width=0) # Estratégico
        fig.add_shape(type="rect", x0=0, y0=5.5, x1=5.5, y1=11, fillcolor="#F59E0B", opacity=0.1, line_width=0) # Cuello Botella
        fig.add_shape(type="rect", x0=0, y0=0, x1=5.5, y1=5.5, fillcolor="#64748B", opacity=0.1, line_width=0) # No Crítico

        fig.add_trace(go.Scatter(
            x=res['Impacto'], y=res['Riesgo'], mode='markers+text',
            text=res['Subcategoría'], textposition="top center",
            marker=dict(size=25, color='#0F172A', line=dict(width=2, color='white')),
            hovertemplate="Sub: %{text}<br>Gasto: %{customdata:,.2f}€<br>Proveedores: %{text}",
            customdata=res['Gasto']
        ))
        
        fig.update_layout(xaxis=dict(title="Impacto Financiero", range=[0, 11]), yaxis=dict(title="Riesgo Suministro", range=[0, 11]), height=600)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📋 Recomendaciones por Cuadrante")
        for q in ['Estratégico', 'Apalancamiento', 'Cuello de Botella', 'No Crítico']:
            items = res[res['Cuadrante'] == q]
            if not items.empty:
                with st.expander(f"🛒 Ver {q.upper()}"):
                    st.dataframe(
                        items[['Subcategoría', 'Proveedores', 'Gasto']].rename(columns={'Gasto': 'Gasto Total (€)'}),
                        hide_index=True,
                        column_config={
                            "Subcategoría": st.column_config.TextColumn("Subcategoría", width=250),
                            "Proveedores": st.column_config.TextColumn("Proveedores", width=250),
                            "Gasto Total (€)": st.column_config.NumberColumn("Gasto Total (€)", format="%.2f €", width=200)
                        }
                    )
