#!/bin/sh
cd -- "$(dirname -- "$0")" || exit 1
if command -v python3.13 >/dev/null 2>&1; then python3.13 preparar.py; else python3 preparar.py; fi
printf "\nPresiona Enter para cerrar."
read respuesta
