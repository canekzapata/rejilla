#!/bin/sh
cd -- "$(dirname -- "$0")" || exit 1
if [ ! -x .venv/bin/python ]; then printf "Ejecuta primero Preparar-Mac.command\n"; exit 1; fi
.venv/bin/python python/ventana.py
