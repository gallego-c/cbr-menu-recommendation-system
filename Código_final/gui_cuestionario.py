"""
Sistema CBR - Interfaz Gráfica para Generación de Menús
=======================================================

GUI con tkinter para el cuestionario de preferencias del usuario.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import json
from datetime import datetime

# Importar el sistema CBR
from sistema_cbr import SistemaCBR, PreferenciasUsuario


class CBRApp:
    """Aplicación gráfica para el Sistema CBR de Menús."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🍽️ Sistema CBR - Generador de Menús")
        self.root.geometry("900x750")
        self.root.resizable(True, True)
        
        # Configurar estilo
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Colores
        self.colors = {
            'bg': '#f5f5f5',
            'primary': '#2196F3',
            'secondary': '#4CAF50',
            'accent': '#FF9800',
            'text': '#333333',
            'light': '#ffffff'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Variables
        self.tipo_evento_var = tk.StringVar(value='familiar')
        self.temporada_var = tk.StringVar(value='')
        self.estilo_var = tk.StringVar(value='clasico')
        self.tradicion_var = tk.StringVar(value='')
        self.restricciones_vars = {}
        
        # Rating variables (individuales, el general se calcula como media)
        self.rating_entrante_var = tk.DoubleVar(value=4.0)
        self.rating_principal_var = tk.DoubleVar(value=4.0)
        self.rating_postre_var = tk.DoubleVar(value=4.0)
        
        # Estado
        self.sistema = None
        self.ultimo_resultado = None
        self.ultimo_caso_id = None
        
        # Crear interfaz
        self._crear_interfaz()
        
        # Inicializar sistema en segundo plano
        self._inicializar_sistema()
    
    def _crear_interfaz(self):
        """Crea todos los elementos de la interfaz."""
        # Frame principal con scroll
        main_canvas = tk.Canvas(self.root, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        self.main_frame = ttk.Frame(main_canvas)
        
        self.main_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=self.main_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind mousewheel
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        scrollbar.pack(side="right", fill="y")
        main_canvas.pack(side="left", fill="both", expand=True)
        
        # Título
        self._crear_titulo()
        
        # Secciones del cuestionario
        self._crear_seccion_tipo_evento()
        self._crear_seccion_temporada()
        self._crear_seccion_restricciones()
        self._crear_seccion_estilo()
        self._crear_seccion_tradicion()
        
        # Botón generar
        self._crear_boton_generar()
        
        # Área de resultados
        self._crear_area_resultados()
        
        # Sección de rating
        self._crear_seccion_rating()
        
        # Barra de estado
        self._crear_barra_estado()
    
    def _crear_titulo(self):
        """Crea el título de la aplicación."""
        titulo_frame = tk.Frame(self.main_frame, bg=self.colors['primary'], pady=15)
        titulo_frame.pack(fill='x', padx=10, pady=(10, 5))
        
        titulo = tk.Label(
            titulo_frame,
            text="🍽️ Sistema de Generación de Menús",
            font=('Helvetica', 18, 'bold'),
            fg='white',
            bg=self.colors['primary']
        )
        titulo.pack()
        
        subtitulo = tk.Label(
            titulo_frame,
            text="Basado en Razonamiento Basado en Casos (CBR)",
            font=('Helvetica', 10),
            fg='#e3f2fd',
            bg=self.colors['primary']
        )
        subtitulo.pack()
    
    def _crear_seccion_tipo_evento(self):
        """Crea la sección de tipo de evento."""
        frame = self._crear_seccion_frame("1. Tipo de Evento")
        
        opciones = [
            ('Familiar', 'familiar'),
            ('Boda', 'boda'),
            ('Congreso', 'congreso')
        ]
        
        for texto, valor in opciones:
            rb = ttk.Radiobutton(
                frame,
                text=texto,
                variable=self.tipo_evento_var,
                value=valor
            )
            rb.pack(anchor='w', padx=20, pady=2)
    
    def _crear_seccion_temporada(self):
        """Crea la sección de temporada."""
        frame = self._crear_seccion_frame("2. Temporada")
        
        opciones = [
            ('🌸 Primavera', 'primavera'),
            ('☀️ Verano', 'verano'),
            ('🍂 Otoño', 'otoño'),
            ('❄️ Invierno', 'invierno'),
            ('Sin preferencia', '')
        ]
        
        for texto, valor in opciones:
            rb = ttk.Radiobutton(
                frame,
                text=texto,
                variable=self.temporada_var,
                value=valor
            )
            rb.pack(anchor='w', padx=20, pady=2)
    
    def _crear_seccion_restricciones(self):
        """Crea la sección de restricciones dietéticas."""
        frame = self._crear_seccion_frame("3. Restricciones Dietéticas (selecciona las que apliquen)")
        
        restricciones = [
            ('🥬 Vegetariano', 'vegetariano'),
            ('🌱 Vegano', 'vegano'),
            ('🌾 Sin Gluten', 'sin_gluten'),
            ('🥛 Sin Lactosa', 'sin_lactosa'),
            ('🥚 Sin Huevo', 'sin_huevo')
        ]
        
        for texto, valor in restricciones:
            var = tk.BooleanVar(value=False)
            self.restricciones_vars[valor] = var
            
            cb = ttk.Checkbutton(
                frame,
                text=texto,
                variable=var
            )
            cb.pack(anchor='w', padx=20, pady=2)
    
    def _crear_seccion_estilo(self):
        """Crea la sección de estilo culinario."""
        frame = self._crear_seccion_frame("4. Estilo Culinario")
        
        opciones = [
            ('👨‍🍳 Clásico', 'clasico'),
            ('🔬 Molecular', 'molecular')
        ]
        
        for texto, valor in opciones:
            rb = ttk.Radiobutton(
                frame,
                text=texto,
                variable=self.estilo_var,
                value=valor
            )
            rb.pack(anchor='w', padx=20, pady=2)
    
    def _crear_seccion_tradicion(self):
        """Crea la sección de tradición cultural."""
        frame = self._crear_seccion_frame("5. Tradición Cultural")
        
        opciones = [
            ('🇪🇸 Catalana', 'catalana'),
            ('🇲🇽 Mexicana', 'mexicana'),
            ('🇮🇹 Italiana', 'italiana'),
            ('🇮🇳 India', 'india'),
            ('🇫🇷 Francesa', 'francesa'),
            ('🇨🇳 China', 'china'),
            ('Sin preferencia', '')
        ]
        
        # Usar grid para 2 columnas
        inner_frame = ttk.Frame(frame)
        inner_frame.pack(fill='x', padx=20)
        
        for i, (texto, valor) in enumerate(opciones):
            rb = ttk.Radiobutton(
                inner_frame,
                text=texto,
                variable=self.tradicion_var,
                value=valor
            )
            rb.grid(row=i//2, column=i%2, sticky='w', padx=10, pady=2)
    
    def _crear_seccion_frame(self, titulo):
        """Crea un frame de sección con título."""
        container = tk.Frame(self.main_frame, bg=self.colors['bg'])
        container.pack(fill='x', padx=10, pady=5)
        
        # Título de sección
        label = tk.Label(
            container,
            text=titulo,
            font=('Helvetica', 11, 'bold'),
            fg=self.colors['text'],
            bg=self.colors['bg'],
            anchor='w'
        )
        label.pack(fill='x', pady=(5, 2))
        
        # Frame interior
        frame = ttk.LabelFrame(container, padding=10)
        frame.pack(fill='x')
        
        return frame
    
    def _crear_boton_generar(self):
        """Crea el botón de generar menú."""
        btn_frame = tk.Frame(self.main_frame, bg=self.colors['bg'])
        btn_frame.pack(fill='x', padx=10, pady=15)
        
        self.btn_generar = tk.Button(
            btn_frame,
            text="🍳 GENERAR MENÚ",
            font=('Helvetica', 14, 'bold'),
            fg='white',
            bg=self.colors['secondary'],
            activebackground='#388E3C',
            activeforeground='white',
            relief='flat',
            padx=30,
            pady=10,
            cursor='hand2',
            command=self._generar_menu
        )
        self.btn_generar.pack(expand=True)
        
        # Efecto hover
        self.btn_generar.bind('<Enter>', lambda e: self.btn_generar.config(bg='#388E3C'))
        self.btn_generar.bind('<Leave>', lambda e: self.btn_generar.config(bg=self.colors['secondary']))
    
    def _crear_area_resultados(self):
        """Crea el área de resultados."""
        self.resultado_frame = tk.Frame(self.main_frame, bg=self.colors['bg'])
        self.resultado_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Título
        titulo = tk.Label(
            self.resultado_frame,
            text="📋 Resultado",
            font=('Helvetica', 11, 'bold'),
            fg=self.colors['text'],
            bg=self.colors['bg'],
            anchor='w'
        )
        titulo.pack(fill='x', pady=(5, 2))
        
        # Frame del menú
        self.menu_frame = ttk.LabelFrame(self.resultado_frame, text="Menú Generado", padding=15)
        self.menu_frame.pack(fill='both', expand=True)
        
        # Labels para el menú
        self.lbl_entrante = tk.Label(
            self.menu_frame,
            text="🥗 Entrante: -",
            font=('Helvetica', 11),
            fg=self.colors['text'],
            anchor='w',
            wraplength=500,
            justify='left'
        )
        self.lbl_entrante.pack(fill='x', pady=5)
        
        self.lbl_principal = tk.Label(
            self.menu_frame,
            text="🍝 Principal: -",
            font=('Helvetica', 11),
            fg=self.colors['text'],
            anchor='w',
            wraplength=500,
            justify='left'
        )
        self.lbl_principal.pack(fill='x', pady=5)
        
        self.lbl_postre = tk.Label(
            self.menu_frame,
            text="🍰 Postre: -",
            font=('Helvetica', 11),
            fg=self.colors['text'],
            anchor='w',
            wraplength=500,
            justify='left'
        )
        self.lbl_postre.pack(fill='x', pady=5)
        
        # Información adicional
        self.lbl_info = tk.Label(
            self.menu_frame,
            text="",
            font=('Helvetica', 9),
            fg='#666666',
            anchor='w'
        )
        self.lbl_info.pack(fill='x', pady=(10, 0))
        
        # Área de detalles (expandible)
        self.detalles_frame = ttk.LabelFrame(self.resultado_frame, text="Detalles del Proceso", padding=10)
        self.detalles_frame.pack(fill='both', expand=True, pady=(10, 0))
        
        self.txt_detalles = scrolledtext.ScrolledText(
            self.detalles_frame,
            height=6,
            font=('Consolas', 9),
            wrap=tk.WORD
        )
        self.txt_detalles.pack(fill='both', expand=True)
    
    def _crear_seccion_rating(self):
        """Crea la sección de rating."""
        self.rating_frame = tk.Frame(self.main_frame, bg=self.colors['bg'])
        self.rating_frame.pack(fill='x', padx=10, pady=10)
        
        # Título
        titulo = tk.Label(
            self.rating_frame,
            text="⭐ Calificar Menú",
            font=('Helvetica', 11, 'bold'),
            fg=self.colors['text'],
            bg=self.colors['bg'],
            anchor='w'
        )
        titulo.pack(fill='x', pady=(5, 2))
        
        # Frame de ratings
        ratings_container = ttk.LabelFrame(self.rating_frame, text="Tu Valoración", padding=15)
        ratings_container.pack(fill='x')
        
        # Nota explicativa
        ttk.Label(ratings_container, text="Califica cada plato (el rating general se calcula automáticamente):", 
                  font=('Helvetica', 9)).pack(anchor='w', pady=(0, 10))
        
        for nombre, var, emoji in [
            ('Entrante', self.rating_entrante_var, '🥗'),
            ('Principal', self.rating_principal_var, '🍝'),
            ('Postre', self.rating_postre_var, '🍰')
        ]:
            frame = ttk.Frame(ratings_container)
            frame.pack(fill='x', pady=2)
            ttk.Label(frame, text=f"  {emoji} {nombre}:").pack(side='left')
            scale = ttk.Scale(frame, from_=1, to=5, variable=var, orient='horizontal', length=150)
            scale.pack(side='left', padx=10)
            lbl = ttk.Label(frame, text="4.0")
            lbl.pack(side='left')
            var.trace('w', lambda *args, l=lbl, v=var: l.config(text=f"{v.get():.1f}"))
        
        # Botón guardar rating
        self.btn_guardar_rating = tk.Button(
            ratings_container,
            text="💾 Guardar Calificación",
            font=('Helvetica', 10, 'bold'),
            fg='white',
            bg=self.colors['accent'],
            activebackground='#F57C00',
            activeforeground='white',
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2',
            command=self._guardar_rating,
            state='disabled'
        )
        self.btn_guardar_rating.pack(pady=(15, 5))
    
    def _crear_barra_estado(self):
        """Crea la barra de estado inferior."""
        self.status_bar = tk.Label(
            self.root,
            text="🔄 Inicializando sistema...",
            font=('Helvetica', 9),
            fg='#666666',
            bg='#e0e0e0',
            anchor='w',
            padx=10,
            pady=5
        )
        self.status_bar.pack(side='bottom', fill='x')
    
    def _inicializar_sistema(self):
        """Inicializa el sistema CBR en segundo plano."""
        def init():
            try:
                self.sistema = SistemaCBR()
                self.root.after(0, lambda: self._actualizar_estado("✅ Sistema listo. Selecciona tus preferencias."))
            except Exception as e:
                self.root.after(0, lambda: self._actualizar_estado(f"❌ Error: {str(e)}"))
        
        thread = threading.Thread(target=init, daemon=True)
        thread.start()
    
    def _actualizar_estado(self, mensaje):
        """Actualiza la barra de estado."""
        self.status_bar.config(text=mensaje)
    
    def _generar_menu(self):
        """Genera el menú basado en las preferencias."""
        if not self.sistema:
            messagebox.showerror("Error", "El sistema aún no está inicializado. Espera un momento.")
            return
        
        # Deshabilitar botón
        self.btn_generar.config(state='disabled', text='⏳ Generando...')
        self._actualizar_estado("🔄 Generando menú...")
        
        def generar():
            try:
                # Recoger restricciones seleccionadas
                restricciones = [k for k, v in self.restricciones_vars.items() if v.get()]
                
                # Crear preferencias
                preferencias = PreferenciasUsuario(
                    tipo_evento=self.tipo_evento_var.get(),
                    temporada=self.temporada_var.get() if self.temporada_var.get() else None,
                    restricciones=restricciones,
                    estilo=self.estilo_var.get(),
                    tradicion=self.tradicion_var.get() if self.tradicion_var.get() else None
                )
                
                # Ejecutar ciclo CBR (sin pedir rating por consola)
                resultado = self.sistema.generar_menu(preferencias, collect_rating=False)
                
                # Actualizar UI en el hilo principal
                self.root.after(0, lambda r=resultado: self._mostrar_resultado(r))
                
            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda msg=error_msg: self._mostrar_error(msg))
        
        thread = threading.Thread(target=generar, daemon=True)
        thread.start()
    
    def _mostrar_resultado(self, resultado):
        """Muestra el resultado en la interfaz."""
        self.ultimo_resultado = resultado
        
        # DEBUG: Ver qué recibimos
        print(f"DEBUG _mostrar_resultado:")
        print(f"  tipo resultado: {type(resultado)}")
        print(f"  exito: {resultado.exito}")
        print(f"  menu: {resultado.menu}")
        print(f"  tipo menu: {type(resultado.menu)}")
        
        # ResultadoCBR es un dataclass, acceder con atributos
        if resultado.exito and resultado.menu:
            menu = resultado.menu
            
            # menu puede ser un objeto Menu (dataclass) o un dict
            if hasattr(menu, 'entrante'):
                # Es un objeto Menu
                entrante = menu.entrante
                principal = menu.principal
                postre = menu.postre
            else:
                # Es un diccionario
                entrante = menu.get('entrante', 'N/A')
                principal = menu.get('principal', 'N/A')
                postre = menu.get('postre', 'N/A')
            
            # Actualizar labels del menú
            self.lbl_entrante.config(text=f"🥗 Entrante: {entrante}")
            self.lbl_principal.config(text=f"🍝 Principal: {principal}")
            self.lbl_postre.config(text=f"🍰 Postre: {postre}")
            
            # Información adicional
            similitud = resultado.similitud_caso_base
            reparaciones = len(resultado.reparaciones_aplicadas)
            
            self.ultimo_caso_id = resultado.nuevo_caso_id or resultado.caso_base_id
            
            info_text = f"📊 Similitud: {similitud:.1%} | 🔧 Reparaciones: {reparaciones}"
            if self.ultimo_caso_id:
                info_text += f" | 🆔 Caso: {self.ultimo_caso_id}"
            self.lbl_info.config(text=info_text)
            
            # Detalles
            detalles = self._formatear_detalles(resultado)
            self.txt_detalles.delete('1.0', tk.END)
            self.txt_detalles.insert('1.0', detalles)
            
            # Habilitar rating
            self.btn_guardar_rating.config(state='normal')
            
            self._actualizar_estado(f"✅ Menú generado exitosamente. Caso: {self.ultimo_caso_id or 'N/A'}")
        else:
            self.lbl_entrante.config(text="🥗 Entrante: Error al generar")
            self.lbl_principal.config(text="🍝 Principal: -")
            self.lbl_postre.config(text="🍰 Postre: -")
            self.lbl_info.config(text="")
            
            errores = resultado.fallos_encontrados if resultado.fallos_encontrados else [resultado.mensaje or 'Error desconocido']
            self.txt_detalles.delete('1.0', tk.END)
            self.txt_detalles.insert('1.0', "ERRORES:\n" + "\n".join(errores))
            
            self.btn_guardar_rating.config(state='disabled')
            self._actualizar_estado("❌ No se pudo generar el menú")
        
        # Rehabilitar botón
        self.btn_generar.config(state='normal', text='🍳 GENERAR MENÚ')
    
    def _formatear_detalles(self, resultado):
        """Formatea los detalles del resultado."""
        lineas = []
        
        # Caso base
        if resultado.caso_base_id:
            lineas.append(f"CASO BASE: {resultado.caso_base_id}")
            lineas.append(f"  Similitud: {resultado.similitud_caso_base:.1%}")
            lineas.append("")
        
        # Reparaciones
        reparaciones = resultado.reparaciones_aplicadas
        if reparaciones:
            lineas.append(f"REPARACIONES APLICADAS ({len(reparaciones)}):")
            for i, rep in enumerate(reparaciones, 1):
                if isinstance(rep, dict):
                    tipo = rep.get('tipo_plato', 'N/A')
                    original = rep.get('plato_original', 'N/A')
                    nuevo = rep.get('plato_nuevo', 'N/A')
                    lineas.append(f"  {i}. {tipo.upper()}")
                    if original != nuevo:
                        lineas.append(f"     Original: {original}")
                        lineas.append(f"     Nuevo: {nuevo}")
                    else:
                        lineas.append(f"     Modificado: {nuevo}")
                else:
                    lineas.append(f"  {i}. {rep}")
            lineas.append("")
        
        # Fallos encontrados
        if resultado.fallos_encontrados:
            lineas.append(f"FALLOS ENCONTRADOS:")
            for fallo in resultado.fallos_encontrados[:5]:
                lineas.append(f"  - {fallo}")
            lineas.append("")
        
        # Mensaje
        if resultado.mensaje:
            lineas.append(f"MENSAJE: {resultado.mensaje}")
        
        # Nuevo caso
        if resultado.nuevo_caso_id:
            lineas.append(f"\n✅ NUEVO CASO CREADO: {resultado.nuevo_caso_id}")
        
        return "\n".join(lineas) if lineas else "Sin detalles adicionales"
    
    def _mostrar_error(self, mensaje):
        """Muestra un error."""
        messagebox.showerror("Error", f"Error al generar menú:\n{mensaje}")
        self.btn_generar.config(state='normal', text='🍳 GENERAR MENÚ')
        self._actualizar_estado(f"❌ Error: {mensaje}")
    
    def _guardar_rating(self):
        """Guarda el rating del menú."""
        if not self.ultimo_caso_id or not self.ultimo_resultado:
            messagebox.showwarning("Aviso", "No hay menú para calificar. Genera uno primero.")
            return
        
        try:
            per_menu_scores = {
                'entrante': self.rating_entrante_var.get(),
                'principal': self.rating_principal_var.get(),
                'postre': self.rating_postre_var.get()
            }
            # Calcular rating general como media de los tres
            rating_general = (per_menu_scores['entrante'] + 
                            per_menu_scores['principal'] + 
                            per_menu_scores['postre']) / 3.0
            timestamp = datetime.now().isoformat()
            
            # Guardar usando el sistema
            self.sistema._actualizar_rating_caso(
                self.ultimo_caso_id,
                rating_general,
                per_menu_scores,
                timestamp
            )
            
            messagebox.showinfo(
                "Rating Guardado",
                f"✅ Rating guardado exitosamente!\n\n"
                f"Caso: {self.ultimo_caso_id}\n"
                f"Entrante: {per_menu_scores['entrante']:.1f}\n"
                f"Principal: {per_menu_scores['principal']:.1f}\n"
                f"Postre: {per_menu_scores['postre']:.1f}\n"
                f"\nRating General (media): {rating_general:.2f}/5.0"
            )
            
            self._actualizar_estado(f"⭐ Rating guardado: {rating_general:.2f}/5.0")
            self.btn_guardar_rating.config(state='disabled')
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar rating:\n{str(e)}")


def main():
    """Función principal."""
    root = tk.Tk()
    
    # Configurar icono si existe
    try:
        root.iconbitmap('icon.ico')
    except:
        pass
    
    # Centrar ventana
    root.update_idletasks()
    width = 900
    height = 750
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    app = CBRApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
