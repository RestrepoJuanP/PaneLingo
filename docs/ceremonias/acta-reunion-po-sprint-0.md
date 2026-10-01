# Acta de reunión con el Product Owner — Sprint 0

| Campo | Valor |
|---|---|
| Proyecto | PaneLingo — Proyecto Integrador 2 |
| Ceremonia | Validación del prototipo con el Product Owner |
| Sprint | 0 |
| Fecha | 4 de agosto de 2026 |
| Modalidad | Videollamada |
| Duración | Aproximadamente 13 minutos |
| Asistentes | Equipo de PaneLingo y el Product Owner, Juan Sebastián López |
| Evidencia | Transcripción conservada por el equipo |

## 1. Problema y solución propuesta

El equipo presentó la problemática: quien traduce cómics, manga o webtoons reparte su trabajo entre varias herramientas. Guarda en carpetas las páginas traducidas y las pendientes, edita las burbujas en programas como Photoshop y lleva las transcripciones en otros documentos.

PaneLingo propone una plataforma web que centralice esas tareas: guardar el avance en un único lugar, saber qué páginas faltan, editar y traducir sin cambiar de herramienta.

## 2. Recorrido por el prototipo

Se mostró el mockup de alta fidelidad:

- Inicio de sesión, creación de cuenta y acceso con SSO.
- Panel principal con los álbumes, desde donde se crea un álbum, se suben páginas o se continúa una traducción.
- Creación de álbum con idioma de origen, idioma de destino, tipo de traducción y carga de páginas.
- Detalle del álbum con sus páginas, un resumen del progreso y las opciones de eliminar el álbum o añadir páginas.
- Editor de página con la detección del texto, la propuesta de traducción, la opción de reintentar con IA y la edición manual.
- Revisión general de los álbumes con el desglose del trabajo.
- Carga y escaneo de páginas, perfil, preferencias de idioma y trabajo en equipo.

## 3. Enfoque tecnológico

- OCR para detectar los textos de cada página.
- Traducción asistida con IA que tenga en cuenta el contexto de la obra, incluido el lenguaje coloquial habitual en el manga.
- La traducción generada es una **pretraducción** que el traductor revisa; no pretende ser la versión final.

## 4. Contexto de trabajo del Product Owner

El Product Owner, traductor e intérprete profesional, describió las herramientas que usa hoy:

- InDesign para colocar los textos.
- Photoshop para limpiar las páginas.
- Una aplicación aparte para colocar los guiones.
- Un OCR cuando no reconoce algún carácter.

## 5. Observaciones del Product Owner

1. **Página en blanco.** Poder obtener la página limpia, con las burbujas o los cuadros de texto en blanco y en su color original, para guardarla o añadir el texto después. Es especialmente útil cuando el texto está muy deformado y hay que tratarlo con un programa especializado como Photoshop.
2. **Fuentes tipográficas.** Ofrecer fuentes de cómic gratuitas que sirvan de alternativa a las de pago, como Comicraft, BadaBoom, Victory Speech o Tight BB, y permitir que el usuario suba las fuentes de pago para las que tenga licencia.
3. **Traducción con IA sin selector de estilo.** La aplicación no debería pedir un tipo o estilo de traducción. Debería haber un único bloque de traducción en el que la IA lea el contexto, por ejemplo para tratar las onomatopeyas japonesas, y traduzca de forma lineal. Las instrucciones de estilo pueden desviar a la IA.

Sobre el enfoque general, el Product Owner considera que el problema está bien planteado y que lo que falta son detalles. Destacó como más importantes las fuentes y la página en blanco, para que el usuario no tenga que recurrir a otras herramientas.

## Compromisos

| # | Compromiso | Responsable | Plazo |
|---|---|---|---|
| 1 | Evaluar e incorporar al backlog la opción de página en blanco | Equipo | Sprints posteriores |
| 2 | Evaluar e incorporar al backlog el uso y la carga de fuentes tipográficas | Equipo | Sprints posteriores |
| 3 | Plantear la traducción con IA como un único bloque, sin selector de estilo | Equipo | Al diseñar la traducción asistida |

## Seguimiento

- El tercer compromiso ya se aplicó: el formulario de creación de álbum omite el estilo de traducción que aparecía en el mockup, y la historia HU-16 (#16) lo recoge como criterio de aceptación.
- Los dos primeros implican editar la imagen de la página, algo que el alcance del producto mínimo viable deja fuera. Quedan pendientes de una épica posterior y relacionados con la exportación (HU-27, #27).
