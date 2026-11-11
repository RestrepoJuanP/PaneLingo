/* =============================================================================
   PaneLingo — Editor de maquetación (HU-89, ADR-003)

   Vanilla, sin dependencias. El servidor es la ÚNICA fuente de verdad
   (ADR-003, decisión 4): este archivo nunca calcula líneas, tamaños de letra
   ni interlineados. Pinta lo que devuelven region_layout,
   region_layout_reset y region_translation_edit.

   Lo único que hace en local es mover y redimensionar la CAJA mientras se
   arrastra o se pulsan las flechas, en píxeles de la imagen original, y
   limitarla a los bordes por comodidad: la autoridad sigue siendo el
   servidor, que valida y responde con la maquetación recalculada.

   Las fuentes, los límites de tamaño, el tamaño mínimo de caja y el formato
   del color los emite el servidor en el marcado (patrón de BUG-043). Aquí no
   se escribe ninguno.
   ========================================================================== */

(function () {
  "use strict";

  var SAVE_DELAY_MS = 300;
  var UNDO_LIMIT = 20;
  var LARGE_STEP = 10;
  var DRAG_THRESHOLD_PX = 3;
  var ARROWS = {
    ArrowLeft: [-1, 0],
    ArrowRight: [1, 0],
    ArrowUp: [0, -1],
    ArrowDown: [0, 1],
  };

  function clamp(value, minimum, maximum) {
    return Math.min(Math.max(value, minimum), maximum);
  }

  function readJson(response) {
    return response.json().then(function (payload) {
      return { ok: response.ok, status: response.status, payload: payload };
    });
  }

  function geometryOf(stored) {
    return {
      x: stored.x,
      y: stored.y,
      width: stored.width,
      height: stored.height,
    };
  }

  function storedFromLayout(layout) {
    return {
      x: layout.x,
      y: layout.y,
      width: layout.width,
      height: layout.height,
      font_family: layout.font_choice,
      font_size: layout.is_auto_size ? "auto" : String(layout.font_size),
      text_align: layout.text_align,
      text_color: layout.text_color,
    };
  }

  function createEditor(root) {
    var imageWidth = Number(root.dataset.imageWidth);
    var imageHeight = Number(root.dataset.imageHeight);
    var minBox = Number(root.dataset.minBox);
    var canvas = root.querySelector("[data-ts-canvas]");
    var canvasArea = root.querySelector("[data-ts-canvas-area]");
    var layer = root.querySelector("[data-ts-layer]");
    var status = root.querySelector("[data-ts-status]");
    var retry = root.querySelector("[data-ts-retry]");
    var undoButton = root.querySelector("[data-ts-undo]");
    var undoCount = root.querySelector("[data-ts-undo-count]");
    var approveForm = root.querySelector("[data-ts-approve-form]");
    var approveButton = root.querySelector("[data-ts-approve]");
    var approveReason = root.querySelector("[data-ts-approve-reason]");
    var chip = root.querySelector("[data-ts-chip]");
    var requirements = root.querySelector("[data-ts-requirements]");
    var warnings = root.querySelector("[data-ts-warnings]");
    var empty = root.querySelector("[data-ts-empty]");
    var props = root.querySelector("[data-ts-props]");
    var propsTitle = root.querySelector("[data-ts-props-title]");
    var propsText = root.querySelector("[data-ts-text]");
    var fontSizeInput = root.querySelector("[data-ts-font-size]");
    var colorPicker = root.querySelector("[data-ts-color-picker]");
    var colorHex = root.querySelector("[data-ts-color-hex]");
    var jump = root.querySelector("[data-ts-jump]");
    var jumpNumber = root.querySelector("[data-ts-jump-number]");
    var csrf = approveForm.querySelector("[name=csrfmiddlewaretoken]").value;

    var regions = [];
    var selected = null;
    var undoStack = [];
    var inFlight = 0;
    var hasUnresolvedError = false;
    var retryRegion = null;
    var drag = null;
    var editing = null;

    /* --- Estado de guardado (indicador de HU-23) ------------------------ */

    function setStatus(message, state) {
      status.textContent = message;
      status.dataset.state = state;
    }

    function markDisabled(button, isDisabled) {
      // aria-disabled y no disabled: el botón conserva el foco (CLAUDE.md).
      button.disabled = false;
      button.setAttribute("aria-disabled", String(isDisabled));
    }

    /* --- Regiones -------------------------------------------------------- */

    function regionFrom(box) {
      var data = box.dataset;
      return {
        box: box,
        number: data.number,
        kind: data.kind,
        layoutUrl: data.layoutUrl,
        resetUrl: data.resetUrl,
        translationUrl: data.translationUrl,
        layoutVersion: data.layoutVersion,
        translationVersion: data.translationVersion,
        translation: data.translation,
        fontSize: data.fontSize,
        stored: {
          x: Number(data.x),
          y: Number(data.y),
          width: Number(data.width),
          height: Number(data.height),
          font_family: data.fontChoice,
          font_size: data.autoSize === "true" ? "auto" : data.fontSize,
          text_align: data.textAlign,
          text_color: data.textColor,
        },
        shown: null,
        pending: null,
        undoEntry: null,
        timer: null,
        saving: false,
        queued: false,
        current: Promise.resolve(),
        pick: root.querySelector('[data-ts-pick="' + data.number + '"]'),
      };
    }

    function regionOf(element) {
      var box = element && element.closest("[data-ts-box]");
      return regions.find(function (region) {
        return region.box === box;
      });
    }

    function percent(value, total) {
      return ((value / total) * 100).toFixed(3) + "%";
    }

    function place(region, geometry) {
      var style = region.box.style;
      style.left = percent(geometry.x, imageWidth);
      style.top = percent(geometry.y, imageHeight);
      style.width = percent(geometry.width, imageWidth);
      style.height = percent(geometry.height, imageHeight);
      region.shown = geometry;
    }

    function paint(region, preview) {
      var box = region.box;
      var text = preview.lines.join(" ");
      var lines = box.querySelector("[data-ts-lines]");
      var notice = box.querySelector("[data-ts-notice]");
      box.setAttribute("style", preview.style);
      box.dataset.textAlign = preview.layout.text_align;
      lines.textContent = "";
      preview.lines.forEach(function (line) {
        var span = document.createElement("span");
        span.textContent = line;
        lines.appendChild(span);
      });
      box.classList.toggle("is-overflowing", !preview.fits);
      box.querySelector("[data-ts-overflow]").hidden = preview.fits;
      notice.textContent = preview.export_notice || "";
      notice.hidden = !preview.export_notice;
      box.classList.toggle("ts-box--pending", Boolean(preview.export_notice));
      box.setAttribute("aria-label", "Región " + region.number + ", texto: " + text);
      if (region.pick) {
        region.pick.querySelector("[data-ts-pick-text]").textContent = text;
      }
      region.stored = storedFromLayout(preview.layout);
      region.fontSize = String(preview.layout.font_size);
      region.shown = geometryOf(region.stored);
      if (region.pending && "x" in region.pending) {
        place(region, {
          x: Number(region.pending.x),
          y: Number(region.pending.y),
          width: Number(region.pending.width),
          height: Number(region.pending.height),
        });
      }
      if (region === selected) {
        fillPanel(region);
      }
    }

    /* --- Estado de la página: P7, chip y requisitos ---------------------- */

    function applyPageStatus(page) {
      if (!page) {
        return;
      }
      markDisabled(approveButton, page.is_typeset || Boolean(page.blocker));
      approveButton.textContent = page.is_typeset
        ? "Página maquetada"
        : "Aprobar página";
      approveReason.textContent = page.blocker;
      approveReason.hidden = !page.blocker;
      var badge = chip.querySelector(".badge");
      badge.textContent = page.is_typeset ? "Maquetada" : "Sin aprobar";
      badge.className =
        "badge badge--" + (page.is_typeset ? "success" : "neutral");
      requirements.textContent = "";
      page.requirements.forEach(function (requirement) {
        var item = document.createElement("li");
        item.className =
          "ts-requirements__item ts-requirements__item--" + requirement.state;
        item.textContent = requirement.text;
        requirements.appendChild(item);
      });
      if (!page.is_typeset) {
        warnings.textContent = "";
      }
    }

    function showWarnings(list) {
      warnings.textContent = "";
      list.forEach(function (text) {
        var item = document.createElement("p");
        item.className = "ts-warning";
        item.textContent = text;
        warnings.appendChild(item);
      });
    }

    /* --- Deshacer: 20 pasos por página, en memoria ----------------------- */

    function updateUndo() {
      undoCount.textContent = undoStack.length ? String(undoStack.length) : "";
      markDisabled(undoButton, !undoStack.length);
    }

    function pushUndo(region) {
      var entry = { region: region, fields: Object.assign({}, region.stored) };
      undoStack.push(entry);
      if (undoStack.length > UNDO_LIMIT) {
        undoStack.shift();
      }
      updateUndo();
      return entry;
    }

    function dropUndo(entry) {
      var index = undoStack.indexOf(entry);
      if (index >= 0) {
        undoStack.splice(index, 1);
        updateUndo();
      }
    }

    /* --- Guardado ---------------------------------------------------------- */

    function formFor(region, fields) {
      var data = new FormData();
      data.set("csrfmiddlewaretoken", csrf);
      data.set("version", region.layoutVersion);
      Object.keys(fields).forEach(function (name) {
        data.set(name, fields[name]);
      });
      return data;
    }

    function firstError(errors) {
      var names = Object.keys(errors || {});
      return names.length ? errors[names[0]][0] : "No se pudo guardar.";
    }

    function handleLayoutResult(region, result, entry) {
      var payload = result.payload;
      if (result.ok) {
        region.layoutVersion = payload.version;
        paint(region, payload.preview);
        applyPageStatus(payload.page);
        hasUnresolvedError = false;
        setStatus(payload.message, "saved");
        return;
      }
      dropUndo(entry);
      hasUnresolvedError = true;
      if (payload.status === "conflict") {
        // Nunca se reintenta en silencio: se muestra y se repinta.
        region.pending = null;
        region.layoutVersion = payload.version;
        paint(region, payload.preview);
        setStatus(payload.message, "conflict");
        return;
      }
      place(region, geometryOf(region.stored));
      if (region === selected) {
        fillPanel(region);
      }
      setStatus(firstError(payload.errors), "error");
    }

    function failSave(region, fields, entry) {
      region.pending = Object.assign({}, fields, region.pending || {});
      region.undoEntry = region.undoEntry || entry;
      hasUnresolvedError = true;
      retryRegion = region;
      retry.hidden = false;
      setStatus("No se pudo guardar.", "error");
    }

    function send(region, url, fields, entry, keepalive) {
      var request = {
        method: "POST",
        body: formFor(region, fields),
        credentials: "same-origin",
        headers: { Accept: "application/json" },
      };
      if (keepalive) {
        // Al salir de la página: el navegador termina el envío por su cuenta.
        request.keepalive = true;
        window.fetch(url, request).catch(function () {});
        return Promise.resolve();
      }
      region.saving = true;
      inFlight += 1;
      retry.hidden = true;
      setStatus("Guardando…", "saving");
      region.current = window
        .fetch(url, request)
        .then(readJson)
        .then(function (result) {
          handleLayoutResult(region, result, entry);
        })
        .catch(function () {
          failSave(region, fields, entry);
        })
        .then(function () {
          region.saving = false;
          inFlight -= 1;
          if (region.queued) {
            region.queued = false;
            flush(region, false);
          }
        });
      return region.current;
    }

    function flush(region, keepalive) {
      window.clearTimeout(region.timer);
      if (!region.pending) {
        return region.current;
      }
      if (region.saving && !keepalive) {
        region.queued = true;
        return region.current;
      }
      var fields = region.pending;
      var entry = region.undoEntry;
      region.pending = null;
      region.undoEntry = null;
      return send(region, region.layoutUrl, fields, entry, keepalive);
    }

    function flushAll(keepalive) {
      return Promise.all(
        regions.map(function (region) {
          return flush(region, keepalive);
        }),
      );
    }

    function change(region, fields) {
      if (!region.pending) {
        region.pending = {};
        region.undoEntry = pushUndo(region);
      }
      Object.assign(region.pending, fields);
      window.clearTimeout(region.timer);
      region.timer = window.setTimeout(function () {
        flush(region, false);
      }, SAVE_DELAY_MS);
    }

    function boxFields(geometry) {
      return {
        x: geometry.x,
        y: geometry.y,
        width: geometry.width,
        height: geometry.height,
      };
    }

    function discardPending(region) {
      window.clearTimeout(region.timer);
      if (region.undoEntry) {
        dropUndo(region.undoEntry);
      }
      region.pending = null;
      region.undoEntry = null;
    }

    function undo() {
      var entry = undoStack.pop();
      updateUndo();
      if (!entry) {
        return;
      }
      var region = entry.region;
      discardPending(region);
      place(region, geometryOf(entry.fields));
      region.current.then(function () {
        send(region, region.layoutUrl, entry.fields, null, false);
      });
    }

    function reset(region) {
      discardPending(region);
      var entry = pushUndo(region);
      region.current.then(function () {
        send(region, region.resetUrl, {}, entry, false);
      });
    }

    /* --- Selección y panel ------------------------------------------------- */

    function checkRadio(name, value) {
      var radio = props.querySelector(
        'input[name="' + name + '"][value="' + value + '"]',
      );
      if (radio) {
        radio.checked = true;
      }
    }

    function fillPanel(region) {
      var stored = region.stored;
      var isAuto = stored.font_size === "auto";
      propsTitle.textContent = "Región " + region.number + " · " + region.kind;
      propsText.textContent =
        region.translation || region.box.getAttribute("aria-label");
      checkRadio("font_family", stored.font_family);
      checkRadio("size_mode", isAuto ? "auto" : "fixed");
      fontSizeInput.disabled = isAuto;
      fontSizeInput.value = isAuto ? region.fontSize : stored.font_size;
      checkRadio("text_align", stored.text_align);
      colorPicker.value = stored.text_color.toLowerCase();
      colorHex.value = stored.text_color;
    }

    function select(region, focusBox) {
      if (selected && selected !== region) {
        selected.box.setAttribute("aria-pressed", "false");
        toggleHandles(selected, false);
        if (selected.pick) {
          selected.pick.removeAttribute("aria-current");
        }
      }
      selected = region || null;
      props.hidden = !selected;
      empty.hidden = Boolean(selected);
      jump.hidden = !selected;
      if (!selected) {
        return;
      }
      selected.box.setAttribute("aria-pressed", "true");
      toggleHandles(selected, true);
      if (selected.pick) {
        selected.pick.setAttribute("aria-current", "true");
      }
      jumpNumber.textContent = selected.number;
      fillPanel(selected);
      if (focusBox) {
        selected.box.focus();
      }
    }

    function toggleHandles(region, isVisible) {
      region.box.querySelectorAll("[data-ts-handle]").forEach(function (handle) {
        handle.hidden = !isVisible;
      });
    }

    /* --- Mover y redimensionar: punteros y teclado ------------------------ */

    function clampMove(geometry) {
      return {
        x: clamp(Math.round(geometry.x), 0, imageWidth - geometry.width),
        y: clamp(Math.round(geometry.y), 0, imageHeight - geometry.height),
        width: geometry.width,
        height: geometry.height,
      };
    }

    function resizeFrom(origin, corner, deltaX, deltaY) {
      var left = origin.x;
      var top = origin.y;
      var right = origin.x + origin.width;
      var bottom = origin.y + origin.height;
      if (corner.indexOf("w") >= 0) {
        left = clamp(Math.round(left + deltaX), 0, right - minBox);
      }
      if (corner.indexOf("e") >= 0) {
        right = clamp(Math.round(right + deltaX), left + minBox, imageWidth);
      }
      if (corner.indexOf("n") >= 0) {
        top = clamp(Math.round(top + deltaY), 0, bottom - minBox);
      }
      if (corner.indexOf("s") >= 0) {
        bottom = clamp(Math.round(bottom + deltaY), top + minBox, imageHeight);
      }
      return { x: left, y: top, width: right - left, height: bottom - top };
    }

    function imageScale() {
      return imageWidth / canvas.getBoundingClientRect().width;
    }

    function startDrag(event) {
      var region = regionOf(event.target);
      if (!region || event.button !== 0 || event.target.closest(".ts-edit")) {
        if (!region && !event.target.closest(".ts-edit")) {
          select(null);
        }
        return;
      }
      var handle = event.target.closest("[data-ts-handle]");
      select(region, false);
      region.box.focus({ preventScroll: true });
      drag = {
        region: region,
        corner: handle ? handle.dataset.tsHandle : "",
        startX: event.clientX,
        startY: event.clientY,
        origin: Object.assign({}, region.shown || geometryOf(region.stored)),
        scale: imageScale(),
        moved: false,
      };
      region.box.setPointerCapture(event.pointerId);
      event.preventDefault();
    }

    function moveDrag(event) {
      if (!drag) {
        return;
      }
      var screenX = event.clientX - drag.startX;
      var screenY = event.clientY - drag.startY;
      if (!drag.moved && Math.hypot(screenX, screenY) < DRAG_THRESHOLD_PX) {
        return;
      }
      drag.moved = true;
      drag.region.box.classList.add("is-dragging");
      var deltaX = screenX * drag.scale;
      var deltaY = screenY * drag.scale;
      var origin = drag.origin;
      var geometry = drag.corner
        ? resizeFrom(origin, drag.corner, deltaX, deltaY)
        : clampMove({
            x: origin.x + deltaX,
            y: origin.y + deltaY,
            width: origin.width,
            height: origin.height,
          });
      place(drag.region, geometry);
    }

    function endDrag() {
      if (!drag) {
        return;
      }
      var region = drag.region;
      region.box.classList.remove("is-dragging");
      if (drag.moved) {
        change(region, boxFields(region.shown));
      }
      drag = null;
    }

    function nudge(region, event, direction) {
      var step = event.shiftKey ? LARGE_STEP : 1;
      var shown = region.shown || geometryOf(region.stored);
      var geometry = event.altKey
        ? resizeFrom(
            shown,
            (direction[0] ? "e" : "") + (direction[1] ? "s" : ""),
            direction[0] * step,
            direction[1] * step,
          )
        : clampMove({
            x: shown.x + direction[0] * step,
            y: shown.y + direction[1] * step,
            width: shown.width,
            height: shown.height,
          });
      place(region, geometry);
      change(region, boxFields(geometry));
    }

    function onBoxKey(event) {
      var region = regionOf(event.target);
      if (!region || event.target.closest(".ts-edit")) {
        return;
      }
      var direction = ARROWS[event.key];
      if (direction && !event.ctrlKey && !event.metaKey) {
        event.preventDefault();
        event.stopPropagation();
        select(region, false);
        nudge(region, event, direction);
      } else if (event.key === "Enter" && !event.ctrlKey && !event.metaKey) {
        event.preventDefault();
        startTextEdit(region);
      } else if (event.key === " ") {
        event.preventDefault();
        select(region, false);
      } else if (event.key === "Escape") {
        select(null);
      }
    }

    /* --- Editar el texto en el sitio (CA-89.5, reutiliza HU-18) ----------- */

    function finishTextEdit() {
      if (!editing) {
        return;
      }
      var region = editing.region;
      editing.area.remove();
      editing.hint.remove();
      editing = null;
      region.box.focus();
    }

    function saveText(region, text) {
      var data = new FormData();
      data.set("csrfmiddlewaretoken", csrf);
      data.set("text", text);
      data.set("version", region.translationVersion);
      inFlight += 1;
      setStatus("Guardando…", "saving");
      window
        .fetch(region.translationUrl, {
          method: "POST",
          body: data,
          credentials: "same-origin",
          headers: { Accept: "application/json", "X-Autosave": "1" },
        })
        .then(readJson)
        .then(function (result) {
          var payload = result.payload;
          if (result.ok) {
            region.translationVersion = payload.version;
            region.translation = text;
            paint(region, payload.preview);
            applyPageStatus(payload.page);
            hasUnresolvedError = false;
            setStatus(payload.message, "saved");
            finishTextEdit();
            return;
          }
          // Conflicto o traducción en curso: el texto escrito se conserva.
          if (payload.version) {
            region.translationVersion = payload.version;
          }
          hasUnresolvedError = true;
          setStatus(payload.message, "conflict");
        })
        .catch(function () {
          hasUnresolvedError = true;
          setStatus("No se pudo guardar el texto.", "error");
        })
        .then(function () {
          inFlight -= 1;
        });
    }

    function startTextEdit(region) {
      if (editing) {
        return;
      }
      select(region, false);
      var area = document.createElement("textarea");
      var hint = document.createElement("span");
      hint.className = "ts-edit__hint";
      hint.id = "ts-edit-hint";
      hint.textContent = "Ctrl+Enter guarda · Escape cancela";
      area.className = "ts-edit";
      area.value = region.translation;
      area.setAttribute("aria-label", "Texto de la región " + region.number);
      area.setAttribute("aria-describedby", hint.id);
      area.addEventListener("keydown", function (event) {
        // Todo el teclado pertenece al textarea, incluido su Ctrl+Z nativo.
        event.stopPropagation();
        if (event.key === "Escape") {
          event.preventDefault();
          finishTextEdit();
        } else if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
          event.preventDefault();
          saveText(region, area.value);
        }
      });
      region.box.appendChild(area);
      region.box.appendChild(hint);
      editing = { region: region, area: area, hint: hint };
      area.focus();
    }

    /* --- Panel de propiedades -------------------------------------------- */

    function onPanelChange(event) {
      var field = event.target;
      if (!selected) {
        return;
      }
      if (field.name === "font_family" || field.name === "text_align") {
        change(selected, { [field.name]: field.value });
      } else if (field.name === "size_mode") {
        var isAuto = field.value === "auto";
        fontSizeInput.disabled = isAuto;
        fontSizeInput.value = selected.fontSize;
        change(selected, { font_size: isAuto ? "auto" : selected.fontSize });
      }
    }

    function onPanelInput(event) {
      var field = event.target;
      if (!selected) {
        return;
      }
      if (field === fontSizeInput) {
        if (field.value && field.checkValidity()) {
          change(selected, { font_size: field.value });
        }
      } else if (field === colorPicker) {
        colorHex.value = colorPicker.value.toUpperCase();
        change(selected, { text_color: colorHex.value });
      } else if (field === colorHex) {
        if (field.value && field.checkValidity()) {
          colorPicker.value = field.value.toLowerCase();
          change(selected, { text_color: field.value.toUpperCase() });
        }
      }
    }

    /* --- Aprobar página (P7) ---------------------------------------------- */

    function approve(event) {
      event.preventDefault();
      if (approveButton.getAttribute("aria-disabled") === "true") {
        return;
      }
      markDisabled(approveButton, true);
      flushAll(false)
        .then(function () {
          return window.fetch(approveForm.action, {
            method: "POST",
            body: new FormData(approveForm),
            credentials: "same-origin",
            headers: { Accept: "application/json", "X-Autosave": "1" },
          });
        })
        .then(readJson)
        .then(function (result) {
          applyPageStatus(result.payload.page);
          showWarnings(result.ok ? result.payload.warnings : []);
          setStatus(result.payload.message, result.ok ? "saved" : "error");
        })
        .catch(function () {
          markDisabled(approveButton, false);
          setStatus("No se pudo aprobar la página.", "error");
        });
    }

    /* --- Salir con cambios pendientes ------------------------------------ */

    function onLinkClick(event) {
      var link = event.target.closest("a[href]");
      if (!link || !link.closest(".ws")) {
        return;
      }
      if (link.getAttribute("href").charAt(0) === "#") {
        return;
      }
      flushAll(true);
    }

    function onBeforeUnload(event) {
      if (inFlight > 0 || hasUnresolvedError) {
        event.preventDefault();
        event.returnValue = "";
      }
    }

    /* --- Arranque ---------------------------------------------------------- */

    root.querySelectorAll("[data-ts-js-only]").forEach(function (element) {
      element.hidden = false;
    });
    root.querySelectorAll("[data-ts-nojs]").forEach(function (element) {
      element.hidden = true;
    });
    regions = Array.prototype.map.call(
      root.querySelectorAll("[data-ts-box]"),
      regionFrom,
    );
    markDisabled(approveButton, approveButton.disabled);
    updateUndo();

    layer.addEventListener("pointerdown", startDrag);
    layer.addEventListener("pointermove", moveDrag);
    layer.addEventListener("pointerup", endDrag);
    layer.addEventListener("pointercancel", endDrag);
    layer.addEventListener("keydown", onBoxKey);
    layer.addEventListener("focusin", function (event) {
      var region = regionOf(event.target);
      if (region && !event.target.closest(".ts-edit")) {
        select(region, false);
      }
    });
    layer.addEventListener("dblclick", function (event) {
      var region = regionOf(event.target);
      if (region && !event.target.closest(".ts-edit")) {
        startTextEdit(region);
      }
    });
    // Ctrl+Z solo con el foco en el lienzo o en una caja, nunca en la
    // página entera ni dentro del textarea de edición.
    canvasArea.addEventListener("keydown", function (event) {
      var isUndo =
        (event.ctrlKey || event.metaKey) &&
        !event.shiftKey &&
        event.key.toLowerCase() === "z";
      if (isUndo && !event.target.closest(".ts-edit")) {
        event.preventDefault();
        undo();
      }
    });
    undoButton.addEventListener("click", function () {
      if (undoButton.getAttribute("aria-disabled") !== "true") {
        undo();
      }
    });
    retry.addEventListener("click", function () {
      retry.hidden = true;
      if (retryRegion) {
        flush(retryRegion, false);
      }
    });
    root.querySelector("[data-ts-edit-text]").addEventListener("click", function () {
      if (selected) {
        startTextEdit(selected);
      }
    });
    root.querySelector("[data-ts-reset]").addEventListener("click", function () {
      if (selected) {
        reset(selected);
      }
    });
    root.querySelectorAll("[data-ts-pick]").forEach(function (button) {
      button.addEventListener("click", function () {
        select(
          regions.find(function (region) {
            return region.pick === button;
          }),
          true,
        );
      });
    });
    props.addEventListener("change", onPanelChange);
    props.addEventListener("input", onPanelInput);
    props.addEventListener("submit", function (event) {
      event.preventDefault();
    });
    approveForm.addEventListener("submit", approve);
    document.addEventListener("click", onLinkClick, true);
    window.addEventListener("pagehide", function () {
      flushAll(true);
    });
    window.addEventListener("beforeunload", onBeforeUnload);
  }

  function init() {
    var root = document.querySelector("[data-typesetting-editor]");
    if (root && window.fetch) {
      createEditor(root);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
