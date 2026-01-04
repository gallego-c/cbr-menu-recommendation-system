"""
Sistema CBR Limpio - Solo funcionalidad esencial
"""

from sistema_cbr import SistemaCBR, PreferenciasUsuario

def generar_menu_simple(tipo_evento='familiar', temporada='verano', restricciones=[], 
                       estilo='clasico', tradicion='catalana'):
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
    
    # Caso 1: Evento familiar en verano con tradición catalana
    resultado1 = generar_menu_simple('congreso', 'invierno', ['sin gluten'], 'moderno', 'mexicana')
    
    print("=== SISTEMA FUNCIONANDO ===")


if __name__ == "__main__":
    ejemplo_uso()