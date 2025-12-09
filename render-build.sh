#!/usr/bin/env bash
# O comando abaixo faz o processo parar se der qualquer erro
set -o errexit

# 1. Atualiza o pip e instala as dependências (Streamlit, Pandas, etc)
pip install --upgrade pip
pip install -r requirements.txt

# 2. Instala APENAS o navegador Chromium do Playwright
# (Isso garante que o arquivo executável exista)
playwright install chromium
