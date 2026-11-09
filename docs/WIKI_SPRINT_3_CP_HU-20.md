# Borrador para la wiki — Casos de prueba de HU-20

## Decisión funcional

La eliminación es permanente, sin papelera y sin pedir que se escriba el
título. CA-20.1 define el modal con los botones “Eliminar definitivamente” y
“Cancelar”, y CA-20.2 exige que el álbum y sus páginas se eliminen. Esta
decisión deja el archivado existente como la alternativa recuperable.

## HU-20 — Eliminar álbum

Como traductor, quiero eliminar un álbum que ya no necesito para mantener
organizada mi lista de proyectos.

### CP-20.1 — Ver la confirmación — Happy Path

| Campo | Descripción |
|---|---|
| Precondición | Sesión iniciada y álbum propio “Neon Yokai Bureau” con 24 páginas. |
| Pasos | Pulsar “Eliminar” en el detalle del álbum. |
| Resultado esperado | El modal identifica el álbum, avisa que se borrarán las 24 páginas y ofrece “Eliminar definitivamente” y “Cancelar”. |
| CA relacionado | CA-20.1 |
| Pruebas automáticas | `albums/tests/test_album_delete.py` › `test_confirmation_identifies_the_album_and_its_pages`, `test_detail_offers_an_accessible_confirmation_modal` |

### CP-20.2 — Confirmar la eliminación — Happy Path

| Campo | Descripción |
|---|---|
| Precondición | Álbum propio con páginas, regiones, traducciones y archivos. |
| Pasos | Confirmar “Eliminar definitivamente”. |
| Resultado esperado | Se eliminan el álbum, sus datos y archivos; se vuelve a “Mis álbumes” y aparece el mensaje de confirmación. |
| CA relacionado | CA-20.2 |
| Prueba automática | `test_confirming_deletes_the_album_pages_regions_and_files` |

### CP-20.3 — Cancelar la eliminación — Flujo alternativo

| Campo | Descripción |
|---|---|
| Precondición | Confirmación de eliminación abierta. |
| Pasos | Pulsar “Cancelar”, el velo o Escape. |
| Resultado esperado | No cambia ningún dato y el sistema de modal devuelve el foco al botón “Eliminar”. |
| CA relacionado | CA-20.3 |
| Prueba automática | `test_canceling_keeps_the_album_and_returns_to_the_trigger`; contrato genérico de modal en `static/js/app.js`. |

### CP-20.4 — Intentar eliminar un álbum ajeno — Flujo alternativo

| Campo | Descripción |
|---|---|
| Precondición | Existe un álbum de otra cuenta. |
| Pasos | Abrir su confirmación o enviar un POST a su dirección de eliminación. |
| Resultado esperado | Ambas peticiones responden 404 y el álbum permanece intacto. |
| CA relacionado | CA-20.4 |
| Prueba automática | `test_a_foreign_album_returns_404_and_survives` |

### CP-20.5 — Abrir la dirección no elimina — Flujo alternativo

| Campo | Descripción |
|---|---|
| Precondición | Álbum propio existente. |
| Pasos | Realizar un GET a la dirección de eliminación. |
| Resultado esperado | Se muestra la confirmación y no se modifica el álbum, sus páginas ni sus archivos. |
| CA relacionado | CA-20.5 |
| Prueba automática | `test_a_get_never_deletes_the_album` |

### Seguridad y accesibilidad

- La vista usa `OwnedAlbumMixin`: una cuenta ajena recibe 404.
- El formulario POST exige CSRF y la ruta requiere sesión.
- El modal tiene nombre accesible, atrapa el foco, se cierra con Escape y lo
  devuelve al enlace que lo abrió mediante el sistema común de modales.
- La confirmación también existe como página privada sin JavaScript.
