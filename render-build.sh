#!/usr/bin/env bash
# O comando abaixo faz o processo parar se der qualquer erro
set -o errexit

# 1. Instala as dependências do Python (Streamlit, Pandas, etc)
pip install -r requirements.txt

# 2. Instala APENAS o navegador Chromium do Playwright
# (Isso evita o erro de senha "su" e garante que o arquivo exista)
playwright install chromium
