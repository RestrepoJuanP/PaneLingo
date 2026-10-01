# Sprint 1 — Trazabilidad

Relaciona cada historia de usuario con sus criterios de aceptación, sus casos de prueba, la prueba automática que los verifica y la evidencia del Quality Gate.

**Estado global:** las 10 historias implementadas y sus 20 casos de prueba cubiertos por prueba automática, más 23 casos adicionales (21 automáticos, 1 manual y 1 pendiente). 227 pruebas en total, todas en verde.

Los nombres de prueba están tomados del código, no transcritos a mano: el inventario se generó recorriendo los archivos de prueba y leyendo el CP citado en cada docstring.

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

Además de los 20 casos diseñados y ejecutados manualmente, cada historia del Sprint 1 tiene en su issue criterios adicionales: reglas que ya estaban implementadas y probadas pero que no figuraban como criterio. Se registran aquí como casos de prueba.

**Ejecución:** pipeline de integración continua sobre `main`, commit `13934c4`, 12/09/2026 a las 21:58 (hora de Colombia): 227 pruebas, todas en verde. Evidencia: [`E12-quality-gate-06-django-test.txt`](https://github.com/RestrepoJuanP/PaneLingo/blob/main/docs/evidence/sprint-1/etapa-12/E12-quality-gate-06-django-test.txt).

| HU | CA | CP | Qué verifica | Tipo | Prueba | Resultado |
|---|---|---|---|---|---|---|
| [HU-01](https://github.com/RestrepoJuanP/PaneLingo/issues/1) | CA-01.3 | CP-01.3 | Correo ya registrado, sin distinguir mayúsculas | Alternativo | `RegistrationViewErrorTests::test_duplicate_email_creates_no_second_user` | Aprobada |
| [HU-01](https://github.com/RestrepoJuanP/PaneLingo/issues/1) | CA-01.4 | CP-01.4 | Un usuario con sesión no ve el registro | Alternativo | `RegistrationViewGetTests::test_authenticated_user_is_sent_to_the_panel` | Aprobada |
| [HU-02](https://github.com/RestrepoJuanP/PaneLingo/issues/2) | CA-02.3 | CP-02.3 | Mantener la sesión iniciada en el dispositivo | Happy path | `RememberMeTests` (3) | Aprobada |
| [HU-02](https://github.com/RestrepoJuanP/PaneLingo/issues/2) | CA-02.4 | CP-02.4 | Volver a la página privada pedida; se ignora un retorno a otro sitio | Happy path | `LoginRedirectTests` (4) | Aprobada |
| [HU-02](https://github.com/RestrepoJuanP/PaneLingo/issues/2) | CA-02.5 | CP-02.5 | Un usuario con sesión no ve el formulario de inicio | Alternativo | `LoginViewTests::test_authenticated_user_is_redirected_away_from_login` | Aprobada |
| [HU-03](https://github.com/RestrepoJuanP/PaneLingo/issues/3) | CA-03.3 | CP-03.3 | El botón Atrás no muestra contenido privado | Alternativo | `LogoutViewTests::test_private_response_is_not_stored_by_the_browser` | Aprobada |
| [HU-04](https://github.com/RestrepoJuanP/PaneLingo/issues/4) | CA-04.3 | CP-04.3 | Enlace ya usado, manipulado, caducado o con identificador inválido | Alternativo | `PasswordResetTokenTests` (4) | Aprobada |
| [HU-04](https://github.com/RestrepoJuanP/PaneLingo/issues/4) | CA-04.4 | CP-04.4 | Nueva contraseña débil o que no coincide | Alternativo | `NewPasswordValidationTests` (2) | Aprobada |
| [HU-04](https://github.com/RestrepoJuanP/PaneLingo/issues/4) | CA-04.5 | CP-04.5 | Las demás sesiones se cierran al cambiar la contraseña | Happy path | `OtherSessionsTests::test_another_open_session_is_invalidated` | Aprobada |
| [HU-05](https://github.com/RestrepoJuanP/PaneLingo/issues/5) | CA-05.3 | CP-05.3 | El propietario es siempre la cuenta con sesión | Alternativo | `AlbumOwnershipTests` (2) | Aprobada |
| [HU-06](https://github.com/RestrepoJuanP/PaneLingo/issues/6) | CA-06.3 | CP-06.3 | Título de un solo carácter | Happy path | `AlbumRenameSuccessTests::test_a_single_character_title_is_accepted` | Aprobada |
| [HU-06](https://github.com/RestrepoJuanP/PaneLingo/issues/6) | CA-06.4 | CP-06.4 | Renombrar no altera idiomas ni estado | Alternativo | `AlbumRenameSuccessTests::test_renaming_leaves_languages_and_status_untouched` | Aprobada |
| [HU-06](https://github.com/RestrepoJuanP/PaneLingo/issues/6) | CA-06.5 | CP-06.5 | No se renombran álbumes de otra cuenta | Alternativo | `AlbumRenameIsolationTests` (4) | Aprobada |
| [HU-07](https://github.com/RestrepoJuanP/PaneLingo/issues/7) | CA-07.3 | CP-07.3 | El idioma de destino debe ser distinto del de origen | Alternativo | `SameLanguageRuleTests` (3) | Aprobada |
| [HU-08](https://github.com/RestrepoJuanP/PaneLingo/issues/8) | CA-08.3 | CP-08.3 | Datos inválidos no producen cambios parciales | Alternativo | `AlbumEditErrorTests` (2) | Aprobada |
| [HU-08](https://github.com/RestrepoJuanP/PaneLingo/issues/8) | CA-08.4 | CP-08.4 | No se editan álbumes de otra cuenta; el estado no es editable | Alternativo | `AlbumEditIsolationTests` (4), `AlbumStatusIsNotEditableTests` (2) | Aprobada |
| [HU-09](https://github.com/RestrepoJuanP/PaneLingo/issues/9) | CA-09.3 | CP-09.3 | Lote con archivos válidos e inválidos | Alternativo | `PageRejectionTests::test_a_batch_with_one_bad_file_still_loads_the_good_ones` | Aprobada |
| [HU-09](https://github.com/RestrepoJuanP/PaneLingo/issues/9) | CA-09.5 | CP-09.5 | Imagen de baja resolución: se carga con aviso | Alternativo | `LowResolutionWarningTests` (3) | Aprobada |
| [HU-09](https://github.com/RestrepoJuanP/PaneLingo/issues/9) | CA-09.7 | CP-09.7 | No se cargan páginas en álbumes de otra cuenta | Alternativo | `PageUploadIsolationTests` (4) | Aprobada |
| [HU-10](https://github.com/RestrepoJuanP/PaneLingo/issues/10) | CA-10.3 | CP-10.3 | No se eliminan páginas de álbumes de otra cuenta | Alternativo | `PageDeleteIsolationTests` (3) | Aprobada |
| [HU-10](https://github.com/RestrepoJuanP/PaneLingo/issues/10) | CA-10.4 | CP-10.4 | Abrir la dirección de eliminación no borra nada | Alternativo | `PageDeleteCancelTests::test_a_get_does_not_delete_anything` | Aprobada |
| [HU-09](https://github.com/RestrepoJuanP/PaneLingo/issues/9) | CA-09.6 | CP-09.6 | Ver los archivos elegidos antes de cargarlos | Happy path | Verificación manual en el navegador, tras corregir BUG-043 (04/09/2026) | Aprobada |
| [HU-09](https://github.com/RestrepoJuanP/PaneLingo/issues/9) | CA-09.4 | CP-09.4 | Enviar el formulario sin archivos | Alternativo | Sin prueba automática | Pendiente |

**Pendiente:** CP-09.4 no tiene prueba automática. Además, las pruebas de esta tabla citan en su docstring el caso de prueba original de su historia; actualizarlas para que citen su CP nuevo queda para la próxima etapa de código.

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

## Bugs corregidos durante el Sprint 1

> **Sobre la numeración:** los identificadores de bug no son consecutivos porque el contador de *issues* de GitHub es **compartido con los pull requests**. Entre BUG-043 y BUG-046 hay números consumidos por PR. No falta ningún bug: son los dos únicos registrados en el sprint.

| Bug | Issue | Detectado en | Rama | PR | Estado |
|---|---|---|---|---|---|
| BUG-043 — La zona de carga no muestra los archivos seleccionados | [#43](https://github.com/RestrepoJuanP/PaneLingo/issues/43) | HU-09, durante la ejecución manual de **CP-09.1** | `fix/BUG-043-upload-queue-feedback` | [#44](https://github.com/RestrepoJuanP/PaneLingo/pull/44) | Cerrado |
| BUG-046 — Comentarios de plantilla renderizados como texto visible | [#46](https://github.com/RestrepoJuanP/PaneLingo/issues/46) | HU-10, revisión de la rejilla de páginas del detalle de álbum | `fix/BUG-046-template-comments` | [#47](https://github.com/RestrepoJuanP/PaneLingo/pull/47) | Cerrado |

### BUG-043 — Detalle

La zona de carga no mostraba nada tras seleccionar archivos: la pantalla seguía con el texto inicial.

Corregido con una cola de selección en cliente que muestra miniatura, nombre, tamaño y estado, permite quitar archivos y avisa de extensión o tamaño no admitidos. Los límites los emite el servidor como atributos de datos, de modo que `settings` sigue siendo la única fuente. El aviso del navegador **no bloquea el envío**: la autoridad es el servidor.

Evidencia: [`etapa-10b/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-10b).

### BUG-046 — Detalle

Los comentarios `{# ... #}` de Django solo funcionan en una línea; escritos en varias se renderizaban literalmente. **46 comentarios en 35 plantillas**, prácticamente todas las escritas desde la Etapa 2.

Corregido convirtiéndolos a `{% comment %} … {% endcomment %}`. Se añadió `config/tests/test_template_hygiene.py` con tres pruebas que verifican que ni los delimitadores ni el texto de los comentarios llegan al HTML de las 14 pantallas principales, y que ninguna plantilla del repositorio usa la sintaxis breve en varias líneas.

Se corrigió además un problema **independiente** descubierto al revisar la captura del issue: la etiqueta `Pendiente de procesamiento` desbordaba la celda de 146 px y pisaba el botón de eliminar. El chip de estado pasó al cuerpo de la tarjeta, como en el mockup, y se añadieron etiquetas breves.

Evidencia: [`etapa-11b/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-11b).

---

## Índice de evidencias

| Etapa | Contenido | Carpeta |
|---|---|---|
| 01 | Bootstrap del proyecto e infraestructura de calidad | [`etapa-01/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-01) |
| 02 | Sistema de diseño y layout base | [`etapa-02/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-02) |
| 03 | HU-01 Crear cuenta | [`etapa-03/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-03) |
| 04 | HU-02 Iniciar sesión | [`etapa-04/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-04) |
| 05 | HU-03 Cerrar sesión y auditoría de vistas privadas | [`etapa-05/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-05) |
| 06 | HU-04 Recuperar contraseña | [`etapa-06/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-06) |
| 07 | HU-05 Crear álbum y modelo de dominio | [`etapa-07/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-07) |
| 08 | HU-06 Título del álbum | [`etapa-08/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-08) |
| 08b | HU-07 Idiomas del álbum | [`etapa-08b/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-08b) |
| 09 | HU-08 Editar álbum | [`etapa-09/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-09) |
| 10 | HU-09 Cargar páginas | [`etapa-10/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-10) |
| 10b | BUG-043 | [`etapa-10b/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-10b) |
| 11 | HU-10 Eliminar páginas | [`etapa-11/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-11) |
| 11b | BUG-046 | [`etapa-11b/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-11b) |
| 12 | Cierre del sprint, `check --deploy` y `makemigrations --check` | [`etapa-12/`](https://github.com/RestrepoJuanP/PaneLingo/tree/main/docs/evidence/sprint-1/etapa-12) |

Cada carpeta contiene la salida de los siete pasos del Quality Gate y un resumen en Markdown con la rama, el commit y el estado del árbol de trabajo en el momento de generarla.
