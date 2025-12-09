#!/usr/bin/env bash
# O comando abaixo faz o processo parar se der qualquer erro
set -o errexit

# 1. Atualiza o pip e instala as dependências
pip install --upgrade pip
pip install -r requirements.txt

# 2. Instala APENAS os navegadores do Playwright
# Removemos o "install-deps" porque ele requer sudo e falha no Render
playwright install chromium chromium-headless-shell
