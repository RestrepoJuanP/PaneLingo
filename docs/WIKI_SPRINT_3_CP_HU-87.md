# Casos de prueba — HU-87 Vista previa de la página traducida

## Trazabilidad

| CP | Criterio | Prueba automática |
|---|---|---|
| CP-87.1 | Alternar «Original / Traducida» y recordar elección | `TranslatedPreviewTests.test_original_and_translated_selector_controls_the_decorative_layer` |
| CP-87.2 | Ajustar texto, respetar 8 px y avisar desborde | `FitTextTests` y `TranslatedPreviewTests.test_long_and_impossible_text_are_reflowed_or_warned` |
| CP-87.3 | Comic Neue regular/cursiva y caracteres españoles | `TranslatedPreviewTests.test_dialogue_and_narration_use_local_comic_neue_variants` |
| CP-87.4 | Actualizar tras autoguardado sin recargar | `TranslatedPreviewTests.test_translation_autosave_returns_and_renders_a_new_preview` |
| CP-87.5 | Diferenciar sin traducir de «No traducir» | `TranslatedPreviewTests.test_untranslated_uses_source_and_skipped_region_has_no_overlay` |
| CP-87.6 | Escalar con −, + y Ajustar | `TranslatedPreviewTests.test_preview_font_uses_container_units_and_shares_the_zoom_target` |
| CP-87.7 | Selector por teclado y capa decorativa | `TranslatedPreviewTests.test_selector_is_keyboard_operable_and_preview_is_not_announced_twice` |

## Fuentes

- Comic Neue Regular, Bold e Italic desde Google Fonts.
- Bangers Regular queda disponible para onomatopeyas de la maquetación.
- Ambas familias incluyen su aviso SIL Open Font License 1.1 en
  `static/fonts/`.
