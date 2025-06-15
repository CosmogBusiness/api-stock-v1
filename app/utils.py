import pandas as pd
import io

def read_stock_csv(content: bytes) -> pd.DataFrame:
    """
    Lee y valida el archivo stock.csv.
    """
    df = pd.read_csv(io.BytesIO(content))
    expected_cols = [
        "SKU", "Producto", "Categoría", "Talla", "Color", "Stock", "Precio_Unitario", "Umbral"
    ]
    if list(df.columns) != expected_cols:
        raise ValueError(f"stock.csv debe tener columnas: {expected_cols}")
    return df

def read_ventas_csv(content: bytes) -> pd.DataFrame:
    """
    Lee y valida el archivo ventas.csv.
    """
    df = pd.read_csv(io.BytesIO(content))
    expected_cols = ["Fecha", "SKU", "Unidades_Vendidas"]
    if list(df.columns) != expected_cols:
        raise ValueError(f"ventas.csv debe tener columnas: {expected_cols}")
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    return df

def read_historico_csv(content: bytes) -> pd.DataFrame:
    """
    Lee y valida el archivo historico_stock_ventas.csv.
    Debe incluir: Fecha, SKU, Stock, Unidades_Vendidas, Reposicion, Precio_Unitario, Ingresos_Brutos
    """
    df = pd.read_csv(io.BytesIO(content))
    expected_cols = [
        "Fecha",
        "SKU",
        "Stock",
        "Unidades_Vendidas",
        "Reposicion",
        "Precio_Unitario",
        "Ingresos_Brutos"
    ]
    if list(df.columns) != expected_cols:
        raise ValueError(f"historico_stock_ventas.csv debe tener columnas: {expected_cols}")
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    return df
