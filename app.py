import streamlit as st
import pandas as pd
from playwright.sync_api import sync_playwright
import os
import time
from io import BytesIO

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Automação de Precatórios SP", layout="wide")

# --- FUNÇÃO DE AUTOMAÇÃO (ROBÔ) ---
def consultar_processos_sp(df_entrada):
    resultados = []
    
    # Barra de progresso visual
    progresso_bar = st.progress(0)
    status_text = st.empty()
    total = len(df_entrada)

    with sync_playwright() as p:
        # CONFIGURAÇÃO CRÍTICA PARA O RENDER
        browser = p.chromium.launch(
            headless=True, 
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        page = context.new_page()

        for index, row in df_entrada.iterrows():
            # Tenta pegar a coluna do processo (ajuste o nome se necessário baseando-se no seu PDF)
            # No seu PDF a coluna chama "N° Processo DEPRE" ou similar
            numero_processo = str(row.get('N° Processo DEPRE', row.get('Processo', '')))
            
            # Limpa formatação (remove pontos e traços) para a busca
            processo_limpo = ''.join(filter(str.isdigit, numero_processo))

            dado_coletado = {
                "Processo Original": numero_processo,
                "Status": "Não processado",
                "Última Movimentação": "",
                "Juiz/Vara": ""
            }

            if len(processo_limpo) < 10:
                dado_coletado["Status"] = "Número inválido"
                resultados.append(dado_coletado)
                continue

            try:
                status_text.text(f"Consultando {index + 1}/{total}: {numero_processo}...")
                
                # --- LÓGICA DE NAVEGAÇÃO NO TJSP (ESAJ) ---
                # URL de consulta de 1º grau (exemplo)
                page.goto("https://esaj.tjsp.jus.br/cpopg/open.do", timeout=60000)
                
                # Preenche o campo de processo unificado (ajuste o seletor se o site mudar)
                page.locator("#processoMascaradoClient").fill(numero_processo)
                page.locator("#button-consultarProcesso").click()
                
                # Espera carregar. Se pedir senha ou der erro, vai cair no 'except'
                try:
                    # Espera aparecer o título do processo ou aviso de erro
                    page.wait_for_selector("#tabelaTodasMovimentacoes, #mensagemRetorno", timeout=5000)
                except:
                    pass

                # Verifica se achou
                if page.locator("#tabelaTodasMovimentacoes").count() > 0:
                    # Pega a última movimentação
                    ult_mov = page.locator("#tabelaTodasMovimentacoes tr").first.inner_text()
                    vara = page.locator("#varaProcesso").inner_text() if page.locator("#varaProcesso").count() > 0 else ""
                    
                    dado_coletado["Status"] = "Encontrado"
                    dado_coletado["Última Movimentação"] = ult_mov.strip()
                    dado_coletado["Juiz/Vara"] = vara.strip()
                else:
                    dado_coletado["Status"] = "Não encontrado / Segredo de Justiça / Captcha"

            except Exception as e:
                dado_coletado["Status"] = f"Erro: {str(e)}"

            resultados.append(dado_coletado)
            
            # Atualiza barra de progresso
            progresso_bar.progress((index + 1) / total)
            time.sleep(1) # Pausa pequena para não bloquear o IP

        browser.close()
    
    status_text.text("Finalizado!")
    return pd.DataFrame(resultados)

# --- INTERFACE DO USUÁRIO ---

st.title("🤖 Robô de Consulta - Precatórios SP")
st.markdown("Faça upload da lista (Excel ou PDF convertido) e o sistema consultará automaticamente no TJSP.")

arquivo_upload = st.file_uploader("Solte seu arquivo aqui (.xlsx)", type=["xlsx"])

if arquivo_upload:
    df = pd.read_excel(arquivo_upload)
    st.dataframe(df.head())
    
    st.info(f"Arquivo carregado com {len(df)} linhas. Clique abaixo para iniciar a automação.")

    if st.button("🚀 Iniciar Automação"):
        with st.spinner("O robô está trabalhando... Isso pode levar alguns minutos."):
            # Chama a função de automação
            df_resultado = consultar_processos_sp(df)
            
            st.success("Consulta concluída!")
            st.dataframe(df_resultado)
            
            # Botão para baixar o Excel final
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_resultado.to_excel(writer, index=False, sheet_name='Resultados')
            
            st.download_button(
                label="📥 Baixar Relatório Completo em Excel",
                data=buffer.getvalue(),
                file_name="Relatorio_Precatórios_SP.xlsx",
                mime="application/vnd.ms-excel"
            )
