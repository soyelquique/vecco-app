
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Vecco Cloud", layout="wide")
st.title("👨‍🍳 Vecco: Gestión de Costos")

@st.cache_data
def load_data():
    df_insumos = pd.read_excel('vecco_database.xlsx', sheet_name='Insumos')
    df_recetas = pd.read_excel('vecco_database.xlsx', sheet_name='Recetas')
    
    # --- LA SOLUCIÓN ---
    # Forzamos a que los IDs sean números enteros en ambas hojas para que coincidan siempre
    df_insumos['ID'] = pd.to_numeric(df_insumos['ID'], errors='coerce').fillna(-1).astype(int)
    df_recetas['ID_Insumo'] = pd.to_numeric(df_recetas['ID_Insumo'], errors='coerce').fillna(-1).astype(int)
    
    return df_insumos, df_recetas

try:
    df_insumos, df_recetas = load_data()
    
    # Menú lateral
    st.sidebar.header("Menú Vecco")
    modo = st.sidebar.radio("Ir a:", ["Calculadora de Recetas", "Lista de Insumos"])

    if modo == "Calculadora de Recetas":
        st.header("📊 Calculadora de Costos")
        
        # Selector de receta
        nombres_recetas = sorted([str(r) for r in df_recetas['Receta'].unique() if pd.notna(r)])
        receta_seleccionada = st.selectbox("Elegí un producto:", nombres_recetas)
        
        # Margen (por defecto 60% como usás en Vecco)
        margen = st.sidebar.slider("Margen de ganancia (%)", 10, 90, 60)
        
        if receta_seleccionada:
            items = df_recetas[df_recetas['Receta'] == receta_seleccionada]
            total_mp = 0
            
            # Preparamos los datos para la tabla
            datos_tabla = []
            
            for _, row in items.iterrows():
                # Buscamos el insumo
                match = df_insumos[df_insumos['ID'] == row['ID_Insumo']]
                
                if not match.empty:
                    p_unit = float(match.iloc[0]['Precio_Unit'])
                    cantidad = float(row['Cantidad'])
                    costo = cantidad * p_unit
                    total_mp += costo
                    datos_tabla.append([row['ID_Insumo'], row['Insumo'], cantidad, f"$ {costo:,.2f}"])
                else:
                    # Si un insumo no se encuentra, te avisa en la tabla
                    datos_tabla.append([row['ID_Insumo'], row['Insumo'], row['Cantidad'], "Falta en Insumos"])
            
            # Mostramos la tabla de ingredientes
            st.table(pd.DataFrame(datos_tabla, columns=["ID", "Ingrediente", "Cantidad", "Subtotal"]))
            
            st.divider()
            
            # Cálculos finales
            col1, col2 = st.columns(2)
            col1.metric("COSTO MATERIA PRIMA", f"$ {total_mp:,.2f}")
            
            # Fórmula de pastelería: Costo / (1 - margen) -> ej: Costo / 0.4 para 60%
            try:
                precio_sugerido = total_mp / (1 - (margen/100))
            except:
                precio_sugerido = total_mp * 2
                
            col2.metric(f"PRECIO DE VENTA ({margen}%)", f"$ {precio_sugerido:,.2f}")

    elif modo == "Lista de Insumos":
        st.header("🛒 Buscador de Artículos")
        busqueda = st.text_input("Buscar insumo por nombre...")
        
        if busqueda:
            filtrado = df_insumos[df_insumos['Insumo'].astype(str).str.contains(busqueda, case=False, na=False)]
            st.dataframe(filtrado[['ID', 'Insumo', 'Precio_Unit']], use_container_width=True)
        else:
            st.dataframe(df_insumos[['ID', 'Insumo', 'Precio_Unit']], use_container_width=True)

except Exception as e:
    st.error(f"Asegurate de que el archivo 'vecco_database.xlsx' esté subido a Colab. Error: {e}")
    