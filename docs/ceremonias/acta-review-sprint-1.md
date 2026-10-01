# Acta de Sprint Review — Sprint 1

| Campo | Valor |
|---|---|
| Proyecto | PaneLingo — Proyecto Integrador 2 |
| Ceremonia | Sprint Review |
| Sprint | 1 |
| Fecha | 9 de septiembre de 2026 |
| Grabación | Entregada en el formulario habilitado por el docente |
| Estado del sprint | Cerrado |

## Asistentes

| Integrante | Rol |
|---|---|
| Juan Sebastián Lopez | Product Owner |
| Tomás Sepúlveda Franco | Líder del proyecto / Scrum Master |
| Sebastian Salazar Henao | Desarrollador frontend |
| Simon Mazo Gomez | Desarrollador backend |
| Andres Felipe Velez | Responsable de OCR e IA |
| Juan Pablo Restrepo | Diseñador UX/UI |

## Objetivo del sprint

> Habilitar el acceso del usuario, la creación y configuración de proyectos, y la gestión inicial de páginas, incluyendo su carga y eliminación.

## Resultados presentados al Product Owner

Se demostró la aplicación en funcionamiento con las diez historias comprometidas:

| HU | Funcionalidad demostrada |
|---|---|
| HU-01 | Crear cuenta con validación completa y acceso automático tras el registro |
| HU-02 | Iniciar sesión por correo, con mensaje de error que no revela si la cuenta existe |
| HU-03 | Cerrar sesión y bloqueo de las vistas privadas |
| HU-04 | Recuperar contraseña en cuatro pantallas, con enlace de un solo uso que caduca en una hora |
| HU-05 | Crear álbum, con biblioteca de tarjetas y portada propia |
| HU-06 | Título del álbum, con validación y renombrado rápido |
| HU-07 | Idiomas de origen y destino, con la regla de que deben ser distintos |
| HU-08 | Detalle del álbum y edición de su información |
| HU-09 | Carga múltiple de páginas, con validación real de imagen y miniaturas |
| HU-10 | Eliminar páginas, con confirmación y limpieza de los archivos en disco |

Indicadores presentados:

- 10 de 10 historias de usuario entregadas.
- 20 de 20 casos de prueba ejecutados, cubiertos además por 227 pruebas automáticas.
- Quality Gate de 7 pasos en verde en las 14 etapas del sprint.
- 2 errores detectados, corregidos y cerrados durante el sprint (BUG-043 y BUG-046).

## Observaciones del Product Owner y compromisos

El Product Owner aceptó el avance presentado y solicitó dos funcionalidades para mejorar la comodidad de uso:

| # | Compromiso | Tipo | Estado | Responsable |
|---|---|---|---|---|
| 1 | Búsqueda de los álbumes del usuario por título | Historia nueva | Por dar de alta en el backlog | Por asignar en la planificación del Sprint 2 |
| 2 | Edición de la imagen de portada de cada álbum | Historia nueva | Por dar de alta en el backlog | Por asignar en la planificación del Sprint 2 |

## Decisiones que quedaron abiertas para el Product Owner

El equipo planteó estos puntos y se acordó que los decide el Product Owner antes de planificarlos:

1. ¿El estado del álbum se deriva del avance o lo declara el usuario como etiqueta?
2. ¿Se construyen los filtros de la biblioteca? Dependen de la decisión anterior.
3. ¿Se habilita la eliminación de álbumes? Hoy el botón está visible y deshabilitado.
4. ¿Se permite reordenar o insertar páginas? Hoy no se renumera al borrar, así que pueden quedar huecos.
5. ¿Se construyen el perfil y las preferencias del usuario?
6. Alcance de la exportación: el Product Owner espera imágenes PNG con la traducción insertada, pero el alcance del producto mínimo viable contempla exportar el texto por región, sin recomponer la imagen.

## Deudas técnicas registradas

| ID | Deuda | Gravedad | Momento de resolverla |
|---|---|---|---|
| DT-01 | Sin pruebas de navegador para el JavaScript | Media | Cuando se decida el stack de pruebas de cliente |
| DT-02 | Los archivos de `media/` no tienen control de acceso | Alta | Antes del primer despliegue |
| DT-03 | Umbral de baja resolución sin calibrar | Baja | Cuando exista el OCR |
| DT-04 | Cuatro advertencias de HTTPS en `check --deploy` | Alta | Antes del primer despliegue |
| DT-05 | Sin paginación en la biblioteca ni en la rejilla de páginas | Media | Cuando un álbum supere las 100 páginas |
| DT-06 | Sin límite de archivos por lote de carga | Baja | Junto con DT-05 |

## Fuera del alcance del Sprint 1

OCR, detección de burbujas, traducción con inteligencia artificial, espacio de trabajo de traducción, exportación, eliminación de álbumes, colaboración en equipo, envío real de correo en producción y pagos.

## Acuerdos de cierre

1. El Sprint 1 se cierra con las diez historias comprometidas terminadas y sus casos de prueba ejecutados.
2. Las dos funcionalidades solicitadas por el Product Owner entran al backlog como historias nuevas, pendientes de estimar en la planificación del Sprint 2.
3. Las seis decisiones abiertas se resuelven con el Product Owner antes de planificar las historias que dependen de ellas.
4. DT-02 y DT-04 se resuelven antes de cualquier despliegue.
