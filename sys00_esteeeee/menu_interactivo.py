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
        '2': 'formal',
        '3': 'casual',
        '4': 'romantico',
        '5': 'celebracion'
    }
    
    for key, value in opciones.items():
        print(f"   {key}. {value.capitalize()}")
    
    while True:
        respuesta = input("\nSelecciona una opcion (1-5) [1]: ").strip()
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
        '2': 'moderno',
        '3': 'fusion',
        '4': 'tradicional',
        '5': 'gourmet'
    }
    
    print("   1. Clasico")
    print("   2. Moderno")
    print("   3. Fusion")
    print("   4. Tradicional")
    print("   5. Gourmet")
    
    while True:
        respuesta = input("\nSelecciona una opcion (1-5) [1]: ").strip()
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
    else:
        print("NO SE PUDO GENERAR EL MENU")
        print("="*60)
        print(f"\nMotivo: {resultado.get('mensaje', 'Error desconocido')}")
    
    print("="*60 + "\n")


def preguntar_continuar():
    respuesta = input("Deseas generar otro menu? (s/n) [n]: ").strip().lower()
    return respuesta == 's' or respuesta == 'si'


def main():
    continuar = True
    
    while continuar:
        mostrar_banner()
        
        tipo_evento = preguntar_tipo_evento()
        temporada = preguntar_temporada()
        restricciones = preguntar_restricciones()
        estilo = preguntar_estilo()
        tradicion = preguntar_tradicion()
        
        mostrar_resumen_preferencias(tipo_evento, temporada, restricciones, estilo, tradicion)
        
        confirmar = input("\nGenerar menu con estas preferencias? (s/n) [s]: ").strip().lower()
        if confirmar == 'n' or confirmar == 'no':
            print("\nGeneracion cancelada. Volviendo al inicio...\n")
            continue
        
        print("\nGenerando menu... Por favor espera.\n")
        
        resultado = generar_menu_simple(
            tipo_evento=tipo_evento,
            temporada=temporada,
            restricciones=restricciones,
            estilo=estilo,
            tradicion=tradicion
        )
        
        mostrar_resultado(resultado)
        
        continuar = preguntar_continuar()
    
    print("\nGracias por usar el Sistema de Generacion de Menus!\n")


if __name__ == "__main__":
    main()
