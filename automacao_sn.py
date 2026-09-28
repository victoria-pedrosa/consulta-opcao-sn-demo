import os
import time
import re
import shutil
import random
import pandas as pd
from DrissionPage import ChromiumPage, ChromiumOptions
from dotenv import load_dotenv
load_dotenv()  # lê o .env local (não vai para o GitHub)

def higienizar_nome_arquivo(nome):
    """Remove caracteres inválidos para o nome do arquivo"""
    return re.sub(r'[\\/*?:"<>|]', "", str(nome)).strip()

def aguardar_novo_pdf(pasta_origem, arquivos_antes, timeout=25):
    """Fica monitorando a pasta de downloads até o PDF baixar"""
    inicio = time.time()
    while time.time() - inicio < timeout:
        arquivos_agora = set(f for f in os.listdir(pasta_origem) if f.lower().endswith(".pdf"))
        novos = arquivos_agora - arquivos_antes
        if novos:
            arquivo_novo = list(novos)[0]
            caminho = os.path.join(pasta_origem, arquivo_novo)
            try:
                tam1 = os.path.getsize(caminho)
                time.sleep(0.5)
                tam2 = os.path.getsize(caminho)
                if tam1 == tam2 and tam1 > 0:
                    return caminho
            except:
                pass
        time.sleep(1)
    return None

def main():
    # ==========================================
    # 1. CONFIGURAÇÃO DE PASTAS E ARQUIVOS
    # ==========================================
    PASTA_DOWNLOADS = os.getenv("PASTA_DOWNLOADS")
    PASTA_DESTINO = os.getenv("PASTA_DESTINO")
    os.makedirs(PASTA_DESTINO, exist_ok=True)
    
    PLANILHA_ORIGINAL = "Consulta SN 2026.xlsx"
    PLANILHA_RESULTADO = "Resultado_Consulta_Automatizada_Drission.xlsx"
    
    print("\n" + "="*70)
    print("🚀 INICIANDO SISTEMA COM DRISSIONPAGE (FINGERPRINT ZERO)")
    print("="*70)
    
    if os.path.exists(PLANILHA_RESULTADO):
        print(f"📖 Encontrado arquivo de progresso: '{PLANILHA_RESULTADO}'. Retomando de onde parou...")
        df = pd.read_excel(PLANILHA_RESULTADO)
    else:
        print(f"📖 Lendo planilha original: '{PLANILHA_ORIGINAL}'...")
        try:
            df = pd.read_excel(PLANILHA_ORIGINAL)
            df['Status_Processamento'] = "Pendente"
            df['Aviso_Exclusao_2027'] = ""
        except Exception as e:
            print(f"❌ Erro ao ler a planilha original: {e}")
            return

    # ==========================================
    # 2. INICIAR O NAVEGADOR (Sem WebDriver)
    # ==========================================
    print("\n🔌 Iniciando o Navegador Indetectável...")
    
    co = ChromiumOptions()
    co.set_pref("download.default_directory", PASTA_DOWNLOADS)
    co.set_pref("download.prompt_for_download", False)
    co.set_pref("plugins.always_open_pdf_externally", True)
    
    # NOVOS COMANDOS: Desativando a verificação de vírus/segurança do Chrome
    co.set_pref("safebrowsing.enabled", False)
    co.set_pref("safebrowsing.disable_download_protection", True)
    co.set_argument("--disable-features=SafeBrowsing")
    co.set_argument("--safebrowsing-disable-download-protection")
    co.set_argument("--no-sandbox")
    
    try:
        page = ChromiumPage(co)
        print("✅ Navegador aberto com sucesso e downloads liberados!")
    except Exception as e:
        print(f"❌ ERRO ao abrir o navegador: {e}")
        return

    # ==========================================
    # 3. LOOP DE PROCESSAMENTO
    # ==========================================
    for index, row in df.iterrows():
        if str(row.get('Status_Processamento')) == "Concluído":
            continue
            
        cnpj_raw = row.get('CNPJ Sem Pontuação', '')
        empresa_nome = row.get('Empresa', f'Empresa_{index+1}')
        cnpj = ''.join(filter(str.isdigit, str(cnpj_raw))).zfill(14)
        
        if len(cnpj) != 14:
            df.at[index, 'Status_Processamento'] = "Erro - CNPJ Inválido"
            df.to_excel(PLANILHA_RESULTADO, index=False)
            continue
            
        print(f"\n[{index+1}/{len(df)}] Processando: {empresa_nome} (CNPJ: {cnpj})")
        
        max_tentativas = 3
        tentativa_atual = 0
        sucesso_processamento = False
        
        while tentativa_atual < max_tentativas and not sucesso_processamento:
            tentativa_atual += 1
            
            try:
                # 3.1 NAVEGAÇÃO
                page.get("https://consopt.www8.receita.fazenda.gov.br/consultaoptantes")
                page.wait(2, 3.5)
                
                # 3.2 PREENCHIMENTO NATIVO DRISSIONPAGE
                try:
                    # Localiza o campo CNPJ
                    campo_cnpj = page.ele('#Cnpj')
                    
                    # O método input do DrissionPage já simula digitação humana nativamente
                    campo_cnpj.input(cnpj, clear=True)
                    page.wait(0.5, 1.2)
                    
                    # Clica no botão Consultar
                    btn_consultar = page.ele('xpath://button[contains(text(), "Consultar")]')
                    btn_consultar.click()
                    
                    page.wait(3, 5)
                except Exception as e:
                    print(f"⚠️ Erro ao preencher: {e}")
                
                # 3.3 VERIFICA BLOQUEIOS REAIS
                if "Impedido por proteção Captcha" in page.html or "Comportamento de Robô" in page.html:
                    print(f"🛑 Bloqueio detectado (Tentativa {tentativa_atual}/{max_tentativas}). Recuando...")
                    page.get("about:blank")
                    tempo_espera = random.uniform(5.0, 8.0)
                    print(f"⏳ Aguardando {tempo_espera:.1f} seg...")
                    time.sleep(tempo_espera) 
                    continue 
                    
                # 3.4 LEITURA DA TELA DE RESULTADO
                prefixo_pdf = "REGULAR"
                status_para_planilha = "Não existem"
                
                try:
                    btn_mais_info = page.ele('#btnMaisInfo', timeout=3)
                    if btn_mais_info:
                        btn_mais_info.click()
                        page.wait(1.5, 2.5)
                        
                        texto_tela_info = page.html
                        if "Exclusão de Ofício - Débitos" in texto_tela_info and "2027" in texto_tela_info:
                            status_para_planilha = "Exclusão de Ofício - Débitos (01/2027)"
                            prefixo_pdf = "EXCLUSAO012027"
                except:
                    status_para_planilha = "Sem botão de Mais Informações (REGULAR)"
                    
                # 3.5 GERAR E AGUARDAR O PDF
                arquivos_pdf_antes = set(f for f in os.listdir(PASTA_DOWNLOADS) if f.lower().endswith(".pdf"))
                
                btn_gerar_pdf = page.ele('#GerarPDF')
                if btn_gerar_pdf:
                    btn_gerar_pdf.click()
                    
                    print(f"🔎 Lendo status ({prefixo_pdf}) | Baixando PDF...")
                    novo_pdf_caminho = aguardar_novo_pdf(PASTA_DOWNLOADS, arquivos_pdf_antes)
                    
                    # 3.6 SALVAMENTO
                    if novo_pdf_caminho:
                        nome_limpo = higienizar_nome_arquivo(empresa_nome)
                        novo_nome_arquivo = f"{prefixo_pdf}-{nome_limpo}.pdf"
                        caminho_final = os.path.join(PASTA_DESTINO, novo_nome_arquivo)
                        
                        if os.path.exists(caminho_final):
                            os.remove(caminho_final)
                            
                        shutil.move(novo_pdf_caminho, caminho_final)
                        print(f"✅ PDF salvo: {novo_nome_arquivo}")
                        
                        df.at[index, 'Status_Processamento'] = "Concluído"
                        df.at[index, 'Aviso_Exclusao_2027'] = status_para_planilha
                        sucesso_processamento = True 
                    else:
                        print("⚠️ Erro: O PDF falhou ao baixar.")
                        if tentativa_atual == max_tentativas:
                            df.at[index, 'Status_Processamento'] = "Erro - Falha no Download"
                else:
                    print("⚠️ Erro: Botão Gerar PDF não encontrado.")
                    if tentativa_atual == max_tentativas:
                        df.at[index, 'Status_Processamento'] = "Erro - Tela Inesperada"
                        
            except Exception as e:
                print(f"❌ Erro na execução: {e}")
                if tentativa_atual == max_tentativas:
                    df.at[index, 'Status_Processamento'] = "Erro Inesperado"
                time.sleep(random.uniform(2.0, 4.0))
                
        df.to_excel(PLANILHA_RESULTADO, index=False)
        print("💾 Checkpoint salvo.")

    print("\n" + "="*70)
    print("🎉 PROCESSAMENTO CONCLUÍDO!")
    print("="*70)
    page.quit()

if __name__ == "__main__":
    main()
