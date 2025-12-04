"""
Gestor de persistencia - Maneja carga, guardado y backups de archivos JSON
"""

import json
import os
import shutil
from typing import List, Dict, Any
from datetime import datetime


class GestorPersistencia:
    """Gestiona la persistencia de las bases de conocimiento en archivos JSON"""
    
    def __init__(self, directorio_conocimiento: str):
        self.dir_conocimiento = directorio_conocimiento
    
    def cargar_json(self, nombre_archivo: str) -> Any:
        """
        Carga un archivo JSON desde el directorio de conocimiento.
        
        Args:
            nombre_archivo: Nombre del archivo (ej: 'ingredientes.json')
            
        Returns:
            Contenido del archivo JSON (lista o diccionario)
        """
        ruta = os.path.join(self.dir_conocimiento, nombre_archivo)
        default = {} if nombre_archivo == 'reparaciones.json' else []
        
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Advertencia: {nombre_archivo} - {type(e).__name__}")
            return default
    
    def guardar_json(self, nombre_archivo: str, datos: Any) -> bool:
        """
        Guarda datos en un archivo JSON.
        
        Args:
            nombre_archivo: Nombre del archivo (ej: 'ingredientes.json')
            datos: Datos a guardar (lista o diccionario)
            
        Returns:
            True si se guardó exitosamente, False en caso de error
        """
        ruta = os.path.join(self.dir_conocimiento, nombre_archivo)
        try:
            with open(ruta, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error guardando {nombre_archivo}: {e}")
            return False
    
    def guardar_todas_las_bases(self, ingredientes: List[Dict], platos: List[Dict],
                                casos: List[Dict], reparaciones: Dict) -> bool:
        """
        Guarda todas las bases de conocimiento.
        
        Args:
            ingredientes: Lista de ingredientes
            platos: Lista de platos
            casos: Lista de casos
            reparaciones: Diccionario de reparaciones
            
        Returns:
            True si todas se guardaron exitosamente
        """
        print(f"\nGUARDANDO BASES DE CONOCIMIENTO")
        
        bases = [
            ('ingredientes.json', ingredientes),
            ('platos.json', platos),
            ('casos.json', casos),
            ('reparaciones.json', reparaciones)
        ]
        
        try:
            for nombre, datos in bases:
                self.guardar_json(nombre, datos)
            print(f"Todas las bases guardadas exitosamente")
            return True
        except Exception as e:
            print(f"Error guardando bases: {e}")
            return False
    
    def crear_backup(self) -> str:
        """
        Crea un backup de todas las bases de conocimiento.
        
        Returns:
            Ruta del backup creado
        """
        backup_path = os.path.join(self.dir_conocimiento, 'backup', 
                                   datetime.now().strftime("%Y%m%d_%H%M%S"))
        os.makedirs(backup_path, exist_ok=True)
        
        archivos = ['ingredientes.json', 'platos.json', 'casos.json', 'reparaciones.json']
        for archivo in archivos:
            src = os.path.join(self.dir_conocimiento, archivo)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(backup_path, archivo))
        
        print(f"Backup creado: {backup_path}")
        return backup_path
    
    def restaurar_backup(self, backup_path: str = None) -> bool:
        """
        Restaura desde un backup específico o el más reciente.
        
        Args:
            backup_path: Ruta del backup a restaurar (opcional)
            
        Returns:
            True si se restauró exitosamente
        """
        backup_dir = os.path.join(self.dir_conocimiento, 'backup')
        
        if not backup_path:
            backups = self.listar_backups()
            if not backups:
                print("No hay backups disponibles")
                return False
            backup_path = os.path.join(backup_dir, backups[0])  # El más reciente (lista ordenada)
        
        # Restaurar archivos
        archivos = ['ingredientes.json', 'platos.json', 'casos.json', 'reparaciones.json']
        for archivo in archivos:
            src = os.path.join(backup_path, archivo)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(self.dir_conocimiento, archivo))
        
        print(f"Restaurado desde: {backup_path}")
        return True
    
    def listar_backups(self) -> List[str]:
        """
        Lista todos los backups disponibles.
        
        Returns:
            Lista de nombres de backups (timestamps)
        """
        backup_dir = os.path.join(self.dir_conocimiento, 'backup')
        
        if not os.path.exists(backup_dir):
            return []
        
        backups = [d for d in os.listdir(backup_dir) 
                  if os.path.isdir(os.path.join(backup_dir, d))]
        return sorted(backups, reverse=True)
    
    def eliminar_backups_antiguos(self, mantener: int = 5) -> int:
        """
        Elimina backups antiguos, manteniendo solo los más recientes.
        
        Args:
            mantener: Número de backups a mantener (default: 5)
            
        Returns:
            Número de backups eliminados
        """
        backups = self.listar_backups()
        
        if len(backups) <= mantener:
            return 0
        
        backups_a_eliminar = backups[mantener:]
        eliminados = 0
        
        backup_dir = os.path.join(self.dir_conocimiento, 'backup')
        for backup in backups_a_eliminar:
            backup_path = os.path.join(backup_dir, backup)
            try:
                shutil.rmtree(backup_path)
                eliminados += 1
            except Exception as e:
                print(f"Error eliminando backup {backup}: {e}")
        
        return eliminados
