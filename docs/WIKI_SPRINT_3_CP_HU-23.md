# HU-23 — Autoguardar el trabajo

## Decisión funcional

El autoguardado aplica tanto a la corrección del texto de origen como a la
traducción. Se ejecuta después de dos segundos sin escribir y al abandonar el
campo para cambiar de región.

Cada formulario envía la fecha de su última versión conocida. Si otra pestaña,
ventana o dispositivo ya guardó una versión más reciente, el servidor responde
con conflicto y **no sobrescribe** el texto guardado. El navegador conserva el
texto local pendiente y explica que la región cambió en otra pestaña.

## Casos de prueba

### CP-23.1 — Autoguardar el trabajo — Happy path

- **Dado** que el usuario está editando una corrección o traducción propia
- **Cuando** deja de escribir durante dos segundos o cambia de región
- **Entonces** el texto se guarda en la región correcta
- **Y** se muestra `Guardado` con la hora del guardado

### CP-23.2 — Fallo de conexión y recuperación

- **Dado** que hay cambios pendientes
- **Cuando** el autoguardado no puede comunicarse con el servidor
- **Entonces** el texto permanece en el campo
- **Y** se muestra `No se pudo guardar` junto con `Reintentar`
- **Y** al recuperar la conexión se vuelve a intentar automáticamente

### CP-23.3 — Cerrar con cambios pendientes

- **Dado** que el texto actual aún no se ha guardado
- **Cuando** el usuario intenta cerrar, recargar o salir de la página
- **Entonces** el navegador solicita confirmación

### CP-23.4 — Aislamiento y asociación

- **Dado** un cambio perteneciente a un usuario, álbum, página y región
- **Cuando** se autoguarda
- **Entonces** solo cambia esa región
- **Y** una región perteneciente a otra cuenta responde 404

### CP-23.5 — Edición concurrente

- **Dado** que dos pestañas cargaron la misma versión de una región
- **Y** la primera pestaña ya guardó un cambio
- **Cuando** la segunda intenta guardar su texto
- **Entonces** el servidor responde con conflicto
- **Y** no sobrescribe la versión de la primera pestaña
- **Y** la segunda conserva su texto local pendiente

