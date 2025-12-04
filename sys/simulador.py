# El simulador si ha de tener reglas no?
# .

from typing import List, Tuple
from dominio import ConocimientoDominio
from models import Menu, Caso, EstiloCulinario, TradicionCultural


class Simulador:
    """Simula la ejecución del menú y detecta fallos potenciales"""

    def __init__(self):
        self.conocimiento = ConocimientoDominio()

    def simular_menu(self, menu: Menu, caso: Caso) -> Tuple[bool, List[str]]:
        print("\n" + "-"*70)
        print("SIMULATOR: Ejecutando menú propuesto...")
        print("-"*70)

        fallos = []

        fallos.extend(self._verificar_restricciones(menu, caso.restricciones))
        fallos.extend(self._verificar_balance(menu))
        fallos.extend(self._verificar_temporada(menu, caso.temporada))
        fallos.extend(self._verificar_coherencia_cultural(menu))

        exito = len(fallos) == 0

        if exito:
            print("✓ Menú válido: todos los objetivos cumplidos")
            self._mostrar_resultados_positivos(menu)
        else:
            print(f"✗ Se detectaron {len(fallos)} problemas:")
            for i, fallo in enumerate(fallos, 1):
                print(f"  {i}. {fallo}")

        return exito, fallos

    def _verificar_restricciones(self, menu: Menu, restricciones: List[str]) -> List[str]:
        fallos = []
        platos = [
            ("entrante", menu.entrante),
            ("principal", menu.principal),
            ("postre", menu.postre)
        ]

        for nombre_plato, plato in platos:
            for restriccion in restricciones:
                for ingrediente in plato.ingredientes:
                    if not self.conocimiento.verificar_restriccion(ingrediente, restriccion):
                        fallos.append(
                            f"RESTRICCION-VIOLADA: {ingrediente} en {nombre_plato} "
                            f"viola restricción '{restriccion}'"
                        )

        return fallos

    def _verificar_balance(self, menu: Menu) -> List[str]:
        fallos = []
        texturas = [menu.entrante.textura, menu.principal.textura, menu.postre.textura]
        if texturas[0] == texturas[1] == texturas[2]:
            fallos.append(
                f"DESBALANCE-TEXTURA: todas las texturas son '{texturas[0]}'. "
                f"Se recomienda variedad"
            )

        sabores = [menu.entrante.sabor_dominante, menu.principal.sabor_dominante,
                   menu.postre.sabor_dominante]
        if sabores.count(sabores[0]) == 3:
            # Usar el campo ingrediente_sabor de cada plato
            ingredientes_causantes = [
                f"{menu.entrante.ingrediente_sabor} en entrante",
                f"{menu.principal.ingrediente_sabor} en principal", 
                f"{menu.postre.ingrediente_sabor} en postre"
            ]
            
            fallos.append(
                f"DESBALANCE-SABOR: todos los platos tienen sabor dominante '{sabores[0]}' "
                f"debido a: {', '.join(ingredientes_causantes)}"
            )

        return fallos

    def _verificar_temporada(self, menu: Menu, temporada: str) -> List[str]:
        fallos = []
        platos = [
            ("entrante", menu.entrante),
            ("principal", menu.principal),
            ("postre", menu.postre)
        ]

        for nombre_plato, plato in platos:
            # Verificar si el plato tiene temporada especificada
            if temporada not in plato.temporada and "todo" not in plato.temporada:
                # Usar ingredientes_temporada para explicar el problema específicamente
                if plato.ingredientes_temporada:
                    # Mostrar qué ingredientes específicos determinan la temporada incorrecta
                    ingredientes_con_temporada = []
                    for ing in plato.ingredientes_temporada:
                        # Buscar en qué temporada está ese ingrediente
                        for temp, ings_temp in self.conocimiento.TEMPORADA.items():
                            if ing in ings_temp and temp != temporada:
                                ingredientes_con_temporada.append(f"{ing} (temporada {temp})")
                                break
                    
                    if ingredientes_con_temporada:
                        fallos.append(
                            f"FUERA-TEMPORADA: {plato.nombre} no es de temporada '{temporada}' "
                            f"debido a: {', '.join(ingredientes_con_temporada)}"
                        )
                    else:
                        # Si ingredientes_temporada está definido pero no se encuentra temporada específica
                        fallos.append(
                            f"FUERA-TEMPORADA: {plato.nombre} no es de temporada '{temporada}' "
                            f"debido a: {', '.join(plato.ingredientes_temporada)}"
                        )
                else:
                    # Fallback al mensaje genérico si no hay ingredientes_temporada definidos
                    fallos.append(
                        f"FUERA-TEMPORADA: {plato.nombre} no es de temporada '{temporada}'"
                    )
            
            # Verificar ingredientes individuales de temporada
            ingredientes_fuera_temporada = []
            for ingrediente in plato.ingredientes:
                if self.conocimiento.ingrediente_temporada(ingrediente, temporada):
                    # Ingrediente está en temporada, es positivo
                    pass
                else:
                    # Verificar si es un ingrediente de temporada específico de otra época
                    for temp, ings_temp in self.conocimiento.TEMPORADA.items():
                        if ingrediente in ings_temp and temp != temporada:
                            ingredientes_fuera_temporada.append(f"{ingrediente} (temporada {temp})")
                            break
                    else:
                        # Si no está en ninguna temporada específica, no marcar como error estacional
                        pass
            
            if ingredientes_fuera_temporada:
                fallos.append(
                    f"INGREDIENTES-FUERA-TEMPORADA: {', '.join(ingredientes_fuera_temporada)} "
                    f"en {nombre_plato} no son de temporada '{temporada}'"
                )

        return fallos

    def _verificar_coherencia_cultural(self, menu: Menu) -> List[str]:
        fallos = []
        if menu.estilo == EstiloCulinario.MOLECULAR:
            if menu.tradicion in [TradicionCultural.RUSA, TradicionCultural.ETIOPE]:
                fallos.append(
                    f"INCOHERENCIA-ESTILO: estilo '{menu.estilo.value}' poco común "
                    f"con tradición '{menu.tradicion.value}'"
                )

        return fallos

    def _mostrar_resultados_positivos(self, menu: Menu):
        print("\nResultados de la simulación:")
        print(f"  • Texturas: {menu.entrante.textura} → {menu.principal.textura} → {menu.postre.textura}")
        print(f"  • Sabores: {menu.entrante.sabor_dominante} → {menu.principal.sabor_dominante} → {menu.postre.sabor_dominante}")
        print(f"  • Coherencia: {menu.estilo.value} + {menu.tradicion.value} ✓")
