
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Vecco Web", layout="wide")
st.title("👨‍🍳 Vecco: Costos por Porción")

@st.cache_data
def load():
    df_i = pd.read_excel('vecco_database.xlsx', sheet_name='Insumos')
    df_r = pd.read_excel('vecco_database.xlsx', sheet_name='Recetas')
    return df_i, df_r

try:
    df_i, df_r = load()
    receta_sel = st.selectbox("Producto:", sorted(df_r['Receta'].unique()))
    margen = st.sidebar.slider("Margen %", 10, 90, 60)
    
    if receta_sel:
        datos = df_r[df_r['Receta'] == receta_sel]
        porc = float(datos['Porciones'].iloc[0])
        total = 0
        tabla = []
        for _, row in datos.iterrows():
            m = df_i[df_i['ID'] == row['ID_Insumo']]
            if not m.empty:
                c = row['Cantidad'] * m.iloc[0]['Precio_Unit']
                total += c
                tabla.append([row['Insumo'], row['Cantidad'], f"$ {c:,.2f}"])
        
        st.write(f"### Rinde: {int(porc)} porciones")
        st.table(pd.DataFrame(tabla, columns=["Insumo", "Cant", "Subtotal"]))
        
        c1, c2, c3 = st.columns(3)
        c1.metric("TOTAL RECETA", f"$ {total:,.2f}")
        c2.metric("COSTO x UNIDAD", f"$ {total/porc:,.2f}")
        c3.metric(f"VENTA x UNIDAD ({margen}%)", f"$ {(total/(1-margen/100))/porc:,.2f}")
except Exception as e:
    st.error(f"Error: {e}")
        