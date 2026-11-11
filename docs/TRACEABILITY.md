# Anexo — Detalle de pruebas automáticas del Sprint 1

> Anexo de la sección [Casos de prueba](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-1#casos-de-prueba) de la página [Sprint 1](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-1). Para cada criterio y caso de prueba indica qué prueba automática lo verifica y en qué etapa quedó su evidencia. Los criterios, los casos de prueba, su ejecución y los bugs están en la página Sprint 1.

Relaciona cada historia de usuario con sus criterios de aceptación, sus casos de prueba, la prueba automática que los verifica y la evidencia del Quality Gate.

**Estado global:** las 10 historias implementadas y sus 20 casos de prueba cubiertos por prueba automática, más 23 casos adicionales (21 automáticos, 1 manual y 1 pendiente). 227 pruebas en total, todas en verde.

Los nombres de prueba están tomados del código, no transcritos a mano: el inventario se generó recorriendo los archivos de prueba y leyendo el CP citado en cada docstring.

Al final se añade la épica [EP-08 Edición de imagen](#sprint-3--ep-08-edición-de-imagen) del Sprint 3 (HU-89, HU-90 y HU-91) y la sección de [bugs](#bugs) con el mismo formato. El resto de las historias del Sprint 3 está en el [reporte de pruebas del Sprint 3](WIKI_SPRINT_3_REPORTE_PRUEBAS.md).

---

## HU-01 — Crear cuenta

Issue: [#1](https://github.com/RestrepoJuanP/PaneLingo/issues/1)

> Como traductor, quiero crear una cuenta personal para poder acceder a PaneLingo y gestionar mis proyectos de traducción.

| CA | CP | Prueba automática | Evidencia | Estado |
|---|---|---|---|---|
| CA-01.1 | CP-01.1 | `accounts/tests/test_views.py::RegistrationViewSuccessTests::test_valid_post_creates_exactly_one_user` | [`etapa-03/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-03) | Cubierto |
| CA-01.1 | CP-01.1 | `accounts/tests/test_views.py::RegistrationViewSuccessTests::test_password_is_stored_hashed` | [`etapa-03/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-03) | Cubierto |
| CA-01.1 | CP-01.1 | `accounts/tests/test_views.py::RegistrationViewSuccessTests::test_confirmation_message_is_shown` | [`etapa-03/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-03) | Cubierto |
| CA-01.1 | CP-01.1 | `accounts/tests/test_forms.py::UserRegistrationFormValidTests::test_form_is_valid_with_complete_data` | [`etapa-03/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-03) | Cubierto |
| CA-01.1 | CP-01.1 | `accounts/tests/test_forms.py::UserRegistrationFormValidTests::test_save_hashes_the_password` | [`etapa-03/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-03) | Cubierto |
| CA-01.2 | CP-01.2 | `accounts/tests/test_views.py::RegistrationViewErrorTests::test_missing_required_field_creates_no_user` | [`etapa-03/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-03) | Cubierto |
| CA-01.2 | CP-01.2 | `accounts/tests/test_views.py::RegistrationViewErrorTests::test_field_error_is_rendered_next_to_its_field` | [`etapa-03/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-03) | Cubierto |
| CA-01.2 | CP-01.2 | `accounts/tests/test_views.py::RegistrationViewErrorTests::test_submitted_data_is_kept_except_passwords` | [`etapa-03/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-03) | Cubierto |
| CA-01.2 | CP-01.2 | `accounts/tests/test_views.py::RegistrationViewErrorTests::test_duplicate_email_creates_no_second_user` | [`etapa-03/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-03) | Cubierto |
| CA-01.2 | CP-01.2 | `accounts/tests/test_views.py::RegistrationViewErrorTests::test_unaccepted_terms_creates_no_user` | [`etapa-03/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-03) | Cubierto |
| CA-01.2 | CP-01.2 | `accounts/tests/test_views.py::RegistrationViewErrorTests::test_mismatched_passwords_create_no_user` | [`etapa-03/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-03) | Cubierto |
| CA-01.2 | CP-01.2 | `accounts/tests/test_forms.py::UserRegistrationFormRequiredFieldTests` (3 pruebas) | [`etapa-03/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-03) | Cubierto |
| CA-01.2 | CP-01.2 | `accounts/tests/test_forms.py::UserRegistrationFormValidationTests` (5 pruebas) | [`etapa-03/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-03) | Cubierto |

**Total CP-01.1: 6 pruebas · CP-01.2: 14 pruebas.**

---

## HU-02 — Iniciar sesión

Issue: [#2](https://github.com/RestrepoJuanP/PaneLingo/issues/2)

> Como traductor, quiero iniciar sesión para acceder a mis álbumes y traducciones guardadas.

| CA | CP | Prueba automática | Evidencia | Estado |
|---|---|---|---|---|
| CA-02.1 | CP-02.1 | `accounts/tests/test_views.py::LoginViewTests::test_valid_credentials_authenticate_and_redirect_to_panel` | [`etapa-04/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-04) | Cubierto |
| CA-02.1 | CP-02.1 | `accounts/tests/test_views.py::LoginViewTests::test_login_form_is_shown` | [`etapa-04/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-04) | Cubierto |
| CA-02.2 | CP-02.2 | `accounts/tests/test_views.py::LoginViewTests::test_wrong_password_is_rejected` | [`etapa-04/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-04) | Cubierto |
| CA-02.2 | CP-02.2 | `accounts/tests/test_views.py::LoginViewTests::test_unknown_email_gives_the_same_message_as_a_wrong_password` | [`etapa-04/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-04) | Cubierto |
| CA-02.2 | CP-02.2 | `accounts/tests/test_views.py::LoginViewTests::test_inactive_account_gives_the_same_message` | [`etapa-04/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-04) | Cubierto |

**Total CP-02.1: 2 pruebas · CP-02.2: 3 pruebas.**

Pruebas de apoyo sin CP asociado: `LoginRedirectTests` (4, parámetro `next`) y `RememberMeTests` (3, duración de la sesión).

---

## HU-03 — Cerrar sesión

Issue: [#3](https://github.com/RestrepoJuanP/PaneLingo/issues/3)

> Como traductor, quiero cerrar sesión para proteger el acceso a mi información y proyectos.

| CA | CP | Prueba automática | Evidencia | Estado |
|---|---|---|---|---|
| CA-03.1 | CP-03.1 | `accounts/tests/test_views.py::LogoutViewTests::test_post_ends_the_session_and_redirects_to_login` | [`etapa-05/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-05) | Cubierto |
| CA-03.1 | CP-03.1 | `accounts/tests/test_views.py::LogoutViewTests::test_confirmation_message_is_shown` | [`etapa-05/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-05) | Cubierto |
| CA-03.2 | CP-03.2 | `accounts/tests/test_views.py::LogoutViewTests::test_panel_is_unreachable_after_logging_out` | [`etapa-05/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-05) | Cubierto |
| CA-03.2 | CP-03.2 | `config/tests/test_route_access.py::PrivateRouteAccessTests::test_private_routes_redirect_anonymous_visitors` | [`etapa-05/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-05) | Cubierto |

**Total CP-03.1: 2 pruebas · CP-03.2: 2 pruebas.**

Pruebas de apoyo: GET no cierra la sesión (405), POST sin CSRF rechazado (403), respuesta privada con `Cache-Control: no-store`.

---

## HU-04 — Recuperar contraseña

Issue: [#4](https://github.com/RestrepoJuanP/PaneLingo/issues/4)

> Como traductor, quiero recuperar el acceso a mi cuenta cuando olvide mi contraseña para poder continuar trabajando en mis proyectos.

| CA | CP | Prueba automática | Evidencia | Estado |
|---|---|---|---|---|
| CA-04.1 | CP-04.1 | `accounts/tests/test_password_reset.py::PasswordResetHappyPathTests::test_request_with_a_registered_email_sends_a_message` | [`etapa-06/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-06) | Cubierto |
| CA-04.1 | CP-04.1 | `accounts/tests/test_password_reset.py::PasswordResetHappyPathTests::test_email_carries_a_working_link_and_mentions_the_expiry` | [`etapa-06/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-06) | Cubierto |
| CA-04.1 | CP-04.1 | `accounts/tests/test_password_reset.py::PasswordResetHappyPathTests::test_link_allows_setting_a_new_password` | [`etapa-06/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-06) | Cubierto |
| CA-04.1 | CP-04.1 | `accounts/tests/test_password_reset.py::PasswordResetHappyPathTests::test_the_old_password_stops_working` | [`etapa-06/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-06) | Cubierto |
| CA-04.1 | CP-04.1 | `accounts/tests/test_password_reset.py::PasswordResetHappyPathTests::test_the_user_can_authenticate_with_the_new_password` | [`etapa-06/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-06) | Cubierto |
| CA-04.2 | CP-04.2 | `accounts/tests/test_password_reset.py::PasswordResetUnknownEmailTests` (3 pruebas) | [`etapa-06/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-06) | Cubierto |
| CA-04.2 | CP-04.2 | `accounts/tests/test_password_reset.py::PasswordResetTokenTests` (4 pruebas: reutilizado, manipulado, uid inválido, caducado) | [`etapa-06/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-06) | Cubierto |
| CA-04.2 | CP-04.2 | `accounts/tests/test_password_reset.py::NewPasswordValidationTests` (2 pruebas) | [`etapa-06/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-06) | Cubierto |

**Total CP-04.1: 5 pruebas · CP-04.2: 9 pruebas.**

Prueba de apoyo: `OtherSessionsTests::test_another_open_session_is_invalidated`, que fija una garantía del framework.

---

## HU-05 — Crear álbum

Issue: [#5](https://github.com/RestrepoJuanP/PaneLingo/issues/5)

> Como traductor, quiero crear un álbum para organizar las páginas pertenecientes a un mismo cómic, manga o webtoon.

| CA | CP | Prueba automática | Evidencia | Estado |
|---|---|---|---|---|
| CA-05.1 | CP-05.1 | `albums/tests/test_views.py::AlbumCreateSuccessTests::test_valid_post_creates_one_album_for_the_signed_in_user` | [`etapa-07/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-07) | Cubierto |
| CA-05.1 | CP-05.1 | `albums/tests/test_views.py::AlbumCreateSuccessTests::test_the_new_album_appears_in_the_library` | [`etapa-07/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-07) | Cubierto |
| CA-05.1 | CP-05.1 | `albums/tests/test_views.py::AlbumCreateSuccessTests::test_a_confirmation_message_is_shown` | [`etapa-07/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-07) | Cubierto |
| CA-05.1 | CP-05.1 | `albums/tests/test_forms.py::AlbumFormValidTests::test_form_is_valid_with_complete_data` | [`etapa-07/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-07) | Cubierto |
| CA-05.2 | CP-05.2 | `albums/tests/test_views.py::AlbumCreateErrorTests` (3 pruebas) | [`etapa-07/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-07) | Cubierto |
| CA-05.2 | CP-05.2 | `albums/tests/test_forms.py::AlbumFormValidationTests` (6 pruebas) | [`etapa-07/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-07) | Cubierto |

**Total CP-05.1: 4 pruebas · CP-05.2: 9 pruebas.**

Aislamiento: `AlbumOwnershipTests` (2) y `AlbumLibraryIsolationTests` (2).

---

## HU-06 — Asignar título al álbum

Issue: [#6](https://github.com/RestrepoJuanP/PaneLingo/issues/6)

> Como traductor, quiero asignar un título a un álbum para identificar fácilmente mi proyecto de traducción.

| CA | CP | Prueba automática | Evidencia | Estado |
|---|---|---|---|---|
| CA-06.1 | CP-06.1 | `albums/tests/test_rename.py::AlbumRenameSuccessTests::test_renaming_persists_the_new_title` | [`etapa-08/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-08) | Cubierto |
| CA-06.1 | CP-06.1 | `albums/tests/test_rename.py::AlbumRenameSuccessTests::test_the_new_title_is_shown_in_the_library` | [`etapa-08/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-08) | Cubierto |
| CA-06.1 | CP-06.1 | `albums/tests/test_rename.py::AlbumRenameSuccessTests::test_the_title_is_trimmed_when_renaming` | [`etapa-08/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-08) | Cubierto |
| CA-06.2 | CP-06.2 | `albums/tests/test_rename.py::AlbumRenameErrorTests::test_an_empty_title_is_not_saved` | [`etapa-08/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-08) | Cubierto |
| CA-06.2 | CP-06.2 | `albums/tests/test_rename.py::AlbumRenameErrorTests::test_a_whitespace_only_title_is_not_saved` | [`etapa-08/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-08) | Cubierto |
| CA-06.2 | CP-06.2 | `albums/tests/test_rename.py::AlbumRenameErrorTests::test_an_overlong_title_is_not_saved` | [`etapa-08/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-08) | Cubierto |

**Total CP-06.1: 3 pruebas · CP-06.2: 3 pruebas.**

Escapado: `AlbumTitleEscapingTests` (3, incluido el caso de comillas dobles dentro de `aria-label`). Aislamiento: `AlbumRenameIsolationTests` (4).

---

## HU-07 — Idiomas de origen y destino

Issue: [#7](https://github.com/RestrepoJuanP/PaneLingo/issues/7)

> Como traductor, quiero seleccionar el idioma de origen y el idioma de destino de un álbum para definir cómo se realizará la traducción.

| CA | CP | Prueba automática | Evidencia | Estado |
|---|---|---|---|---|
| CA-07.1 | CP-07.1 | `albums/tests/test_languages.py::LanguagePersistenceTests::test_both_languages_are_stored` | [`etapa-08b/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-08b) | Cubierto |
| CA-07.1 | CP-07.1 | `albums/tests/test_languages.py::LanguagePersistenceTests::test_both_languages_are_recovered_when_consulting_the_album` | [`etapa-08b/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-08b) | Cubierto |
| CA-07.1 | CP-07.1 | `albums/tests/test_languages.py::LanguagePersistenceTests::test_the_language_pair_is_rendered_on_the_card` | [`etapa-08b/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-08b) | Cubierto |
| CA-07.2 | CP-07.2 | `albums/tests/test_languages.py::LanguageRequiredTests::test_a_missing_source_language_is_rejected` | [`etapa-08b/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-08b) | Cubierto |
| CA-07.2 | CP-07.2 | `albums/tests/test_languages.py::LanguageRequiredTests::test_a_missing_target_language_is_rejected` | [`etapa-08b/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-08b) | Cubierto |
| CA-07.2 | CP-07.2 | `albums/tests/test_languages.py::LanguageRequiredTests::test_a_language_outside_the_catalogue_is_rejected` | [`etapa-08b/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-08b) | Cubierto |

**Total CP-07.1: 3 pruebas · CP-07.2: 3 pruebas.**

Regla adicional documentada: `SameLanguageRuleTests` (3), origen distinto de destino.

---

## HU-08 — Modificar la información del álbum

Issue: [#8](https://github.com/RestrepoJuanP/PaneLingo/issues/8)

> Como traductor, quiero modificar la información de un álbum para mantener actualizados los datos de mi proyecto.

| CA | CP | Prueba automática | Evidencia | Estado |
|---|---|---|---|---|
| CA-08.1 | CP-08.1 | `albums/tests/test_edit.py::AlbumEditSuccessTests::test_saving_updates_the_same_record` | [`etapa-09/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-09) | Cubierto |
| CA-08.1 | CP-08.1 | `albums/tests/test_edit.py::AlbumEditSuccessTests::test_the_changes_are_visible_when_reloading_the_detail` | [`etapa-09/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-09) | Cubierto |
| CA-08.1 | CP-08.1 | `albums/tests/test_edit.py::AlbumEditSuccessTests::test_a_confirmation_message_is_shown` | [`etapa-09/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-09) | Cubierto |
| CA-08.2 | CP-08.2 | `albums/tests/test_edit.py::AlbumEditCancelTests::test_opening_and_leaving_the_form_changes_nothing` | [`etapa-09/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-09) | Cubierto |

**Total CP-08.1: 3 pruebas · CP-08.2: 1 prueba.**

CP-08.2 se refuerza con `test_the_cancel_control_is_a_link_and_not_a_submit`, que fija que cancelar no produce ninguna escritura.

---

## HU-09 — Cargar páginas

Issue: [#9](https://github.com/RestrepoJuanP/PaneLingo/issues/9)

> Como traductor, quiero cargar imágenes completas de páginas de cómic para comenzar el proceso de extracción y traducción del contenido.

| CA | CP | Prueba automática | Evidencia | Estado |
|---|---|---|---|---|
| CA-09.1 | CP-09.1 | `albums/tests/test_pages.py::PageUploadSuccessTests::test_a_valid_png_creates_a_page_in_the_album` | [`etapa-10/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-10) | Cubierto |
| CA-09.1 | CP-09.1 | `albums/tests/test_pages.py::PageUploadSuccessTests::test_a_valid_jpeg_is_accepted` | [`etapa-10/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-10) | Cubierto |
| CA-09.1 | CP-09.1 | `albums/tests/test_pages.py::PageUploadSuccessTests::test_the_stored_file_is_a_complete_image` | [`etapa-10/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-10) | Cubierto |
| CA-09.1 | CP-09.1 | `albums/tests/test_pages.py::PageUploadSuccessTests::test_a_thumbnail_is_generated` | [`etapa-10/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-10) | Cubierto |
| CA-09.1 | CP-09.1 | `albums/tests/test_pages.py::PageUploadSuccessTests::test_the_page_appears_in_the_album_detail` | [`etapa-10/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-10) | Cubierto |
| CA-09.2 | CP-09.2 | `albums/tests/test_pages.py::PageRejectionTests::test_an_unsupported_format_is_rejected` | [`etapa-10/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-10) | Cubierto |
| CA-09.2 | CP-09.2 | `albums/tests/test_pages.py::PageRejectionTests::test_a_fake_png_is_rejected` | [`etapa-10/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-10) | Cubierto |
| CA-09.2 | CP-09.2 | `albums/tests/test_pages.py::PageRejectionTests::test_a_file_over_the_size_limit_is_rejected` | [`etapa-10/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-10) | Cubierto |
| CA-09.2 | CP-09.2 | `albums/tests/test_pages.py::PageRejectionTests::test_an_empty_file_is_rejected` | [`etapa-10/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-10) | Cubierto |
| CA-09.2 | CP-09.2 | `albums/tests/test_pages.py::PageRejectionTests::test_a_decompression_bomb_is_rejected` | [`etapa-10/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-10) | Cubierto |
| CA-09.2 | CP-09.2 | `albums/tests/test_pages.py::PageRejectionTests::test_a_batch_with_one_bad_file_still_loads_the_good_ones` | [`etapa-10/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-10) | Cubierto |

**Total CP-09.1: 5 pruebas · CP-09.2: 6 pruebas.**

Apoyo: numeración (3), nombre en disco y recorrido de rutas (4), aislamiento (4), advertencia de baja resolución (3).

---

## HU-10 — Eliminar páginas

Issue: [#10](https://github.com/RestrepoJuanP/PaneLingo/issues/10)

> Como usuario, quiero eliminar imágenes completas de páginas de cómic para retirar del álbum las páginas que ya no necesito o que fueron cargadas por error.

| CA | CP | Prueba automática | Evidencia | Estado |
|---|---|---|---|---|
| CA-10.1 | CP-10.1 | `albums/tests/test_page_delete.py::PageDeleteSuccessTests::test_confirming_removes_the_page_from_the_album` | [`etapa-11/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-11) | Cubierto |
| CA-10.1 | CP-10.1 | `albums/tests/test_page_delete.py::PageDeleteSuccessTests::test_the_files_stop_existing_in_media_root` | [`etapa-11/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-11) | Cubierto |
| CA-10.1 | CP-10.1 | `albums/tests/test_page_delete.py::PageDeleteSuccessTests::test_no_orphan_files_are_left_behind` | [`etapa-11/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-11) | Cubierto |
| CA-10.1 | CP-10.1 | `albums/tests/test_page_delete.py::PageDeleteSuccessTests::test_the_page_no_longer_appears_in_the_detail` | [`etapa-11/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-11) | Cubierto |
| CA-10.1 | CP-10.1 | `albums/tests/test_page_delete.py::PageDeleteSuccessTests::test_the_page_counter_is_recalculated` | [`etapa-11/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-11) | Cubierto |
| CA-10.1 | CP-10.1 | `albums/tests/test_page_delete.py::PageDeleteSuccessTests::test_a_confirmation_message_is_shown` | [`etapa-11/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-11) | Cubierto |
| CA-10.2 | CP-10.2 | `albums/tests/test_page_delete.py::PageDeleteCancelTests::test_opening_the_confirmation_and_leaving_changes_nothing` | [`etapa-11/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-11) | Cubierto |
| CA-10.2 | CP-10.2 | `albums/tests/test_page_delete.py::PageDeleteCancelTests::test_a_get_does_not_delete_anything` | [`etapa-11/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-11) | Cubierto |
| CA-10.3 | CP-10.3 | `albums/tests/test_page_delete.py::PageDeleteIsolationTests` (3 pruebas) | [`etapa-11/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-11) | Cubierto |

**Total CP-10.1: 6 pruebas · CP-10.2: 2 pruebas.**

Apoyo: numeración tras borrar (3), último borrado (4), cascada de álbum y de cuenta (2), tolerancia a archivo inexistente (1).

---

## Casos de prueba adicionales

Los criterios, el tipo y el resultado de estos casos están en [Sprint 1 › Casos de prueba adicionales](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-1#7-casos-de-prueba-adicionales). Aquí solo se indica qué prueba los verifica.

| CP | Prueba automática |
|---|---|
| [CP-01.3](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-1#7-casos-de-prueba-adicionales) | `RegistrationViewErrorTests::test_duplicate_email_creates_no_second_user` |
| [CP-01.4](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-1#7-casos-de-prueba-adicionales) | `RegistrationViewGetTests::test_authenticated_user_is_sent_to_the_panel` |
| [CP-02.3](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-1#7-casos-de-prueba-adicionales) | `RememberMeTests` (3) |
| [CP-02.4](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-1#7-casos-de-prueba-adicionales) | `LoginRedirectTests` (4) |
| [CP-02.5](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-1#7-casos-de-prueba-adicionales) | `LoginViewTests::test_authenticated_user_is_redirected_away_from_login` |
| [CP-03.3](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-1#7-casos-de-prueba-adicionales) | `LogoutViewTests::test_private_response_is_not_stored_by_the_browser` |
| [CP-04.3](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-1#7-casos-de-prueba-adicionales) | `PasswordResetTokenTests` (4) |
| [CP-04.4](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-1#7-casos-de-prueba-adicionales) | `NewPasswordValidationTests` (2) |
| [CP-04.5](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-1#7-casos-de-prueba-adicionales) | `OtherSessionsTests::test_another_open_session_is_invalidated` |
| [CP-05.3](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-1#7-casos-de-prueba-adicionales) | `AlbumOwnershipTests` (2) |
| [CP-06.3](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-1#7-casos-de-prueba-adicionales) | `AlbumRenameSuccessTests::test_a_single_character_title_is_accepted` |
| [CP-06.4](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-1#7-casos-de-prueba-adicionales) | `AlbumRenameSuccessTests::test_renaming_leaves_languages_and_status_untouched` |
| [CP-06.5](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-1#7-casos-de-prueba-adicionales) | `AlbumRenameIsolationTests` (4) |
| [CP-07.3](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-1#7-casos-de-prueba-adicionales) | `SameLanguageRuleTests` (3) |
| [CP-08.3](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-1#7-casos-de-prueba-adicionales) | `AlbumEditErrorTests` (2) |
| [CP-08.4](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-1#7-casos-de-prueba-adicionales) | `AlbumEditIsolationTests` (4), `AlbumStatusIsNotEditableTests` (2) |
| [CP-09.3](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-1#7-casos-de-prueba-adicionales) | `PageRejectionTests::test_a_batch_with_one_bad_file_still_loads_the_good_ones` |
| [CP-09.4](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-1#7-casos-de-prueba-adicionales) | Sin prueba automática |
| [CP-09.5](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-1#7-casos-de-prueba-adicionales) | `LowResolutionWarningTests` (3) |
| [CP-09.6](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-1#7-casos-de-prueba-adicionales) | Verificación manual en el navegador, tras corregir BUG-043 (04/09/2026) |
| [CP-09.7](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-1#7-casos-de-prueba-adicionales) | `PageUploadIsolationTests` (4) |
| [CP-10.3](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-1#7-casos-de-prueba-adicionales) | `PageDeleteIsolationTests` (3) |
| [CP-10.4](https://github.com/RestrepoJuanP/PaneLingo/wiki/Sprint-1#7-casos-de-prueba-adicionales) | `PageDeleteCancelTests::test_a_get_does_not_delete_anything` |

Estas pruebas citan hoy en su docstring el caso de prueba original de su historia; actualizarlas para que citen su CP nuevo queda para la próxima etapa de código.

---

## Verificación manual

Ningún caso de prueba se verifica **solo** de forma manual: los 20 tienen cobertura automática.

Se verificaron adicionalmente a mano, sin prueba automática que los cubra:

| Comprobación | Motivo de no automatizarla | Dónde consta |
|---|---|---|
| Comportamiento de la cola de archivos en el navegador (previsualización, quitar archivo, arrastre, deduplicación) | Requiere navegador; el cliente de pruebas de Django no ejecuta JavaScript | Deuda técnica DT-01 |
| Aspecto visual frente a las capturas del mockup | Comparación visual | `/design-system/` |
| Flujo de recuperación con el enlace tomado de la consola | Complementa a `test_password_reset.py`, que ya lo cubre de extremo a extremo | README |

---

# Sprint 3 — EP-08 Edición de imagen

Historias de la épica EP-08 que se cierran en este sprint ([ADR-003](adr/ADR-003-edicion-de-imagen.md)). HU-85 a HU-88 están en el [reporte de pruebas del Sprint 3](WIKI_SPRINT_3_REPORTE_PRUEBAS.md); los casos detallados de cada historia, en `docs/WIKI_SPRINT_3_CP_HU-*.md`.

## HU-89 — Maquetar la traducción sobre la imagen

Issue: [#89](https://github.com/RestrepoJuanP/PaneLingo/issues/89) · Casos: [WIKI_SPRINT_3_CP_HU-89.md](WIKI_SPRINT_3_CP_HU-89.md)

> Como traductor, quiero ajustar cada texto traducido directamente sobre la página (su posición, tamaño, fuente y alineación) para que la página final se vea como un cómic editado profesionalmente.

| CA | CP | Prueba automática | Evidencia | Estado |
|---|---|---|---|---|
| CA-89.1 | CP-89.1 | `albums/tests/test_typesetting_editor.py::LayoutAlgorithmTests::test_default_layout_uses_the_ocr_box_and_the_kind_font` | [`etapa-89/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-89) | Cubierto |
| CA-89.1 | CP-89.1 | `albums/tests/test_typesetting_workspace.py::InitialLayoutTests::test_each_region_carries_the_server_lines_and_size` | [`etapa-89b/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-89b) | Cubierto |
| CA-89.1 | CP-89.1 | `albums/tests/test_typesetting_workspace.py::InitialLayoutTests::test_the_editor_starts_from_the_cleaned_image` | [`etapa-89b/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-89b) | Cubierto |
| CA-89.2 | CP-89.2 | `albums/tests/test_typesetting_workspace.py::EditorMarkupTests::test_each_box_carries_urls_versions_and_an_accessible_name` | [`etapa-89b/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-89b) | Cubierto (automático y manual) |
| CA-89.3 | CP-89.3 | `albums/tests/test_typesetting_editor.py::LayoutStyleTests::test_a_box_outside_the_image_is_rejected` | [`etapa-89/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-89) | Cubierto (automático y manual) |
| CA-89.3 | CP-89.3 | `albums/tests/test_typesetting_editor.py::LayoutStyleTests::test_a_box_touching_the_edges_is_accepted` | [`etapa-89/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-89) | Cubierto (automático y manual) |
| CA-89.4 | CP-89.4 | `albums/tests/test_typesetting_editor.py::LayoutStyleTests::test_each_valid_style_is_saved` | [`etapa-89/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-89) | Cubierto |
| CA-89.4 | CP-89.4 | `albums/tests/test_typesetting_editor.py::LayoutStyleTests::test_the_panel_style_of_the_scenario_is_applied` | [`etapa-89/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-89) | Cubierto |
| CA-89.4 | CP-89.4 | `albums/tests/test_typesetting_editor.py::LayoutStyleTests::test_each_invalid_value_is_rejected_and_nothing_changes` | [`etapa-89/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-89) | Cubierto |
| CA-89.4 | CP-89.4 | `albums/tests/test_typesetting_editor.py::RenderPageTests::test_left_and_right_alignment_are_drawn_where_they_belong` | [`etapa-99b/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-99b) | Cubierto |
| CA-89.5 | CP-89.5 | `albums/tests/test_typesetting_editor.py::TranslationEditTests::test_editing_updates_the_translation_and_removes_approval` | [`etapa-89/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-89) | Cubierto |
| CA-89.6 | CP-89.6 | `albums/tests/test_typesetting_editor.py::LayoutResetTests::test_reset_restores_the_ocr_box_and_the_default_style` | [`etapa-89/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-89) | Cubierto (automático y manual) |
| CA-89.7 | CP-89.7 | `albums/tests/test_typesetting_editor.py::TypesetApprovalTests::test_approving_with_everything_ready` | [`etapa-89/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-89) | Cubierto |
| CA-89.7 | CP-89.7 | `albums/tests/test_typesetting_editor.py::TypesetApprovalTests::test_the_grid_shows_the_typeset_chip` | [`etapa-89/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-89) | Cubierto |
| CA-89.7 | CP-89.7 | `albums/tests/test_typesetting_editor.py::TypesetApprovalTests::test_rejected_without_a_cleaned_image` | [`etapa-89/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-89) | Cubierto |
| CA-89.7 | CP-89.7 | `albums/tests/test_typesetting_editor.py::TypesetApprovalTests::test_rejected_with_translations_not_approved` | [`etapa-89/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-89) | Cubierto |
| CA-89.7 | CP-89.7 | `albums/tests/test_typesetting_editor.py::TypesetApprovalTests::test_without_javascript_it_redirects_with_a_message` | [`etapa-89/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-89) | Cubierto |
| CA-89.7 | CP-89.7 | `albums/tests/test_typesetting_editor.py::TypesetApprovalTests::test_a_later_change_removes_the_typeset_state` | [`etapa-89/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-89) | Cubierto |
| CA-89.7 | CP-89.7 | `albums/tests/test_typesetting_workspace.py::EditorMarkupTests::test_approve_is_disabled_with_its_reason` | [`etapa-89b/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-89b) | Cubierto |
| CA-89.7 | CP-89.7 | `albums/tests/test_typesetting_workspace.py::EditorMarkupTests::test_an_approved_page_says_so_in_text` | [`etapa-89b/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-89b) | Cubierto |
| CA-89.7 | CP-89.7 | `albums/tests/test_typesetting_workspace.py::EditorMarkupTests::test_layout_responses_carry_the_page_status` | [`etapa-89b/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-89b) | Cubierto |
| CA-89.8 | CP-89.8 | `albums/tests/test_typesetting_editor.py::RenderPageTests::test_the_render_keeps_resolution_and_mode` | [`etapa-89/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-89) | Cubierto (automático y manual) |
| CA-89.8 | CP-89.8 | `albums/tests/test_typesetting_editor.py::RenderPageTests::test_pixels_change_inside_each_box_and_nowhere_else` | [`etapa-89/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-89) | Cubierto (automático y manual) |
| CA-89.8 | CP-89.8 | `albums/tests/test_typesetting_editor.py::RenderPageTests::test_the_drawn_text_matches_the_layout_within_two_pixels` | [`etapa-89/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-89) | Cubierto (automático y manual) |
| CA-89.8 | CP-89.8 | `albums/tests/test_typesetting_editor.py::RenderPageTests::test_the_stored_style_is_drawn` | [`etapa-89/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-89) | Cubierto (automático y manual) |
| CA-89.8 | CP-89.8 | `albums/tests/test_typesetting_editor.py::RenderPageTests::test_left_and_right_alignment_are_drawn_where_they_belong` | [`etapa-99b/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-99b) | Cubierto (automático y manual) |
| CA-89.8 | CP-89.8 | `albums/tests/test_png_export.py::ImageFidelityTests::test_same_resolution_rgb_and_identical_to_render_page` | [`etapa-90/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-90) | Cubierto (automático y manual) |
| CA-89.9 | CP-89.9 | `albums/tests/test_typesetting_editor.py::ForeignResourceTests::test_every_endpoint_answers_404_without_changes` | [`etapa-89/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-89) | Cubierto |

**Total CP-89.1: 3 · CP-89.2: 1 · CP-89.3: 2 · CP-89.4: 4 · CP-89.5: 1 · CP-89.6: 1 · CP-89.7: 9 · CP-89.8: 6 · CP-89.9: 1.** CP-89.8 incluye una prueba de HU-90 que compara el PNG con `render_page`. La prueba de alineación cubre CP-89.4 y CP-89.8 y se añadió en la verificación final (etapa 99b).

Partes manuales, con su procedimiento en el anexo de casos: selección con clic y `Tab` (CP-89.2), arrastre y teclado (CP-89.3), guardado y `Ctrl+Z` (CP-89.6) y comparación visual con el PNG (CP-89.8). **Ejecutadas el 11/11/2026 con resultado correcto**; el registro está en [Resultado de la ejecución manual](WIKI_SPRINT_3_CP_HU-89.md#resultado-de-la-ejecución-manual).

Regresión: `TypesetInvalidationTests::test_every_path_clears_the_typeset_state` recorre los 20 caminos que quitan «Maquetada» (ADR-003, P1). Apoyo: pestañas y `?paso=` (5), sin JavaScript (2), fuentes y límites emitidos por el servidor (6, patrón BUG-043), conflicto de versión (1).

---

## HU-90 — Exportar las páginas traducidas como PNG

Issue: [#90](https://github.com/RestrepoJuanP/PaneLingo/issues/90) · Casos: [WIKI_SPRINT_3_CP_HU-90.md](WIKI_SPRINT_3_CP_HU-90.md)

> Como traductor, quiero descargar las páginas del álbum ya traducidas como imágenes para entregarlas o publicarlas sin pasar por otro programa.

| CA | CP | Prueba automática | Evidencia | Estado |
|---|---|---|---|---|
| CA-90.1 | CP-90.1 | `albums/tests/test_png_export.py::FormatChoiceTests::test_the_dialog_offers_both_formats_as_native_radios` | [`etapa-90/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-90) | Cubierto |
| CA-90.1 | CP-90.1 | `albums/tests/test_png_export.py::FormatChoiceTests::test_docx_still_works_the_same` | [`etapa-90/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-90) | Cubierto |
| CA-90.2 | CP-90.2 | `albums/tests/test_png_export.py::ArchiveContentTests::test_zip_name_type_and_page_order_with_a_gap` | [`etapa-90/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-90) | Cubierto |
| CA-90.2 | CP-90.2 | `albums/tests/test_png_export.py::PreparingPngExportTests::test_png_export_waits_as_preparing_and_is_queued_once` | [`etapa-99b/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-99b) | Cubierto |
| CA-90.3 | CP-90.3 | `albums/tests/test_png_export.py::ImageFidelityTests::test_same_resolution_rgb_and_identical_to_render_page` | [`etapa-90/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-90) | Cubierto |
| CA-90.3 | CP-90.3 | `albums/tests/test_png_export.py::ImageFidelityTests::test_a_grayscale_original_exports_in_l` | [`etapa-90/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-90) | Cubierto |
| CA-90.3 | CP-90.3 | `albums/tests/test_png_export.py::ImageFidelityTests::test_an_rgba_original_exports_in_rgb_without_alpha` | [`etapa-90/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-90) | Cubierto |
| CA-90.3 | CP-90.3 | `albums/tests/test_png_export.py::ImageFidelityTests::test_a_gray_palette_exports_in_l_and_a_color_one_in_rgb` | [`etapa-90/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-90) | Cubierto |
| CA-90.3 | CP-90.3 | `albums/tests/test_png_export.py::ImageFidelityTests::test_a_sixteen_bit_gray_page_is_scaled_not_whitened` | [`etapa-90/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-90) | Cubierto |
| CA-90.4 | CP-90.4 | `albums/tests/test_png_export.py::UntypesetPagesTests::test_the_warning_counts_only_pages_with_text_to_typeset` | [`etapa-90/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-90) | Cubierto |
| CA-90.4 | CP-90.4 | `albums/tests/test_png_export.py::UntypesetPagesTests::test_confirmation_is_required_before_exporting` | [`etapa-90/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-90) | Cubierto |
| CA-90.4 | CP-90.4 | `albums/tests/test_png_export.py::UntypesetPagesTests::test_an_untypeset_page_uses_its_saved_layout` | [`etapa-90/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-90) | Cubierto |
| CA-90.5 | CP-90.5 | `albums/tests/test_png_export.py::BlankAndKeptTextTests::test_a_blank_page_is_identical_to_the_original` | [`etapa-90/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-90) | Cubierto |
| CA-90.5 | CP-90.5 | `albums/tests/test_png_export.py::BlankAndKeptTextTests::test_a_skipped_region_keeps_its_original_text` | [`etapa-90/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-90) | Cubierto |
| CA-90.6 | CP-90.6 | `albums/tests/test_png_export.py::FailureTests::test_a_failure_mid_task_leaves_an_error_and_no_file` | [`etapa-90/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-90) | Cubierto |
| CA-90.6 | CP-90.6 | `albums/tests/test_png_export.py::FailureTests::test_a_cleaned_image_changed_after_the_snapshot_fails` | [`etapa-90/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-90) | Cubierto |
| CA-90.6 | CP-90.6 | `albums/tests/test_png_export.py::FailureTests::test_a_missing_original_fails` | [`etapa-90/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-90) | Cubierto |
| CA-90.7 | CP-90.7 | `albums/tests/test_png_export.py::ForeignAlbumTests::test_foreign_export_and_download_answer_not_found` | [`etapa-90/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-90) | Cubierto |

**Total CP-90.1: 2 · CP-90.2: 2 · CP-90.3: 5 · CP-90.4: 3 · CP-90.5: 2 · CP-90.6: 3 · CP-90.7: 1.**

La espera «Preparando exportación…» de CA-90.2 reutiliza el mecanismo de HU-27; `PreparingPngExportTests`, añadida en la verificación final (etapa 99b), la verifica con el formato PNG, incluido que un segundo POST no crea otra exportación. Apoyo: requisito para exportar en PNG, formato en el historial, miniatura de 16 bits, aviso de «Limpieza manual» y página sin imagen limpia (5).

---

## HU-91 — Limpiar con IA el texto que está sobre el dibujo

Issue: [#91](https://github.com/RestrepoJuanP/PaneLingo/issues/91) · Nota: [WIKI_SPRINT_3_CP_HU-91.md](WIKI_SPRINT_3_CP_HU-91.md)

**Descartada tras el spike**, sin CA implementados, CP ni pruebas. Motivo y datos en [ADR-003, P4](adr/ADR-003-edicion-de-imagen.md#p4--spike-de-hu-91). Evidencia del Quality Gate de la etapa de documentación: [`etapa-91/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-91).

---

## Bugs

| Bug | Detectado en | Rama | Corrección | Prueba de regresión | Evidencia | Estado |
|---|---|---|---|---|---|---|
| BUG-096 | HU-90 | `fix/BUG-096-16bit-grayscale` | `albums/ocr/layout.py` escala las páginas de 16 bits con `albums/imaging.py` antes de calcular la luminosidad. Sin ello, todas las regiones de una página gris de 16 bits se clasificaban como globo, en el OCR automático y en el manual. **La primera parte se corrigió en HU-90**, que creó `albums/imaging.py` para la miniatura, la limpieza, el recorte del OCR manual y el dibujo de la página. | `albums/tests/test_ocr_layout.py::SixteenBitRegionKindTests` (3 pruebas) | [`etapa-90b/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-3/etapa-90b) | Corregido; pendiente de fusión |

Las regiones de páginas de 16 bits procesadas antes de la corrección siguen clasificadas como globo hasta reprocesar la página, lo que borra su trabajo ([ADR-003, P9 y P10](adr/ADR-003-edicion-de-imagen.md)).
