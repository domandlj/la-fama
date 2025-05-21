import streamlit as st
from lafama import download_productos, create_df_products, add_missing_columns
import pandas as pd
from io import BytesIO

st.title("🧉 La Fama (Minorista)")

if st.button("Descargar datos mayorista"):
    all_products = download_productos()
    df = create_df_products(all_products)
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
