import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
import textwrap

# === CONFIGURACIÓN DE CLAVES ===
API_URL = st.secrets["API_URL"]
CONSUMER_KEY = st.secrets["CONSUMER_KEY"]
CONSUMER_SECRET = st.secrets["CONSUMER_SECRET"]

# === FUNCIONES ===
def download_mayorista():
    all_products = []
    page = 1
    per_page = 100
    while True:
        params = {'per_page': per_page, 'page': page}
        resp = requests.get(API_URL, auth=HTTPBasicAuth(CONSUMER_KEY, CONSUMER_SECRET), params=params)
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        all_products.extend(batch)
        page += 1
    return all_products

def df_catalogo(all_products):
    data = []
    for product in all_products:
        row = {
            'Nombre': product.get('name', ''),
            'Precio': product.get('price', ''),
            'Foto': product.get('images', [{}])[0].get('src', '') if product.get('images') else '',
            'Categorías': ",".join([cat['name'] for cat in product.get('categories', [])])
        }
        data.append(row)
    df = pd.DataFrame(data)
    df['Precio'] = pd.to_numeric(df['Precio'], errors='coerce')
    return df

def wrap_text(text, max_chars, max_lines=2):
    wrapped = textwrap.wrap(text, width=max_chars)
    if len(wrapped) > max_lines:
        wrapped = wrapped[:max_lines]
        wrapped[-1] += "..."
    return wrapped

def generate_catalog_pdf(df_chico):
    df_chico['Precio'] = pd.to_numeric(df_chico['Precio'], errors='coerce').fillna(0)
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin_x = 40
    margin_y = 40
    footer_lines = [
        "PRECIOS SUJETOS A VARIACIÓN, SIN IMPUESTOS NI GASTOS DE ENVÍO",
        "VENTA MAYORISTA SOLO A COMERCIOS REGISTRADOS - WWW.LAFAMAONLINE.COM - 3517 59-1598"
    ]
    rows, cols = 3, 3
    logo_reserved_height = 80
    usable_width = width - 2 * margin_x
    usable_height = height - 2 * margin_y - logo_reserved_height
    cell_width = usable_width / cols
    cell_height = usable_height / rows
    max_img_width = cell_width * 0.9
    max_img_height = cell_height * 0.6
    products_per_page = rows * cols
    logo_url = "https://lafamaonline.com/wp-content/uploads/2020/03/logo-fama-new-png.png"
    try:
        logo_response = requests.get(logo_url, timeout=5)
        logo_img = ImageReader(BytesIO(logo_response.content))
        logo_w, logo_h = logo_img.getSize()
    except Exception:
        logo_img = None
    for i in range(0, len(df_chico), products_per_page):
        if logo_img:
            max_logo_w = width * 0.4
            max_logo_h = 60
            ratio = min(max_logo_w / logo_w, max_logo_h / logo_h)
            draw_w = logo_w * ratio
            draw_h = logo_h * ratio
            x_pos = (width - draw_w) / 2
            y_pos = height - margin_y - draw_h
            c.drawImage(logo_img, x_pos, y_pos, width=draw_w, height=draw_h, mask='auto')
        else:
            c.setFont("Helvetica-Bold", 20)
            c.drawCentredString(width / 2, height - 50, "La Fama")

        c.setFont("Helvetica", 7)
        c.setFillGray(0.3)
        footer_y_start = 30
        for j, line in enumerate(footer_lines):
            c.drawCentredString(width / 2, footer_y_start - j * 10, line)
        c.setFillGray(0)

        page_items = df_chico.iloc[i:i + products_per_page]

        for idx in range(products_per_page):
            if idx >= len(page_items): continue
            row = page_items.iloc[idx]
            col = idx % cols
            row_num = idx // cols
            x = margin_x + col * cell_width
            y = height - margin_y - logo_reserved_height - (row_num + 1) * cell_height

            try:
                response = requests.get(row['Foto'], timeout=5)
                img = ImageReader(BytesIO(response.content))
                iw, ih = img.getSize()
                ratio = min(max_img_width / iw, max_img_height / ih)
                img_width = iw * ratio
                img_height = ih * ratio
                img_x = x + (cell_width - img_width) / 2
                img_y = y + cell_height - img_height - 10
                c.drawImage(img, img_x, img_y, width=img_width, height=img_height, preserveAspectRatio=True)
            except Exception:
                pass

            nombre = str(row['Nombre'])
            lines = wrap_text(nombre, max_chars=25, max_lines=2)
            c.setFont("Helvetica-Bold", 8)
            for line_num, line in enumerate(lines):
                line_y = y + cell_height * 0.32 - (line_num * 10)
                c.drawCentredString(x + cell_width / 2, line_y, line)

            c.setFont("Helvetica", 9)
            precio = row.get("Precio", 0)
            if precio > 0:
                precio_str = f"$ {precio:,.2f}"
                precio_y = y + cell_height * 0.15
                c.drawCentredString(x + cell_width / 2, precio_y, precio_str)

        c.showPage()

    c.save()
    buffer.seek(0)
    return buffer
