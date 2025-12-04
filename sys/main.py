from models import Plato, Menu, Caso, EstiloCulinario, TradicionCultural, TipoEvento
from sistema import SistemaCBR


def main():
    print("\n" + "="*70)
    print("SISTEMA CBR DE PLANIFICACIÓN DE MENÚS")
    print("Inspirado en CHEF (Hammond, 1986)")
    print("="*70)

    sistema = SistemaCBR()

    # EJEMPLO 1
    print("\n\n" + "#"*70)
    print("# EJEMPLO 1: Boda vegetariana en verano")
    print("#"*70)

    caso_test1 = Caso(
        id="TEST001",
        tipo_evento=TipoEvento.FAMILIAR,
        num_comensales=120,
        presupuesto=6000.0,
        restricciones=["vegetariano"],
        preferencias=["elegante", "fresco"],
        temporada="verano",
        menu=Menu(
            entrante=Plato("", [], [], [], "", "", "", []),
            principal=Plato("", [], [], [], "", "", "", []),
            postre=Plato("", [], [], [], "", "", "", []),
            estilo=EstiloCulinario.MEDITERRANEO,
            tradicion=TradicionCultural.ITALIANA
        )
    )

    propuestas1 = sistema.resolver(caso_test1)
    sistema.mostrar_propuestas(propuestas1)

    # # EJEMPLO 2
    # print("\n\n" + "#"*70)
    # print("# EJEMPLO 2: Congreso con restricciones halal")
    # print("#"*70)

    # caso_test2 = Caso(
    #     id="TEST002",
    #     tipo_evento=TipoEvento.CONGRESO,
    #     num_comensales=80,
    #     presupuesto=3000.0,
    #     restricciones=["halal"],
    #     preferencias=["tradicional", "sustancioso"],
    #     temporada="otoño",
    #     menu=Menu(
    #         entrante=Plato("", [], "", [], "", "", []),
    #         principal=Plato("", [], "", [], "", "", []),
    #         postre=Plato("", [], "", [], "", "", []),
    #         estilo=EstiloCulinario.CLASICO,
    #         tradicion=TradicionCultural.MARROQUI
    #     )
    # )

    # propuestas2 = sistema.resolver(caso_test2)
    # sistema.mostrar_propuestas(propuestas2)

    # # EJEMPLO 3
    # print("\n\n" + "#"*70)
    # print("# EJEMPLO 3: Banquete de alta cocina molecular")
    # print("#"*70)

    # caso_test3 = Caso(
    #     id="TEST003",
    #     tipo_evento=TipoEvento.BANQUETE,
    #     num_comensales=40,
    #     presupuesto=8000.0,
    #     restricciones=[],
    #     preferencias=["vanguardista", "sorprendente", "espectacular"],
    #     temporada="primavera",
    #     menu=Menu(
    #         entrante=Plato("", [], "", [], "", "", []),
    #         principal=Plato("", [], "", [], "", "", []),
    #         postre=Plato("", [], "", [], "", "", []),
    #         estilo=EstiloCulinario.MOLECULAR,
    #         tradicion=TradicionCultural.CATALANA
    #     )
    # )

    # propuestas3 = sistema.resolver(caso_test3)
    # sistema.mostrar_propuestas(propuestas3)

    # Estadísticas finales
    print("\n\n" + "="*70)
    print("ESTADÍSTICAS DEL SISTEMA")
    print("="*70)

    casos_totales = len(sistema.base_casos.obtener_todos())
    if casos_totales > 0:
        casos_exitosos = len([c for c in sistema.base_casos.obtener_todos() if c.exito >= 0.9])

        print(f"Total de casos en la base: {casos_totales}")
        print(f"Casos exitosos (≥90%): {casos_exitosos}")
        print(f"Tasa de éxito: {casos_exitosos/casos_totales*100:.1f}%")

        print("\nDistribución por tipo de evento:")
        tipos = {}
        for caso in sistema.base_casos.obtener_todos():
            tipo = caso.tipo_evento.value
            tipos[tipo] = tipos.get(tipo, 0) + 1

        for tipo, count in tipos.items():
            print(f"  {tipo.capitalize()}: {count}")
    else:
        print("No hay casos en la base de datos")

    print("\n" + "="*70)
    print("Sistema CBR finalizado")
    print("="*70)


if __name__ == "__main__":
    main()
