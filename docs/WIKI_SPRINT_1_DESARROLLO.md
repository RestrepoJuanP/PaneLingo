# Sprint 1 — Desarrollo

Borrador listo para copiar a la wiki del proyecto.

---

## 1. Resumen

El Sprint 1 entrega el MVP de **autenticación y gestión de álbumes y páginas** de PaneLingo. Las diez historias de usuario están implementadas y sus veinte casos de prueba cubiertos por pruebas automáticas.

| Indicador | Valor |
|---|---|
| Historias de usuario entregadas | 10 de 10 |
| Casos de prueba cubiertos | 20 de 20 |
| Pruebas automáticas | 227, todas en verde |
| Quality Gate | 7 de 7 pasos en verde en las 14 etapas |
| Bugs registrados y cerrados | 2 |
| Módulos Python | 51 |
| Plantillas | 38 |

Trazabilidad completa en [`docs/TRACEABILITY.md`](../TRACEABILITY.md). Evidencia por etapa en `docs/evidence/sprint-1/`.

---

## 2. Alcance implementado por historia

| HU | Título | Entregado |
|---|---|---|
| HU-01 | Crear cuenta | Registro con nombre, correo, contraseña con confirmación y aceptación de términos. Validación completa y autenticación automática tras el alta. |
| HU-02 | Iniciar sesión | Autenticación por correo. Mensaje de error genérico e idéntico para credenciales inválidas, correo inexistente y cuenta inactiva. Casilla de sesión persistente funcional. |
| HU-03 | Cerrar sesión | Cierre por POST desde el bloque de perfil, en escritorio y en móvil. Auditoría completa de acceso a vistas privadas. |
| HU-04 | Recuperar contraseña | Flujo de cuatro pantallas sobre las vistas nativas de Django, con correo en texto plano y HTML. Enlace de un solo uso con caducidad de una hora. |
| HU-05 | Crear álbum | Modelo de dominio (`Language`, `Album`), biblioteca con rejilla de tarjetas, portada determinista y creación como modal con degradación a página. |
| HU-06 | Título del álbum | Validación reforzada y renombrado rápido desde la biblioteca. |
| HU-07 | Idiomas del álbum | Selectores con apariencia de pill sobre grupos de radios nativos. Regla de origen distinto de destino. |
| HU-08 | Editar álbum | Pantalla de detalle completa y edición de la información. Cancelar sin escritura. |
| HU-09 | Cargar páginas | Modelo `ComicPage`, carga múltiple, validación real con Pillow, generación de miniaturas y cola de resultados por archivo. |
| HU-10 | Eliminar páginas | Borrado con confirmación, limpieza de archivos en disco y cobertura del borrado en cascada. |

### Pantallas construidas

Autenticación (iniciar sesión, crear cuenta), recuperación de contraseña (solicitar, confirmación de envío, nueva contraseña, resultado), biblioteca de álbumes, crear álbum, detalle de álbum, editar álbum, renombrar álbum, cargar páginas, elegir álbum para cargar, eliminar página. Más `/design-system/`, que es una referencia de estilos solo para desarrollo.

---

## 3. Decisiones técnicas y su justificación

### 3.1 Modelo de usuario personalizado desde el primer día

`accounts.User` hereda de `AbstractUser` con el correo como `USERNAME_FIELD` y sin campo `username`. Se definió en la Etapa 1, antes de la primera migración, porque cambiar el modelo de usuario una vez que hay datos exige una migración compleja y arriesgada.

### 3.2 Patrón obligatorio de vista privada

`accounts/access.py` aporta `private_view` (funciones) y `PrivateViewMixin` (clases), que combinan `login_required` y `never_cache`. Se agruparon a propósito: aplicados por separado, **olvidar `never_cache` no rompe ninguna prueba** y deja contenido privado en la caché del navegador tras cerrar sesión.

`config/tests/test_route_access.py` exige que **toda** ruta con nombre esté clasificada como pública, privada o de acción. Una ruta nueva sin clasificar hace fallar la prueba.

### 3.3 Aislamiento por propietario, en tres capas

1. Los formularios **no exponen `owner`**, ni siquiera oculto: sin campo no hay nada que manipular.
2. Las vistas asignan el propietario desde `request.user`.
3. Los *querysets* filtran por propietario, de modo que un objeto ajeno responde **404 y no 403**: un 403 confirmaría que existe.

Las tres capas están cubiertas por pruebas que comprueban el **valor final** de `owner`, no solo que la petición no falle.

### 3.4 Caducidad del enlace de recuperación: una hora

Django trae tres días. Se redujo a `PASSWORD_RESET_TIMEOUT = 3600` porque el enlace es una **credencial al portador** que concede la toma completa de la cuenta y viaja por correo, un canal que no controlamos y donde el mensaje queda archivado. Quien lo solicita está delante del ordenador en ese momento; tres días no cubren un caso legítimo, solo alargan la exposición.

### 3.5 La invalidación de sesiones no se implementó: se verificó

Al cambiar la contraseña, **Django ya invalida todas las demás sesiones** mediante el HMAC que guarda en la sesión. Añadir código propio habría duplicado el framework. En su lugar se añadió una prueba que fija ese comportamiento, porque era una garantía implícita que nadie defendía.

### 3.6 Validación de imágenes: no se cree nada del cliente

Ni la extensión del nombre ni el `content_type`. Lo que decide es abrir el archivo con Pillow.

- `verify()` recorre el archivo entero, pero lo **consume**: hay que reabrir para leer dimensiones, y **rebobinar antes de guardar**. Sin ese último paso la validación pasa y en disco queda un archivo truncado, sin que nada lo delate.
- **Decompression bombs:** un archivo de pocos kilobytes puede declarar 60 000 × 60 000 píxeles. Pillow avisa pero no bloquea, así que el aviso se eleva a rechazo. La comprobación ocurre al abrir, leyendo la cabecera, sin reservar memoria.

### 3.7 El nombre en disco lo genera el servidor

El nombre del cliente **se descarta**, no se sanea. Sanear obliga a acertar con una lista de casos —recorrido de rutas, nombres reservados de Windows, longitudes, unicode, doble extensión, colisiones— y basta fallar en uno. Generando el nombre completo con un identificador aleatorio, ninguno llega al sistema de archivos. La extensión sale del formato **real** detectado por Pillow.

### 3.8 Limpieza de archivos con señal, no sobrescribiendo `delete()`

Al eliminar un álbum, el recolector de Django borra sus páginas **sin llamar al método `delete()`** de cada instancia. Una señal `post_delete` sí se dispara en cascada, y registrarla desactiva el borrado rápido que se la saltaría. Quedan cubiertos los cuatro caminos: página, queryset, álbum y cuenta.

La limpieza es **tolerante a fallos**: corre dentro de la transacción, así que dejar escapar una excepción revertiría el borrado del registro. Un archivo huérfano es recuperable; un borrado a medias no.

### 3.9 Selectores de idioma: radios nativos, no botones

Las pills se construyeron sobre un grupo de radios con el input oculto a la vista pero enfocable. Las flechas del teclado recorren el grupo por sí solas y el formulario se envía sin JavaScript. Con botones habría que programar la navegación a mano.

### 3.10 Numeración de páginas: no se renumera al borrar

Renumerar, o mostrar la posición en lugar del número guardado, **mueve igualmente la etiqueta que el usuario ve**. Además, en una herramienta de traducción de cómic **el hueco dice la verdad**: una secuencia 1, 2, 4 informa de que a la obra le falta esa página. El salto se explica en el mensaje de confirmación.

---

## 4. Resultados del Quality Gate

Los siete pasos, en el orden fijado, se ejecutaron al cierre de cada una de las 14 etapas. **Todas terminaron en 7/7 verde.**

| Paso | Comando | Resultado en la etapa 12 |
|---|---|---|
| 1 | `ruff check . --fix` | All checks passed |
| 2 | `black .` | Sin cambios |
| 3 | `ruff check .` | All checks passed |
| 4 | `black --check .` | Sin cambios |
| 5 | `python manage.py check` | Sin incidencias |
| 6 | `python manage.py test` | 227 pruebas, OK |
| 7 | `pip-audit -r requirements.txt` | Sin vulnerabilidades conocidas |

La captura de evidencias está automatizada en `scripts/quality_gate.sh`, que ejecuta los siete pasos aunque alguno falle y registra el código de salida de cada uno, con cabecera de fecha, rama, commit y versión de herramienta.

### Comprobaciones adicionales de cierre

| Comando | Resultado |
|---|---|
| `python manage.py makemigrations --check --dry-run` | *No changes detected* — no hay migraciones pendientes |
| `python manage.py check --deploy` | 4 advertencias, todas de configuración de HTTPS. Ver sección 7 |

### Incidencias resueltas durante el sprint

- **Pillow 11.3.0** acumulaba 25 vulnerabilidades conocidas. Se actualizó a 12.3.0 en lugar de ignorarlas.
- **`E501` en migraciones autogeneradas:** las cadenas `help_text` que hereda `AbstractUser` no se pueden partir. Se añadió un `per-file-ignores` limitado a una regla y una ruta, con el motivo comentado.

---

## 5. Bugs: ciclo completo

> Los identificadores no son consecutivos porque el contador de *issues* de GitHub es **compartido con los pull requests**.

### BUG-043 — La zona de carga no muestra los archivos seleccionados

| | |
|---|---|
| Issue | #43 |
| Detectado en | HU-09, durante la ejecución manual de CP-09.1 |
| Rama | `fix/BUG-043-upload-queue-feedback` |
| PR | #44 |

**Síntoma:** tras pulsar "Elegir archivos" y seleccionar, la pantalla seguía mostrando el texto inicial.

**Corrección:** cola de selección en cliente con miniatura, nombre, tamaño y estado; posibilidad de quitar archivos; aviso temprano de extensión o tamaño no admitidos.

**Lo importante de la corrección:** los límites **no se escriben en el JavaScript**. El servidor los emite como atributos de datos y el navegador los lee de ahí, con una prueba que verifica que cambiar el ajuste cambia el atributo. Y el aviso del navegador **nunca bloquea el envío**: es una comodidad, y la autoridad es el servidor.

### BUG-046 — Comentarios de plantilla renderizados como texto visible

| | |
|---|---|
| Issue | #46 |
| Detectado en | HU-10, revisión de la rejilla de páginas |
| Rama | `fix/BUG-046-template-comments` |
| PR | #47 |

**Síntoma:** los comentarios `{# ... #}` de varias líneas aparecían como texto en la interfaz. La sintaxis breve de Django solo funciona en una línea.

**Alcance real, mayor que el reportado:** 46 comentarios en 35 plantillas, prácticamente todas las escritas desde la Etapa 2.

**Por qué no se detectó antes:** ninguna prueba podía delatarlo. Todas comprobaban que **apareciera** lo que debía aparecer, ninguna que **no apareciera** lo que no debía.

**Corrección:** conversión a `{% comment %} … {% endcomment %}` y tres pruebas nuevas que verifican delimitadores, texto de comentarios en las 14 pantallas principales, y sintaxis en el código de todas las plantillas.

Se corrigió además un problema **independiente**: la etiqueta `Pendiente de procesamiento` desbordaba la celda de 146 px y pisaba el botón de eliminar.

---

## 6. Propuestas abiertas para el Product Owner

Estas decisiones se dejaron deliberadamente sin tomar. **Ninguna es un olvido**: cada una se planteó, se argumentó y se aplazó para que la decida el PO.

### 6.1 ¿Activamos el estado editable del álbum?

**Situación actual.** Todos los álbumes muestran el badge "Borrador" durante todo el sprint. El campo `status` existe en el modelo con sus cuatro valores, pero ninguna historia lo cambia.

**Qué implicaría activarlo.** Añadir `status` al formulario de edición: una línea más su prueba.

**Qué desbloquearía.**
- Los badges dejarían de decir todos lo mismo.
- Los filtros de la biblioteca (propuesta 6.2) pasarían a tener sentido.
- El traductor podría organizar su trabajo con una etiqueta propia.

**Qué riesgo tiene.**
- Los cuatro valores **no son etiquetas neutras, son fases de un flujo que no existe**. "En revisión" supone bloques esperando revisión, y no hay bloques. "Completado" supone una traducción terminada. Marcar "Completado" un álbum con cero páginas sería afirmar algo que el sistema sabe que es falso, y quedaría grabado.
- **Invertiría la naturaleza del dato.** El estado es un hecho derivado del avance. Convertirlo en etiqueta declarada obliga a decidir, cuando llegue el flujo de traducción, si el sistema pisa lo que el usuario escribió o si el campo se bifurca en dos significados.

**Recomendación del equipo.** Si se quiere, que entre como **historia nueva del backlog** con sus criterios y casos de prueba, no como parche. Esa historia debería además revisar si los cuatro valores son los adecuados para una etiqueta manual.

### 6.2 ¿Construimos los filtros de la biblioteca?

**Situación actual.** El mockup muestra cinco filtros: Todos, En progreso, Necesita revisión, Completado, Archivado. No se construyeron.

**Motivo.** Con un único estado posible, cuatro de los cinco devolverían **lista vacía siempre**. Una fila de filtros que nunca devuelve nada no parece una función pendiente: parece que la aplicación está rota. Además "Necesita revisión" pertenece a la revisión de traducción y "Archivado" ni siquiera está entre los valores del modelo.

**Dependencia.** Esta propuesta **depende de la 6.1**. Sin estado editable no hay nada que filtrar.

### 6.3 ¿Habilitamos eliminar álbumes?

**Situación actual.** El botón existe en el detalle, con el estilo destructivo del mockup, pero **deshabilitado** y con un texto que indica que llega más adelante.

**Motivo.** No hay HU, CA ni CP que lo respalden.

**Nota técnica favorable.** La limpieza de archivos en cascada **ya funciona**: hay pruebas que borran un álbum entero y una cuenta completa, y verifican que no queda ningún archivo en disco. Cuando llegue esa historia, esa parte no habrá que construirla.

### 6.4 ¿Reordenar o insertar páginas?

**Situación actual.** Las páginas se numeran por orden de carga y no se renumeran al borrar, de modo que pueden aparecer huecos. Una página cargada después siempre va al final.

**Consecuencia práctica.** Si el traductor borra la página 3 por error y vuelve a subirla, aparece como página 11 al final del álbum, no en su sitio.

**Recomendación.** Es la carencia funcional más visible que deja el sprint. Merece una historia propia, que decidiría también si renumera.

### 6.5 ¿Perfil y preferencias?

**Situación actual.** No se construyeron. La única acción del bloque de perfil es cerrar sesión.

**Nota técnica.** Los idiomas predeterminados que muestra el mockup vivirían en `accounts.User` y crearían una clave foránea de `accounts` hacia `albums`, invirtiendo la dependencia actual. Cuando llegue esa historia conviene decidir si esos valores van en el usuario, en un modelo de preferencias aparte o en la sesión.

---

## 7. Deudas técnicas y pendientes

Detalladas en formato de issue en el informe de cierre. Resumen:

| ID | Deuda | Gravedad | Momento de resolverla |
|---|---|---|---|
| DT-01 | Sin pruebas de navegador para el JavaScript | Media | Cuando el equipo decida sobre el stack de pruebas de cliente |
| DT-02 | Los archivos de `media/` no tienen control de acceso | **Alta** | **Antes del primer despliegue** |
| DT-03 | Umbral de baja resolución sin calibrar | Baja | Cuando exista el OCR |
| DT-04 | `check --deploy`: cuatro advertencias de HTTPS | **Alta** | **Antes del primer despliegue** |
| DT-05 | Sin paginación en la biblioteca ni en la rejilla de páginas | Media | Cuando un álbum supere las ~100 páginas |
| DT-06 | Sin límite de archivos por lote de carga | Baja | Junto con DT-05 |

### DT-02 y DT-04 merecen atención antes de cualquier despliegue

**DT-02 — Control de acceso a los archivos.** Verificado empíricamente: con `DEBUG=True`, una cuenta ajena y un visitante anónimo obtienen **200** al pedir la URL directa de una imagen privada. Las vistas HTML sí están protegidas —el detalle del álbum devuelve 404 a una cuenta ajena— pero el archivo se sirve sin comprobación.

El nombre en disco es un identificador aleatorio, así que la URL no es adivinable, pero **eso es ofuscación, no control de acceso**: quien obtenga la URL una vez la conserva.

Con `DEBUG=False` Django deja de servir esa ruta y responde 404, pero en un despliegue real el servidor web sirve `/media/` y el agujero reaparece salvo que se configure lo contrario.

**DT-04 — Configuración de HTTPS.** `check --deploy` reporta cuatro advertencias con `DEBUG=False`: `SECURE_HSTS_SECONDS`, `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE` y `CSRF_COOKIE_SECURE`. Las cuatro son **aceptables en desarrollo** —activarlas rompería el servidor local, que no usa HTTPS— y **obligatorias antes de un despliegue real**. No se han silenciado.

---

## 8. Cumplimiento de estándares

| Estándar | Verificación | Resultado |
|---|---|---|
| Nombramiento (PEP 8 + Django Coding Style) | Auditoría automática del AST de los 51 módulos | Sin desviaciones |
| Identificadores en inglés, interfaz en español | Búsqueda de acentos en identificadores | Sin desviaciones |
| Ruff `["E","F","N","B","I","C90"]`, línea 88, complejidad máxima 10 | Paso 3 del Quality Gate | En verde |
| Black, línea 88 | Paso 4 del Quality Gate | En verde |
| Docstring en español en toda función y clase pública | Revisión durante cada etapa | Cumplido |
| CP citado en el docstring de las pruebas | 91 de 227 pruebas citan un CP; el resto son de apoyo | Cumplido |
| `csrf_token` en todo formulario POST | Recuento automático sobre las plantillas | 14 de 14 |
| Sin secretos versionados | Búsqueda en el historial completo de Git | Ninguno |

---

## 9. Convenciones de trabajo aplicadas

- **GitHub Flow** con una rama por historia de usuario. `main` nunca se tocó directamente.
- **Conventional Commits** con el identificador de la HU o del bug.
- **Quality Gate obligatorio** al cierre de cada etapa, con evidencia versionada.
- **Evidencia regenerada sobre árbol limpio** tras cada commit, para que el resumen apunte a un hash reproducible.
- Cuando una etapa cubrió dos historias, se dividió en dos ramas y dos PR, y la evidencia se numeró con sufijo de letra (`08` y `08b`).
