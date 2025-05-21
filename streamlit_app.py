import streamlit as st
from lafama import download_productos, create_df_products, add_missing_columns

st.title("🧉 La Fama (Minorista)")

if st.button("Crear excel"):
    all_products = download_productos()
    df = create_df_products(all_products)
    df = add_missing_columns(df)

    st.dataframe(df)  # This will display the DataFrame as an interactive table
