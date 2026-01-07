"""
Sistema CBR Limpio - Solo funcionalidad esencial
"""

from sistema_cbr import SistemaCBR, PreferenciasUsuario

def generar_menu_simple(tipo_evento='familiar', temporada='invierno', restricciones=[], 
                       estilo='clasico', tradicion='mexicana'):
    """Función simple para generar menús sin prints decorativos."""
    
    sistema = SistemaCBR()
    preferencias = PreferenciasUsuario(
        tipo_evento=tipo_evento,
        temporada=temporada, 
        restricciones=restricciones,
        estilo=estilo,
        tradicion=tradicion
    )
    
    resultado = sistema.generar_menu(preferencias)
    
    return {
        'exito': resultado.exito,
        'menu': resultado.menu if resultado.exito else None,
        'mensaje': resultado.mensaje,
        'caso_base': resultado.caso_base_id,
        'similitud': resultado.similitud_caso_base,
        'nuevo_caso': resultado.nuevo_caso_id
    }


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