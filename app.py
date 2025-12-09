import streamlit as st
import pandas as pd
from playwright.sync_api import sync_playwright
import time
import os
from io import BytesIO

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Robô TJSP - Consulta Rápida", layout="wide")

st.title("🤖 Robô de Consulta - TJSP")
st.markdown("""
Cole a lista de processos abaixo (um por linha) e o robô buscará os detalhes automaticamente.
""")

# --- FUNÇÃO DE CONSULTA (O CÉREBRO DO ROBÔ) ---
def consultar_processos_sp(lista_numeros):
    dados_coletados = []
    
    with sync_playwright() as p:
        # Tenta lançar o navegador. Se der erro no caminho, usa o padrão.
        try:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        except:
            browser = p.chromium.launch(headless=True)
            
        page = browser.new_page()

        # Barra de progresso visual
        progresso_texto = st.empty()
        barra = st.progress(0)
        total = len(lista_numeros)

        for i, processo in enumerate(lista_numeros):
            processo = processo.strip() # Remove espaços extras
            if not processo:
                continue # Pula linhas vazias
                
            progresso_texto.text(f"🔍 Consultando processo {i+1}/{total}: {processo}")
            barra.progress((i + 1) / total)

            try:
                # 1. Tenta acessar direto pelo link do processo unificado
                url = f"https://esaj.tjsp.jus.br/cpopg/search.do?conversationId=&dadosConsulta.localPesquisa.cdLocal=-1&cbPesquisa=NUMPROC&dadosConsulta.tipoNuProcesso=UNIFICADO&dadosConsulta.valorConsultaNuProcesso={processo}"
                page.goto(url, timeout=30000)
                
                # Espera um pouco para garantir que carregou
                page.wait_for_timeout(2000)

                # Verifica se apareceu mensagem de erro (ex: Não encontrado)
                if page.locator("text=Não foram encontrados dados").count() > 0:
                    status = "Não encontrado"
                    valor = ""
                    partes = ""
                else:
                    status = "Encontrado"
                    
                    # Tenta pegar o valor da ação (se existir)
                    try:
                        valor = page.locator("#valorAcaoProcesso").inner_text()
                    except:
                        valor = "Não localizado"

                    # Tenta pegar as partes (Autor/Réu)
                    try:
                        partes = page.locator("#tablePartesPrincipais").inner_text()
                        partes = partes.replace("\n", " | ") # Deixa tudo numa linha só
                    except:
                        partes = ""

                # Salva o resultado
                dados_coletados.append({
                    "Numero_Processo": processo,
                    "Status": status,
                    "Valor_Acao": valor,
                    "Envolvidos": partes,
                    "Link": url
                })

            except Exception as e:
                # Se der erro em um, não para tudo. Apenas anota o erro.
                dados_coletados.append({
                    "Numero_Processo": processo,
                    "Status": f"Erro: {str(e)}",
                    "Valor_Acao": "",
                    "Envolvidos": "",
                    "Link": ""
                })

        browser.close()
        barra.empty()
        progresso_texto.empty()

    return pd.DataFrame(dados_coletados)

# --- INTERFACE DE ENTRADA (MUDAMOS AQUI) ---
entrada_texto = st.text_area(
    "Digite ou cole os números dos processos aqui (pressione Enter para pular linha):", 
    height=200,
    placeholder="Exemplo:\n1002345-12.2023.8.26.0100\n0004567-89.2022.8.26.0001"
)

col1, col2 = st.columns([1, 4])

if col1.button("🚀 Iniciar Consulta"):
    if not entrada_texto.strip():
        st.warning("⚠️ Por favor, cole pelo menos um número de processo.")
    else:
        # Transforma o texto em uma lista, separando por linha
        lista_processos = entrada_texto.split('\n')
        # Remove linhas vazias
        lista_processos = [p for p in lista_processos if p.strip()]
        
        st.info(f"Iniciando busca de {len(lista_processos)} processos...")
        
        # Chama a função do robô
        df_resultado = consultar_processos_sp(lista_processos)
        
        st.success("✅ Consulta Finalizada!")
        
        # Mostra a tabela na tela
        st.dataframe(df_resultado)

        # Botão para baixar o Excel
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_resultado.to_excel(writer, index=False, sheet_name='Resultados')
            
        st.download_button(
            label="📥 Baixar Planilha Excel",
            data=buffer.getvalue(),
            file_name="Resultado_Consulta_TJSP.xlsx",
            mime="application/vnd.ms-excel"
        )
