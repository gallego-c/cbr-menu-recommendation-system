"""
Gestor de casos - Detecta y agrega casos nuevos a la base
"""

from typing import List, Dict, Any
from datetime import datetime
from conocimiento import Caso, Menu


class GestorCasos:
    """Gestiona la detección y agregación de casos nuevos"""
    
    def __init__(self, casos: List[Dict], casos_dict: Dict[str, Dict]):
        self.casos = casos
        self.casos_dict = casos_dict
    
    def _generar_id(self) -> str:
        """
        Genera un ID único para un nuevo caso.
        
        Returns:
            ID en formato C### (ej: C001, C042)
        """
        # Obtener el número máximo de los IDs existentes
        numeros = [int(cid[1:]) for cid in self.casos_dict.keys() 
                   if cid.startswith('C') and cid[1:].isdigit()]
        max_num = max(numeros, default=0)
        return f"C{max_num + 1:03d}"
    
    def agregar(self, caso: Caso) -> tuple[str, bool]:
        """
        Agrega un nuevo caso a la base solo si no existe uno igual.
        
        Args:
            caso: Objeto Caso a agregar (puede tener id vacío, se generará)
            
        Returns:
            tuple: (caso_id, fue_agregado) donde fue_agregado es True si se agregó el caso
        """
        # Verificar si ya existe un caso duplicado
        caso_existente_id = self._buscar_duplicado(caso)
        if caso_existente_id:
            print(f"\nCaso duplicado encontrado: {caso_existente_id} - No se agrega")
            return caso_existente_id, False
        
        # Generar ID si no tiene
        if not caso.id:
            caso.id = self._generar_id()
        
        # Agregar timestamp si no tiene
        if not caso.timestamp:
            caso.timestamp = datetime.now().isoformat()
        
        print(f"\nAGREGANDO NUEVO CASO: {caso.id}")
        
        # Convertir a dict para almacenar
        caso_dict = caso.to_dict()
        self.casos.append(caso_dict)
        self.casos_dict[caso.id] = caso_dict
        
        print(f"Caso {caso.id} agregado exitosamente")
        return caso.id, True
    
    def _buscar_duplicado(self, caso: Caso) -> str:
        """
        Busca si ya existe un caso con el mismo menú y características.
        
        Args:
            caso: Caso a buscar
            
        Returns:
            ID del caso duplicado o None si no existe
        """
        menu_dict = caso.menu.to_dict()
        
        for caso_existente in self.casos:
            if (caso_existente['menu'] == menu_dict and 
                caso_existente.get('tipo_evento') == caso.tipo_evento and
                caso_existente.get('temporada') == caso.temporada and
                caso_existente.get('tradicion') == caso.tradicion and
                caso_existente.get('estilo') == caso.estilo and
                caso_existente.get('restricciones') == caso.restricciones):
                return caso_existente['id']
        
        return None
