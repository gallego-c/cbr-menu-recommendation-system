"""
Sistema CBR Limpio - Solo funcionalidad esencial
Incluye soporte para ratings de calidad de casos
"""

from sistema_cbr import SistemaCBR, PreferenciasUsuario

def generar_menu_simple(tipo_evento='familiar', temporada=None, restricciones=[], 
                       estilo='clasico', tradicion='italiana', 
                       recolectar_rating=False):
    """
    Función simple para generar menús sin prints decorativos.
    
    Args:
        tipo_evento: Tipo de evento (familiar, boda, congreso)
        temporada: Temporada del año (primavera, verano, otoño, invierno, None)
        restricciones: Lista de restricciones dietéticas
        estilo: Estilo culinario (clasico, moderno, fusion, etc.)
        tradicion: Tradición cultural (catalana, italiana, francesa, etc.)
        recolectar_rating: Si preguntar al usuario por rating del menú
        
    Returns:
        Diccionario con el resultado de la generación
    """
    
    sistema = SistemaCBR()
    preferencias = PreferenciasUsuario(
        tipo_evento=tipo_evento,
        temporada=temporada, 
        restricciones=restricciones,
        estilo=estilo,
        tradicion=tradicion
    )
    
    resultado = sistema.generar_menu(preferencias)
    
    resultado_dict = {
        'exito': resultado.exito,
        'menu': resultado.menu if resultado.exito else None,
        'mensaje': resultado.mensaje,
        'caso_base': resultado.caso_base_id,
        'similitud': resultado.similitud_caso_base,
        'nuevo_caso': resultado.nuevo_caso_id
    }
    
    # Si se debe recolectar rating y el menú fue exitoso
    if recolectar_rating and resultado.exito and resultado.menu:
        rating = sistema.recolectar_y_guardar_rating(
            resultado.menu,
            caso_id=resultado.caso_base_id,
            guardar_en_base=True
        )
        resultado_dict['rating'] = rating
    
    return resultado_dict


def ejemplo_uso():
    """Ejemplo de uso del sistema."""
    print("=== SISTEMA CBR LIMPIO ===")
    
    try:
        # Caso 1: Evento familiar en verano con tradición catalana
        resultado1 = generar_menu_simple()
        # El resultado detallado se puede ver descomentando la siguiente línea:
        # print(f"\n\n[DEBUG] Resultado: {resultado1}")
    except Exception as e:
        import traceback
        print(f"\n\n[ERROR] Excepción capturada:")
        print(traceback.format_exc())
    
    print("=== SISTEMA FUNCIONANDO ===")


if __name__ == "__main__":
    ejemplo_uso()