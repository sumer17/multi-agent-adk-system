import os
import json
import pandas as pd
from datetime import datetime
import logging

from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool


from gerente.sub_agent.analista_bd.agent import agente_analista

logger = logging.getLogger(__name__)


async def llamar_analista_bd(peticion: str, tool_context: ToolContext):
    """Herramienta para delegar la extracción de datos de BigQuery al Analista."""
    logger.debug("Llamando al Analista BD con: %s", peticion)

    agent_tool = AgentTool(agent=agente_analista)

    resultado_analista = await agent_tool.run_async(
        args={"request": peticion}, tool_context=tool_context
    )
    
    tool_context.state["datos_extraidos"] = resultado_analista
    return resultado_analista

def csv_report_generator(nombre_archivo: str = "reporte.csv", top_n: int = 5, tipo_reporte: str = "rentabilidad", guardar_csv: bool = True) -> str:
    """
    Lee los datos del disco, calcula métricas y opcionalmente genera un CSV.
    NOTA PARA EL AGENTE: Si tipo_reporte='general', el parámetro top_n se ignora, no te preocupes por él.
    """
    try:
        # 1. Definimos la ruta absoluta hacia tu carpeta de reportes
        ruta_reportes = r"C:\Users\Fabian\Desktop\estudio\repo1\practica_adkw\mis_agentes\multi-agent-adk-system\gerente\generated_reports"
        
        # 2. Nos aseguramos de que la carpeta exista antes de intentar guardar algo
        os.makedirs(ruta_reportes, exist_ok=True)

        if not os.path.exists("datos_temporales.json"):
            return "Error crítico: No se encontró el archivo temporal de datos. El analista debe extraerlos primero."
            
        with open("datos_temporales.json", "r", encoding="utf-8") as f:
            datos = json.load(f)
        
        if isinstance(datos, dict) and "error" in datos:
            return f"No puedo procesar los datos. Error: {datos['error']} {datos.get('sugerencia', '')}"
            
        df = pd.DataFrame(datos)
        
        if tipo_reporte == "general":
            resumen_texto = f"- Se han procesado y extraído un total de {len(df)} registros de ventas exitosamente."
            
            if guardar_csv:
                marca_tiempo = datetime.now().strftime("%Y%m%d_%H%M%S")
                nombre_base, extension = os.path.splitext(nombre_archivo)
                nombre_unico = f"{nombre_base}_general_{marca_tiempo}{extension if extension else '.csv'}"
                ruta_absoluta = os.path.join(ruta_reportes, nombre_unico)
                
                df.to_csv(ruta_absoluta, index=False, encoding='utf-8')
                return f"ÉXITO: Reporte general guardado en: {ruta_absoluta}.\n\nAquí tienes el resumen de los datos calculados para mostrar por pantalla:\n{resumen_texto}"
            else:
                return f"ÉXITO: Cálculos realizados (No se guardó archivo físico).\n\nAquí tienes el resumen de los datos calculados para mostrar por pantalla:\n{resumen_texto}"
        
        elif tipo_reporte == "rentabilidad":
            columnas_esperadas = ['nombre_region', 'marca_homologada', 'monto_venta_neta_sin_iva', 'costo_venta', 'cantidad_unidades_vendidas']
            for col in columnas_esperadas:
                if col not in df.columns:
                    return f"Error: Faltan columnas en los datos. El SQL debe traer: {', '.join(columnas_esperadas)}"


            df['precio_unitario'] = (df['monto_venta_neta_sin_iva'] / df['cantidad_unidades_vendidas']).fillna(0)
            df['costo_base'] = (df['costo_venta'] / df['cantidad_unidades_vendidas']).fillna(0)
            df['cantidad'] = df['cantidad_unidades_vendidas']
            
            # FÓRMULA
            df['rentabilidad_fila'] = (df['precio_unitario'] - df['costo_base']) * df['cantidad']
            
            df_agrupado = df.groupby(['nombre_region', 'marca_homologada'])['rentabilidad_fila'].sum().reset_index()
            df_agrupado.rename(columns={'rentabilidad_fila': 'rentabilidad_total'}, inplace=True)
            
            df_ordenado = df_agrupado.sort_values(by=['nombre_region', 'rentabilidad_total'], ascending=[True, False])
            df_top_final = df_ordenado.groupby('nombre_region').head(top_n)

            resumen_texto = "\n".join([f"- {row['marca_homologada']}: Rentabilidad ${row['rentabilidad_total']:,.0f}" for _, row in df_top_final.iterrows()])
            

            mensajes_extra = []
            for region in df_top_final['nombre_region'].unique():
                cantidad_real = len(df_top_final[df_top_final['nombre_region'] == region])
                if cantidad_real < top_n:
                    mensajes_extra.append(f"En la región {region} solo se encontraron {cantidad_real} marcas con ventas en este periodo.")
            
            nota_advertencia = " ".join(mensajes_extra)
            
            if guardar_csv:
                nombre_base, extension = os.path.splitext(nombre_archivo)
                marca_tiempo = datetime.now().strftime("%Y%m%d_%H%M%S")
                nombre_unico = f"{nombre_base}_rentabilidad_{marca_tiempo}{extension if extension else '.csv'}"
                ruta_absoluta = os.path.join(ruta_reportes, nombre_unico)
                df_top_final.to_csv(ruta_absoluta, index=False, encoding='utf-8')
                mensaje_final = f"ÉXITO: Reporte guardado en: {ruta_absoluta}."
            else:
                mensaje_final = "ÉXITO: Cálculos realizados (No se guardó archivo físico)."

            if nota_advertencia:
                mensaje_final += f" IMPORTANTE DILE AL USUARIO: {nota_advertencia}"
                
            return f"{mensaje_final}\n\nAquí tienes el resumen de los datos calculados para mostrar por pantalla:\n{resumen_texto}"

    except Exception as e:
        return f"Error procesando los datos o generando el CSV: {str(e)}"