# Case-Based Reasoning (CBR) Menu Recommendation System

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-Complete-brightgreen.svg)]()
[![Topic](https://img.shields.io/badge/Topic-Artificial_Intelligence-orange.svg)]()
[![Paradigm](https://img.shields.io/badge/Paradigm-Case--Based_Reasoning-purple.svg)]()

A full implementation of a **Case-Based Reasoning (CBR)** system for automatic restaurant menu generation, designed for event catering contexts. The system follows the classical **4R CBR cycle** — Retrieve, Reuse, Revise, Retain — to propose personalized menus based on user dietary preferences, event type, season, and culinary style.

---

## 📌 Project Overview

The system acts as an intelligent menu generator. Given a set of user preferences (event type, season, dietary restrictions, culinary style, cultural tradition), the CBR engine retrieves the most similar historical case from its knowledge base, adapts the menu to the current requirements, validates the proposal, and optionally retains the experience as a new case for future use.

### Key CBR Phases

| Phase | Module | Description |
| :--- | :--- | :--- |
| **Retrieve** | `recuperador/` | Finds the most similar past case using feature similarity metrics. |
| **Reuse** | `sistema_cbr.py` | Adapts the retrieved solution to current user preferences. |
| **Revise** | `validador/` | Validates the proposed menu against constraints and coherence rules. |
| **Retain** | `actualizador/` | Optionally stores the new experience in the case library. |

---

## 📂 Repository Structure

```directory
cbr-menu-recommendation-system/
├── actualizador/            # Case retention logic (Retain phase)
├── conocimiento/            # Domain knowledge base & case library
├── recuperador/             # Case retrieval & similarity metrics (Retrieve phase)
├── reparador/               # Menu adaptation & repair strategies
├── validador/               # Constraint validation (Revise phase)
├── sistema_cbr.py           # Main CBR engine & user preference model
├── cbr_limpio.py            # Lightweight CBR interface (essential functionality only)
├── gui_cuestionario.py      # Interactive graphical questionnaire (GUI)
├── menu_interactivo.py      # Terminal-mode interactive menu interface
└── add_ratings_to_casos.py  # Utility to collect and append user ratings to cases
```

---

## 🚀 How to Run

### Interactive GUI Mode
```bash
python gui_cuestionario.py
```

### Terminal Interactive Mode
```bash
python menu_interactivo.py
```

### Programmatic API Usage
```python
from cbr_limpio import generar_menu_simple

result = generar_menu_simple(
    tipo_evento='boda',
    temporada='primavera',
    restricciones=['vegetariano'],
    estilo='moderno',
    tradicion='francesa'
)
print(result['menu'])
```

---

## 🧠 System Parameters

| Parameter | Options |
| :--- | :--- |
| `tipo_evento` | `familiar`, `boda`, `congreso` |
| `temporada` | `primavera`, `verano`, `otoño`, `invierno`, `None` |
| `restricciones` | `vegetariano`, `vegano`, `sin_gluten`, `sin_lactosa`, etc. |
| `estilo` | `clasico`, `moderno`, `fusion`, `mediterraneo` |
| `tradicion` | `catalana`, `italiana`, `francesa`, `asiática`, etc. |

---

## 👥 Authors & License

Developed as part of the **Knowledge-Based Systems (SBC)** course.  
Distributed under the **MIT License**.
