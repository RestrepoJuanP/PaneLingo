# Borrador para la wiki — HU-91, descartada tras el spike

## HU-91 — Limpiar con IA el texto que está sobre el dibujo

Issue: [#91](https://github.com/RestrepoJuanP/PaneLingo/issues/91) ·
Prioridad *Could* · Precedida de un *spike*

**Estado: descartada. No tiene casos de prueba ni pruebas automáticas.**

El *spike* del 10 de noviembre de 2026 comparó las dos opciones de la
historia y ninguna cumplió:

- **Gemini con edición de imagen:** descartado sin enviar ninguna imagen.
  Ningún modelo que edite imágenes tiene nivel gratuito y el proyecto no
  tiene `GEMINI_API_KEY`.
- **OpenCV (`cv2.inpaint`):** 0 de 3 regiones reales aceptables con
  cualquiera de las 16 configuraciones probadas, frente a un criterio fijado
  de antemano de al menos 2 de 3. La máscara por umbral no separa el texto
  del dibujo.

Por eso no se añade ninguna dependencia y los CP-91.1 a CP-91.6 propuestos
en el issue no se redactan. Las regiones que la limpieza de HU-88 deja en
«Limpieza manual» se avisan antes de aprobar la maquetación y antes de
exportar, y la caja del editor de HU-89 puede tapar el texto original.

El material, las configuraciones, el resultado y las alternativas con su
coste están en
[ADR-003, P4 — Spike de HU-91](adr/ADR-003-edicion-de-imagen.md#p4--spike-de-hu-91).
