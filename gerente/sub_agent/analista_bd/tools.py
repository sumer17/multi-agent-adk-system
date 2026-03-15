import os
import json
from datetime import datetime
from google.cloud import bigquery


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

proyecto_bq = os.getenv("GOOGLE_CLOUD_PROJECT", "projectid") #projectid
dataset_bq = os.getenv("BQ_DATASET_ID", "cloudmart_sales_data")

def get_retail_data(sql_query: str) -> str:
    """
    Ejecuta una consulta SQL en BigQuery para obtener datos de ventas, tiendas y productos.
    Incluye validación de seguridad, ejecución en tiempo real y logs de auditoría.
    """
    
    
    query_segura = sql_query.lower()
    
    if any(palabra in query_segura for palabra in ['drop', 'delete', 'insert', 'update', 'alter']):
        return "ERROR DE SEGURIDAD: Solo tienes permitido hacer consultas SELECT."
        
    if "cloudmart_sales_data" not in query_segura:
        return "ERROR DE SEGURIDAD: Solo puedes consultar tablas dentro del dataset 'cloudmart_sales_data'."
    
    # GUARDAR LA CONSULTA 
    try:
        with open("historial_consultas_agente.txt", "a", encoding="utf-8") as archivo_log:
            marca_tiempo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            archivo_log.write(f"[{marca_tiempo}] Consulta Ejecutada:\n{sql_query}\n{'-'*50}\n")
    except Exception as e:
        print(f"Error al guardar log de auditoría: {e}")

    print(f"\n[LOG DEL SISTEMA] El LLM generó y ejecutó el siguiente SQL:\n{sql_query}\n")
    
    try:
        cliente = bigquery.Client(project=proyecto_bq)
        trabajo = cliente.query(sql_query)
        resultados = trabajo.result()
        
        datos = [dict(fila) for fila in resultados]
        
        # MANEJO DE ERRORES
        if len(datos) == 0:
            
            parte_where = query_segura.split('where')[-1] if 'where' in query_segura else ""
            
            if 'ciudad' in parte_where:
                query_sugerencia = f"SELECT DISTINCT ciudad_tienda FROM `{proyecto_bq}.{dataset_bq}.tienda` WHERE ciudad_tienda IS NOT NULL LIMIT 20"
                tipo_dato = "ciudades"
                columna = "ciudad_tienda"
            elif 'marca' in parte_where:
                query_sugerencia = f"SELECT DISTINCT marca_homologada FROM `{proyecto_bq}.{dataset_bq}.producto` WHERE marca_homologada IS NOT NULL LIMIT 20"
                tipo_dato = "marcas"
                columna = "marca_homologada"
            else:
                
                query_sugerencia = f"SELECT DISTINCT nombre_region FROM `{proyecto_bq}.{dataset_bq}.tienda` WHERE nombre_region IS NOT NULL"
                tipo_dato = "regiones"
                columna = "nombre_region"
            
            
            opciones_reales = [str(fila[columna]) for fila in cliente.query(query_sugerencia).result()]
            lista_opciones = ", ".join(opciones_reales)
            
            
            with open("datos_temporales.json", "w", encoding="utf-8") as f:
                f.write(json.dumps({"error": f"No hay datos para procesar."}))
                
            
            return f"ADVERTENCIA: No se encontraron datos. DILE ESTO EXACTAMENTE AL USUARIO: 'No encontré datos para tu búsqueda. Algunas de las {tipo_dato} que sí tenemos disponibles en la base de datos son: {lista_opciones}'"
            
        
        datos_json = json.dumps(datos, default=str)
        
        with open("datos_temporales.json", "w", encoding="utf-8") as f:
            f.write(datos_json)
            
        return f"ÉXITO: Se extrajeron {len(datos)} filas. Los datos ya están guardados en el disco temporal listos para el CSV."

    except Exception as e:
        return f"Error ejecutando SQL en BigQuery: {str(e)}"