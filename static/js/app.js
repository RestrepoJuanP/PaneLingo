/* =============================================================================
   PaneLingo — JavaScript de interfaz
   -----------------------------------------------------------------------------
   Vanilla, sin dependencias. Solo interacciones: modales, toasts, medidor de
   fuerza de contraseña y pills. Ninguna lógica de negocio.
   ========================================================================== */

(function () {
  "use strict";

  var FOCUSABLE = [
    "a[href]",
    "button:not([disabled])",
    "input:not([disabled])",
    "select:not([disabled])",
    "textarea:not([disabled])",
    '[tabindex]:not([tabindex="-1"])',
  ].join(",");

  /* ---------------------------------------------------------------------------
     Modales: foco atrapado, cierre con Escape y devolución del foco.
     ------------------------------------------------------------------------ */

  var lastTrigger = null;

  function focusableIn(modal) {
    return Array.prototype.filter.call(
      modal.querySelectorAll(FOCUSABLE),
      function (el) {
        return el.offsetParent !== null;
      },
    );
  }

  /* Rellena un modal compartido con los datos del elemento que lo abrió.
     Permite usar un único modal para toda una rejilla de tarjetas en lugar de
     repetir uno por elemento. */
  function fillModalFrom(modal, trigger) {
    var form = modal.querySelector("form");
    if (form && trigger.dataset.modalAction) {
      form.setAttribute("action", trigger.dataset.modalAction);
    }
    var field = modal.querySelector("[data-modal-field]");
    if (field && typeof trigger.dataset.modalValue === "string") {
      field.value = trigger.dataset.modalValue;
    }
  }

  function openModal(modal, trigger) {
    if (!modal) {
      return;
    }
    if (trigger) {
      fillModalFrom(modal, trigger);
    }
    modal.hidden = false;
    document.body.style.overflow = "hidden";
    var targets = focusableIn(modal);
    if (targets.length) {
      targets[0].focus();
    }
  }

  function closeModal(modal) {
    if (!modal || modal.hidden) {
      return;
    }
    modal.hidden = true;
    document.body.style.overflow = "";
    if (lastTrigger) {
      lastTrigger.focus();
      lastTrigger = null;
    }
  }

  function openModals() {
    return Array.prototype.filter.call(
      document.querySelectorAll(".modal"),
      function (modal) {
        return !modal.hidden;
      },
    );
  }

  document.addEventListener("click", function (event) {
    var opener = event.target.closest("[data-modal-open]");
    if (opener) {
      event.preventDefault();
      lastTrigger = opener;
      openModal(document.getElementById(opener.dataset.modalOpen), opener);
      return;
    }

    var closer = event.target.closest("[data-modal-close]");
    if (closer) {
      event.preventDefault();
      closeModal(closer.closest(".modal"));
      return;
    }

    // Clic en el velo, fuera del diálogo.
    if (
      event.target.classList &&
      event.target.classList.contains("modal") &&
      !event.target.hidden
    ) {
      closeModal(event.target);
    }
  });

  document.addEventListener("keydown", function (event) {
    var open = openModals();
    if (!open.length) {
      return;
    }
    var modal = open[open.length - 1];

    if (event.key === "Escape") {
      closeModal(modal);
      return;
    }

    if (event.key !== "Tab") {
      return;
    }

    var targets = focusableIn(modal);
    if (!targets.length) {
      return;
    }
    var first = targets[0];
    var last = targets[targets.length - 1];

    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  });

  /* ---------------------------------------------------------------------------
     Toasts: cierre manual. No se ocultan solos, para no hacer desaparecer un
     mensaje antes de que alguien con lectura lenta pueda leerlo.
     ------------------------------------------------------------------------ */

  document.addEventListener("click", function (event) {
    var close = event.target.closest("[data-toast-close]");
    if (close) {
      var toast = close.closest(".toast");
      if (toast) {
        toast.remove();
      }
    }
  });

  /* ---------------------------------------------------------------------------
     Medidor de fuerza de contraseña.
     Los umbrales replican los del mockup: menos de 6, de 6 a 9, 10 o más.
     ------------------------------------------------------------------------ */

  var LEVELS = [
    { level: "weak", width: "33%", label: "Muy corta" },
    { level: "medium", width: "66%", label: "Aceptable" },
    { level: "strong", width: "100%", label: "Segura" },
  ];

  function levelFor(length) {
    if (length === 0) {
      return null;
    }
    if (length < 6) {
      return LEVELS[0];
    }
    if (length < 10) {
      return LEVELS[1];
    }
    return LEVELS[2];
  }

  function bindStrength(meter) {
    var input = document.getElementById(meter.dataset.strengthFor);
    if (!input) {
      return;
    }
    var fill = meter.querySelector(".strength__fill");
    var label = meter.querySelector(".strength__label");

    function update() {
      var current = levelFor(input.value.length);
      if (!current) {
        meter.removeAttribute("data-level");
        fill.style.width = "0";
        label.textContent = "";
        return;
      }
      meter.dataset.level = current.level;
      fill.style.width = current.width;
      label.textContent = current.label;
    }

    input.addEventListener("input", update);
    update();
  }

  /* ---------------------------------------------------------------------------
     Pills de selección única dentro de un grupo.
     El estado real lo guarda un input oculto, para que el formulario funcione
     igual si el JavaScript no llega a cargar.
     ------------------------------------------------------------------------ */

  function bindPillGroup(group) {
    var target = document.getElementById(group.dataset.pillTarget);

    group.addEventListener("click", function (event) {
      var pill = event.target.closest(".pill");
      if (!pill || !group.contains(pill)) {
        return;
      }
      Array.prototype.forEach.call(
        group.querySelectorAll(".pill"),
        function (other) {
          other.setAttribute("aria-pressed", String(other === pill));
        },
      );
      if (target) {
        target.value = pill.dataset.value || pill.textContent.trim();
      }
    });
  }

  /* ---------------------------------------------------------------------------
     Estado de carga al enviar un formulario.
     Evita además el doble envío, que crearía dos cuentas.
     ------------------------------------------------------------------------ */

  function bindSubmitBusy(button) {
    var form = button.form || button.closest("form");
    if (!form) {
      return;
    }
    form.addEventListener("submit", function () {
      if (button.disabled) {
        return;
      }
      var spinner = button.querySelector(".btn__spinner");
      var label = button.querySelector("[data-submit-label]");
      if (spinner) {
        spinner.hidden = false;
      }
      if (label && label.dataset.busyLabel) {
        label.textContent = label.dataset.busyLabel;
      }
      button.classList.add("btn--loading");
      // Se deshabilita después del envío para que el navegador incluya el
      // botón en los datos del formulario.
      window.setTimeout(function () {
        button.disabled = true;
      }, 0);
    });
  }

  /* ---------------------------------------------------------------------------
     Arranque
     ------------------------------------------------------------------------ */

  function init() {
    Array.prototype.forEach.call(
      document.querySelectorAll("[data-strength-for]"),
      bindStrength,
    );
    Array.prototype.forEach.call(
      document.querySelectorAll("[data-pill-target]"),
      bindPillGroup,
    );
    Array.prototype.forEach.call(
      document.querySelectorAll("[data-submit-busy]"),
      bindSubmitBusy,
    );
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
