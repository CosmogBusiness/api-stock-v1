import pandas as pd
import numpy as np
from typing import List, Dict, Any
from collections import defaultdict

# --- BLOQUE OPENAI ---

def productos_bajo_stock(stock_df: pd.DataFrame) -> List[dict]:
    """Devuelve lista de productos con stock <= umbral."""
    return stock_df[stock_df['Stock'] <= stock_df['Umbral']].to_dict(orient='records')

def productos_rotacion_lenta(ventas_df: pd.DataFrame, historico_df: pd.DataFrame, stock_df: pd.DataFrame, umbral: float = 0.5) -> List[dict]:
    """Detecta productos cuya media diaria de ventas es baja respecto al promedio."""
    ventas_por_sku = ventas_df.groupby('SKU')['Unidades_Vendidas'].sum()
    dias = (ventas_df['Fecha'].max() - ventas_df['Fecha'].min()).days + 1
    media_global = ventas_df['Unidades_Vendidas'].sum() / (len(ventas_por_sku)*dias) if dias and len(ventas_por_sku) else 0
    lentos = []
    for sku, total in ventas_por_sku.items():
        media_diaria = total / dias if dias else 0
        if media_diaria < umbral * media_global:
            producto = stock_df[stock_df['SKU'] == sku].iloc[0].to_dict()
            producto['media_diaria'] = media_diaria
            lentos.append(producto)
    return lentos

def productos_muertos(ventas_df: pd.DataFrame, stock_df: pd.DataFrame, umbral_dias:int = 14) -> List[dict]:
    """Detecta productos sin ventas en los últimos umbral_dias."""
    fecha_max = ventas_df['Fecha'].max()
    muertos = []
    for sku in stock_df['SKU']:
        ult_venta = ventas_df[ventas_df['SKU'] == sku]['Fecha'].max()
        if pd.isnull(ult_venta) or (fecha_max - ult_venta).days >= umbral_dias:
            producto = stock_df[stock_df['SKU'] == sku].iloc[0].to_dict()
            muertos.append(producto)
    return muertos

def top_n_vendidos_mes(ventas_df: pd.DataFrame, stock_df: pd.DataFrame, n=5) -> List[dict]:
    """Top n productos más vendidos en el mes actual."""
    if len(ventas_df) == 0:
        return []
    mes = ventas_df['Fecha'].max().month
    año = ventas_df['Fecha'].max().year
    mes_df = ventas_df[(ventas_df['Fecha'].dt.month == mes) & (ventas_df['Fecha'].dt.year == año)]
    ranking = mes_df.groupby('SKU')['Unidades_Vendidas'].sum().sort_values(ascending=False).head(n)
    res = []
    for sku, total in ranking.items():
        prod = stock_df[stock_df['SKU'] == sku].iloc[0].to_dict()
        prod['total_vendido_mes'] = int(total)
        res.append(prod)
    return res

def estimaciones_velocidad_venta(ventas_df: pd.DataFrame, stock_df: pd.DataFrame) -> Dict[str, float]:
    """Estimación de velocidad de venta por SKU (unidades/día)."""
    dias = (ventas_df['Fecha'].max() - ventas_df['Fecha'].min()).days + 1
    ventas = ventas_df.groupby('SKU')['Unidades_Vendidas'].sum()
    return {str(int(sku)): round(ventas.get(sku, 0) / dias, 2) if dias else 0 for sku in stock_df['SKU']}

def promedios_unidades_vendidas(ventas_df: pd.DataFrame) -> Dict[str, float]:
    """Promedio de unidades vendidas por SKU."""
    dias = (ventas_df['Fecha'].max() - ventas_df['Fecha'].min()).days + 1
    ventas = ventas_df.groupby('SKU')['Unidades_Vendidas'].sum()
    return {str(int(sku)): round(ventas.get(sku, 0) / dias, 2) if dias else 0 for sku in ventas.index}

def metricas_globales(stock_df: pd.DataFrame, ventas_df: pd.DataFrame, historico_df: pd.DataFrame) -> Dict[str, Any]:
    """Métricas globales relevantes."""
    total_stock = int(stock_df['Stock'].sum())
    total_vendido = int(ventas_df['Unidades_Vendidas'].sum())
    num_productos = int(stock_df['SKU'].nunique())
    roturas = historico_df[historico_df['Stock'] == 0].shape[0]
    reposiciones = historico_df[historico_df['Reposicion'] == 1].shape[0]
    media_rotacion = round(total_vendido / num_productos, 2) if num_productos else 0
    return {
        "total_stock": total_stock,
        "total_vendido": total_vendido,
        "num_productos": num_productos,
        "num_roturas_detectadas": roturas,
        "num_reposiciones_detectadas": reposiciones,
        "media_rotacion_por_producto": media_rotacion
    }

def eventos_detectados(historico_df: pd.DataFrame) -> List[dict]:
    """Devuelve eventos relevantes: roturas, reposiciones, retrasos, etc."""
    eventos = []
    for _, row in historico_df.iterrows():
        if row['Stock'] == 0:
            eventos.append({"tipo": "rotura_stock", "SKU": int(row['SKU']), "fecha": str(row['Fecha'].date())})
        if row['Reposicion'] == 1:
            eventos.append({"tipo": "reposicion", "SKU": int(row['SKU']), "fecha": str(row['Fecha'].date())})
    return eventos

# --- BLOQUE DASHBOARD ---

def resumen_global_dashboard(stock_df: pd.DataFrame, ventas_df: pd.DataFrame, historico_df: pd.DataFrame) -> dict:
    """Resumen global para dashboard frontend."""
    total_productos = int(stock_df['SKU'].nunique())
    total_vendido = int(ventas_df['Unidades_Vendidas'].sum())
    dias = (ventas_df['Fecha'].max() - ventas_df['Fecha'].min()).days + 1
    media_rotacion = round(total_vendido / total_productos, 2) if total_productos else 0
    return {
        "total_productos": total_productos,
        "total_vendido": total_vendido,
        "promedio_rotacion": media_rotacion
    }

def top_3_vendidos_dashboard(ventas_df: pd.DataFrame, stock_df: pd.DataFrame) -> List[dict]:
    """Top 3 productos más vendidos."""
    ranking = ventas_df.groupby('SKU')['Unidades_Vendidas'].sum().sort_values(ascending=False).head(3)
    res = []
    for sku, total in ranking.items():
        prod = stock_df[stock_df['SKU'] == sku].iloc[0].to_dict()
        res.append({
            "nombre": prod["Producto"],
            "sku": int(sku),
            "total_vendido": int(total)
        })
    return res

def fecha_ultimo_analisis(ventas_df: pd.DataFrame, historico_df: pd.DataFrame) -> str:
    """Devuelve la fecha del último análisis (última fecha de ventas o histórico)."""
    fecha_ventas = ventas_df['Fecha'].max() if not ventas_df.empty else None
    fecha_hist = historico_df['Fecha'].max() if not historico_df.empty else None
    fechas = [f for f in [fecha_ventas, fecha_hist] if pd.notnull(f)]
    if fechas:
        return str(max(fechas).date())
    return ""