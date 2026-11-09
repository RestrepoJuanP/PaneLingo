# ADR-003 — Componer la página traducida a partir de capas

- **Estado:** provisional; autorizado para implementación, aprobación formal
  del Product Owner pendiente
- **Fecha:** 9 de noviembre de 2026
- **Épica:** EP-08 Edición de imagen
- **Requisito:** RF-15

## Contexto

El Product Owner espera descargar páginas limpias y traducidas como PNG. El
flujo actual detecta, corrige, traduce y aprueba texto, pero la exportación de
HU-27 y HU-28 solo produce un DOCX. Generar una imagen completa con IA no es
repetible, puede alterar el dibujo y dificulta corregir una palabra sin rehacer
la página.

El issue #84 conserva la aprobación formal del PO como pendiente. El equipo
decidió comenzar la implementación usando esta decisión como línea técnica
provisional. Si el PO solicita un cambio, debe registrarse en este ADR antes de
modificar las historias dependientes.

## Decisión

### Composición por capas

La página final se obtiene al combinar:

1. La imagen original de `ComicPage.image`.
2. Una imagen limpia, que se añadirá en HU-88.
3. Los textos traducidos y sus propiedades de maquetación, que se añadirán en
   HU-87 y HU-89.

### Flujo

El workspace evoluciona por cuatro pasos que permiten volver atrás:

1. Detección.
2. Traducción.
3. Maquetación.
4. Exportación.

HU-85 añade regiones omitidas por el OCR y HU-86 permite eliminar falsos
positivos o conservar texto sin traducir.

### Coordenadas y renderizado

- Todas las coordenadas se guardan en píxeles de la imagen original.
- El navegador solo transforma esas coordenadas para el zoom.
- El ajuste del texto se calcula en el servidor con Pillow.
- La vista previa y la exportación comparten el mismo algoritmo.
- Las fuentes deben tener licencia SIL OFL 1.1 y vivir en `static/fonts/`.

### Procesamiento

- La limpieza de páginas y la generación de ZIP son tareas de Huey.
- Añadir una única región puede ejecutar OCR durante la petición porque solo
  procesa un recorte pequeño.
- Todos los proveedores externos permanecen detrás de adaptadores y las
  pruebas usan proveedores simulados.
- La IA de limpieza es opcional, se aplica región por región y exige aceptar
  o descartar el resultado.

## Orden de implementación

1. HU-85 — Añadir una región manual.
2. HU-86 — Eliminar y marcar “No traducir”.
3. HU-87 — Vista previa traducida.
4. HU-88 — Limpiar el texto original.
5. HU-89 — Editor de maquetación.
6. HU-90 — Exportar PNG en ZIP.
7. HU-91 — Limpieza con IA, opcional y precedida por un spike.

HU-85, HU-86 y HU-87 no dependen entre sí. HU-88 depende de HU-86; HU-89
depende de HU-87 y HU-88; HU-90 depende de HU-89; HU-91 depende de HU-88.

## Consecuencias

- Se amplía el alcance del producto con RF-15.
- HU-27 y HU-28 conservarán DOCX y ganarán un segundo formato en HU-90.
- El estado “Completado” tendrá que considerar la maquetación cuando la épica
  esté completa; hasta entonces se conserva la regla actual de HU-26.
- Pillow sigue siendo la única dependencia obligatoria de imagen.
- OpenCV solo puede incorporarse si el spike de HU-91 lo justifica y pasa la
  auditoría de dependencias.

## Validación pendiente

- [ ] Aprobación formal del Product Owner.
- [ ] Actualización de RF-15 y del alcance en la Wiki.
- [ ] Confirmación de las fuentes y sus licencias antes de HU-87.
- [ ] Decisión del proveedor para HU-91 después del spike.
