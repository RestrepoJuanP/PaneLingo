# Borrador para la wiki — Casos de prueba de HU-69

> Borrador de la sección "Casos de prueba" de la página Sprint 2 de la wiki, con el mismo formato que HU-12 a HU-19. Cada CP tiene pruebas automáticas que lo citan en el docstring.

### HU-69 — Archivar álbum

**Historia de usuario:**  
Como traductor, quiero archivar los álbumes en los que ya no trabajo para que no estorben en mi biblioteca sin perderlos.

**Origen:** respuesta del Product Owner del 21 de octubre de 2026 a la pregunta 6.2 del cierre del Sprint 1. El mockup trae el filtro "Archived" en la biblioteca.

**Decisiones de diseño:**
- Archivar es **independiente del estado derivado** (HU-26): un álbum archivado conserva si estaba "En revisión" o "Completado", y lo recupera al desarchivarlo. Se guarda en un campo propio, `archived_at`.
- **Sin confirmación**, porque se puede deshacer desde el aviso. Archivar no borra nada ni cambia la fecha de edición del álbum.
- La **cuota mensual de OCR** sigue contando las páginas de álbumes archivados, porque ese uso ya se hizo; las estadísticas de la biblioteca, no.

### Criterios de aceptación

**CA-69.1:** Cuando elijo "Archivar" en el menú "···" de la tarjeta o en el detalle del álbum, entonces el álbum queda archivado sin pedir confirmación y veo el aviso "Álbum archivado" con la opción "Deshacer".

**CA-69.2:** Dado que el álbum está archivado, cuando abro "Mis álbumes", uso los filtros por estado o busco por su título, entonces no aparece, y el filtro "Archivados (1)" lo muestra.

**CA-69.3:** Dado que el álbum está archivado, cuando elijo "Desarchivar" (o "Deshacer" en el aviso), entonces vuelve a la biblioteca con su estado derivado de siempre.

**CA-69.4:** Dado que el álbum está archivado, cuando abro su detalle, entonces veo el aviso "Este álbum está archivado" con el botón "Desarchivar" y puedo abrir sus páginas.

**CA-69.5:** Dado que el álbum está archivado, entonces no cuenta en las estadísticas de la biblioteca, en el aviso de regiones por revisar de la barra lateral ni en "Continuar donde lo dejaste".

**CA-69.6:** Cuando intento archivar o desarchivar un álbum de otra cuenta, entonces recibo "no encontrado" (404) y el álbum no cambia.

### CP-69.1 — Archivar un álbum — Happy Path

| Campo | Descripción |
|---|---|
| **Precondición** | Álbum propio "Neon Yokai Bureau" activo. |
| **Pasos** | Abrir el menú "···" de su tarjeta y elegir "Archivar" (o pulsar "Archivar" en su detalle). |
| **Resultado esperado** | Sin confirmación, aparece "Álbum «Neon Yokai Bureau» archivado." con "Deshacer". Se vuelve a la misma vista de la biblioteca (mismo filtro y búsqueda); una dirección de otro dominio en `next` se ignora. La fecha "Editado hace…" no cambia. |
| **CA relacionado** | CA-69.1 |
| **Prueba automática** | `albums/tests/test_archive.py` › `ArchiveAlbumTests` |
| **Estado** | Aprobada |

### CP-69.2 — Los archivados no aparecen en la biblioteca

| Campo | Descripción |
|---|---|
| **Precondición** | "Neon Yokai Bureau" archivado y "Ember Line" activo. |
| **Pasos** | Abrir "Mis álbumes" con "Todos", "En progreso" y "Por revisar"; buscar "neon"; elegir "Archivados". |
| **Resultado esperado** | "Neon Yokai Bureau" no aparece en los filtros por estado ni en la búsqueda. El filtro "Archivados (1)" lo muestra, con "Archivado hace…". Si todos los álbumes están archivados, la biblioteca dice "Todos tus álbumes están archivados" y ofrece "Ver archivados". |
| **CA relacionado** | CA-69.2 |
| **Prueba automática** | `albums/tests/test_archive.py` › `HiddenFromLibraryTests` |
| **Estado** | Aprobada |

### CP-69.3 — Desarchivar — Flujo alternativo

| Campo | Descripción |
|---|---|
| **Precondición** | "Neon Yokai Bureau" archivado con una página "Por revisar". |
| **Pasos** | Pulsar "Desarchivar" en el menú "···" o en el detalle, o "Deshacer" en el aviso. |
| **Resultado esperado** | Aparece "Álbum «Neon Yokai Bureau» devuelto a la biblioteca." y el álbum vuelve a "Todos" con su estado "En revisión". |
| **CA relacionado** | CA-69.3 |
| **Prueba automática** | `albums/tests/test_archive.py` › `UnarchiveTests` |
| **Estado** | Aprobada |

### CP-69.4 — Un álbum archivado sigue accesible

| Campo | Descripción |
|---|---|
| **Precondición** | "Neon Yokai Bureau" archivado. |
| **Pasos** | Abrir su detalle desde "Archivados" y luego una de sus páginas. |
| **Resultado esperado** | El detalle muestra "Este álbum está archivado." con "Desarchivar" y sin "Archivar". Sus páginas se abren con normalidad. |
| **CA relacionado** | CA-69.4 |
| **Prueba automática** | `albums/tests/test_archive.py` › `ArchivedDetailTests` |
| **Estado** | Aprobada |

### CP-69.5 — Los archivados no cuentan en los resúmenes

| Campo | Descripción |
|---|---|
| **Precondición** | El álbum tiene una página "Por revisar" con una región por revisar, y es el único con trabajo pendiente. |
| **Pasos** | Ver la biblioteca, archivar el álbum y volver a verla. |
| **Resultado esperado** | Antes: la barra lateral avisa de 1 región por revisar y aparece "Continuar donde lo dejaste". Después: el aviso marca 0, "Continuar donde lo dejaste" desaparece y las estadísticas "Regiones por revisar" y "Páginas procesadas esta semana" marcan 0. |
| **CA relacionado** | CA-69.5 |
| **Prueba automática** | `albums/tests/test_archive.py` › `SummariesTests` |
| **Estado** | Aprobada |

### CP-69.6 — Solo álbumes propios — Flujo alternativo

| Campo | Descripción |
|---|---|
| **Precondición** | Existe un álbum de otra cuenta. |
| **Pasos** | Enviar un POST a `/albumes/<id ajeno>/archivar/` y a `/albumes/<id ajeno>/desarchivar/`. |
| **Resultado esperado** | Ambas responden 404 y el álbum ajeno no cambia. Por GET, las dos rutas responden 405. |
| **CA relacionado** | CA-69.6 |
| **Prueba automática** | `albums/tests/test_archive.py` › `ArchiveAccessTests` y `config/tests/test_route_access.py` |
| **Estado** | Aprobada |

### Estrategia de pruebas automáticas

| Funcionalidad | Tipo de prueba | Justificación |
|---|---|---|
| Archivar y desarchivar | Escenarios por vista con el servicio `albums/archiving.py` | Comprueban el campo, el aviso con "Deshacer", la vuelta a la página de origen y que no cambia la fecha de edición |
| Biblioteca y búsqueda | Escenarios de la vista "Mis álbumes" con cada filtro | CA-69.2 en todos los filtros, la búsqueda y el estado vacío |
| Resúmenes | Escenario antes y después de archivar | Estadísticas, barra lateral y "Continuar" en una sola prueba (CA-69.5) |
| Aislamiento | Álbum ajeno → 404; GET → 405 (`config/tests/test_route_access.py`) | Definición de terminado |

**Ejecución manual (21/10/2026)** sobre la biblioteca de la cuenta de prueba, con cuatro álbumes:
- **"···" › "Archivar" en "The Flash"** (En revisión): apareció "Álbum «The Flash» archivado." con "Deshacer". La biblioteca pasó a 3 álbumes y las estadísticas se recalcularon sin él.
- **Filtro "Archivados 1":** mostró "The Flash" con su estado "En revisión" y "Archivado hace … · Editado hace 5 horas".
- **Detalle:** mostró "Este álbum está archivado." con "Desarchivar" y sin "Archivar". Al desarchivar, apareció "Álbum «The Flash» devuelto a la biblioteca." y volvió el botón "Archivar".
