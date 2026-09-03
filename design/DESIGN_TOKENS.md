# PaneLingo — Tokens de diseño

Fuente de verdad visual del proyecto. Extraído de [`PaneLingo.dc.html`](PaneLingo.dc.html), el mockup de alta fidelidad aprobado por el Product Owner.

**Lee este archivo antes de maquetar cualquier pantalla.** Declara estos tokens como variables CSS en `:root` dentro de la hoja de estilos base. Los nombres de variable son la referencia única: no uses valores hex, tamaños ni radios sueltos en las plantillas.

Regla: **un token = un valor CSS único**. Donde el mockup usa dos medidas cercanas con intención distinta, existen dos tokens con nombres distintos. No inventes valores intermedios.

---

## Color — marca y acento

| Token | Valor | Uso en el mockup |
|---|---|---|
| `--brand` | `#4c3fd9` | Color primario: botones, enlaces, foco, barras de progreso, acentos de icono |
| `--brand-hover` | `#3f34bb` | Hover del botón primario; también texto sobre fondos violeta claros |
| `--brand-light` | `#8d7bf0` | Extremo claro de degradados de marca |
| `--brand-deep` | `#2b2560` | Extremo oscuro de degradados de marca |
| `--brand-tint` | `#eef0ff` | Fondo de chip "en progreso" |
| `--brand-tint-2` | `#f5f3ff` | Hover de zonas de carga (dropzone) |
| `--brand-surface` | `#faf7ff` | Fondo de panel informativo de marca |
| `--brand-surface-border` | `#e0daf8` | Borde de ese panel |
| `--accent` | `#f2765a` | Coral: CTA destacado, cifras del hero, etiquetas kicker |
| `--accent-hover` | `#e4674b` | Hover del CTA coral |
| `--accent-ink` | `#231a17` | Texto sobre fondo coral |

## Color — texto

| Token | Valor | Uso | Contraste sobre `--surface` / `--bg` |
|---|---|---|---|
| `--ink-900` | `#191821` | Texto principal, bordes de viñeta, fondo del toast | 17.6:1 / 16.3:1 |
| `--ink-800` | `#2b2740` | Texto de botones secundarios | 13.6:1 / 12.6:1 |
| `--ink-700` | `#3a3730` | Etiquetas de formulario, énfasis medio | 11.9:1 / 11.0:1 |
| `--ink-600` | `#4a463d` | Texto de checkbox y descripciones | 9.4:1 / 8.7:1 |
| `--ink-500` | `#5a5548` | Texto terciario, chip neutro | 7.4:1 / 6.9:1 |
| `--muted` | `#6f6a60` | **Texto secundario por defecto** (ver regla de contraste) | 5.4:1 / 5.0:1 |
| `--muted-2` | `#8a8478` | Solo iconografía y elementos decorativos (ver regla de contraste) | 3.7:1 / 3.4:1 |
| `--muted-3` | `#a09a8e` | Solo elementos decorativos (ver regla de contraste) | 2.8:1 / 2.6:1 |

## Color — superficies

| Token | Valor | Uso |
|---|---|---|
| `--bg` | `#f7f6f3` | Fondo de la aplicación |
| `--surface` | `#ffffff` | Tarjetas, barra lateral, inputs, modales |
| `--surface-subtle` | `#fbfaf7` | Estado vacío, dropzone, pie de modal |
| `--surface-subtle-2` | `#faf9f6` | Panel interior de la barra lateral |
| `--surface-muted` | `#f2f0ea` | Hover de navegación, chip neutro |
| `--surface-muted-2` | `#f4f2ec` | Hover de ítems de menú, botón de cierre del modal |
| `--surface-muted-3` | `#efece5` | Contenedor del selector de pestañas de autenticación |
| `--surface-navy` | `#1b1836` | Panel oscuro del hero, banda destacada, barra de selección |
| `--surface-black` | `#17161a` | Contorno del lettering de cómic |
| `--track` | `#eeebe3` | Fondo de barras de progreso y divisores internos |

## Color — bordes y superposiciones

| Token | Valor | Uso |
|---|---|---|
| `--border` | `#e7e3db` | Borde por defecto de tarjetas y paneles |
| `--divider` | `#e2ded4` | Separadores y bordes de menú desplegable |
| `--border-strong` | `#ddd8ce` | Borde de inputs y botones secundarios |
| `--border-hover` | `#bdb7aa` | Hover del borde de botones secundarios |
| `--border-dashed` | `#c6c0b3` | Zonas de carga punteadas |
| `--border-dashed-soft` | `#d5d0c4` | Estado vacío punteado |
| `--border-dashed-faint` | `#c9c4b8` | Marcos ilustrativos del estado vacío |
| `--focus-ring` | `rgba(76,63,217,.12)` | Halo de foco (`0 0 0 3px`) |
| `--overlay` | `rgba(25,24,33,.45)` | Fondo de modal (con `blur(3px)`) |

## Color — semánticos de estado

| Token | Valor | Uso |
|---|---|---|
| `--success` | `#2f7d4f` | Barra e indicador de éxito |
| `--success-fg` | `#215c3a` | Texto de chip "Completado" (7.1:1 sobre `--success-bg`) |
| `--success-bg` | `#eaf6ee` | Fondo de chip de éxito |
| `--success-border` | `#dfe9e2` | Borde de chip de éxito |
| `--warning` | `#f2b23a` | Barra de advertencia |
| `--warning-fg` | `#8a5b12` | Texto de chip "Borrador" / "Revisar" (5.4:1 sobre `--warning-bg`) |
| `--warning-bg` | `#fff5e0` | Fondo de chip de advertencia |
| `--warning-border` | `#f2e2b4` | Borde de chip de advertencia |
| `--warning-border-strong` | `#f0d99c` | Borde de badge de advertencia sobre miniatura |
| `--danger` | `#b13c22` | Texto y botón destructivo (5.2:1 sobre `--danger-bg`) |
| `--danger-strong` | `#d9482b` | Icono circular de error |
| `--danger-fg` | `#8c2f1a` | Texto dentro de la alerta de error |
| `--danger-bg` | `#fdece7` | Fondo de alerta y chip de error |
| `--danger-border` | `#f3c4b8` | Borde de alerta de error |
| `--danger-border-soft` | `#f0d6cd` | Borde de botón destructivo secundario |
| `--danger-deep` | `#7a2a17` | Fondo del toast de error |
| `--neutral-bar` | `#c8c3b7` | Barra de progreso en estado neutro o sin datos |

## Sombras

| Token | Valor | Uso |
|---|---|---|
| `--shadow-card-hover` | `0 10px 26px rgba(25,24,33,.11)` | Hover de tarjeta de álbum |
| `--shadow-tile-hover` | `0 8px 20px rgba(25,24,33,.10)` | Hover de miniatura de página |
| `--shadow-menu` | `0 14px 34px rgba(25,24,33,.16)` | Menú contextual "···" |
| `--shadow-modal` | `0 26px 70px rgba(0,0,0,.30)` | Modales |
| `--shadow-toast` | `0 16px 40px rgba(0,0,0,.24)` | Toast |

---

## Tipografía — familias y pesos

| Familia | Pesos | Uso |
|---|---|---|
| **Plus Jakarta Sans** (`'Plus Jakarta Sans', system-ui, sans-serif`) | 400, 500, 600, 700, 800 | Toda la interfaz. 400 párrafos largos · 500 texto de apoyo · 600 etiquetas, navegación y botones secundarios · 700 títulos de sección y botones primarios · 800 títulos de página y cifras destacadas |
| **Archivo** (`Archivo, sans-serif`) | 500, 700 | Lettering de cómic: onomatopeyas, cajas de narración de las ilustraciones, etiquetas de par de idiomas en mayúsculas |
| **Zen Kaku Gothic New** | 500, 700 | Texto fuente en japonés dentro de las viñetas (decorativo en Sprint 1) |
| **Noto Sans KR** | 500, 700 | Texto fuente en coreano dentro de las viñetas (decorativo en Sprint 1) |

Las cuatro se cargan desde Google Fonts con `preconnect` a `fonts.googleapis.com` y `fonts.gstatic.com`. Define siempre una pila de reserva (`system-ui, sans-serif`).

Tokens de familia:

| Token | Valor |
|---|---|
| `--font-ui` | `'Plus Jakarta Sans', system-ui, sans-serif` |
| `--font-comic` | `Archivo, system-ui, sans-serif` |
| `--font-ja` | `'Zen Kaku Gothic New', system-ui, sans-serif` |
| `--font-ko` | `'Noto Sans KR', system-ui, sans-serif` |

## Tipografía — escala (un valor por token)

| Token | Valor | Peso habitual | Uso |
|---|---|---|---|
| `--fs-hero` | `clamp(26px, 3vw, 38px)` | 800 | Titular del panel de autenticación |
| `--fs-h1` | `clamp(21px, 2.4vw, 28px)` | 800 | Título de pantalla |
| `--fs-stat` | `25px` | 800 | Cifra destacada de tarjeta de estadística |
| `--fs-h2` | `24px` | 700 | Título del formulario de autenticación |
| `--fs-wordmark` | `19px` | 800 | Logotipo en el panel de autenticación |
| `--fs-modal-title` | `18px` | 700 | Título del modal de creación |
| `--fs-section` | `17px` | 700–800 | Título de sección del dashboard, título del modal de confirmación, logotipo de la barra lateral |
| `--fs-subsection` | `16px` | 700 | Título de subsección dentro del detalle de álbum |
| `--fs-lead` | `15px` | 700 | Título de estado vacío y de dropzone |
| `--fs-card-title` | `14.5px` | 700 | Título de tarjeta de álbum |
| `--fs-body` | `13.5px` | 400–500 | Párrafos e inputs |
| `--fs-ui` | `13px` | 600–700 | Botones y navegación lateral |
| `--fs-sm` | `12.5px` | 500–600 | Texto de apoyo, ítems de menú, toast |
| `--fs-label` | `12px` | 600 | Etiquetas de formulario de autenticación, filtros |
| `--fs-label-sm` | `11.5px` | 600 | Etiquetas de formulario en modal, metadatos de tarjeta |
| `--fs-xs` | `11px` | 500–700 | Texto de menor jerarquía, chip de estado del detalle |
| `--fs-badge` | `10.5px` | 700 | Píldoras de estado sobre portada, badge de navegación |
| `--fs-micro` | `9.5px` | 600–700 | Etiquetas de navegación móvil y micro-badges |

### Interlineado

| Token | Valor | Uso |
|---|---|---|
| `--lh-tight` | `1` | Botones, etiquetas y chips de una sola línea |
| `--lh-heading` | `1.2` | Títulos de h1 a h3 |
| `--lh-title` | `1.3` | Títulos de tarjeta y textos cortos de dos líneas |
| `--lh-snug` | `1.4` | Metadatos y textos de badge |
| `--lh-body` | `1.5` | Párrafos de interfaz |
| `--lh-relaxed` | `1.6` | Párrafos largos y explicativos |

### Interletrado

| Token | Valor | Uso |
|---|---|---|
| `--ls-hero` | `-.03em` | `--fs-hero`, `--fs-h1`, `--fs-stat` |
| `--ls-heading` | `-.02em` | `--fs-h2`, `--fs-modal-title`, `--fs-section`, `--fs-subsection` |
| `--ls-title` | `-.01em` | `--fs-card-title` |
| `--ls-caps` | `.08em` | Etiquetas en mayúsculas (kicker) |
| `--ls-caps-tight` | `.06em` | Etiquetas de par de idiomas en Archivo |

---

## Radios de borde (un valor por token)

| Token | Valor | Uso |
|---|---|---|
| `--r-xs` | `4px` | Casillas de verificación, barras de progreso |
| `--r-thumb` | `5px` | Miniaturas de la cola de carga, marcos ilustrativos del estado vacío |
| `--r-badge` | `6px` | Badges pequeños sobre miniatura, cuadros de icono de navegación |
| `--r-sm` | `7px` | Botones de icono, avatar, botón "Renombrar" |
| `--r-menu` | `8px` | Ítems de menú desplegable, botones compactos, botón de cierre del modal |
| `--r-md` | `9px` | Ítems de la navegación lateral, badge del header, miniatura de portada del álbum |
| `--r-lg` | `10px` | **Radio por defecto de controles:** botones e inputs |
| `--r-option` | `11px` | Tarjetas de opción seleccionable, contenedor de pestañas de autenticación |
| `--r-xl` | `12px` | Toast, barra de selección, tarjeta de página, menú contextual, panel de la barra lateral |
| `--r-2xl` | `14px` | Tarjetas de panel y de estadística |
| `--r-3xl` | `16px` | Tarjetas de álbum, dropzone, estado vacío |
| `--r-modal` | `18px` | Diálogos modales |
| `--r-pill` | `20px` | Chips, filtros y píldoras de estado |
| `--r-full` | `50%` | Puntos indicadores, spinners, avatares circulares |

---

## Escala de espaciado

Base de 4px, con los pasos impares heredados del mockup. Un valor por token.

| Token | Valor | Uso |
|---|---|---|
| `--sp-1` | `4px` | Separación mínima entre elementos pegados |
| `--sp-2` | `6px` | Gap de filtros y chips |
| `--sp-3` | `8px` | Gap general de iconos y botones adyacentes |
| `--sp-4` | `9px` | Gap por defecto entre botones e ítems de lista |
| `--sp-5` | `11px` | Gap de navegación; padding vertical de inputs |
| `--sp-6` | `12px` | Padding de tarjetas compactas; gap de la grilla de estadísticas |
| `--sp-7` | `14px` | Gap de la grilla de páginas; padding de tarjeta de álbum |
| `--sp-8` | `16px` | Gap de la grilla de álbumes; separación entre bloques |
| `--sp-9` | `18px` | Padding de contenedores medianos |
| `--sp-10` | `22px` | Separación entre secciones |
| `--sp-11` | `26px` | Separación entre bloques de encabezado |
| `--sp-12` | `30px` | Padding máximo de página |

## Medidas de layout

| Token | Valor |
|---|---|
| `--pad-page` | `clamp(16px, 2.4vw, 30px)` |
| `--pad-header` | `12px clamp(14px, 2.2vw, 26px)` |
| `--pad-auth-panel` | `clamp(24px, 3.4vw, 52px)` |
| `--w-sidebar` | `246px` (padding interno `18px 14px`) |
| `--w-auth-form` | `394px` |
| `--w-modal` | `520px` |
| `--w-modal-sm` | `410px` |
| `--pad-btn` | `11px 16px` (primario) |
| `--pad-btn-secondary` | `11px 15px` |
| `--pad-input` | `11px 13px` |
| `--pad-chip` | `4px 9px` |
| `--pad-filter` | `7px 12px` |
| `--ratio-page` | `3 / 4.24` (miniatura de página) |

## Grillas

| Contexto | Definición |
|---|---|
| Álbumes | `repeat(auto-fill, minmax(252px, 1fr))`, `gap: var(--sp-8)` |
| Páginas | `repeat(auto-fill, minmax(146px, 1fr))`, `gap: var(--sp-7)` |
| Estadísticas | `repeat(auto-fit, minmax(178px, 1fr))`, `gap: var(--sp-6)` |

---

## Desviaciones deliberadas respecto al mockup

El mockup es la referencia visual, pero la wiki declara **WCAG 2.1 nivel AA** como requisito no funcional del sistema. Donde ambos entran en conflicto, gana la accesibilidad. Estas son las desviaciones acordadas:

### 1. Contraste de los grises claros

Contrastes medidos sobre `--surface` (`#ffffff`) y sobre `--bg` (`#f7f6f3`):

| Token | Hex | Sobre `--surface` | Sobre `--bg` | ¿Cumple AA para texto pequeño (4.5:1)? |
|---|---|---|---|---|
| `--muted` | `#6f6a60` | 5.38:1 | 4.97:1 | Sí |
| `--muted-2` | `#8a8478` | 3.72:1 | 3.44:1 | **No** |
| `--muted-3` | `#a09a8e` | 2.80:1 | 2.59:1 | **No** |

El mockup usa `--muted-2` y `--muted-3` para metadatos de tarjeta, etiquetas de estadística y textos tipo "Editado hace 2 horas", todos entre 11px y 12.5px. **En nuestra implementación esos textos usan `--muted`.**

Regla operativa:

- Cualquier texto por debajo de 14px usa `--muted` (`#6f6a60`) o un tono más oscuro de la escala `--ink-*`.
- `--muted-2` y `--muted-3` quedan reservados para iconografía, bordes, separadores y elementos decorativos.
- Nota sobre "texto grande": WCAG define texto grande como ≥24px normal o ≥18.66px en negrita, no 18px. Como la escala tipográfica de PaneLingo no supera los 17px fuera de los títulos `--fs-hero`, `--fs-h1`, `--fs-stat` y `--fs-h2` (que nunca usan grises claros), en la práctica **`--muted-2` y `--muted-3` no se usan para texto en ninguna pantalla**.
- El cambio es visualmente sutil: `#6f6a60` frente a `#8a8478` mantiene la misma jerarquía percibida de gris secundario sobre el fondo arena.

Los demás tokens de texto y las parejas de estado (`--success-fg` sobre `--success-bg` 7.1:1, `--warning-fg` sobre `--warning-bg` 5.4:1, `--danger` sobre `--danger-bg` 5.2:1, blanco sobre `--brand` 6.95:1, `--accent-ink` sobre `--accent` 6.1:1, blanco sobre `--danger` 5.9:1) cumplen AA sin ajustes.

### 2. Anillo de foco

`--focus-ring` (`rgba(76,63,217,.12)`) es el halo suave del mockup, pensado solo para el estado de foco de inputs acompañado de un cambio de `border-color` a `--brand`. Por sí solo no alcanza los 3:1 que AA exige para indicadores no textuales. En `:focus-visible` se combina siempre con un contorno sólido:

```css
:focus-visible {
  outline: 2px solid var(--brand);
  outline-offset: 2px;
  box-shadow: 0 0 0 3px var(--focus-ring);
}
```

### 3. Idioma de la interfaz

El mockup está redactado en inglés. La interfaz de PaneLingo va en **español**, porque los casos de prueba de la wiki referencian los rótulos en español ("Crear cuenta", "Cargar página", "Eliminar", "Cancelar"). Los tokens y los identificadores de código siguen en inglés.
