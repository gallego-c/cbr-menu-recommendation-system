"""
Sistema CBR Interactivo - Generacion de Menus
"""

from cbr_limpio import generar_menu_simple


def mostrar_banner():
    print("\n" + "="*60)
    print("   SISTEMA DE GENERACION DE MENUS - CBR")
    print("="*60)
    print("Responde las siguientes preguntas para generar tu menu ideal")
    print("="*60 + "\n")


def preguntar_tipo_evento():
    print("Que tipo de evento es?")
    opciones = {
        '1': 'familiar',
        '2': 'boda',
        '3': 'congreso'
    }
    
    print("   1. Familiar")
    print("   2. Boda")
    print("   3. Congreso")
    
    while True:
        respuesta = input("\nSelecciona una opcion (1-3) [1]: ").strip()
        if respuesta == '':
            return 'familiar'
        if respuesta in opciones:
            return opciones[respuesta]
        print("Opcion no valida. Intenta de nuevo.")


def preguntar_temporada():
    print("\nPara que temporada es el menu?")
    opciones = {
        '1': 'primavera',
        '2': 'verano',
        '3': 'otono',
        '4': 'invierno',
        '5': None
    }
    
    print("   1. Primavera")
    print("   2. Verano")
    print("   3. Otono")
    print("   4. Invierno")
    print("   5. Sin preferencia de temporada")
    
    while True:
        respuesta = input("\nSelecciona una opcion (1-5) [5]: ").strip()
        if respuesta == '':
            return None
        if respuesta in opciones:
            return opciones[respuesta]
        print("Opcion no valida. Intenta de nuevo.")


def preguntar_restricciones():
    print("\nHay alguna restriccion dietetica?")
    print("   Puedes seleccionar varias separadas por coma (ej: 1,3)")
    
    opciones = {
        '1': 'vegetariano',
        '2': 'vegano',
        '3': 'sin_gluten',
        '4': 'sin_lactosa'
    }
    
    print("\n   1. Vegetariano")
    print("   2. Vegano")
    print("   3. Sin gluten")
    print("   4. Sin lactosa")
    print("   0. Ninguna restriccion")
    
    while True:
        respuesta = input("\nSelecciona opciones (ej: 1,3) [0]: ").strip()
        
        if respuesta == '' or respuesta == '0':
            return []
        
        try:
            selecciones = [s.strip() for s in respuesta.split(',')]
            restricciones = []
            
            for sel in selecciones:
                if sel in opciones:
                    restricciones.append(opciones[sel])
                elif sel != '0':
                    raise ValueError(f"Opcion '{sel}' no valida")
            
            return restricciones
        except ValueError as e:
            print(f"{e}. Intenta de nuevo.")


def preguntar_estilo():
    print("\nQue estilo culinario prefieres?")
    opciones = {
        '1': 'clasico',
        '2': 'molecular'
    }
    
    print("   1. Clasico")
    print("   2. Molecular")
    
    while True:
        respuesta = input("\nSelecciona una opcion (1-2) [1]: ").strip()
        if respuesta == '':
            return 'clasico'
        if respuesta in opciones:
            return opciones[respuesta]
        print("Opcion no valida. Intenta de nuevo.")


def preguntar_tradicion():
    print("\nDe que tradicion culinaria quieres el menu?")
    opciones = {
        '1': 'catalana',
        '2': 'mexicana',
        '3': 'italiana',
        '4': 'india',
        '5': 'francesa',
        '6': 'china',
        '7': None
    }
    
    print("   1. Catalana")
    print("   2. Mexicana")
    print("   3. Italiana")
    print("   4. India")
    print("   5. Francesa")
    print("   6. China")
    print("   7. Sin preferencia de tradicion")
    
    while True:
        respuesta = input("\nSelecciona una opcion (1-7) [7]: ").strip()
        if respuesta == '':
            return None
        if respuesta in opciones:
            return opciones[respuesta]
        print("Opcion no valida. Intenta de nuevo.")


def mostrar_resumen_preferencias(tipo_evento, temporada, restricciones, estilo, tradicion):
    print("\n" + "-"*50)
    print("RESUMEN DE TUS PREFERENCIAS:")
    print("-"*50)
    print(f"   Tipo de evento: {tipo_evento.capitalize()}")
    print(f"   Temporada: {temporada.capitalize() if temporada else 'Sin preferencia'}")
    print(f"   Restricciones: {', '.join(restricciones) if restricciones else 'Ninguna'}")
    print(f"   Estilo: {estilo.capitalize()}")
    print(f"   Tradicion: {tradicion.capitalize() if tradicion else 'Sin preferencia'}")
    print("-"*50)


def mostrar_resultado(resultado):
    print("\n" + "="*60)
    
    if resultado['exito']:
        print("MENU GENERADO CON EXITO")
        print("="*60)
        print("\nTU MENU PERSONALIZADO:\n")
        
        menu = resultado['menu']
        print(f"   Entrante:  {menu['entrante']}")
        print(f"   Principal: {menu['principal']}")
        print(f"   Postre:    {menu['postre']}")
        
        print("\n" + "-"*50)
        print(f"Estadisticas:")
        print(f"   Caso base utilizado: {resultado['caso_base']}")
        print(f"   Similitud: {resultado['similitud']:.1%}")
        if resultado.get('nuevo_caso'):
            print(f"   Nuevo caso guardado: {resultado['nuevo_caso']}")
        
        # Retornar True para indicar éxito (usado para pregunta de rating)
        return True
    else:
        print("NO SE PUDO GENERAR EL MENU")
        print("="*60)
        print(f"\nMotivo: {resultado.get('mensaje', 'Error desconocido')}")
        return False
    
    print("="*60 + "\n")


def preguntar_rating_menu(menu, caso_id=None):
    """
    Pregunta al usuario si desea calificar el menú generado.
    
    Args:
        menu: Diccionario con el menú generado
        caso_id: ID del caso (opcional, para mostrar)
        
    Returns:
        Rating (1-5) o None si se omite
    """
    print("\n" + "-"*60)
    print("CALIFICACIÓN DEL MENÚ")
    print("-"*60)
    print("¿Te gustaría calificar este menú?")
    print("Esto ayudará al sistema a mejorar futuras recomendaciones.")
    print()
    
    respuesta = input("¿Calificar menú? (s/n) [s]: ").strip().lower()
    
    if respuesta == 'n' or respuesta == 'no':
        print("Calificación omitida.")
        return None
    
    print("\nCalifica el menú del 1 al 5:")
    print("  1 - Muy malo")
    print("  2 - Malo")
    print("  3 - Regular")
    print("  4 - Bueno")
    print("  5 - Excelente")
    print()
    
    max_intentos = 3
    for intento in range(max_intentos):
        try:
            rating_str = input("Tu calificación (1-5): ").strip()
            rating = float(rating_str)
            
            if 1 <= rating <= 5:
                print(f"\n✓ Gracias por tu calificación: {rating}/5")
                return rating
            else:
                print("Error: La calificación debe estar entre 1 y 5")
        except ValueError:
            print("Error: Por favor ingresa un número entre 1 y 5")
        except (EOFError, KeyboardInterrupt):
            print("\nCalificación cancelada")
            return None
    
    print("Demasiados intentos. Calificación omitida.")
    return None


def preguntar_continuar():
    respuesta = input("Deseas generar otro menu? (s/n) [n]: ").strip().lower()
    return respuesta == 's' or respuesta == 'si'


def main():
    from sistema_cbr import SistemaCBR, PreferenciasUsuario
    
    # Inicializar sistema CBR una sola vez
    print("\nInicializando sistema CBR...")
    sistema = SistemaCBR()
    print("Sistema listo.\n")
    
    continuar = True
    
    while continuar:
        mostrar_banner()
        
        tipo_evento = preguntar_tipo_evento()
        temporada = preguntar_temporada()
        restricciones = preguntar_restricciones()
        estilo = preguntar_estilo()
        tradicion = preguntar_tradicion()
        
        mostrar_resumen_preferencias(tipo_evento, temporada, restricciones, estilo, tradicion)
        
        confirmar = input("\n¿Generar menú con estas preferencias? (s/n) [s]: ").strip().lower()
        if confirmar == 'n' or confirmar == 'no':
            print("\nGeneración cancelada. Volviendo al inicio...\n")
            continue
        
        print("\nGenerando menú... Por favor espera.\n")
        
        # Crear preferencias y generar menú
        preferencias = PreferenciasUsuario(
            tipo_evento=tipo_evento,
            temporada=temporada,
            restricciones=restricciones,
            estilo=estilo,
            tradicion=tradicion
        )
        
        resultado_cbr = sistema.generar_menu(preferencias)
        
        # Convertir resultado a formato para mostrar
        resultado = {
            'exito': resultado_cbr.exito,
            'menu': resultado_cbr.menu if resultado_cbr.exito else None,
            'mensaje': resultado_cbr.mensaje,
            'caso_base': resultado_cbr.caso_base_id,
            'similitud': resultado_cbr.similitud_caso_base,
            'nuevo_caso': resultado_cbr.nuevo_caso_id
        }
        
        menu_exitoso = mostrar_resultado(resultado)
        
        continuar = preguntar_continuar()
    
    print("\n¡Gracias por usar el Sistema de Generación de Menús!\n")


if __name__ == "__main__":
    main()
