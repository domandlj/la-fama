import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
import streamlit as st
import numpy as np
import re


# Tus claves
API_URL = st.secrets["API_URL"]
CONSUMER_KEY = st.secrets["CONSUMER_KEY"]
CONSUMER_SECRET = st.secrets["CONSUMER_SECRET"]



def download_productos():
    """
        Descarga todos los productos y los retorna en list.
    """



    all_products = []
    page = 1
    per_page = 100  # WooCommerce permite un máximo de 100

    while True:
        params = {
            'per_page': per_page,
            'page': page,
        }
        resp = requests.get(API_URL, auth=HTTPBasicAuth(CONSUMER_KEY, CONSUMER_SECRET), params=params)
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        all_products.extend(batch)
        print(f"Página {page}: obtenidos {len(batch)} productos")
        page += 1

    print(f"Total de productos obtenidos: {len(all_products)}")

    return all_products



# Regex que permite letras, números, espacios y los símbolos permitidos
regex_permitidos = re.compile(r"[^a-zA-Z0-9 /\-!'\",.+\[\]:#]")

def create_df_products(all_products, margin = 0.85):
    """
        Retorna todos los productos en df más un márgen.
    """
    # Assuming your list of products is called 'all_products'
    data = []
    for product in all_products:
        row = {
            'Nombre': product.get('name', ''),
            'Precio': product.get('price', '')
           # 'Foto': product.get('images', [{}])[0].get('src', '') if product.get('images') else ''
        }

        categorias = list(map(
            lambda x : x['name'], 
            product.get('categories',''))
        )


        categorias = [c.replace(" ", "") for c in categorias]
        categorias = [regex_permitidos.sub('', c) for c in categorias]
        row["Categorías"] =  categorias[0] if categorias else "Sin-categoría"
        
        #if "TIENDA" in row['categoria']:
        data.append(row)

        
    df = pd.DataFrame(data)

    # Convert price to numeric type
    df['Precio'] = np.floor(pd.to_numeric(df['Precio'], errors='coerce') * (1 + margin))

    return df



def limpiar_nombre(nombre):
    if not isinstance(nombre, str):
        return None
    # Eliminar caracteres no permitidos
    nombre_limpio = regex_permitidos.sub('', nombre)
    # Recortar si es más largo que 80 caracteres
    nombre_limpio = nombre_limpio[:80]
    # Si tiene menos de 2 caracteres luego de limpiar, descartarlo
    if len(nombre_limpio) < 2:
        return "none"
    return nombre_limpio


def add_missing_columns(df):
    """
    Limpia y valida los datos del DataFrame:
    - Elimina columnas no necesarias.
    - Agrega las columnas faltantes con valores por defecto.
    - Valida y corrige campos según la documentación.
    """

    # Asegurar existencia de columnas requeridas
    required_columns = {
        'Stock': 1,
        'SKU': 'no',
        'Precio oferta': 1,
        'Nombre atributo 1': 'no',
        'Valor atributo 1': 'no',
        'Nombre atributo 2': 'no',
        'Valor atributo 2': 'no',
        'Nombre atributo 3': 'no',
        'Valor atributo 3': 'no',
        'Peso': 1,
        'Alto': 1,
        'Ancho': 1,
        'Profundidad': 1,
    }

    for col, default in required_columns.items():
        if col not in df.columns:
            df[col] = default

    # Validaciones y correcciones

    # Nombre: limitar entre 2 y 80 caracteres
    df['Nombre'] = df['Nombre'].apply(limpiar_nombre)
    # Precio y Precio oferta: asegurarse que sean numéricos
    df['Precio'] = pd.to_numeric(df['Precio'], errors='coerce')
    df['Precio oferta'] = pd.to_numeric(df['Precio'], errors='coerce')

    # Mostrar en tienda: normalizar a "Sí"

    return df

