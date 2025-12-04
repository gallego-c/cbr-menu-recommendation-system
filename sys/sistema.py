from copy import deepcopy
from typing import List, Dict, Any
from base_casos import BaseCasos
from similitud import CalculadorSimilitud
from recuperacion import ModuloRecuperacion
from simulador import Simulador
from reparador_pkg.reparador_global import reparador_global
from models import Caso, Menu


class SistemaCBR:
    def __init__(self):
        self.base_casos = BaseCasos()
        self.calculador = CalculadorSimilitud()
        self.recuperacion = ModuloRecuperacion(self.base_casos, self.calculador)
        self.simulador = Simulador()

    def resolver(self, caso_nuevo: Caso) -> List[Dict[str, Any]]:
        print("\n" + "="*70)
        print(f"ANTICIPATOR: Procesando solicitud {caso_nuevo.id}")
        print(f"  Evento: {caso_nuevo.tipo_evento.value}, {caso_nuevo.num_comensales} comensales")
        print(f"  Presupuesto: {caso_nuevo.presupuesto}€, Temporada: {caso_nuevo.temporada}")
        print("="*70)

        casos_similares = self.recuperacion.recuperar(caso_nuevo, k=3)

        propuestas_finales = []

        for i, (caso_recuperado, similitud) in enumerate(casos_similares, 1):
            print(f"\n{'='*70}")
            print(f"MODIFICADOR: Procesando candidato {i}/{len(casos_similares)}")
            print(f"  Caso base: {caso_recuperado.id}")
            print(f"  Menú: {caso_recuperado.menu.entrante.nombre} + "
                  f"{caso_recuperado.menu.principal.nombre} + {caso_recuperado.menu.postre.nombre}")
            print("="*70)

            menu_adaptado = deepcopy(caso_recuperado.menu)

            exito, fallos = self.simulador.simular_menu(menu_adaptado, caso_nuevo)

            if not exito:
                menu_reparado, reparaciones = reparador_global(
                    menu_adaptado, fallos, caso_nuevo, self.base_casos
                )

                print(f"\nRE-SIMULACIÓN después de reparaciones:")
                exito_rep, fallos_rep = self.simulador.simular_menu(menu_reparado, caso_nuevo)

                propuesta = {
                    'caso_origen': caso_recuperado.id,
                    'similitud': similitud,
                    'menu': menu_reparado,
                    'valido': exito_rep,
                    'fallos': fallos_rep,
                    'reparaciones': reparaciones,
                    'puntuacion': 0.9 if exito_rep else 0.6
                }
            else:
                propuesta = {
                    'caso_origen': caso_recuperado.id,
                    'similitud': similitud,
                    'menu': menu_adaptado,
                    'valido': True,
                    'fallos': [],
                    'reparaciones': [],
                    'puntuacion': 1.0
                }

            propuestas_finales.append(propuesta)

        self._retener_mejor_caso(caso_nuevo, propuestas_finales)

        return propuestas_finales

    def _retener_mejor_caso(self, caso_nuevo: Caso, propuestas: List[Dict]):
        propuestas_validas = [p for p in propuestas if p['valido']]

        if propuestas_validas:
            mejor = max(propuestas_validas, key=lambda x: x['puntuacion'])

            print("\n" + "="*70)
            print("RETAIN: Almacenando experiencia en la base de casos")
            print("="*70)

            nuevo_caso = Caso(
                id=f"C{len(self.base_casos.obtener_todos()) + 1:03d}",
                tipo_evento=caso_nuevo.tipo_evento,
                num_comensales=caso_nuevo.num_comensales,
                presupuesto=caso_nuevo.presupuesto,
                restricciones=caso_nuevo.restricciones,
                preferencias=caso_nuevo.preferencias,
                temporada=caso_nuevo.temporada,
                menu=mejor['menu'],
                exito=mejor['puntuacion'],
                fallos_detectados=mejor['fallos'],
                reparaciones_aplicadas=mejor['reparaciones']
            )

            agregado = self.base_casos.agregar_caso(nuevo_caso)

            if agregado:
                print(f"✓ Caso {nuevo_caso.id} añadido a la base")
                print(f"  Menú: {nuevo_caso.menu.entrante.nombre}")
                print(f"        {nuevo_caso.menu.principal.nombre}")
                print(f"        {nuevo_caso.menu.postre.nombre}")
                print(f"  Puntuación: {nuevo_caso.exito:.2f}")
            else:
                print(f"→ Caso ya existe en la base de datos. No se agregó.")
        else:
            print("\n⚠ No hay propuestas válidas para retener")

    def mostrar_propuestas(self, propuestas: List[Dict]):
        print("\n" + "="*70)
        print("PROPUESTAS FINALES")
        print("="*70)

        for i, prop in enumerate(propuestas, 1):
            print(f"\n--- PROPUESTA {i} ---")
            print(f"Origen: {prop['caso_origen']} (similitud: {prop['similitud']:.3f})")
            print(f"Estado: {'✓ VÁLIDO' if prop['valido'] else '✗ CON PROBLEMAS'}")
            print(f"Puntuación: {prop['puntuacion']:.2f}")

            menu = prop['menu']
            print(f"\nMenú {menu.estilo.value} - {menu.tradicion.value}:")
            print(f"  Entrante:  {menu.entrante.nombre}")
            print(f"    Ingredientes: {', '.join(menu.entrante.ingredientes)}")
            print(f"    Textura: {menu.entrante.textura}, Sabor: {menu.entrante.sabor_dominante}")
            print(f"  Principal: {menu.principal.nombre}")
            print(f"    Ingredientes: {', '.join(menu.principal.ingredientes)}")
            print(f"    Textura: {menu.principal.textura}, Sabor: {menu.principal.sabor_dominante}")
            print(f"  Postre:    {menu.postre.nombre}")
            print(f"    Ingredientes: {', '.join(menu.postre.ingredientes)}")
            print(f"    Textura: {menu.postre.textura}, Sabor: {menu.postre.sabor_dominante}")

            if prop['reparaciones']:
                print(f"\nReparaciones aplicadas:")
                for rep in prop['reparaciones']:
                    print(f"  • {rep}")

            if not prop['valido'] and prop['fallos']:
                print(f"\n⚠ Problemas pendientes:")
                for fallo in prop['fallos']:
                    print(f"  • {fallo}")

        if propuestas:
            mejor = max(propuestas, key=lambda x: x['puntuacion'])
            print(f"\n{'='*70}")
            print(f"RECOMENDACIÓN: Propuesta {propuestas.index(mejor) + 1} (puntuación: {mejor['puntuacion']:.2f})")
            print("="*70)
