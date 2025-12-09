import streamlit as st
import pandas as pd
import robo_core
from playwright.sync_api import sync_playwright
import time

# CONFIGURAÇÃO VISUAL
st.set_page_config(page_title="Atlas Jurídico", page_icon="⚖️", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    .stButton>button { background-color: #0d6efd; color: white; border-radius: 8px; height: 3em; width: 100%; }
</style>
""", unsafe_allow_html=True)

# LOGIN
if "logado" not in st.session_state: st.session_state["logado"] = False

if not st.session_state["logado"]:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.title("🔐 Atlas Login")
        email = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("ACESSAR"):
            # AQUI VOCÊ CONTROLA QUEM ENTRA
            if email == "admin" and senha == "1234":
                st.session_state["logado"] = True
                st.rerun()
            elif email == "cliente@atlas.com" and senha == "atlas10":
                st.session_state["logado"] = True
                st.rerun()
            else:
                st.error("Acesso negado.")
    st.stop()

# ÁREA DO CLIENTE
with st.sidebar:
    st.title("Atlas Jurídico")
    st.write("v2.0 - Multi-Tribunal")
    if st.button("Sair"):
        st.session_state["logado"] = False
        st.rerun()

st.title("🚀 Central de Varredura de Precatórios")
st.info("O sistema detecta automaticamente se o arquivo é do TJSP, Federal, etc.")

# UPLOAD
arquivos = st.file_uploader("Solte seus arquivos (PDF ou Excel)", type=["pdf", "xlsx"], accept_multiple_files=True)

if arquivos:
    lista_consolidada = []
    st.write("---")
    
    # 1. PREPARAÇÃO
    for arq in arquivos:
        with st.spinner(f"Lendo {arq.name}..."):
            df, tribunal = robo_core.converter_arquivo_para_dados(arq)
            if df is not None:
                st.success(f"✅ **{arq.name}**: Identificado como **{tribunal}** ({len(df)} processos)")
                df["Tribunal_Alvo"] = tribunal
                lista_consolidada.append(df)
            else:
                st.error(f"❌ Erro ao ler {arq.name}")

    # 2. EXECUÇÃO
    if lista_consolidada:
        df_final = pd.concat(lista_consolidada, ignore_index=True)
        st.metric("Processos na Fila", len(df_final))
        
        if st.button("INICIAR VARREDURA AUTOMÁTICA"):
            resultados = []
            bar = st.progress(0)
            status = st.empty()
            total = len(df_final)
            
            with sync_playwright() as p:
                # HEADLESS=TRUE É OBRIGATÓRIO NA NUVEM
                browser = p.chromium.launch(
    headless=True,
    args=["--no-sandbox", "--disable-setuid-sandbox"]
)
                page = browser.new_page()
                
                for i, row in df_final.iterrows():
                    proc = row["Processo"]
                    trib = row["Tribunal_Alvo"]
                    
                    status.markdown(f"🔍 Analisando **{i+1}/{total}**: `{proc}` ({trib})...")
                    
                    # CÉREBRO: Decide qual robô usar
                    dados = robo_core.analisar_processo_router(page, proc, trib)
                    
                    final = row.to_dict()
                    final.update(dados)
                    resultados.append(final)
                    
                    bar.progress((i+1)/total)
                
                browser.close()
            
            st.success("Varredura Completa!")
            
            # RESULTADOS
            df_res = pd.DataFrame(resultados)
            st.dataframe(df_res)
            
            # DOWNLOAD
            import io
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_res.to_excel(writer, index=False)
                

            st.download_button("📥 BAIXAR RELATÓRIO FINAL", buffer, "Atlas_Brasil.xlsx", "application/vnd.ms-excel")
