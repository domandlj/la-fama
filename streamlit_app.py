import streamlit as st
from lafama import download_productos, create_df_products, add_missing_columns
import pandas as pd
from io import BytesIO
from catalogo import generate_catalog_pdf, df_catalogo, download_mayorista
import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import WorksheetNotFound

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

PALABRA_SECRETA = "matecocido"  # Cambiala por la que quieras

# Autenticación Google Sheets
def get_gs_client():
    creds = Credentials.from_service_account_info(st.secrets["google_service_account"], scopes=[
        "https://www.googleapis.com/auth/spreadsheets"
    ])
    return gspread.authorize(creds)

# Cargar tareas
def cargar_tareas_gs():
    client = get_gs_client()
    sheet = client.open_by_key(SPREADSHEET_ID)
    try:
        worksheet = sheet.worksheet(WORKSHEET_NAME)
    except WorksheetNotFound:
        worksheet = sheet.add_worksheet(title=WORKSHEET_NAME, rows="100", cols="2")
        worksheet.append_row(["tarea", "hecho"])
    records = worksheet.get_all_records()
    return records

# Guardar tareas
def guardar_tareas_gs(tareas):
    client = get_gs_client()
    sheet = client.open_by_key(SPREADSHEET_ID)
    try:
        worksheet = sheet.worksheet(WORKSHEET_NAME)
    except WorksheetNotFound:
        worksheet = sheet.add_worksheet(title=WORKSHEET_NAME, rows="100", cols="2")
    worksheet.clear()
    worksheet.append_row(["tarea", "hecho"])
    for t in tareas:
        worksheet.append_row([t["tarea"], "✅" if t.get("hecho") else ""])

# Pestaña 3: Soporte Técnico
with tab3:
    if "tareas" not in st.session_state:
        st.session_state.tareas = cargar_tareas_gs()

    st.subheader("🧑‍🔧 Soporte Técnico")

    # Agregar tarea
    nueva_tarea = st.text_input("Nueva tarea")
    if st.button("➕ Agregar") and nueva_tarea.strip():
        st.session_state.tareas.append({"tarea": nueva_tarea.strip(), "hecho": False})
        guardar_tareas_gs(st.session_state.tareas)
        st.rerun()

    # Ingreso clave admin (opcional)
    clave_ingresada = st.text_input("🔐 Clave de admin (para marcar como hecho)", type="password")
    es_admin = clave_ingresada == PALABRA_SECRETA

    # Mostrar tareas
    if st.session_state.tareas:
        st.subheader("📌 Tareas actuales")
        for i, tarea in enumerate(st.session_state.tareas):
            cols = st.columns([0.7, 0.2, 0.1])
            hecho = "✅" if tarea.get("hecho") else ""
            cols[0].markdown(f"- {tarea['tarea']} {hecho}")
            if es_admin and not tarea.get("hecho"):
                if cols[1].button("Marcar como hecho", key=f"hecho_{i}"):
                    st.session_state.tareas[i]["hecho"] = True
                    guardar_tareas_gs(st.session_state.tareas)
                    st.rerun()
            if es_admin:
                if cols[2].button("❌", key=f"borrar_{i}"):
                    st.session_state.tareas.pop(i)
                    guardar_tareas_gs(st.session_state.tareas)
                    st.rerun()