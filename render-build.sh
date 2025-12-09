#!/usr/bin/env bash
# O comando abaixo faz o processo parar se der qualquer erro
set -o errexit

# 1. Atualiza o pip e instala as bibliotecas
pip install --upgrade pip
pip install -r requirements.txt

# 2. Instala o navegador Chromium E o componente Headless Shell (IMPORTANTE)
playwright install chromium
playwright install chromium-headless-shell
playwright install-deps
