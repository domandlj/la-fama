import streamlit as st
from lafama import download_productos, create_df_products, add_missing_columns
import pandas as pd
from io import BytesIO
from catalogo import generate_catalog_pdf, df_catalogo, download_mayorista

st.title("🛠️ Herramientas La Fama 🧉")

tab1, tab2 = st.tabs(["📊 Excel del Minorista", "📄 Catálogo PDF para Mayorista"])

with tab1:
    # Input para margen (valor por defecto 0.85)
    margin = st.number_input(
        "Margen (multiplicador sobre el precio mayorista)", 
        min_value=0.01, 
        max_value=3.0, 
        value=0.85, 
        step=0.01
    )

    if st.button("Descargar datos mayorista"):
        all_products = download_productos()
        df = create_df_products(all_products, margin=margin)
        df = add_missing_columns(df)

        st.dataframe(df)

        # Convertir a Excel en memoria
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Productos')
        output.seek(0)

        # Botón de descarga
        st.download_button(
            label="📥 Descargar como Excel",
            data=output,
            file_name="planilla.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

with tab2:
    if st.button("Descargar productos desde WooCommerce"):
        with st.spinner("Descargando productos..."):
            productos = download_mayorista()
            df = df_catalogo(productos)
            st.session_state.df = df
            st.success(f"Se descargaron {len(df)} productos.")

    if 'df' in st.session_state:
        df = st.session_state.df
        categorias = sorted({cat for cats in df['Categorías'].dropna() for cat in cats.split(',')})
        seleccionadas = st.multiselect("Filtrar por categorías", opciones := categorias, default=opciones)
        df_filtrado = df[df['Categorías'].apply(lambda x: any(cat in x for cat in seleccionadas))]
        st.write(f"{len(df_filtrado)} productos seleccionados")

        if st.button("Generar PDF del catálogo"):
            with st.spinner("Generando catálogo..."):
                pdf_buffer = generate_catalog_pdf(df_filtrado)
                st.download_button(
                    "📄 Descargar catálogo PDF",
                    data=pdf_buffer,
                    file_name="catalogo_la_fama.pdf",
                    mime="application/pdf"
                )
