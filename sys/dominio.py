# Puedo poner dominio? no son como reglas? pero al final al exemple
# del chef creava tregles nomes que les generava el model
# .

from typing import List, Optional


class ConocimientoDominio:
    """Ontología y conocimiento causal del dominio gastronómico"""

    INCOMPATIBILIDADES = {
        "vegetariano": ["ternera", "pollo", "pescado"],
        "vegano": ["ternera", "pollo", "pescado", "huevo", "mantequilla"]
    }

    # Solo incluir temporadas que aparecen en la base de datos
    TEMPORADA = {
        "verano": ["fruta"],
        "otoño": ["setas", "calabaza", "manzana"]
    }

    # Reglas organizadas por tipo de problema que resuelven
    # SOLO incluye transformaciones posibles con la base de datos actual
    
    # ==================== REGLAS PARA RESTRICCIONES DIETÉTICAS ====================
    REGLAS_RESTRICCIONES = {
        "vegetariano": [
            # Reemplazar carnes por ingredientes vegetarianos disponibles
            ("any", "vegetariano", {
                "reemplazar": [
                    {"de": "ternera", "por": "setas"},
                    {"de": "pollo", "por": "setas"},
                    {"de": "pescado", "por": "huevo"}  # huevo es vegetariano
                ],
                "eliminar": ["ternera", "pollo", "pescado"]
            })
        ],
        "vegano": [
            # Eliminar productos de origen animal
            ("any", "vegano", {
                "reemplazar": [
                    {"de": "ternera", "por": "setas"},
                    {"de": "pollo", "por": "setas"},
                    {"de": "pescado", "por": "calabaza"},
                    {"de": "huevo", "por": "harina"},  # para textura en preparaciones
                    {"de": "mantequilla", "por": "aceite_oliva"}  # aunque no esté en base, es comú
                ],
                "eliminar": ["ternera", "pollo", "pescado", "huevo", "mantequilla"]
            })
        ]
    }

    # ==================== REGLAS PARA PROBLEMAS DE TEMPORADA ====================
    REGLAS_TEMPORADA = {
        "fuera_temporada": [
            # Reemplazar ingredientes de otoño cuando se necesita verano
            ("Otoño", "Verano", {
                "reemplazar": [
                    {"de": "calabaza", "por": "patata"},  # patata está disponible
                    {"de": "setas", "por": "arroz"},      # cambiar a algo neutral
                    {"de": "manzana", "por": "fruta"}     # fruta es más genérica para verano
                ],
                "eliminar": ["calabaza", "setas", "manzana"]
                
            }),
            ("Verano", "Otoño", {
                "reemplazar": [
                    {"de": "fruta", "por": "manzana"}
                ],
                "eliminar": ["fruta"]
            })
        ]
    }

    # ==================== REGLAS PARA PROBLEMAS DE TEXTURA ====================
    REGLAS_TEXTURA = {
        "desbalance_textura": [
            # Cambios de textura usando ingredientes/técnicas disponibles
            ("suave_a_firme", "variedad_textura", {
                "tecnica": "asado"  # cambiar de hervir/crudo a asado para firmar
            }),
            ("cremoso_a_firme", "variedad_textura", {
                "añadir": ["harina"],
                "tecnica": "horneado"
            }),
            ("firme_a_suave", "variedad_textura", {
                "tecnica": "hervir"
            })
        ]
    }

    # ==================== REGLAS PARA PROBLEMAS DE SABOR ====================
    REGLAS_SABOR = {
        "desbalance_sabor": [
            # Balance de sabores usando ingredientes disponibles
            ("dulce_excesivo", "equilibrio_sabor", {
                "añadir": ["sal"],  # sal está disponible
                "reducir": ["azucar"]
            }),
            ("umami_excesivo", "equilibrio_sabor", {
                "reemplazar": [
                    {"de": "setas", "por": "patata"},    # reducir umami
                    {"de": "pescado", "por": "arroz"}    # neutro
                ]
            }),
            ("salado_a_dulce", "equilibrio_sabor", {
                "añadir": ["azucar"],
                "reducir": ["sal"]
            })
        ]
    }

    @staticmethod
    def verificar_restriccion(ingrediente: str, restriccion: str) -> bool:
        if restriccion in ConocimientoDominio.INCOMPATIBILIDADES:
            return ingrediente not in ConocimientoDominio.INCOMPATIBILIDADES[restriccion]
        return True

    @staticmethod
    def ingrediente_temporada(ingrediente: str, temporada: str) -> bool:
        return ingrediente in ConocimientoDominio.TEMPORADA.get(temporada, [])

    @staticmethod
    def obtener_sustituto(ingrediente: str, restriccion: str) -> Optional[str]:
        if ingrediente in ConocimientoDominio.SUSTITUTOS:
            sustitutos = ConocimientoDominio.SUSTITUTOS[ingrediente]
            for sustituto in sustitutos:
                if ConocimientoDominio.verificar_restriccion(sustituto, restriccion):
                    return sustituto
        return None

    @staticmethod
    def obtener_categoria_ingrediente(ingrediente: str) -> Optional[str]:
        """Encuentra la categoría de un ingrediente en la jerarquía"""
        for categoria_principal, subcategorias in ConocimientoDominio.JERARQUIA_INGREDIENTES.items():
            for subcategoria, ingredientes in subcategorias.items():
                if ingrediente in ingredientes:
                    return subcategoria
        return None

    @staticmethod
    def obtener_ingredientes_por_categoria(categoria: str) -> List[str]:
        """Obtiene todos los ingredientes de una categoría"""
        for cat_principal, subcategorias in ConocimientoDominio.JERARQUIA_INGREDIENTES.items():
            if categoria in subcategorias:
                return subcategorias[categoria]
        return []

    @staticmethod
    def obtener_sustituto_por_jerarquia(ingrediente: str, restricciones: List[str]) -> Optional[str]:
        """Busca sustituto usando la jerarquía de ingredientes"""
        categoria = ConocimientoDominio.obtener_categoria_ingrediente(ingrediente)
        if categoria:
            candidatos = ConocimientoDominio.obtener_ingredientes_por_categoria(categoria)
            for candidato in candidatos:
                if candidato != ingrediente:
                    # Verificar que el candidato cumple todas las restricciones
                    valido = all(
                        ConocimientoDominio.verificar_restriccion(candidato, rest)
                        for rest in restricciones
                    )
                    if valido:
                        return candidato
        return None

    @staticmethod
    def aplicar_regla_cambio_ingrediente(ingrediente: str, objetivo: str) -> Optional[str]:
        """Aplicar reglas declarativas para transformar un ingrediente hacia un objetivo.

        - ingrediente: nombre del ingrediente actual (p.ej. 'ternera' o 'carne')
        - objetivo: restricción o tipo objetivo (p.ej. 'vegetariano', 'vegano')

        Devuelve el nombre de un sustituto recomendado (p.ej. 'tofu') o None.
        La función consulta REGLAS_CAMBIO_INGREDIENTE primero; si no hay reglas, emplea SUSTITUTOS
        y la jerarquía existente.
        """
        # intentar por categoría (si 'ingrediente' es una categoría como 'carne')
        if ingrediente in ConocimientoDominio.REGLAS_CAMBIO_INGREDIENTE:
            reglas = ConocimientoDominio.REGLAS_CAMBIO_INGREDIENTE[ingrediente]
            opciones = reglas.get(objetivo, [])
            for accion in opciones:
                if accion.get("accion") == "reemplazar" and "por" in accion:
                    candidato = accion["por"]
                    # verificar que el candidato cumple la restricción objetivo
                    if ConocimientoDominio.verificar_restriccion(candidato, objetivo):
                        return candidato

        # si no hay regla por categoría, intentar ver si el ingrediente es de una subcategoría
        categoria = ConocimientoDominio.obtener_categoria_ingrediente(ingrediente)
        if categoria and categoria in ConocimientoDominio.REGLAS_CAMBIO_INGREDIENTE:
            reglas = ConocimientoDominio.REGLAS_CAMBIO_INGREDIENTE[categoria]
            opciones = reglas.get(objetivo, [])
            for accion in opciones:
                if accion.get("accion") == "reemplazar" and "por" in accion:
                    candidato = accion["por"]
                    if ConocimientoDominio.verificar_restriccion(candidato, objetivo):
                        return candidato

        # fallback: si hay sustitutos definidos para la palabra ingrediente
        if ingrediente in ConocimientoDominio.SUSTITUTOS:
            for s in ConocimientoDominio.SUSTITUTOS[ingrediente]:
                if ConocimientoDominio.verificar_restriccion(s, objetivo):
                    return s

        # fallback por jerarquía: buscar otro ingrediente de la misma categoría que cumpla objetivo
        if categoria:
            for cand in ConocimientoDominio.obtener_ingredientes_por_categoria(categoria):
                if cand != ingrediente and ConocimientoDominio.verificar_restriccion(cand, objetivo):
                    return cand

        return None

    @staticmethod
    def regla_eliminar_por_no_temporada(ingrediente: str, temporada: str) -> bool:
        """Devuelve True si, según conocimiento, el ingrediente está fuera de temporada y debería considerarse eliminarlo."""
        # Si no está en la temporada solicitada pero aparece en alguna temporada, marcar como fuera
        es_en_temporada = any(
            ingrediente in ings for ings in ConocimientoDominio.TEMPORADA.values()
        )
        if es_en_temporada and not ConocimientoDominio.ingrediente_temporada(ingrediente, temporada):
            return True
        return False

    @staticmethod
    def obtener_regla_textura(origen: str, destino: str):
        """Devuelve la acción sugerida para transformar textura origen→destino: dict con keys 'añadir' y 'tecnica' o None."""
        return ConocimientoDominio.REGLAS_CAMBIO_TEXTURA.get(origen, {}).get(destino)

    @staticmethod
    def obtener_reglas_por_problema(tipo_problema: str):
        """Obtiene las reglas específicas para un tipo de problema.
        
        Args:
            tipo_problema: 'restricciones', 'temporada', 'textura', 'sabor', 'coherencia'
        
        Returns:
            Lista de reglas aplicables al problema
        """
        reglas_por_problema = {
            'restricciones': ConocimientoDominio.REGLAS_RESTRICCIONES,
            'temporada': ConocimientoDominio.REGLAS_TEMPORADA,
            'textura': ConocimientoDominio.REGLAS_TEXTURA,
            'sabor': ConocimientoDominio.REGLAS_SABOR,
            'coherencia': ConocimientoDominio.REGLAS_COHERENCIA
        }
        return reglas_por_problema.get(tipo_problema, {})

    @staticmethod
    def aplicar_reglas_reparador(tipo_problema: str, subtipo: str = None):
        """Aplica reglas del reparador basadas en el tipo de problema detectado.
        
        Args:
            tipo_problema: 'RESTRICCION-VIOLADA', 'FUERA-TEMPORADA', 'DESBALANCE-TEXTURA', etc.
            subtipo: información adicional sobre el problema específico
            
        Returns:
            Lista de acciones de reparación sugeridas
        """
        acciones = []
        
        # Mapear tipos de fallo a categorías de reglas
        if "RESTRICCION-VIOLADA" in tipo_problema:
            if "vegetariano" in tipo_problema.lower():
                reglas = ConocimientoDominio.REGLAS_RESTRICCIONES.get("vegetariano", [])
            elif "vegano" in tipo_problema.lower():
                reglas = ConocimientoDominio.REGLAS_RESTRICCIONES.get("vegano", [])
            elif "sin_gluten" in tipo_problema.lower():
                reglas = ConocimientoDominio.REGLAS_RESTRICCIONES.get("sin_gluten", [])
            elif "halal" in tipo_problema.lower():
                reglas = ConocimientoDominio.REGLAS_RESTRICCIONES.get("halal", [])
            else:
                reglas = []
                
            for _, _, acciones_regla in reglas:
                acciones.append(acciones_regla)
                
        elif "FUERA-TEMPORADA" in tipo_problema:
            reglas = ConocimientoDominio.REGLAS_TEMPORADA.get("fuera_temporada", [])
            for _, _, acciones_regla in reglas:
                acciones.append(acciones_regla)
                
        elif "DESBALANCE-TEXTURA" in tipo_problema:
            reglas = ConocimientoDominio.REGLAS_TEXTURA.get("desbalance_textura", [])
            for _, _, acciones_regla in reglas:
                acciones.append(acciones_regla)
                
        elif "DESBALANCE-SABOR" in tipo_problema:
            reglas = ConocimientoDominio.REGLAS_SABOR.get("desbalance_sabor", [])
            for _, _, acciones_regla in reglas:
                acciones.append(acciones_regla)
                
        elif "INCOHERENCIA-ESTILO" in tipo_problema:
            reglas = ConocimientoDominio.REGLAS_COHERENCIA.get("estilo_tradicion", [])
            for _, _, acciones_regla in reglas:
                acciones.append(acciones_regla)
        
        return acciones
