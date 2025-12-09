#!/usr/bin/env bash
# O comando abaixo faz o processo parar se der qualquer erro
set -o errexit

# 1. Atualiza o pip e instala as dependências do Python
pip install --upgrade pip
pip install -r requirements.txt

# 2. Instala os navegadores do Playwright
# IMPORTANTE: Não usamos "install-deps" aqui pois o Render bloqueia
playwright install chromium chromium-headless-shell
