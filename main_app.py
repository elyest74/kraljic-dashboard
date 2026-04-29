import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io

# ── 1. CONFIGURACIÓN ──
st.set_page_config(page_title="Purchasing Intelligence | Elymar", layout="wide")

st.markdown("""
    <style>
        .main-header { color: #0F172A; font-size: 2rem; font-weight: 800; border-bottom: 3px solid #10B981; margin-bottom: 20px; }
        .stDownloadButton>button { background-color: #059669 !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# ── 2. BARRA LATERAL (SIMPLIFICADA) ──
with st.sidebar:
    st.title("⚙️ Control")
    # ... (mantenemos lógica de descarga Excel si XLSX_AVAILABLE)
    menu = st.radio("Sección:", ["Carga de Datos", "Matriz Estratégica"])

# ── 3. LÓGICA DE PROCESAMIENTO (Igual a la anterior) ──
# (Asumimos que el usuario carga los datos y se guardan en st.session_state['df_kraljic'])
if menu == "Carga de Datos":
    st.markdown("<h1 class='main-header'>📥 Entrada de Datos</h1>", unsafe_allow_html=True)
    # ... (Aquí va tu código de st.data_editor y procesamiento)
    # Asegúrate de generar st.session_state['df_kraljic']

# ── 4. DASHBOARD ESTRATÉGICO (LA SOLUCIÓN VISUAL) ──
elif menu == "Matriz Estratégica":
    st.markdown("<h1 class='main-header'>📊 Cuadro de Mando de Compras</h1>", unsafe_allow_html=True)
    
    if 'df_kraljic' in st.session_state:
        df = st.session_state['df_kraljic'].copy()
        
        # Creamos un ID numérico para cada punto para evitar el solapamiento de texto
        df = df.reset_index().rename(columns={'index': 'ID'})
        df['ID'] = df['ID'] + 1 

        col_graf, col_info = st.columns([3, 1])

        with col_graf:
            fig = go.Figure()

            # Fondo de Cuadrantes (Colores exactos a tu imagen)
            # Estratégico (Rosa/Rojo suave)
            fig.add_shape(type="rect", x0=5.5, y0=5.5, x1=11, y1=11, fillcolor="#fee2e2", line_width=0, layer="below")
            # Cuello Botella (Amarillo/Naranja suave)
            fig.add_shape(type="rect", x0=0, y0=5.5, x1=5.5, y1=11, fillcolor="#fef3c7", line_width=0, layer="below")
            # Apalancamiento (Verde suave)
            fig.add_shape(type="rect", x0=5.5, y0=0, x1=11, y1=5.5, fillcolor="#d1fae5", line_width=0, layer="below")
            # No Crítico (Gris suave)
            fig.add_shape(type="rect", x0=0, y0=0, x1=5.5, y1=5.5, fillcolor="#f1f5f9", line_width=0, layer="below")

            # Etiquetas de Cuadrantes (Posicionadas para no molestar)
            quad_labels = [
                ("ESTRATÉGICO", 8.25, 10.5), ("CUELLO BOTELLA", 2.75, 10.5),
                ("APALANCAMIENTO", 8.25, 0.5), ("NO CRÍTICO", 2.75, 0.5)
            ]
            for txt, x, y in quad_labels:
                fig.add_annotation(x=x, y=y, text=txt, showarrow=False, font=dict(size=18, color="#94a3b8", family="Arial Black"))

            # Puntos de datos: Burbujas con ID numérico
            fig.add_trace(go.Scatter(
                x=df['Impacto'],
                y=df['Riesgo'],
                mode='markers+text',
                text=df['ID'], # Mostramos el número en lugar del nombre largo
                textposition="middle center",
                textfont=dict(color="white", size=10, family="Arial Black"),
                marker=dict(
                    size=df['Gasto']/df['Gasto'].max()*50 + 25, 
                    color='#334155', # Color elegante pizarra
                    line=dict(width=1, color='white')
                ),
                hovertemplate="<b>ID: %{text}</b><br>Cat: %{customdata[0]}<br>Gasto: %{customdata[1]:,.2f}€<extra></extra>",
                customdata=df[['Subcategoría', 'Gasto']]
            ))

            fig.update_layout(
                xaxis=dict(title="IMPACTO FINANCIERO", range=[0, 11], gridcolor="rgba(0,0,0,0.05)"),
                yaxis=dict(title="RIESGO DE SUMINISTRO", range=[0, 11], gridcolor="rgba(0,0,0,0.05)"),
                margin=dict(l=20, r=20, t=20, b=20),
                height=700,
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_info:
            st.write("### 🔑 Leyenda")
            st.write("Identifica cada punto por su número:")
            # Tabla pequeña de referencia rápida
            st.dataframe(
                df[['ID', 'Subcategoría']].sort_values('ID'),
                hide_index=True,
                height=600,
                use_container_width=True
            )

        # Tabla inferior con formato de miles (Ancho 200px)
        st.divider()
        st.write("### 📋 Detalle Completo de Gastos")
        st.dataframe(
            df[['ID', 'Subcategoría', 'Proveedores', 'Gasto', 'Cuadrante']],
            hide_index=True,
            column_config={
                "ID": st.column_config.TextColumn("Nº", width=40),
                "Gasto": st.column_config.NumberColumn("Gasto (€)", format="%.2f €", width=200)
            },
            use_container_width=True
        )
    else:
        st.warning("⚠️ No hay datos. Por favor, cárgalos en la pestaña correspondiente.")
