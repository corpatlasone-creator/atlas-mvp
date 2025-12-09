import pandas as pd
import re
import time
from pypdf import PdfReader
from playwright.sync_api import sync_playwright

# --- 1. DETECTOR DE TRIBUNAL ---
def identificar_tribunal(texto_arquivo):
    texto = texto_arquivo.upper()
    if "SÃO PAULO" in texto or "TJSP" in texto: return "TJSP"
    elif "FEDERAL" in texto or "TRF" in texto: return "TRF3"
    return "TJSP" # Padrão se não identificar

# --- 2. CONVERSOR PDF/EXCEL ---
def converter_arquivo_para_dados(arquivo_upload):
    # Se for Excel
    if arquivo_upload.name.endswith(".xlsx"):
        df = pd.read_excel(arquivo_upload)
        # Procura coluna de processo
        col_proc = next((c for c in df.columns if "PROC" in c.upper()), None)
        if col_proc:
            df = df.rename(columns={col_proc: "Processo"})
            return df, "TJSP" # Assume TJSP por padrão no Excel
        return None, "ERRO: Coluna 'Processo' não encontrada no Excel."

    # Se for PDF
    reader = PdfReader(arquivo_upload)
    texto_completo = ""
    for i, page in enumerate(reader.pages):
        if i > 5: break # Lê só as primeiras 5 pgs pra identificar tribunal
        texto_completo += page.extract_text() + "\n"
        
    tribunal = identificar_tribunal(texto_completo)
    
    # Extrai TODOS os textos para pegar processos
    texto_total = ""
    for page in reader.pages: texto_total += page.extract_text() + "\n"

    # Regex CNJ (Pega qualquer número de processo)
    padrao = re.compile(r"(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})")
    matches = list(padrao.finditer(texto_total))
    
    dados = []
    for m in matches:
        dados.append({"Processo": m.group(1), "Origem": tribunal})
        
    return pd.DataFrame(dados), tribunal

# --- 3. ROBÔ TJSP (Aquele que funciona!) ---
def robo_tjsp(page, processo):
    num_limpo = re.sub(r'[^0-9]', '', str(processo))
    if len(num_limpo) < 13: return {"Status": "Número Inválido", "Valor": 0}

    try:
        page.goto("https://esaj.tjsp.jus.br/cpopg/open.do")
        try: page.wait_for_selector("#cbPesquisa", timeout=3000)
        except: return {"Status": "Erro Conexão", "Valor": 0}
        
        page.evaluate("document.getElementById('cbPesquisa').value = 'NUMPROC'")
        page.dispatch_event("#cbPesquisa", "change")
        
        # Seleciona TODOS OS FOROS (-1) para evitar erro de "não encontrado"
        try: page.select_option("#foroNumeroUnificado", value="-1")
        except: page.evaluate("document.getElementById('foroNumeroUnificado').value = '-1'")
        
        page.click("#numeroDigitoAnoUnificado")
        page.keyboard.type(num_limpo[:13], delay=30) # Digita devagar
        page.click("#botaoConsultarProcessos")
        
        # Verifica se achou
        try:
            page.wait_for_selector("#headerProcessoDados, #mensagemRetorno", timeout=5000)
            if page.locator("#mensagemRetorno").is_visible():
                return {"Status": "Não Encontrado", "Valor": 0}
        except: pass

        # Busca Valor
        valor = 0.0
        if page.get_by_text("Valor da Ação:").count() > 0:
            txt = page.get_by_text("Valor da Ação:").locator("xpath=..").inner_text()
            try: 
                limpo = txt.split("R$")[1].strip().replace(".","").replace(",",".")
                valor = float(limpo)
            except: pass
            
        status = "✅ APROVADO" if valor >= 250000 else "Baixo Valor"
        if valor == 0: status = "Valor não lido"
        
        # Pega Credor
        credor = ""
        try:
            txt = page.locator("#tablePartesPrincipais").inner_text()
            if "Exequente:" in txt: credor = txt.split("Exequente:")[1].split("\n")[0].strip()
        except: pass

        return {"Status": status, "Valor R$": f"{valor:,.2f}", "Credor": credor, "Link": page.url}

    except Exception as e:
        return {"Status": f"Erro: {str(e)[:20]}", "Valor": 0}

# --- 4. ROBÔ TRF3 (O Futuro) ---
def robo_trf3(page, processo):
    # Lógica futura para federal
    return {"Status": "Sistema TRF em desenvolvimento", "Valor": 0}

# --- 5. O MAESTRO (ROUTER) ---
def analisar_processo_router(page, processo, tribunal):
    if tribunal == "TJSP":
        return robo_tjsp(page, processo)
    elif tribunal == "TRF3":
        return robo_trf3(page, processo)
    else:
        return robo_tjsp(page, processo) # Tenta TJSP se não souber