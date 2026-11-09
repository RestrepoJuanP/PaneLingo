# Casos de prueba — HU-86 Gestionar regiones detectadas

## Trazabilidad

| CP | Criterio | Prueba automática |
|---|---|---|
| CP-86.1 | Eliminar un falso positivo y renumerar | `DeleteRegionTests.test_delete_removes_the_region_and_renumbers_the_following_ones` |
| CP-86.2 | Deshacer conserva todos los datos | `DeleteRegionTests.test_undo_restores_every_edit_and_the_original_reading_order` |
| CP-86.3 | «No traducir» excluye de IA, aprobación y exportación | `SkipTranslationTests.test_skipped_region_keeps_source_and_is_excluded_from_every_flow` |
| CP-86.4 | Volver a traducir deja la región pendiente | `SkipTranslationTests.test_enable_translation_returns_an_empty_pending_region` |
| CP-86.5 | Vaciar texto y conservar original son decisiones distintas | `SkipTranslationTests.test_empty_text_and_skip_translation_remain_distinct_decisions` |
| CP-86.6 | Una región ajena responde 404 | `RegionManagementAccessTests.test_foreign_region_actions_return_not_found_without_changes` |

## Notas de implementación

- La región eliminada se guarda en la sesión con texto OCR, corrección,
  traducción, fechas, estado, coordenadas y orden de lectura.
- La instantánea incluye una huella del estado posterior de la página. Cualquier
  cambio antes de pulsar «Deshacer» invalida la restauración para no sobrescribir
  trabajo nuevo.
- `skip_translation` es distinto de una corrección vacía: el primero conserva
  el dibujo original; la segunda indica que la zona deberá limpiarse sin escribir
  traducción.
- Las cuatro acciones son `POST`, usan CSRF y verifican al propietario de la
  página; los objetos de otra cuenta responden 404.
