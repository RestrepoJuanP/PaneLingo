# Borrador para la wiki — Casos de prueba de HU-21

> Borrador de la sección "Casos de prueba" de la página Sprint 2 de la wiki, con el mismo formato que HU-12 a HU-19. Cada CP tiene pruebas automáticas que lo citan en el docstring.

### HU-21 — Visualizar álbumes

**Historia de usuario:**  
Como traductor, quiero ver mis álbumes para llegar rápido al proyecto en el que quiero trabajar.

**Estado real:** "Mis álbumes" se construyó en el Sprint 1 como apoyo a HU-05, sin una HU que lo respaldara. Era un hueco de trazabilidad. Los cinco criterios ya se cumplían en `main`, y la revisión del 21/10/2026 lo confirmó: **no hizo falta cambiar código**. Faltaban los CP formales y pruebas que los citaran, que son lo que aporta esta HU. Las mismas pruebas pasan también con el rediseño de la biblioteca de #61.

### Criterios de aceptación

**CA-21.1:** Dado que tengo 3 álbumes, cuando abro "Mis álbumes", entonces veo 3 tarjetas, y cada una muestra la portada, el título, el par de idiomas (por ejemplo "JA → ES"), el número de páginas, la última edición y el estado.

**CA-21.2:** Dado que otra cuenta tiene el álbum "Ajeno", cuando abro "Mis álbumes", entonces "Ajeno" no aparece.

**CA-21.3:** Cuando pulso la tarjeta de un álbum, entonces llego a su detalle, con sus páginas.

**CA-21.4:** Dado que no tengo álbumes, cuando abro "Mis álbumes", entonces veo un estado vacío con el botón "Nuevo álbum".

**CA-21.5:** Cuando abro "Mis álbumes", entonces los álbumes aparecen del editado más recientemente al más antiguo.

### CP-21.1 — Ver la biblioteca de álbumes — Happy Path

| Campo | Descripción |
|---|---|
| **Precondición** | Sesión iniciada con 3 álbumes propios. |
| **Pasos** | Abrir "Mis álbumes". |
| **Resultado esperado** | Se ven 3 tarjetas. Cada una muestra su portada, el título, el par de idiomas ("JA → ES"), el número de páginas, "Editado hace …" y el chip de estado. |
| **CA relacionado** | CA-21.1 |
| **Prueba automática** | `albums/tests/test_library.py` › `LibraryCardsTests` |
| **Estado** | Aprobada |

### CP-21.2 — Solo veo mis álbumes — Flujo alternativo

| Campo | Descripción |
|---|---|
| **Precondición** | La cuenta propia tiene el álbum "Propio" y otra cuenta tiene "Ajeno". |
| **Pasos** | Abrir "Mis álbumes". |
| **Resultado esperado** | Aparece "Propio" y no aparece "Ajeno". |
| **CA relacionado** | CA-21.2 |
| **Prueba automática** | `albums/tests/test_library.py` › `LibraryIsolationTests`; también `albums/tests/test_views.py` › `AlbumLibraryIsolationTests` |
| **Estado** | Aprobada |

### CP-21.3 — Abrir un álbum — Happy Path

| Campo | Descripción |
|---|---|
| **Precondición** | Un álbum propio. |
| **Pasos** | Pulsar el título o la portada de su tarjeta. |
| **Resultado esperado** | Se abre el detalle del álbum, con su sección "Páginas". |
| **CA relacionado** | CA-21.3 |
| **Prueba automática** | `albums/tests/test_library.py` › `OpenAlbumTests`; también `albums/tests/test_detail.py` › `AlbumCardLinkTests` |
| **Estado** | Aprobada |

### CP-21.4 — Biblioteca vacía — Flujo alternativo

| Campo | Descripción |
|---|---|
| **Precondición** | Sesión iniciada sin álbumes propios. |
| **Pasos** | Abrir "Mis álbumes". |
| **Resultado esperado** | En lugar de la rejilla aparece "Todavía no tienes álbumes", con el botón "Nuevo álbum" y la acción "Crear mi primer álbum". |
| **CA relacionado** | CA-21.4 |
| **Prueba automática** | `albums/tests/test_library.py` › `EmptyLibraryTests` |
| **Estado** | Aprobada |

### CP-21.5 — Orden de la biblioteca — Happy Path

| Campo | Descripción |
|---|---|
| **Precondición** | Tres álbumes editados en días distintos. |
| **Pasos** | Abrir "Mis álbumes"; luego editar el más antiguo y volver a abrirla. |
| **Resultado esperado** | Aparecen del editado más recientemente al más antiguo. Tras editar el más antiguo, pasa al primer lugar. |
| **CA relacionado** | CA-21.5 |
| **Prueba automática** | `albums/tests/test_library.py` › `LibraryOrderTests` |
| **Estado** | Aprobada |

### Estrategia de pruebas automáticas

| Funcionalidad | Tipo de prueba | Justificación |
|---|---|---|
| Tarjetas, aislamiento, apertura y estado vacío | Integración Django (`TestCase` + `Client`) | Recorren la petición completa y verifican lo que ve el usuario |
| Orden | Escenario con fechas de edición fijadas | Comprueba el orden exacto sin depender de la velocidad de la prueba |
