# Borrador para la wiki — Casos de prueba de HU-11

> Borrador de la sección "Casos de prueba" de la página Sprint 2 de la wiki, con el mismo formato que HU-12. Cada CP tiene pruebas automáticas que lo citan en el docstring.

### HU-11 — Visualizar páginas de un álbum

**Historia de usuario:**  
Como traductor, quiero ver las páginas de un álbum para elegir la que deseo traducir o revisar.

**Decisión del 2026-10-20 (pregunta abierta del DoR):** la página seleccionada abre directamente el espacio de trabajo, donde HU-12 a HU-15 muestran sus regiones y su texto. No hay un visor aparte.

### Criterios de aceptación

**CA-11.1:** Dado que el usuario tiene un álbum con 3 páginas, cuando lo abre, entonces ve sus 3 páginas ordenadas por número, cada una con su miniatura, su número y su estado, y solo de ese álbum. *(Implementado en el Sprint 1 con HU-09.)*

**CA-11.2:** Dado que el álbum tiene páginas, cuando el usuario selecciona la página 2, entonces la ve a tamaño completo con su número, su nombre original, sus dimensiones, su estado y su fecha de carga, y puede pasar a la anterior o a la siguiente con botones y con el teclado.

**CA-11.3:** Dado que el álbum no tiene páginas, cuando el usuario lo abre, entonces ve "Este álbum aún no tiene páginas" y el botón "Cargar páginas". *(Implementado en el Sprint 1.)*

**CA-11.4:** Dado que una página pertenece a un álbum de otra cuenta, cuando se pide su vista, su imagen o su miniatura por dirección directa, entonces se responde "Página no encontrada" (404) y la imagen no se entrega. *Sin sesión iniciada, la aplicación pide iniciar sesión (como en todas las vistas privadas) y tampoco entrega la imagen.*

### CP-11.2 — Seleccionar una página — Happy Path

| Campo | Descripción |
|---|---|
| **Precondición** | Álbum propio con tres páginas. |
| **Pasos** | Pulsar la miniatura de la página 2; pulsar "Anterior" y "Siguiente"; repetir con las flechas ← y → del teclado. |
| **Resultado esperado** | Se ve la página 2 a tamaño completo con su número, archivo original, dimensiones, tamaño, estado y fecha de carga, e indica "Página 2 de 3". Los botones y las flechas llevan a las páginas 1 y 3; en la primera y la última no hay a dónde ir. Si se eliminó una página intermedia, la navegación la salta. |
| **CA relacionado** | CA-11.2 |
| **Prueba automática** | `albums/tests/test_page_view.py` › `PageSelectionTests` |
| **Estado** | Aprobada |

### CP-11.4 — Las imágenes de otra cuenta no son accesibles — Flujo alternativo

| Campo | Descripción |
|---|---|
| **Precondición** | Existe una página, con su miniatura, en un álbum de otra cuenta. |
| **Pasos** | Con sesión iniciada, pedir por dirección directa su vista, su imagen y su miniatura. Repetir sin sesión. Pedir también la dirección del archivo en `/media/`. |
| **Resultado esperado** | Con sesión: 404 en las tres. Sin sesión: se pide iniciar sesión. La dirección de `/media/` responde 404: las imágenes solo se entregan por las vistas protegidas, también las portadas de HU-49. |
| **CA relacionado** | CA-11.4 (cierra la deuda DT-02) |
| **Prueba automática** | `test_page_view.py` › `ImageAccessTests`, `CoverAccessTests`; `config/tests/test_route_access.py` |
| **Estado** | Aprobada |
