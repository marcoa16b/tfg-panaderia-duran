"""
dev.components — Componentes UI reutilizables.

Capa: Components / Presentation

Descripción:
    Todos los componentes UI compartidos de la aplicación. Los componentes
    son funciones puras que retornan rx.Component y reciben datos/event handlers
    como parámetros. No contienen lógica de negocio.

Flujo de datos:
    Pages → Components → State.vars / State.event_handlers

Convenciones:
    - Los componentes NO importan pages (evitar dependencias circulares).
    - Los componentes PUEDEN importar states para referenciar vars y event handlers.
    - Cada componente está en su propio archivo con docstring del módulo.

Para agregar un nuevo componente:
    1. Crear el archivo en dev/components/.
    2. Agregar docstring del módulo (descripción, uso, dependencias).
    3. Exportar en este __init__.py.
    4. Documentar en docs/components.md.
"""

from dev.components.sidebar import sidebar
from dev.components.header import header
from dev.components.layout import base_layout
from dev.components.tabla_generica import tabla_generica
from dev.components.modal_confirmacion import modal_confirmacion, modal_desactivar
from dev.components.alerta_card import alerta_card, alerta_stock_bajo, alerta_caducidad
from dev.components.stat_card import stat_card, stat_card_simple
from dev.components.form_producto import form_producto
