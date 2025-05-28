import streamlit as st
from lafama import download_productos, create_df_products, add_missing_columns
import pandas as pd
from io import BytesIO
from catalogo import generate_catalog_pdf, df_catalogo, download_mayorista
import gspread
from google.oauth2.service_account import Credentials

st.title("🛠️ Herramientas La Fama 🧉")

tab1, tab2, tab3 = st.tabs(
    ["📊 Excel del Minorista", 
     "📄 Catálogo PDF para Mayorista",
     "🧑‍💻 Soporte Técnico"])

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




SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "1SC95K-6sgvB4KDl8ujVNhS0LEKbgA3L9FpNbW93dCq4"
WORKSHEET_NAME = "Tareas"

def get_gs_client():
    creds_info = st.secrets["google_service_account"]
    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPE)
    client = gspread.authorize(creds)
    return client

def cargar_tareas_gs():
    client = get_gs_client()
    sheet = client.open_by_key(SPREADSHEET_ID)
    try:
        worksheet = sheet.worksheet(WORKSHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = sheet.add_worksheet(title=WORKSHEET_NAME, rows="100", cols="1")
    values = worksheet.col_values(1)
    return values

def guardar_tareas_gs(tareas):
    client = get_gs_client()
    sheet = client.open_by_key(SPREADSHEET_ID)
    try:
        worksheet = sheet.worksheet(WORKSHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = sheet.add_worksheet(title=WORKSHEET_NAME, rows="100", cols="1")
    worksheet.clear()
    if tareas:
        cell_list = worksheet.range(1, 1, len(tareas), 1)
        for i, cell in enumerate(cell_list):
            cell.value = tareas[i]
        worksheet.update_cells(cell_list)

with tab3:
    st.header("📋 Lista de Tareas - Soporte Técnico")

    if 'tareas' not in st.session_state:
        st.session_state.tareas = cargar_tareas_gs()

    nueva_tarea = st.text_input("Agregar nueva tarea")

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("➕ Agregar") and nueva_tarea.strip():
            st.session_state.tareas.append(nueva_tarea.strip())
            guardar_tareas_gs(st.session_state.tareas)
            st.experimental_rerun()

    if st.session_state.tareas:
        st.subheader("📌 Tareas actuales")
        for i, tarea in enumerate(st.session_state.tareas):
            col1, col2 = st.columns([0.1, 0.9])
            with col1:
                if st.button("❌", key=f"borrar_{i}"):
                    st.session_state.tareas.pop(i)
                    guardar_tareas_gs(st.session_state.tareas)
                    st.experimental_rerun()
            with col2:
                st.markdown(tarea)
    else:
        st.info("No hay tareas por ahora.")