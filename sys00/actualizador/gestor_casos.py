"""
Gestor de casos - Detecta y agrega casos nuevos a la base
Integrado con sistema de retención para curación de memoria.
"""

from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from conocimiento import Caso, Menu

from .config_retencion import ConfiguracionRetencion, CONFIG_RETENCION_DEFAULT
from .gestor_retencion import GestorRetencion
from .recolector_satisfaccion import SatisfaccionCaso


class GestorCasos:
    """
    Gestiona la detección, agregación y retención de casos.
    
    Integra el sistema de curación de memoria para:
    - Mantener límite de casos (MAX_CASES)
    - Priorizar casos con alta satisfacción
    - Favorecer casos difíciles (muchas modificaciones)
    - Mantener diversidad en la base de casos
    """
    
    def __init__(self, casos: List[Dict], casos_dict: Dict[str, Dict],
                 config_retencion: ConfiguracionRetencion = None):
        """
        Inicializa el gestor de casos.
        
        Args:
            casos: Lista de casos (referencia a la lista principal)
            casos_dict: Diccionario de casos por ID
            config_retencion: Configuración del sistema de retención
        """
        self.casos = casos
        self.casos_dict = casos_dict
        self.config_retencion = config_retencion or CONFIG_RETENCION_DEFAULT
        self.gestor_retencion = GestorRetencion(self.config_retencion)
    
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
    
    def agregar(self, caso: Caso, satisfaccion: SatisfaccionCaso = None) -> Tuple[str, bool]:
        """
        Agrega un nuevo caso a la base con curación de memoria.
        
        El proceso:
        1. Verifica duplicados
        2. Enriquece el caso con satisfacción y modification_count
        3. Aplica curación de memoria si se excede el límite
        4. Agrega el caso si corresponde
        
        Args:
            caso: Objeto Caso a agregar (puede tener id vacío, se generará)
            satisfaccion: Información de satisfacción del usuario (opcional)
            
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
        
        # Enriquecer con satisfacción
        if satisfaccion:
            caso.satisfaccion = satisfaccion.to_dict()
        
        # Calcular modification_count si no está
        if caso.modification_count is None:
            caso.modification_count = self._contar_modificaciones(caso)
        
        # Convertir a dict para almacenar
        caso_dict = caso.to_dict()
        
        # Aplicar curación de memoria
        casos_retenidos, ids_eliminados = self.gestor_retencion.curar_memoria(
            self.casos, caso_dict
        )
        
        # Actualizar la lista de casos
        if ids_eliminados:
            self._eliminar_casos(ids_eliminados)
        
        # Verificar si el caso nuevo está en los retenidos
        caso_fue_retenido = any(c.get('id') == caso.id for c in casos_retenidos)
        
        if caso_fue_retenido:
            print(f"\nAGREGANDO NUEVO CASO: {caso.id}")
            self.casos.append(caso_dict)
            self.casos_dict[caso.id] = caso_dict
            print(f"Caso {caso.id} agregado exitosamente")
            
            # Mostrar métricas de retención
            metricas = self.gestor_retencion.calcular_metricas(caso_dict, 
                [c for c in self.casos if c.get('id') != caso.id])
            print(f"  - Keep score: {metricas.keep_score:.3f}")
            print(f"  - Satisfacción (norm): {metricas.satisfaction_score:.2f}")
            print(f"  - Bonus modificaciones: {metricas.modification_bonus:.2f}")
            print(f"  - Novedad: {metricas.novelty:.2f}")
            
            return caso.id, True
        else:
            print(f"\n⚠️ Caso {caso.id} no retenido (baja puntuación de retención)")
            return caso.id, False
    
    def agregar_simple(self, caso: Caso) -> Tuple[str, bool]:
        """
        Agrega un caso sin sistema de retención (comportamiento original).
        
        Mantiene compatibilidad con código que no usa el sistema de retención.
        
        Args:
            caso: Objeto Caso a agregar
            
        Returns:
            tuple: (caso_id, fue_agregado)
        """
        # Verificar duplicado
        caso_existente_id = self._buscar_duplicado(caso)
        if caso_existente_id:
            print(f"\nCaso duplicado encontrado: {caso_existente_id} - No se agrega")
            return caso_existente_id, False
        
        # Generar ID si no tiene
        if not caso.id:
            caso.id = self._generar_id()
        
        # Agregar timestamp
        if not caso.timestamp:
            caso.timestamp = datetime.now().isoformat()
        
        print(f"\nAGREGANDO NUEVO CASO: {caso.id}")
        
        caso_dict = caso.to_dict()
        self.casos.append(caso_dict)
        self.casos_dict[caso.id] = caso_dict
        
        print(f"Caso {caso.id} agregado exitosamente")
        return caso.id, True
    
    def _buscar_duplicado(self, caso: Caso) -> Optional[str]:
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
    
    def _contar_modificaciones(self, caso: Caso) -> int:
        """
        Cuenta el número de modificaciones aplicadas a un caso.
        
        Args:
            caso: Caso a analizar
            
        Returns:
            Número total de modificaciones
        """
        reparaciones = caso.reparaciones_aplicadas or []
        
        if not reparaciones:
            return 0
        
        total = 0
        for rep in reparaciones:
            if isinstance(rep, dict):
                mods = rep.get('modificaciones', [])
                total += len(mods) if mods else 1
            else:
                total += 1
        
        return total
    
    def _eliminar_casos(self, ids: List[str]):
        """
        Elimina casos por sus IDs.
        
        Args:
            ids: Lista de IDs de casos a eliminar
        """
        for caso_id in ids:
            # Eliminar del diccionario
            if caso_id in self.casos_dict:
                del self.casos_dict[caso_id]
            
            # Eliminar de la lista
            self.casos[:] = [c for c in self.casos if c.get('id') != caso_id]
    
    def obtener_resumen_memoria(self) -> Dict[str, Any]:
        """
        Obtiene un resumen del estado de la memoria de casos.
        
        Returns:
            Diccionario con estadísticas de la memoria
        """
        return self.gestor_retencion.resumen_memoria(self.casos)
    
    def forzar_curacion(self) -> Tuple[int, List[str]]:
        """
        Fuerza una curación de memoria inmediata.
        
        Returns:
            Tuple de (casos_actuales, ids_eliminados)
        """
        casos_retenidos, ids_eliminados = self.gestor_retencion.curar_memoria(self.casos)
        
        if ids_eliminados:
            self._eliminar_casos(ids_eliminados)
        
        return len(self.casos), ids_eliminados
