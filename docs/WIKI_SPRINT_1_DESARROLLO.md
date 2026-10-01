# Anexo — Decisiones técnicas del Sprint 1

> Anexo de la sección [Desarrollo MVP V1](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-1#desarrollo-mvp-v1) de la página [Sprint 1](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-1). Recoge el porqué de las decisiones de diseño, las propuestas que quedaron abiertas para el Product Owner y la verificación de los estándares.

---

## 1. Decisiones técnicas y su justificación

### 1.1 Modelo de usuario personalizado desde el primer día

`accounts.User` hereda de `AbstractUser` con el correo como `USERNAME_FIELD` y sin campo `username`. Se definió en la Etapa 1, antes de la primera migración, porque cambiar el modelo de usuario una vez que hay datos exige una migración compleja y arriesgada.

### 1.2 Patrón obligatorio de vista privada

`accounts/access.py` aporta `private_view` (funciones) y `PrivateViewMixin` (clases), que combinan `login_required` y `never_cache`. Se agruparon a propósito: aplicados por separado, **olvidar `never_cache` no rompe ninguna prueba** y deja contenido privado en la caché del navegador tras cerrar sesión.

`config/tests/test_route_access.py` exige que **toda** ruta con nombre esté clasificada como pública, privada o de acción. Una ruta nueva sin clasificar hace fallar la prueba.

### 1.3 Aislamiento por propietario, en tres capas

1. Los formularios **no exponen `owner`**, ni siquiera oculto: sin campo no hay nada que manipular.
2. Las vistas asignan el propietario desde `request.user`.
3. Los *querysets* filtran por propietario, de modo que un objeto ajeno responde **404 y no 403**: un 403 confirmaría que existe.

Las tres capas están cubiertas por pruebas que comprueban el **valor final** de `owner`, no solo que la petición no falle.

### 1.4 Caducidad del enlace de recuperación: una hora

Django trae tres días. Se redujo a `PASSWORD_RESET_TIMEOUT = 3600` porque el enlace es una **credencial al portador** que concede la toma completa de la cuenta y viaja por correo, un canal que no controlamos y donde el mensaje queda archivado. Quien lo solicita está delante del ordenador en ese momento; tres días no cubren un caso legítimo, solo alargan la exposición.

### 1.5 La invalidación de sesiones no se implementó: se verificó

Al cambiar la contraseña, **Django ya invalida todas las demás sesiones** mediante el HMAC que guarda en la sesión. Añadir código propio habría duplicado el framework. En su lugar se añadió una prueba que fija ese comportamiento, porque era una garantía implícita que nadie defendía.

### 1.6 Validación de imágenes: no se cree nada del cliente

Ni la extensión del nombre ni el `content_type`. Lo que decide es abrir el archivo con Pillow.

- `verify()` recorre el archivo entero, pero lo **consume**: hay que reabrir para leer dimensiones, y **rebobinar antes de guardar**. Sin ese último paso la validación pasa y en disco queda un archivo truncado, sin que nada lo delate.
- **Decompression bombs:** un archivo de pocos kilobytes puede declarar 60 000 × 60 000 píxeles. Pillow avisa pero no bloquea, así que el aviso se eleva a rechazo. La comprobación ocurre al abrir, leyendo la cabecera, sin reservar memoria.

### 1.7 El nombre en disco lo genera el servidor

El nombre del cliente **se descarta**, no se sanea. Sanear obliga a acertar con una lista de casos —recorrido de rutas, nombres reservados de Windows, longitudes, unicode, doble extensión, colisiones— y basta fallar en uno. Generando el nombre completo con un identificador aleatorio, ninguno llega al sistema de archivos. La extensión sale del formato **real** detectado por Pillow.

### 1.8 Limpieza de archivos con señal, no sobrescribiendo `delete()`

Al eliminar un álbum, el recolector de Django borra sus páginas **sin llamar al método `delete()`** de cada instancia. Una señal `post_delete` sí se dispara en cascada, y registrarla desactiva el borrado rápido que se la saltaría. Quedan cubiertos los cuatro caminos: página, queryset, álbum y cuenta.

La limpieza es **tolerante a fallos**: corre dentro de la transacción, así que dejar escapar una excepción revertiría el borrado del registro. Un archivo huérfano es recuperable; un borrado a medias no.

### 1.9 Selectores de idioma: radios nativos, no botones

Las pills se construyeron sobre un grupo de radios con el input oculto a la vista pero enfocable. Las flechas del teclado recorren el grupo por sí solas y el formulario se envía sin JavaScript. Con botones habría que programar la navegación a mano.

### 1.10 Numeración de páginas: no se renumera al borrar

Renumerar, o mostrar la posición en lugar del número guardado, **mueve igualmente la etiqueta que el usuario ve**. Además, en una herramienta de traducción de cómic **el hueco dice la verdad**: una secuencia 1, 2, 4 informa de que a la obra le falta esa página. El salto se explica en el mensaje de confirmación.

---

## 2. Propuestas abiertas para el Product Owner

Estas decisiones se dejaron deliberadamente sin tomar. **Ninguna es un olvido**: cada una se planteó, se argumentó y se aplazó para que la decida el PO.

### 2.1 ¿Activamos el estado editable del álbum?

**Situación actual.** Todos los álbumes muestran el badge "Borrador" durante todo el sprint. El campo `status` existe en el modelo con sus cuatro valores, pero ninguna historia lo cambia.

**Qué implicaría activarlo.** Añadir `status` al formulario de edición: una línea más su prueba.

**Qué desbloquearía.**
- Los badges dejarían de decir todos lo mismo.
- Los filtros de la biblioteca (propuesta 2.2) pasarían a tener sentido.
- El traductor podría organizar su trabajo con una etiqueta propia.

**Qué riesgo tiene.**
- Los cuatro valores **no son etiquetas neutras, son fases de un flujo que no existe**. "En revisión" supone bloques esperando revisión, y no hay bloques. "Completado" supone una traducción terminada. Marcar "Completado" un álbum con cero páginas sería afirmar algo que el sistema sabe que es falso, y quedaría grabado.
- **Invertiría la naturaleza del dato.** El estado es un hecho derivado del avance. Convertirlo en etiqueta declarada obliga a decidir, cuando llegue el flujo de traducción, si el sistema pisa lo que el usuario escribió o si el campo se bifurca en dos significados.

**Recomendación del equipo.** Si se quiere, que entre como **historia nueva del backlog** con sus criterios y casos de prueba, no como parche. Esa historia debería además revisar si los cuatro valores son los adecuados para una etiqueta manual.

### 2.2 ¿Construimos los filtros de la biblioteca?

**Situación actual.** El mockup muestra cinco filtros: Todos, En progreso, Necesita revisión, Completado, Archivado. No se construyeron.

**Motivo.** Con un único estado posible, cuatro de los cinco devolverían **lista vacía siempre**. Una fila de filtros que nunca devuelve nada no parece una función pendiente: parece que la aplicación está rota. Además "Necesita revisión" pertenece a la revisión de traducción y "Archivado" ni siquiera está entre los valores del modelo.

**Dependencia.** Esta propuesta **depende de la 6.1**. Sin estado editable no hay nada que filtrar.

### 2.3 ¿Habilitamos eliminar álbumes?

**Situación actual.** El botón existe en el detalle, con el estilo destructivo del mockup, pero **deshabilitado** y con un texto que indica que llega más adelante.

**Motivo.** No hay HU, CA ni CP que lo respalden.

**Nota técnica favorable.** La limpieza de archivos en cascada **ya funciona**: hay pruebas que borran un álbum entero y una cuenta completa, y verifican que no queda ningún archivo en disco. Cuando llegue esa historia, esa parte no habrá que construirla.

### 2.4 ¿Reordenar o insertar páginas?

**Situación actual.** Las páginas se numeran por orden de carga y no se renumeran al borrar, de modo que pueden aparecer huecos. Una página cargada después siempre va al final.

**Consecuencia práctica.** Si el traductor borra la página 3 por error y vuelve a subirla, aparece como página 11 al final del álbum, no en su sitio.

**Recomendación.** Es la carencia funcional más visible que deja el sprint. Merece una historia propia, que decidiría también si renumera.

### 2.5 ¿Perfil y preferencias?

**Situación actual.** No se construyeron. La única acción del bloque de perfil es cerrar sesión.

**Nota técnica.** Los idiomas predeterminados que muestra el mockup vivirían en `accounts.User` y crearían una clave foránea de `accounts` hacia `albums`, invirtiendo la dependencia actual. Cuando llegue esa historia conviene decidir si esos valores van en el usuario, en un modelo de preferencias aparte o en la sesión.

---

### 2.6 Solicitudes del PO en la review del 9 de septiembre

En la Sprint Review el Product Owner pidió dos funciones nuevas, ya registradas en el backlog:

- [HU-49 — Cambiar la imagen de portada del álbum](https://github.com/RestrepoJuanP/PaneLingo/issues/49)
- [HU-50 — Buscar álbumes por título](https://github.com/RestrepoJuanP/PaneLingo/issues/50)

Quedan para estimar y asignar en la planificación del Sprint 2.

---

## 3. Cumplimiento de estándares

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
