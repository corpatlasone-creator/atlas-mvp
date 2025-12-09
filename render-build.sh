#!/usr/bin/env bash
# Para o script se der erro
set -o errexit

# 1. Instala as dependências do Python
pip install --upgrade pip
pip install -r requirements.txt

# 2. Instala o navegador necessário para o Playwright
playwright install chromium
playwright install-deps
