"""
🎯 OBJETIVO:

Estamos desarrollando una API con FastAPI que recibirá 3 archivos CSV:
1. stock.csv
2. ventas.csv
3. historico_stock_ventas.csv

Queremos que, al procesarlos, el sistema devuelva una única respuesta JSON, estructurada en **dos bloques**:

{
  "openai": { ... análisis completo y detallado ... },
  "dashboard": { ... resumen simplificado para frontend ... }
}

🔹 El bloque `openai` se usará como input para un agente de ChatGPT (vía Make), por lo tanto debe incluir:
- productos con stock bajo
- productos con rotación lenta
- productos muertos
- top 5 más vendidos del mes
- estimaciones de velocidad de venta
- promedios de unidades vendidas por SKU
- métricas globales relevantes
- eventos detectados: roturas, reposiciones, lentitud de venta, etc.

🔹 El bloque `dashboard` se usará para alimentar un frontend (Appsmith), por lo tanto solo debe incluir:
- lista de productos con alerta de stock bajo (nombre, SKU, stock restante)
- resumen global (total productos, total vendidos, promedio de rotación)
- top 3 productos más vendidos
- fecha de último análisis

💡 Ambos bloques se devuelven en la misma respuesta JSON al llamar a POST `/procesar-todos/`.

✍️ Asegúrate de que el endpoint tenga docstrings y comentarios que expliquen:
- qué hace cada parte
- cómo se comporta al desplegar en Render.com
- cómo se espera que lo consuma el frontend o el agente

💬 También indica en comentarios:
- cómo acceder a esta API desde Swagger (p. ej. /docs)
- cómo testearlo desde el navegador tras desplegarlo
"""

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from .utils import read_stock_csv, read_ventas_csv, read_historico_csv
from .custom_logic import (
    productos_bajo_stock,
    productos_rotacion_lenta,
    productos_muertos,
    top_n_vendidos_mes,
    estimaciones_velocidad_venta,
    promedios_unidades_vendidas,
    metricas_globales,
    eventos_detectados,
    resumen_global_dashboard,
    top_3_vendidos_dashboard,
    fecha_ultimo_analisis
)

app = FastAPI(
    title="Stock, Ventas e Histórico API",
    description="""
    API para analizar inventario, ventas y su histórico en comercios minoristas.

    - Sube tus archivos en /docs (Swagger UI) y obtén análisis completo y resumen para dashboard.
    - Este endpoint está preparado para funcionar en entornos cloud como Render.com.
    """,
    version="1.0.0"
)

@app.get("/")
async def root():
    """Endpoint de health check para Render.com"""
    return { "status": "ok" }

@app.post("/procesar-todos/")
async def procesar_todos(
    stock_file: UploadFile = File(..., description="Archivo stock.csv"),
    ventas_file: UploadFile = File(..., description="Archivo ventas.csv"),
    historico_file: UploadFile = File(..., description="Archivo historico_stock_ventas.csv")
):
    """
    Procesa tres archivos CSV (stock, ventas, histórico) y devuelve un análisis estructurado para dos usos:
    - openai: Input detallado para agente GPT (Make.com)
    - dashboard: Resumen para frontend (Appsmith)

    Acceso desde Swagger UI: /docs
    Acceso tras desplegar en Render: https://<tu-app>.onrender.com/docs

    ¿Cómo testear tras desplegar?
    1. Accede a /docs
    2. Prueba el endpoint `/procesar-todos/`
    3. Sube los tres archivos CSV con los nombres correctos.
    4. Obtendrás un JSON con dos bloques: openai y dashboard.
    """
    # Leer archivos CSV a memoria
    stock_bytes = await stock_file.read()
    ventas_bytes = await ventas_file.read()
    historico_bytes = await historico_file.read()
    stock_df = read_stock_csv(stock_bytes)
    ventas_df = read_ventas_csv(ventas_bytes)
    historico_df = read_historico_csv(historico_bytes)

    # --- BLOQUE PARA OPENAI (Make/Agente GPT) ---
    openai_block = {
        "productos_bajo_stock": productos_bajo_stock(stock_df),
        "productos_rotacion_lenta": productos_rotacion_lenta(ventas_df, historico_df, stock_df),
        "productos_muertos": productos_muertos(ventas_df, stock_df),
        "top_5_mas_vendidos_mes": top_n_vendidos_mes(ventas_df, stock_df, n=5),
        "estimaciones_velocidad_venta": estimaciones_velocidad_venta(ventas_df, stock_df),
        "promedios_unidades_vendidas": promedios_unidades_vendidas(ventas_df),
        "metricas_globales": metricas_globales(stock_df, ventas_df, historico_df),
        "eventos_detectados": eventos_detectados(historico_df)
    }

    # --- BLOQUE PARA DASHBOARD (Appsmith/Frontend) ---
    dashboard_block = {
        "alerta_stock_bajo": [
            {
                "nombre": prod["Producto"],
                "sku": prod["SKU"],
                "stock_restante": prod["Stock"]
            }
            for prod in productos_bajo_stock(stock_df)
        ],
        "resumen_global": resumen_global_dashboard(stock_df, ventas_df, historico_df),
        "top_3_mas_vendidos": top_3_vendidos_dashboard(ventas_df, stock_df),
        "fecha_ultimo_analisis": fecha_ultimo_analisis(ventas_df, historico_df)
    }

    return JSONResponse(content={
        "openai": openai_block,
        "dashboard": dashboard_block
    })