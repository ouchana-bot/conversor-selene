import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from io import BytesIO
import math
import re

# Mapeamento do De-Para: Tamanho (XML) -> ID (Microvix)
MAPEAMENTO_TAMANHOS = {
    'PP': '2', 'P': '3', 'M': '1', 'G': '4', 'GG': '5', 'XG': '97', 'XGG': '117', 
    'EP': '123', 'EM': '122', 'EG': '102', 'EGG': '124', 'EXG': '41', 'SG': '140', 
    'U': '96', 'G1': '159', 'G2': '160', 'G3': '161', 'G4': '162', 'G5': '163', 
    '01': '98', '02': '158', '03': '99', '04': '150', '06': '151', '08': '152', 
    '10': '153', '12': '154', '14': '155', '16': '156', '18': '157', '34': '20', 
    '36': '22', '38': '24', '40': '26', '42': '28', '44': '30', '46': '69', 
    '48': '165', '50': '71', '52': '72', '54': '73', '56': '74', '58': '75', 
    '60': '76', '90': '133', '95': '134', '100': '135', '105': '136', '110': '137', 
    '115': '138', '120': '139', '6M': '170', '9M': '171', '12M': '172', '18M': '173'
}

def converter_tamanho_para_id(tamanho):
    if not tamanho:
        return ""
    t_clean = str(tamanho).strip().upper()
    if t_clean in MAPEAMENTO_TAMANHOS:
        return MAPEAMENTO_TAMANHOS[t_clean]
    if t_clean.isdigit():
        t_sem_zero = str(int(t_clean))
        if t_sem_zero in MAPEAMENTO_TAMANHOS:
            return MAPEAMENTO_TAMANHOS[t_sem_zero]
        t_com_zero = t_clean.zfill(2)
        if t_com_zero in MAPEAMENTO_TAMANHOS:
            return MAPEAMENTO_TAMANHOS[t_com_zero]
    return "tamanho não cadastrado"

st.set_page_config(page_title="Importador Selene", page_icon="🧦", layout="centered")

st.title("Conversor NFe: Selene 🧦")
st.write("Faça o upload do XML da Selene. O sistema separa Tamanho e Cor e mapeia o Tamanho para o ID do Microvix.")

uploaded_file = st.file_uploader("Arraste e solte o arquivo XML aqui", type=["xml"])

if uploaded_file is not None:
    try:
        tree = ET.parse(uploaded_file)
        root = tree.getroot()
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        
        produtos = root.findall('.//nfe:det', ns)
        
        if not produtos:
            st.error("❌ Nenhum produto encontrado neste XML.")
        else:
            colunas_microvix = [
                "Código", "Descrição", "Referência", "Cód. Auxiliar", "Fornecedor", 
                "Fornecedor exclusivo", "Comprador", "Empresa", "Contabiliza saldo em estoque", 
                "Indisponível para venda", "Setor", "Linha", "Marca", "Coleção", 
                "Espessura", "Classificação", "Tamanho", "Cores", "Unidade de compra", 
                "Unidade de venda", "Fator de conversão", "Múltiplo de venda", "Moeda", 
                "Custo com ICMS (R$)", "Desconto (%)", "Acréscimo (%)", "IPI (%)", 
                "Frete (R$)", "Despesas acessórias (R$)", "Substituição tributária (R$)", 
                "Diferencial ICMS (R$)", "Mark-up (%)", "Preço de venda R$", "Permite desconto", 
                "Comissão %", "Configuração tributária", "NCM", "CEST", "Produto supérfluo", 
                "Tipo de item", "Origem da mercadoria", "Regime de Incidência PIS e COFINS", 
                "Produto é brinde", "Produto de catálogo", "Descrição de catálogo", 
                "Disponível na loja virtual", "Exige controle", "Tipo de controle", 
                "Tamanho controle", "Peso bruto (kg)", "Peso líquido (kg)", "Descrição complementar?", 
                "Altura (frete)", "Largura (frete)", "Comprimento (frete)", "Altura", 
                "Largura", "Comprimento", "Importado por balança", "Produto vendido por (balança)", 
                "Quantidade mínima", "Quantidade máxima", "Quantidade compra", "Localização", 
                "Observação", "Código de barras", "Características", "Status", 
                "Produto Desativado", "Bloqueia atualização de preço franqueadora"
            ]
            
            dados_planilha = []
            
            for det in produtos:
                prod = det.find('nfe:prod', ns)
                
                descricao = prod.find('nfe:xProd', ns).text if prod.find('nfe:xProd', ns) is not None else ""
                referencia = prod.find('nfe:cProd', ns).text if prod.find('nfe:cProd', ns) is not None else ""
                ncm = prod.find('nfe:NCM', ns).text if prod.find('nfe:NCM', ns) is not None else ""
                ean = prod.find('nfe:cEAN', ns).text if prod.find('nfe:cEAN', ns) is not None else ""
                unidade = prod.find('nfe:uCom', ns).text if prod.find('nfe:uCom', ns) is not None else ""
                
                tamanho_extraido = ""
                cor_extraida = "" 
                
                if referencia and "." in referencia:
                    partes = referencia.split(".")
                    if len(partes) >= 3:
                        codigo_final = partes[-1].strip().upper()
                        # Extrai os dois primeiros caracteres para o tamanho e o restante para a cor
                        if len(codigo_final) >= 2:
                            tamanho_extraido = codigo_final[:2]
                            cor_extraida = codigo_final[2:]
                        else:
                            tamanho_extraido = codigo_final
                
                tamanho_id = converter_tamanho_para_id(tamanho_extraido)
                
                custo_str = prod.find('nfe:vUnCom', ns).text if prod.find('nfe:vUnCom', ns) is not None else "0"
                preco_venda_formatado = ""
                try:
                    custo_float = float(custo_str)
                    if custo_float > 0:
                        dobro = custo_float * 2
                        preco_calculado = math.ceil(dobro - 0.90) + 0.90
                        preco_venda_formatado = f"{preco_calculado:.2f}".replace('.', ',')
                except ValueError:
                    preco_venda_formatado = ""
                
                if ean == "SEM GTIN": ean = ""
                
                linha_excel = {coluna: "" for coluna in colunas_microvix}
                
                linha_excel["Descrição"] = descricao
                linha_excel["Referência"] = referencia
                linha_excel["Custo com ICMS (R$)"] = custo_str.replace('.', ',')
                linha_excel["NCM"] = ncm
                linha_excel["Código de barras"] = ean
                linha_excel["Tamanho"] = tamanho_id
                linha_excel["Cores"] = cor_extraida
                linha_excel["Unidade de compra"] = unidade
                linha_excel["Unidade de venda"] = unidade
                linha_excel["Preço de venda R$"] = preco_venda_formatado
                linha_excel["Fator de conversão"] = "1"
                linha_excel["Configuração tributária"] = "1"
                linha_excel["Espessura"] = "0"
                linha_excel["Tipo de item"] = "1"
                linha_excel["Comprador"] = "14"
                linha_excel["Empresa"] = "5"
                linha_excel["Contabiliza saldo em estoque"] = "S"
                
                dados_planilha.append(linha_excel)
                
            df = pd.DataFrame(dados_planilha, columns=colunas_microvix)
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            excel_data = output.getvalue()
            
            st.success(f"✅ Sucesso! {len(produtos)} produtos processados.")
            
            st.download_button(
                label="📥 Baixar Excel Selene",
                data=excel_data,
                file_name="importacao_selene.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
    except Exception as e:
        st.error(f"Erro ao processar: {e}")
