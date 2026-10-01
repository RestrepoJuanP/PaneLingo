# Acta de Sprint Review — Sprint 1

| Campo | Valor |
|---|---|
| Proyecto | PaneLingo — Proyecto Integrador 2 |
| Ceremonia | Sprint Review |
| Sprint | 1 |
| Fecha | 9 de septiembre de 2026 |
| Modalidad | Videollamada |
| Duración | Aproximadamente 12 minutos |
| Grabación | Entregada en el formulario habilitado por el docente |

## Asistentes

| Integrante | Rol |
|---|---|
| Juan Sebastián Lopez | Product Owner |
| Tomás Sepúlveda Franco | Líder del proyecto / Scrum Master |
| Sebastian Salazar Henao | Desarrollador frontend |
| Simon Mazo Gomez | Desarrollador backend |
| Andres Felipe Velez | Responsable de OCR e IA |
| Juan Pablo Restrepo | Diseñador UX/UI |

## 1. Contexto del producto

El equipo recordó el problema que resuelve PaneLingo: los traductores de cómics usan varios programas desconectados para traducir, guardar y editar. PaneLingo los integra en una sola herramienta y conserva el trabajo para poder retomarlo.

## 2. Alcance del Sprint 1

Se presentaron las historias comprometidas, agrupadas por épica:

| Épica | Historias |
|---|---|
| EP-01 Gestión de acceso y cuenta | HU-01 Crear cuenta · HU-02 Iniciar sesión · HU-03 Cerrar sesión · HU-04 Recuperar contraseña |
| EP-02 Gestión de álbumes y proyectos | HU-05 Crear álbum · HU-06 Título del álbum · HU-07 Idiomas del álbum · HU-08 Editar álbum |
| EP-03 Gestión de páginas | HU-09 Cargar páginas · HU-10 Eliminar páginas |

## 3. Demostración en vivo

| Qué se mostró | HU |
|---|---|
| Pantalla de inicio de sesión y creación de cuenta | HU-01, HU-02 |
| Registro de una cuenta nueva, con contraseña de mínimo 8 caracteres y medidor de seguridad; mensaje de bienvenida con el nombre del usuario | HU-01 |
| Opciones de la interfaz marcadas como "próximo sprint", visibles pero sin implementar | — |
| Creación del álbum "Prueba", de japonés a español; la tarjeta muestra título, número de páginas y par de idiomas, con mensaje de confirmación | HU-05, HU-06, HU-07 |
| Renombrado del álbum desde su tarjeta | HU-06 |
| Opciones de edición del álbum en su detalle, como cambiar los idiomas | HU-08 |
| Carga de varias imágenes a la vez, con la cola de archivos seleccionados, el aviso de baja resolución y las páginas visibles después en el álbum | HU-09 |
| Acceso a la carga desde el botón "Cargar páginas" del menú, que lleva al mismo flujo | HU-09 |

Se presentaron como implementadas, pero no se demostraron de forma explícita en la reunión: iniciar sesión con una cuenta existente (HU-02), cerrar sesión (HU-03), recuperar contraseña (HU-04) y eliminar páginas (HU-10).

## 4. Prueba realizada por el Product Owner

El Product Owner pidió poner como título del álbum "Prueba" un texto largo con caracteres de idiomas asiáticos, que envió por la llamada. **El título se guardó y se mostró correctamente**, sin caracteres rotos.

Motivo de la prueba: si una aplicación no soporta los caracteres del japonés, el chino o el coreano, se muestran como cuadros vacíos.

## 5. Observaciones del Product Owner

1. **Sobre lo implementado:** no tiene observaciones. Considera que el avance está bien para el alcance del sprint y que las dificultades aparecerán cuando avance el proyecto.
2. **Imagen de portada:** preguntó si la imagen de portada del álbum se puede cambiar. Hoy es una imagen fija que el usuario no puede modificar.
3. **Búsqueda de álbumes:** con muchos trabajos, encontrar uno es difícil. Explicó que hoy tiene más de 200 trabajos en su computador, que muchos títulos tienen caracteres complejos o empiezan por la misma palabra, y que para encontrarlos depende de la vista previa de Windows que muestra la primera página. Propone poder buscar por título o reconocer los álbumes por su imagen.

El equipo coincidió en que ambas mejoras hacen la herramienta más intuitiva cuando el usuario tiene muchos proyectos.

## 6. Aclaraciones del equipo

1. Los cambios acordados en la primera reunión con el Product Owner, el 4 de agosto, como el OCR y la opción de dejar las páginas en blanco, corresponden a un sprint posterior.
2. Un integrante propuso adelantar lo previsto para el siguiente sprint; se acordó presentarlo en la próxima review.

## Compromisos

| # | Compromiso | Origen | Plazo | Seguimiento |
|---|---|---|---|---|
| 1 | Permitir cambiar la imagen de portada de cada álbum | Solicitud del Product Owner | Implementación futura | HU-49 (#49) |
| 2 | Buscar los álbumes del usuario por título | Solicitud del Product Owner | Implementación futura | HU-50 (#50) |
| 3 | Presentar el alcance del siguiente sprint | Equipo | Próxima review | — |

## Acuerdos

1. El Product Owner da por bueno el avance del Sprint 1, sin observaciones sobre lo implementado.
2. La portada editable y la búsqueda por título se incorporan al backlog para un sprint futuro.
3. El OCR y la opción de dejar las páginas en blanco se mantienen para un sprint posterior.
