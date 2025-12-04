#!/usr/bin/env python3
"""
Test script to force the reparador to activate with a conflicted menu.
Creates a test case that requests vegetarian food but gets a case with meat.
"""
import sys
sys.path.insert(0, 'sys')

from models import Plato, Menu, Caso, EstiloCulinario, TradicionCultural, TipoEvento
from sistema import SistemaCBR

def test_reparador():
    print("\n" + "="*70)
    print("TEST REPARADOR: Forcing conflict resolution")
    print("="*70)

    sistema = SistemaCBR()
    
    # Create a test case that will likely retrieve C001 (which has meat but needs vegetarian)
    caso_test = Caso(
        id="TEST_REPAIR",
        tipo_evento=TipoEvento.BODA,
        num_comensales=100,
        presupuesto=5000.0,
        restricciones=["vegetariano"],  # This conflicts with C001 "ternera" 
        preferencias=["elegante"],
        temporada="primavera",
        menu=Menu(
            entrante=Plato("", [], "", [], "", "", []),
            principal=Plato("", [], "", [], "", "", []),
            postre=Plato("", [], "", [], "", "", []),
            estilo=EstiloCulinario.CLASICO,
            tradicion=TradicionCultural.ITALIANA
        )
    )

    propuestas = sistema.resolver(caso_test)
    sistema.mostrar_propuestas(propuestas)

if __name__ == "__main__":
    test_reparador()