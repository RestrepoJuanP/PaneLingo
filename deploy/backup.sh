#!/bin/sh
# Copia de seguridad diaria de PaneLingo en producción.
# Copia la base en caliente con la API de copia de SQLite (sin detener la
# aplicación), empaqueta las imágenes y conserva los últimos siete días.
set -eu

BACKUP_DIR=/opt/panelingo-backups
VOLUME=panelingo_panelingo-data
STAMP=$(date +%F)

mkdir -p "$BACKUP_DIR"
docker run --rm -v "$VOLUME":/data -v "$BACKUP_DIR":/backup alpine sh -c "
  apk add --no-cache sqlite >/dev/null &&
  rm -rf /tmp/snapshot && mkdir -p /tmp/snapshot &&
  sqlite3 /data/db.sqlite3 \".backup '/tmp/snapshot/db.sqlite3'\" &&
  cp -r /data/media /tmp/snapshot/media &&
  tar czf /backup/panelingo-$STAMP.tar.gz -C /tmp/snapshot .
"
find "$BACKUP_DIR" -name 'panelingo-*.tar.gz' -mtime +7 -delete
echo "Copia lista: $BACKUP_DIR/panelingo-$STAMP.tar.gz"
