import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io

# ── 1. CONFIGURACIÓN PROFESIONAL ──
st.set_page_config(page_title="Strategic Sourcing Dashboard", layout="wide")

# Estilo para mejorar la legibilidad de las tablas y botones
st.markdown("""
    <style>
        .stDataFrame { border: 1px solid #e2e8f0; border-radius: 10px; }
        .main-header { color: #1E293B; font-size: 2.2rem; font-weight: 800; border-bottom: 4px solid #10B981; padding-bottom: 10px; margin-bottom: 25px; }
        .sidebar-text { font-size: 0.9rem; color: #64748B; }
    </style>
""", unsafe_allow_html=True)

# ── 2. NAVEGACIÓN Y CARGA (SIDEBAR) ──
with st.sidebar:
    st.markdown("### 🛠️ Herramientas de Control")
    # Generador de Plantilla Excel (Aseguramos las 4 columnas pedidas)
    try:
        import xlsxwriter
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            pd.DataFrame(columns=['Proveedor', 'Categoría', 'Subcategoría', 'Gasto (€)']).to_excel(writer, index=False)
        st.download_button("📥 Descargar Plantilla Excel", buffer.getvalue(), "plantilla_compras.xlsx", "application/vnd.ms-excel")
    except:
        st.warning("Instala 'xlsxwriter' para descargar Excel")

    st.divider()
    menu = st.radio("Sección actual:", ["1. Carga de Datos", "2. Matriz de Decisiones"])
    st.divider()
    st.markdown("<p class='sidebar-text'>Desarrollado por Elymar Estévez<br>v11.0 - Decision Support System</p>", unsafe_allow_html=True)

# ── 3. LÓGICA DE PROCESAMIENTO ──
if menu == "1. Carga de Datos":
    st.markdown("<h1 class='main-header'>📥 Gestión de Datos de Compras</h1>", unsafe_allow_html=True)
    
    archivo = st.file_uploader("Sube tu archivo (Excel o CSV)", type=['xlsx', 'csv'])
    
    if archivo:
        df_raw = pd.read_excel(archivo) if archivo.name.endswith('.xlsx') else pd.read_csv(archivo)
    else:
        # Datos de ejemplo para que la app no esté vacía al iniciar
        df_raw = pd.DataFrame({
            'Proveedor': ['Global Corp', 'Local S.A.', 'Tech Supply'],
            'Categoría': ['ALIMENTACIÓN', 'LOGÍSTICA', 'PACKAGING'],
            'Subcategoría': ['Cacao', 'Fletes Marítimos', 'Film'],
            'Gasto (€)': [1200000.00, 450000.00, 150000.00]
        })

    st.subheader("📝 Editor de Datos (Validación)")
    df_editor = st.data_editor(df_raw, num_rows="dynamic", use_container_width=True)

    if st.button("🚀 PROCESAR Y GENERAR ESTRATEGIA", use_container_width=True):
        # Limpieza y Cálculo
        df_clean = df_editor.copy()
        df_clean['Gasto (€)'] = pd.to_numeric(df_clean['Gasto (€)'], errors='coerce').fillna(0)
        
        # Agrupación por subcategoría
        res = df_clean.groupby('Subcategoría').agg({
            'Gasto (€)': 'sum',
            'Categoría': 'first',
            'Proveedor': lambda x: ', '.join(x.dropna().unique().astype(str))
        }).reset_index()
        
        total_gasto = res['Gasto (€)'].sum()
        
        final_list = []
        for i, row in res.iterrows():
            g = row['Gasto (€)']
            # Lógica de Impacto (Pareto)
            impacto = 9 if (g/total_gasto) > 0.15 else (6 if (g/total_gasto) > 0.05 else 3)
            # Lógica de Riesgo (Basada en Categoría)
            cat = str(row['Categoría']).upper()
            riesgo = 8 if any(x in cat for x in ["ALIM", "ENER", "QUIM"]) else 4
            
            # Asignación de Cuadrante
            if impacto >= 6 and riesgo >= 6: q = 'Estratégico'
            elif impacto >= 6: q = 'Apalancamiento'
            elif riesgo >= 6: q = 'Cuello de Botella'
            else: q = 'No Crítico'
            
            final_list.append({
                'ID': i + 1,
                'Categoría': row['Categoría'],
                'Subcategoría': row['Subcategoría'],
                'Proveedores': row['Proveedor'],
                'Gasto': g,
                'Impacto': impacto,
                'Riesgo': riesgo,
                'Cuadrante': q
            })
        
        st.session_state['df_kraljic'] = pd.DataFrame(final_list)
        st.success("✅ Análisis completado. Ve a la sección 'Matriz de Decisiones'.")

# ── 4. DASHBOARD DE DECISIONES (VISUALIZACIÓN LIMPIA) ──
elif menu == "2. Matriz de Decisiones":
    st.markdown("<h1 class='main-header'>📊 Análisis de Matriz de Kraljic</h1>", unsafe_allow_html=True)
    
    if 'df_kraljic' in st.session_state:
        df_plot = st.session_state['df_kraljic']
        
        # Filtro por categoría para limpiar la gráfica si hay muchos puntos
        categorias = ["TODAS"] + sorted(df_plot['Categoría'].unique().tolist())
        cat_filter = st.selectbox("🎯 Filtrar por Categoría:", categorias)
        
        if cat_filter != "TODAS":
            df_plot = df_plot[df_plot['Categoría'] == cat_filter]

        col_map, col_list = st.columns([2.5, 1])

        with col_map:
            fig = go.Figure()

            # 1. Fondos de Cuadrantes (Colores exactos a image_8b1011.png)
            # Cuello Botella (Amarillo suave)
            fig.add_shape(type="rect", x0=0, y0=5.5, x1=5.5, y1=11.5, fillcolor="#FEF3C7", line_width=0, layer="below")
            # Estratégico (Rosa suave)
            fig.add_shape(type="rect", x0=5.5, y0=5.5, x1=11.5, y1=11.5, fillcolor="#FEE2E2", line_width=0, layer="below")
            # No Crítico (Gris suave)
            fig.add_shape(type="rect", x0=0, y0=0, x1=5.5, y1=5.5, fillcolor="#F1F5F9", line_width=0, layer="below")
            # Apalancamiento (Verde menta suave)
            fig.add_shape(type="rect", x0=5.5, y0=0, x1=11.5, y1=5.5, fillcolor="#D1FAE5", line_width=0, layer="below")

            # 2. Etiquetas de Cuadrantes (Texto Grande y Claro)
            fig.add_annotation(x=2.75, y=10.8, text="CUELLO BOTELLA", showarrow=False, font=dict(size=20, color="#94A3B8", family="Arial Black"))
            fig.add_annotation(x=8.25, y=10.8, text="ESTRATÉGICO", showarrow=False, font=dict(size=20, color="#94A3B8", family="Arial Black"))
            fig.add_annotation(x=2.75, y=0.5, text="NO CRÍTICO", showarrow=False, font=dict(size=20, color="#94A3B8", family="Arial Black"))
            fig.add_annotation(x=8.25, y=0.5, text="APALANCAMIENTO", showarrow=False, font=dict(size=20, color="#94A3B8", family="Arial Black"))

            # 3. Burbujas con ID Numérico (Eliminamos nombres largos)
            fig.add_trace(go.Scatter(
                x=df_plot['Impacto'], y=df_plot['Riesgo'],
                mode='markers+text',
                text=df_plot['ID'],
                textposition="middle center",
                textfont=dict(color="white", size=11, family="Arial Black"),
                marker=dict(
                    size=df_plot['Gasto']/df_plot['Gasto'].max()*55 + 25,
                    color='#334155',
                    line=dict(width=2, color='white')
                ),
                hovertemplate="<b>ID %{text}</b><br>Subcat: %{customdata[0]}<br>Gasto: %{customdata[1]:,.2f} €<extra></extra>",
                customdata=df_plot[['Subcategoría', 'Gasto']]
            ))

            fig.update_layout(
                xaxis=dict(title="IMPACTO FINANCIERO", range=[-0.5, 11.5], showgrid=False),
                yaxis=dict(title="RIESGO DE SUMINISTRO", range=[-0.5, 11.5], showgrid=False),
                height=750, template="plotly_white", margin=dict(l=0, r=0, t=0, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_list:
            st.markdown("### 🔑 Identificadores")
            st.info("Usa el ID del gráfico para identificar el producto.")
            # Tabla de referencia ID -> Nombre
            st.dataframe(
                df_plot[['ID', 'Subcategoría']].sort_values('ID'),
                hide_index=True, height=650, use_container_width=True
            )

        # ── 5. TABLA DE DETALLE TOTAL ──
        st.divider()
        st.write("### 📋 Listado Detallado de Sourcing")
        st.dataframe(
            df_plot[['ID', 'Subcategoría', 'Proveedores', 'Gasto', 'Cuadrante']],
            hide_index=True,
            column_config={
                "ID": st.column_config.TextColumn("Nº", width=50),
                "Subcategoría": st.column_config.TextColumn("Subcategoría", width=300),
                "Gasto": st.column_config.NumberColumn("Gasto Anual (€)", format="%.2f €", width=200)
            },
            use_container_width=True
        )
    else:
        st.warning("⚠️ No hay datos analizados. Ve a la pestaña 'Carga de Datos' primero.")
