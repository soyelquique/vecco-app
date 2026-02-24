import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Vecco App", layout="centered")
st.title("👨‍🍳 Vecco: Costos y Compras")

# --- EL MOTOR ACTUALIZADO (Con líneas cortas anti-errores) ---
def procesar_excel(archivo_subido):
    df_art = pd.read_excel(archivo_subido, sheet_name='ARTICULOS')
    
    def lim(df, off=0):
        df.columns = ['ID', 'Insumo', 'Factor', 'Precio_Bulto', 'Precio_Unit']
        df['ID'] = pd.to_numeric(df['ID'], errors='coerce')
        df = df.dropna(subset=['ID', 'Insumo'])
        df = df[df['ID'] < 500].copy()
        df['ID'] = df['ID'] + off
        return df[['ID', 'Insumo', 'Factor', 'Precio_Bulto', 'Precio_Unit']]

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
                        
                        # Líneas cortas para evitar cortes al pegar
                        insumo_nombre = str(df_h.iloc[r_idx, col+1])
                        cantidad_val = df_h.iloc[r_idx, col+2]
                        cantidad_final = float(cantidad_val) if pd.notna(cantidad_val) else 0.0
                        
                        ing_temp.append({
                            'ID_Insumo': int(v_id + off),
                            'Insumo': insumo_nombre,
                            'Cantidad': cantidad_final
                        })
                        r_idx += 1
                    
                    porc = 1
                    for rb in range(r_idx, min(r_idx + 10, df_h.shape[0])):
                        for cb in range(col, col + 3):
                            if cb < df_h.shape[1]:
                                cel = str(df_h.iloc[rb, cb]).upper()
                                if any(k in cel for k in ["PORCION", "RINDE", "CANTIDAD", "UNIDADES"]):
                                    for cn in range(cb, cb + 2):
                                        if cn < df_h.shape[1]:
                                            n = pd.to_numeric(df_h.iloc[rb, cn], errors='coerce')
                                            if pd.notna(n) and n > 0: porc = n; break
                    for ing in ing_temp:
                        ing['Receta'] = f"[{hoja}] {nom}"; ing['Porciones'] = porc; rec_list.append(ing)
    
    df_recetas = pd.DataFrame(rec_list)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_insumos.to_excel(writer, sheet_name='Insumos', index=False)
        df_recetas.to_excel(writer, sheet_name='Recetas', index=False)
    output.seek(0)
    return output

@st.cache_data
def load_data():
    try:
        df_insumos = pd.read_excel('vecco_database.xlsx', sheet_name='Insumos')
        df_recetas = pd.read_excel('vecco_database.xlsx', sheet_name='Recetas')
        
        df_insumos['ID'] = pd.to_numeric(df_insumos['ID'], errors='coerce').fillna(-1).astype(int)
        df_recetas['ID_Insumo'] = pd.to_numeric(df_recetas['ID_Insumo'], errors='coerce').fillna(-1).astype(int)
        df_insumos['Precio_Unit'] = pd.to_numeric(df_insumos['Precio_Unit'], errors='coerce').fillna(0)
        
        if 'Factor' not in df_insumos.columns: df_insumos['Factor'] = 0
        if 'Precio_Bulto' not in df_insumos.columns: df_insumos['Precio_Bulto'] = 0
        
        df_insumos['Factor'] = pd.to_numeric(df_insumos['Factor'], errors='coerce').fillna(0)
        df_insumos['Precio_Bulto'] = pd.to_numeric(df_insumos['Precio_Bulto'], errors='coerce').fillna(0)
        
        df_recetas['Cantidad'] = pd.to_numeric(df_recetas['Cantidad'], errors='coerce').fillna(0)
        return df_insumos, df_recetas
    except Exception:
        return None, None

df_insumos, df_recetas = load_data()

# --- LAS 3 PESTAÑAS ---
tab1, tab2, tab3 = st.tabs(["📊 Calculadora", "🛒 Artículos", "⚙️ Procesador"])

with tab1:
    if df_recetas is not None:
        nombres_recetas = sorted([str(r) for r in df_recetas['Receta'].unique() if pd.notna(r)])
        receta_sel = st.selectbox("Elegí una receta:", nombres_recetas)
        margen = st.slider("Margen de ganancia (%)", 10, 90, 60)
        if receta_sel:
            items = df_recetas[df_recetas['Receta'] == receta_sel]
            cant_porciones = float(items['Porciones'].iloc[0]) if 'Porciones' in items.columns else 1
            total_mp = 0
            datos_tabla = []
            for _, row in items.iterrows():
                match = df_insumos[df_insumos['ID'] == row['ID_Insumo']]
                if not match.empty:
                    p_unit = match.iloc[0]['Precio_Unit']
                    costo = row['Cantidad'] * p_unit
                    total_mp += costo
                    datos_tabla.append([row['Insumo'], f"{row['Cantidad']:.3f}", f"$ {costo:,.2f}"])
                else:
                    datos_tabla.append([row['Insumo'], f"{row['Cantidad']:.3f}", "⚠️ Falta"])
            
            st.write(f"**Rinde:** {int(cant_porciones)} porciones")
            st.dataframe(pd.DataFrame(datos_tabla, columns=["Ingrediente", "Cantidad", "Subtotal"]), use_container_width=True)
            st.divider()
            c1, c2 = st.columns(2)
            c1.metric("COSTO TOTAL", f"$ {total_mp:,.2f}")
            costo_uni = total_mp / cant_porciones if cant_porciones > 0 else 0
            c2.metric("COSTO x UNIDAD", f"$ {costo_uni:,.2f}")
            precio_v_total = total_mp / (1 - (margen/100))
            precio_v_uni = precio_v_total / cant_porciones if cant_porciones > 0 else 0
            st.success(f"💰 **VENTA SUGERIDA ({margen}%): $ {precio_v_uni:,.2f} por unidad**")
    else:
        st.warning("Falta subir la base de datos.")

with tab2:
    if df_insumos is not None:
        st.write("Buscador rápido para compras a proveedores:")
        busqueda = st.text_input("🔍 Buscar artículo...")
        columnas_mostrar = ['ID', 'Insumo', 'Factor', 'Precio_Bulto', 'Precio_Unit']
        
        if busqueda:
            filtrado = df_insumos[df_insumos['Insumo'].astype(str).str.contains(busqueda, case=False, na=False)]
            st.dataframe(filtrado[columnas_mostrar], use_container_width=True)
        else:
            st.dataframe(df_insumos[columnas_mostrar], use_container_width=True)

with tab3:
    st.write("### 🚀 Actualizador Vecco")
    st.write("Subí acá tu Excel original `COSTOS RECETAS2.xlsx` para generar la base nueva.")
    archivo_excel = st.file_uploader("Arrastrá tu Excel acá:", type=['xlsx'])
    
    if archivo_excel is not None:
        if st.button("Procesar y Generar"):
            with st.spinner("Cocinando datos..."):
                try:
                    archivo_procesado = procesar_excel(archivo_excel)
                    st.success("✅ ¡Base de datos generada con éxito!")
                    st.download_button(
                        label="⬇️ Descargar vecco_database.xlsx",
                        data=archivo_procesado,
                        file_name="vecco_database.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    st.info("💡 Paso final: Subí este archivo descargado a tu GitHub para que impacten los precios.")
                except Exception as e:
                    st.error(f"Error al procesar: {e}")