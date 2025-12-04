class ConocimientoDominio:
    """Minimal domain knowledge for reparador tests.

    Contains exactly one rule per repair-path to trigger the modifier code paths.
    """

    # minimal hierarchy: categorize 'ternera' as 'carne', 'tofu' as 'vegetariano'
    JERARQUIA_INGREDIENTES = {
        "proteina": {
            "carne": ["ternera"],
            "vegetariano": ["tofu"]
        }
    }

    # incompatibilities minimal
    INCOMPATIBILIDADES = {
        "vegetariano": ["carne"],
        "vegano": ["carne", "pescado"]
    }

    # simple substitutes
    SUSTITUTOS = {
        "ternera": ["tofu"],
        "carne": ["tofu"],

    }

    # Exactly one rule per repair-path (minimal)
    REGLAS_REPARADOR = [
        # 1) textura: pasar de 'suave' a 'crujiente'
        ("suave", "crujiente", {
            "añadir": ["aceite_oliva"],
            "tecnica": "freir"
        }),

        # 2) categoría/cambio: 'carne' -> 'vegetariano'
        ("carne", "vegetariano", {
            "reemplazar": [{"de": "carne", "por": "tofu"}]
        }),

        # 3) pasar a vegano: eliminar lácteos/huevos y reemplazar carnes por tofu
        ("any", "vegano", {
            "eliminar": ["pescado"],
            "reemplazar": [{"de": "carne", "por": "tofu"}]
        })
    ]

    @staticmethod
    def verificar_restriccion(ingrediente: str, restriccion: str) -> bool:
        if restriccion in ConocimientoDominio.INCOMPATIBILIDADES:
            return ingrediente not in ConocimientoDominio.INCOMPATIBILIDADES[restriccion]
        return True

    @staticmethod
    def obtener_categoria_ingrediente(ingrediente: str):
        for cat_principal, subcats in ConocimientoDominio.JERARQUIA_INGREDIENTES.items():
            for subcat, ings in subcats.items():
                if ingrediente in ings:
                    return subcat
        return None

    @staticmethod
    def obtener_ingredientes_por_categoria(categoria: str):
        for cat_principal, subcats in ConocimientoDominio.JERARQUIA_INGREDIENTES.items():
            if categoria in subcats:
                return subcats[categoria]
        return []

    @staticmethod
    def obtener_sustituto(ingrediente: str, restriccion: str):
        if ingrediente in ConocimientoDominio.SUSTITUTOS:
            for s in ConocimientoDominio.SUSTITUTOS[ingrediente]:
                if ConocimientoDominio.verificar_restriccion(s, restriccion):
                    return s
        return None

    @staticmethod
    def obtener_sustituto_por_jerarquia(ingrediente: str, restricciones):
        cat = ConocimientoDominio.obtener_categoria_ingrediente(ingrediente)
        if not cat:
            return None
        for cand in ConocimientoDominio.obtener_ingredientes_por_categoria(cat):
            if cand != ingrediente and all(ConocimientoDominio.verificar_restriccion(cand, r) for r in restricciones):
                return cand
        return None
