/* =============================================================================
   PaneLingo — JavaScript de interfaz
   -----------------------------------------------------------------------------
   Vanilla, sin dependencias. Solo interacciones: modales, toasts, medidor de
   fuerza de contraseña, estado de envío y cola de archivos seleccionados.
   Ninguna lógica de negocio.
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
     Los selectores de idioma NO llevan JavaScript: son grupos de radios
     nativos, con navegación por flechas y envío sin scripts. Ver
     templates/albums/_language_pills.html.
     ------------------------------------------------------------------------ */

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
     Cola de archivos seleccionados en la pantalla de carga (BUG-043).

     Es una MEJORA PROGRESIVA. Sin JavaScript el formulario funciona igual: el
     <label for> abre el selector y el input envía los archivos. Esta cola solo
     enseña, antes de enviar, lo que se va a enviar.

     NO ESCRIBAS AQUÍ NINGÚN LÍMITE. El tamaño máximo y las extensiones
     admitidas llegan en los atributos de datos del input, emitidos por el
     servidor desde settings. Escribirlos aquí crearía una segunda cifra que
     acabaría divergiendo de la del servidor sin que nada lo delatara.
     ------------------------------------------------------------------------ */

  function humanSize(bytes) {
    if (bytes < 1000) {
      return bytes + " B";
    }
    if (bytes < 1000000) {
      return Math.round(bytes / 1000) + " KB";
    }
    return (bytes / 1000000).toFixed(1) + " MB";
  }

  function fileKey(file) {
    // Dos archivos se consideran el mismo si coinciden nombre, tamaño y fecha
    // de modificación. Es una heurística: dos archivos distintos podrían
    // coincidir en los tres, pero es tan improbable que compensa frente al
    // caso real, que es volver a elegir el mismo por descuido.
    return file.name + "|" + file.size + "|" + file.lastModified;
  }

  function bindUploadQueue(input) {
    var form = input.form || input.closest("form");
    var panel = document.querySelector("[data-upload-selection]");
    var list = document.querySelector("[data-upload-list]");
    var counter = document.querySelector("[data-upload-count]");
    var dropzone = document.querySelector("[data-dropzone]");
    if (!form || !panel || !list || !counter) {
      return;
    }

    var maxSize = parseInt(input.dataset.maxSize, 10);
    var allowed = (input.dataset.allowedExtensions || "")
      .split(",")
      .filter(Boolean);
    var entries = [];

    function problemWith(file) {
      // Aviso temprano, NO autoridad. El servidor revalida siempre y puede
      // rechazar un archivo que aquí pareciera correcto, porque comprueba el
      // contenido real y no la extensión. Por eso esto nunca impide enviar.
      var name = file.name.toLowerCase();
      var extensionOk = allowed.some(function (extension) {
        return name.endsWith(extension);
      });
      if (!extensionOk) {
        return "Formato no admitido. Se aceptan " + allowed.join(", ") + ".";
      }
      if (maxSize && file.size > maxSize) {
        return (
          "Pesa " + humanSize(file.size) + " y el máximo es " + humanSize(maxSize) + "."
        );
      }
      return null;
    }

    function syncInput() {
      // input.files es de solo lectura: para quitar un archivo hay que
      // reconstruir la lista con un DataTransfer y reasignarla.
      var transfer = new DataTransfer();
      entries.forEach(function (entry) {
        transfer.items.add(entry.file);
      });
      input.files = transfer.files;
    }

    function removeEntry(index) {
      var entry = entries[index];
      if (entry && entry.preview) {
        URL.revokeObjectURL(entry.preview);
      }
      entries.splice(index, 1);
      syncInput();
      render();
    }

    function buildRow(entry, index) {
      var item = document.createElement("li");
      item.className = "upload-selection__row";

      var thumb = document.createElement("span");
      thumb.className = "upload-selection__thumb";
      if (entry.preview) {
        var image = document.createElement("img");
        image.src = entry.preview;
        image.alt = "";
        thumb.appendChild(image);
      }

      var body = document.createElement("div");
      body.className = "upload-selection__body";

      var name = document.createElement("p");
      name.className = "upload-row__name";
      name.textContent = entry.file.name;

      var state = document.createElement("p");
      state.className = "upload-row__state";
      if (entry.problem) {
        state.classList.add("upload-row__state--error");
        state.textContent = humanSize(entry.file.size) + " · " + entry.problem;
      } else {
        state.classList.add("upload-row__state--ok");
        state.textContent = humanSize(entry.file.size) + " · Listo para subir";
      }

      body.appendChild(name);
      body.appendChild(state);

      var remove = document.createElement("button");
      remove.type = "button";
      remove.className = "btn-icon upload-selection__remove";
      remove.setAttribute("aria-label", "Quitar «" + entry.file.name + "»");
      remove.textContent = "✕";
      remove.addEventListener("click", function () {
        removeEntry(index);
      });

      item.appendChild(thumb);
      item.appendChild(body);
      item.appendChild(remove);
      return item;
    }

    function countLabel(skipped) {
      var total = entries.length;
      var label = total + (total === 1 ? " archivo" : " archivos");
      var warned = entries.filter(function (entry) {
        return entry.problem;
      }).length;
      if (warned) {
        label += " · " + warned + (warned === 1 ? " con aviso" : " con avisos");
      }
      if (skipped) {
        label +=
          " · " +
          skipped +
          (skipped === 1 ? " repetido omitido" : " repetidos omitidos");
      }
      return label;
    }

    function render(skipped) {
      list.textContent = "";
      entries.forEach(function (entry, index) {
        list.appendChild(buildRow(entry, index));
      });
      panel.hidden = entries.length === 0;
      counter.textContent = countLabel(skipped);
    }

    function addFiles(fileList) {
      var known = entries.map(function (entry) {
        return fileKey(entry.file);
      });
      var skipped = 0;

      Array.prototype.forEach.call(fileList, function (file) {
        if (known.indexOf(fileKey(file)) !== -1) {
          // Se ignora en vez de duplicarse: enviarlo dos veces crearía dos
          // páginas idénticas con números distintos, y volver a elegir el
          // mismo archivo casi siempre es un descuido.
          skipped += 1;
          return;
        }
        known.push(fileKey(file));
        entries.push({
          file: file,
          problem: problemWith(file),
          preview:
            file.type.indexOf("image/") === 0 ? URL.createObjectURL(file) : null,
        });
      });

      syncInput();
      render(skipped);
    }

    input.addEventListener("change", function () {
      addFiles(input.files);
    });

    if (dropzone) {
      ["dragenter", "dragover"].forEach(function (name) {
        dropzone.addEventListener(name, function (event) {
          event.preventDefault();
          dropzone.classList.add("dropzone--active");
        });
      });
      ["dragleave", "drop"].forEach(function (name) {
        dropzone.addEventListener(name, function () {
          dropzone.classList.remove("dropzone--active");
        });
      });
      dropzone.addEventListener("drop", function (event) {
        event.preventDefault();
        if (event.dataTransfer && event.dataTransfer.files.length) {
          addFiles(event.dataTransfer.files);
        }
      });
    }

    form.addEventListener("submit", function () {
      // Nunca se llama a preventDefault, ni siquiera con archivos marcados: el
      // aviso del navegador es una comodidad, y la autoridad es el servidor,
      // que revalida y responde con su propio mensaje.
      Array.prototype.forEach.call(
        list.querySelectorAll(".upload-row__state"),
        function (state) {
          state.classList.remove("upload-row__state--ok");
          state.classList.remove("upload-row__state--error");
          state.textContent = "Subiendo…";
        },
      );
      Array.prototype.forEach.call(
        list.querySelectorAll(".upload-selection__remove"),
        function (button) {
          button.disabled = true;
        },
      );
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
      document.querySelectorAll("[data-submit-busy]"),
      bindSubmitBusy,
    );
    Array.prototype.forEach.call(
      document.querySelectorAll("[data-upload-input]"),
      bindUploadQueue,
    );
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
