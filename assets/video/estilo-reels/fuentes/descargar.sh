#!/bin/sh
# Descarga las tipografias del estilo. No se versionan en el repo:
# las tres son gratuitas y estan en Google Fonts (OFL / Apache 2.0).
#
#   Anton     -> linea de golpe (condensada pesada)
#   Roboto    -> linea de apoyo (grotesca ancha, redonda y cursiva)
#   Noto Color Emoji -> los emoji en linea
set -e
cd "$(dirname "$0")"

descarga() {
  familia="$1"; archivo="$2"; consulta="$3"; estilo="$4"
  [ -f "$archivo" ] && { echo "ya esta: $archivo"; return; }
  url=$(curl -sS "https://fonts.googleapis.com/css2?family=$consulta" \
        | awk -v e="$estilo" '/font-style/{s=$2} /src:/{if (s ~ e) {print; exit}}' \
        | sed -E 's/.*url\(([^)]+)\).*/\1/')
  [ -n "$url" ] || { echo "no se pudo resolver $familia"; exit 1; }
  curl -sS -o "$archivo" "$url"
  echo "descargada: $archivo ($(wc -c < "$archivo") bytes)"
}

descarga Anton  Anton-Regular.ttf    "Anton"              normal
descarga Roboto Roboto-Bold.ttf      "Roboto:ital,wght@0,700" normal
descarga Roboto Roboto-BoldItalic.ttf "Roboto:ital,wght@1,700" italic
descarga Noto   NotoColorEmoji.ttf   "Noto+Color+Emoji"   normal
