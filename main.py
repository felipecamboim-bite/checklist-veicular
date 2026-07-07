import streamlit as st
import smtplib
from email.message import EmailMessage
import base64
import os
import re
from datetime import datetime
from supabase import create_client

# --- CONFIGURAÇÃO SUPABASE ---
supabase_url = st.secrets["SUPABASE"]["URL"]
supabase_key = st.secrets["SUPABASE"]["KEY"]
supabase = create_client(supabase_url, supabase_key)
senha = st.secrets["SUPABASE"]["EMAIL_SENHA"]

st.set_page_config(page_title="Checklist Veicular", layout="centered")

# --- ESTILO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;500&display=swap');
    .stApp { background-color: rgba(0, 0, 0, 0.6) !important; background-blend-mode: darken; }
    h1 { font-family: 'Oswald', sans-serif !important; font-weight: 500 !important; font-size: 36px !important; color: #ffffff !important; text-transform: uppercase !important; letter-spacing: 0.5px !important; margin-bottom: 20px !important; }
    div[data-baseweb="select"] > div, .stTextInput > div > div > input, .stTextArea > div > div > textarea { background-color: #2b2b2b !important; color: #ffffff !important; border: 1px solid #444444 !important; font-family: 'Oswald', sans-serif !important; }
    label, p, span, div { color: #ffffff !important; font-family: 'Oswald', sans-serif !important; }
    div[role="listbox"] { background-color: #2b2b2b !important; color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_background_images():
    try:
        base_path = os.path.dirname(os.path.abspath(__file__))
        pasta_imagens = os.path.join(base_path, 'imagens')
        
        # DEBUG: Isso vai mostrar na tela se a pasta existe
        if not os.path.exists(pasta_imagens):
            st.error(f"Pasta 'imagens' não encontrada em: {pasta_imagens}")
            return

        arquivos = {f.lower(): f for f in os.listdir(pasta_imagens)}
        
        # DEBUG: Verifica se os arquivos necessários existem
        arquivos_esperados = ['desktop.png', 'tablet.png', 'mobile.png']
        for arq in arquivos_esperados:
            if arq not in arquivos:
                st.error(f"Arquivo não encontrado: {arq}")
                return

        desktop_bg = get_base64_of_bin_file(os.path.join(pasta_imagens, arquivos['desktop.png']))
        tablet_bg = get_base64_of_bin_file(os.path.join(pasta_imagens, arquivos['tablet.png']))
        mobile_bg = get_base64_of_bin_file(os.path.join(pasta_imagens, arquivos['mobile.png']))
        
        st.markdown(f"""
            <style>
            .stApp {{ background-image: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url("data:image/png;base64,{desktop_bg}"); background-size: cover; background-position: center; }}
            @media (max-width: 1024px) {{ .stApp {{ background-image: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url("data:image/png;base64,{tablet_bg}"); }} }}
            @media (max-width: 600px) {{ .stApp {{ background-image: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url("data:image/png;base64,{mobile_bg}"); }} }}
            </style>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Erro ao carregar imagens: {e}")

# Lembre-se de remover o # para chamar a função abaixo
set_background_images()

def validar_nome(nome): return len(nome.strip().split()) >= 3

def enviar_email(nome, dados):
    email_origem = "automacao.clicklog@gmail.com"
    senha = st.secrets["SUPABASE"]["EMAIL_SENHA"]
    email_destino = "analista@clicklogtransportes.com.br"
    msg = EmailMessage()
    msg['Subject'] = f"Checklist Recebido: {nome}"
    msg['From'] = email_origem
    msg['To'] = email_destino
    corpo = f"Motorista: {nome}\n\nRespostas:\n"
    for p, r in dados.items(): corpo += f"{p}: {r}\n"
    msg.set_content(corpo)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(email_origem, senha)
        smtp.send_message(msg)

def salvar_no_supabase(nome, dados, client):
    dados_banco = {
        "nome_motorista": nome,
        "data_envio": datetime.now().isoformat(),  # ESSENCIAL
        "veiculo_placa": dados["Veículo (Placa)"],
        "data_ultima_manutencao": dados["Data da ultima manutencao"],
        "extintor_validade": dados["Extintor na validade?"],
        "bau_avarias": dados["Bau sem avarias?"],
        "pneus_bons": dados["Pneus bons?"],
        "espelhos_ok": dados["Espelhos ok?"],
        "direcao_ok": dados["Direcao ok?"],
        "nivel_arrefecimento": dados["Nível arrefecimento?"],
        "suspensao_ok": dados["Suspensao ok?"],
        "sinalizacao_ok": dados["Sinalizacao ok?"],
        "carrinho_2_rodas": dados["Carrinho 2 rodas?"],
        "freios_ok": dados["Freios ok?"],
        "nivel_oleo": dados["Nivel oleo motor ok?"],
        "parabrisa_ok": dados["Parabrisa ok?"],
        "chave_triangulo_macaco": dados["Chave/Triângulo/Macaco?"]
    }
    response = client.table("inspecoes").insert(dados_banco).execute()
    return response

# --- LÓGICA DO APP ---
if 'etapa' not in st.session_state: st.session_state.etapa = 'nome'
if 'nome_completo' not in st.session_state: st.session_state.nome_completo = ""

if st.session_state.etapa == 'nome':
    st.title("Seja bem-vindo à página de Checklist do seu veículo.")
    nome = st.text_input("Preencha seu nome completo:")
    if st.button("Avançar"):
        if validar_nome(nome):
            st.session_state.nome_completo = nome
            st.session_state.etapa = 'checklist'
            st.rerun()
        else: st.error("Nome incompleto! Digite nome e sobrenome.")

elif st.session_state.etapa == 'checklist':
    st.title("Checklist de Inspeção")
    st.write(f"Motorista: **{st.session_state.nome_completo}**")
    with st.form("form_check"):
        c1, c2, c3 = st.columns(3)
        respostas = {}
        with c1:
            for q in ["Extintor na validade?", "Bau sem avarias?", "Pneus bons?", "Espelhos ok?", "Direcao ok?"]:
                respostas[q] = st.selectbox(q, ["Conforme", "Não conforme"], index=None, placeholder="Selecione...", key=f"c1_{q}")
        with c2:
            for q in ["Nível arrefecimento?", "Suspensao ok?", "Sinalizacao ok?", "Carrinho 2 rodas?"]:
                respostas[q] = st.selectbox(q, ["Conforme", "Não conforme"], index=None, placeholder="Selecione...", key=f"c2_{q}")
            respostas["Veículo (Placa)"] = st.text_input("Veículo (Placa):", placeholder="ABC-1234")
        with c3:
            for q in ["Freios ok?", "Nivel oleo motor ok?", "Parabrisa ok?", "Chave/Triângulo/Macaco?"]:
                respostas[q] = st.selectbox(q, ["Conforme", "Não conforme"], index=None, placeholder="Selecione...", key=f"c3_{q}")
            respostas["Data da ultima manutencao"] = st.text_input("Data da última manutenção:", placeholder="DD/MM/AAAA", key="data_input")
            
        if st.form_submit_button("Finalizar Checklist"):
            if any(r is None for q, r in respostas.items() if "Data" not in q and "Placa" not in q):
                st.warning("⚠️ Atenção: Por favor, responda todos os itens.")
            elif not re.match(r"^\d{2}/\d{2}/\d{4}$", respostas["Data da ultima manutencao"]):
                st.error("⚠️ Data inválida! Use DD/MM/AAAA.")
            elif not respostas["Veículo (Placa)"].strip():
                st.warning("⚠️ Atenção: Preencha a placa.")
            else:
                try:
                    salvar_no_supabase(st.session_state.nome_completo, respostas, supabase)
                    enviar_email(st.session_state.nome_completo, respostas)
                    st.success("Checklist enviado e salvo com sucesso!")
                except Exception as e:
                    st.error(f"Erro no envio: {e}")