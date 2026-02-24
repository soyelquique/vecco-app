import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Vecco App", layout="centered")
st.title("👨‍🍳 Vecco: Costos y Compras")

# --- EL MOTOR ACTUALIZADO (Ahora guarda el Factor y el Bulto) ---
def procesar_excel(archivo_subido):
    df_art = pd.read_excel(archivo_subido, sheet_name='ARTICULOS')
    
    def lim(df, off=0):
        # Ahora capturamos las 5 columnas enteras (Factor y Precio_Bulto incluidos)
        df.columns = ['ID', 'Insumo', 'Factor', 'Precio_Bulto', 'Precio_Unit']
        df['ID'] = pd.to_numeric(df['ID'], errors='coerce')
        df = df.dropna(subset=['ID', 'Insumo'])
        df = df[df['ID'] < 500].copy()
        df['ID'] = df['ID'] + off
        return df[['ID', 'Insumo', 'Factor', 'Precio_Bulto', 'Precio_Unit']]

    # Procesa la tabla dulce (columnas A a E) y salada (columnas H a L)
    df_insumos = pd.concat([lim(df_art.iloc[:, 0:5].copy()), lim(df_art.iloc[:, 7:12].copy(), 1000)], ignore_index=True)

    xl = pd.ExcelFile(archivo_subido)
    rec_list = []
    for hoja in xl.sheet_names:
        if hoja in ['ARTICULOS', 'SALON', 'LISTA DE PRECIOS']: continue
        off = 1000 if any(k in hoja.upper() for k in ['SALAD', 'CENA']) else 0
        df_h = pd.read_excel(archivo_subido, sheet_name=hoja)
        for col in range(df_h.shape[1] - 2):
            for row in range(df_h.shape[0]):
                if str(df_h.iloc[row, col]).upper().strip() in ['ARTICULO', 'ARTÍCULOS']:
                    nom = str(df_h.iloc[row-2, col]).strip() if row >= 2 else "Receta"
                    r_idx = row + 1
                    ing_temp = []
                    while r_idx < df_h.shape[0]:
                        v_id = pd.to_numeric(df_h.iloc[r_idx, col], errors='coerce')
                        if pd.isna(v_id) or v_id > 500: break
                        ing_temp.append({'ID_Insumo': int(v_id + off), 'Insumo': str(df_h.iloc[r_idx, col