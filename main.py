import streamlit as st
import smtplib
from email.message import EmailMessage
import base64
import os
import re
from datetime import datetime
from supabase import create_client
import pandas as pd

# --- CONFIGURAÇÃO SUPABASE ---
supabase_url = st.secrets["SUPABASE"]["URL"]
supabase_key = st.secrets["SUPABASE"]["KEY"]
supabase = create_client(supabase_url, supabase_key)

st.set_page_config(page_title="Checklist Veicular", layout="centered", initial_sidebar_state="collapsed")

# --- CSS ---
st.markdown("""
    <style>
    /* 1. Barra do topo transparente e reposicionamento da setinha (>>) */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
        z-index: 1 !important;
    }

    button[data-testid="stSidebarCollapseButton"] {
        position: fixed !important;
        top: 70px !important;       /* Regule a altura aqui */
        left: 25px !important;      /* Regule a distância da esquerda aqui */
        z-index: 999999 !important; /* Fica por cima de qualquer elemento */
        background-color: rgba(14, 17, 23, 0.8) !important; /* Fundo escuro sutil */
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
        color: #ffffff !important;
        padding: 4px 8px !important;
            
    }

    button[data-testid="stSidebarCollapseButton"]:hover {
        background-color: #ff4b4b !important;
        border-color: #ff4b4b !important;        
            
    }
    
    /* 2. Força TRANSPARÊNCIA TOTAL nos campos de entrada (Inputs, Selects e Textareas) */
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    div[data-baseweb="input"] input,
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div,
    .stTextArea > div > div > textarea {
        background-color: transparent !important;
        background: transparent !important;
        border: 1px solid rgba(255, 255, 255, 0.4) !important;
        color: #ffffff !important;
            
    }
            
    /* 3. Força TRANSPARÊNCIA TOTAL em TODOS OS BOTÕES (Menu, Avançar, Sidebar, Form, etc.) */
    .stButton button, 
    [data-testid="stFormSubmitButton"] button,
    button[kind="secondary"],
    button[kind="primary"] {
        background-color: transparent !important;
        background: transparent !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.4) !important;
        border-radius: 8px !important;
        white-space: nowrap !important;
    
    }
            
    /* Efeito sutil ao passar o mouse por cima dos botões */
    .stButton button:hover, 
    [data-testid="stFormSubmitButton"] button:hover {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border-color: #ffffff !important;
        color: #ffffff !important;
    
    }
    
    /* 4. Estilização do Menu Dropdown (Lista de opções quando abre um Selectbox) */
    div[role="listbox"],
    ul[data-testid="stSelectboxVirtualDropdown"] {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
            
    }
    
    /* Oculta elementos visuais padrão da sidebar se necessário */
    [data-testid="stSidebar"] section > div > div > div > div > div {
        display: none;

    }
    
    input, select, textarea {
    color: #ffffff !important;

    }

    @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;500&display=swap');
    .stApp { background-color: rgba(0, 0, 0, 0.6) !important; background-blend-mode: darken; }
    h1 { font-family: 'Oswald', sans-serif !important; font-weight: 500 !important; font-size: 36px !important; color: #ffffff !important; text-transform: uppercase !important; letter-spacing: 0.5px !important; margin-bottom: 20px !important; }
    div[data-baseweb="select"] > div, .stTextInput > div > div > input, .stTextArea > div > div > textarea {color: #ffffff !important; border: 1px solid #444444 !important; font-family: 'Oswald', sans-serif !important; }
    label, p, span, div { color: #ffffff !important; font-family: 'Oswald', sans-serif !important; }

    /* Corrige o ícone de recolher a sidebar (evita mostrar o nome do ícone como texto) */
    [data-testid="stIconMaterial"] {
        font-family: 'Material Symbols Rounded' !important;
    }

    /* Reduz a largura da barra lateral */
    section[data-testid="stSidebar"] {
        width: 260px !important;
    }
    section[data-testid="stSidebar"] > div {
        width: 260px !important;
    }

    /* Impede que o texto dos botões quebre linha */
    .stButton button, [data-testid="stFormSubmitButton"] button {
        white-space: nowrap !important;
    }
    </style>
""", unsafe_allow_html=True)


# --- IMAGENS DE FUNDO (com cache para não recarregar a cada rerun) ---
@st.cache_data(show_spinner=False)
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()


@st.cache_data(show_spinner=False)
def carregar_backgrounds():
    """Lê e codifica as imagens de fundo uma única vez (cacheado)."""
    base_path = os.path.dirname(os.path.abspath(__file__))
    pasta_imagens = os.path.join(base_path, 'imagens')

    if not os.path.exists(pasta_imagens):
        return None, f"Pasta 'imagens' não encontrada em: {pasta_imagens}"

    arquivos = {f.lower(): f for f in os.listdir(pasta_imagens)}
    arquivos_esperados = ['desktop.png', 'tablet.png', 'mobile.png']
    for arq in arquivos_esperados:
        if arq not in arquivos:
            return None, f"Arquivo não encontrado: {arq}"

    desktop_bg = get_base64_of_bin_file(os.path.join(pasta_imagens, arquivos['desktop.png']))
    tablet_bg = get_base64_of_bin_file(os.path.join(pasta_imagens, arquivos['tablet.png']))
    mobile_bg = get_base64_of_bin_file(os.path.join(pasta_imagens, arquivos['mobile.png']))
    return (desktop_bg, tablet_bg, mobile_bg), None


def set_background_images():
    imagens, erro = carregar_backgrounds()
    if erro:
        st.error(erro)
        return
    desktop_bg, tablet_bg, mobile_bg = imagens
    st.markdown(f"""
        <style>
        .stApp {{ background-image: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url("data:image/png;base64,{desktop_bg}"); background-size: cover; background-position: center; }}
        @media (max-width: 1024px) {{ .stApp {{ background-image: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url("data:image/png;base64,{tablet_bg}"); }} }}
        @media (max-width: 600px) {{ .stApp {{ background-image: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url("data:image/png;base64,{mobile_bg}"); }} }}
        </style>
    """, unsafe_allow_html=True)


set_background_images()


# --- FUNÇÕES AUXILIARES ---
def validar_nome(nome):
    return len(nome.strip().split()) >= 2


def validar_placa(placa):
    placa = placa.strip().upper()
    padrao_antigo = r"^[A-Z]{3}-?\d{4}$"
    padrao_mercosul = r"^[A-Z]{3}\d[A-Z]\d{2}$"
    return bool(re.match(padrao_antigo, placa) or re.match(padrao_mercosul, placa))


def enviar_email(nome, dados):
    email_origem = "automacao.clicklog@gmail.com"
    senha = st.secrets["SUPABASE"]["EMAIL_SENHA"]
    email_destino = "analista@clicklogtransportes.com.br"
    msg = EmailMessage()
    msg['Subject'] = f"Checklist Recebido: {nome}"
    msg['From'] = email_origem
    msg['To'] = email_destino
    corpo = f"Motorista: {nome}\n\nRespostas:\n"
    for p, r in dados.items():
        corpo += f"{p}: {r}\n"
    msg.set_content(corpo)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(email_origem, senha)
        smtp.send_message(msg)

def formatar_data_para_banco(data_texto):
    if not data_texto or not data_texto.strip():
        return None
    try:
        data_limpa = data_texto.strip()
        if len(data_limpa.split('/')[-1]) == 2:
            dt = datetime.strptime(data_limpa, "%d/%m/%y")
        else:
            dt = datetime.strptime(data_limpa, "%d/%m/%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None

def salvar_no_supabase(nome, dados, observacoes, client):
    data_manutencao_iso = datetime.strptime(dados["Data da ultima manutencao"], "%d/%m/%Y").strftime("%Y-%m-%d")
    dados_banco = {
        "nome_motorista": nome,
        "data_envio": datetime.now().isoformat(),
        "veiculo_placa": dados["Veículo (Placa)"],
        "data_ultima_manutencao": data_manutencao_iso,
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
        "chave_triangulo_macaco": dados["Chave/Triângulo/Macaco?"],
        "observacoes": observacoes,
    }
    response = client.table("inspecoes").insert(dados_banco).execute()
    return response


def validar_admin(usuario, senha):
    """
    Credenciais lidas do secrets.toml, NUNCA hardcoded no código.
    Formato esperado em .streamlit/secrets.toml:

    [ADMIN_CREDENTIALS]
    "Adm@kewin" = "sua_senha_aqui"
    "Adm@felipe" = "outra_senha_aqui"
    """
    admins = st.secrets.get("ADMIN_CREDENTIALS", {})
    return admins.get(usuario) == senha


# --- ESTADO DA SESSÃO ---
if 'etapa' not in st.session_state:
    st.session_state.etapa = 'nome'
if 'nome_completo' not in st.session_state:
    st.session_state.nome_completo = ""
if 'mostrar_admin' not in st.session_state:
    st.session_state.mostrar_admin = False
if 'cadastros_temporarios' not in st.session_state:
    st.session_state.cadastros_temporarios = []


# --- MENU LATERAL (LOGIN ADMIN) ---
if st.button("☰ Menu", key="botao_menu"):
    st.session_state.mostrar_admin = not st.session_state.mostrar_admin
    st.rerun()

if st.session_state.mostrar_admin:
    with st.sidebar:
        st.write("### Login Administrador")
        user = st.text_input("Login", key="admin_login")
        password = st.text_input("Senha", type="password", key="admin_senha")
        if st.button("Entrar", key="admin_entrar"):
            if validar_admin(user, password):
                st.session_state.etapa = 'admin_painel'
                st.session_state.mostrar_admin = False
                st.rerun()
            else:
                st.error("Credenciais inválidas")


# --- TELA 1: NOME DO MOTORISTA ---
if st.session_state.etapa == 'nome':
    st.title("Seja bem-vindo à página de Checklist do seu veículo.")
    nome = st.text_input("Preencha seu nome completo:", key="nome_input")
    if st.button("Avançar", key="avancar_nome"):
        if validar_nome(nome):
            st.session_state.nome_completo = nome
            st.session_state.etapa = 'checklist'
            st.rerun()
        else:
            st.error("Nome incompleto! Digite nome e sobrenome.")

# --- TELA 2: CHECKLIST ---
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
            respostas["Veículo (Placa)"] = st.text_input("Veículo (Placa):", placeholder="ABC-1234", key="placa_input")
        with c3:
            for q in ["Freios ok?", "Nivel oleo motor ok?", "Parabrisa ok?", "Chave/Triângulo/Macaco?"]:
                respostas[q] = st.selectbox(q, ["Conforme", "Não conforme"], index=None, placeholder="Selecione...", key=f"c3_{q}")
            respostas["Data da ultima manutencao"] = st.text_input("Data da última manutenção:", placeholder="DD/MM/AAAA", key="data_input")

            observacoes = st.text_area("Observações:", placeholder="Digite aqui alguma observação se necessário...", key="obs_input")

        if st.form_submit_button("Finalizar Checklist"):
            if any(r is None for q, r in respostas.items() if "Data" not in q and "Placa" not in q):
                st.warning("⚠️ Atenção: Por favor, responda todos os itens.")
            elif not re.match(r"^\d{2}/\d{2}/\d{4}$", respostas["Data da ultima manutencao"]):
                st.error("⚠️ Data inválida! Use DD/MM/AAAA.")
            elif not respostas["Veículo (Placa)"].strip():
                st.warning("⚠️ Atenção: Preencha a placa.")
            elif not validar_placa(respostas["Veículo (Placa)"]):
                st.error("⚠️ Placa inválida! Use o formato ABC1234 ou ABC1D23.")
            else:
                try:
                    salvar_no_supabase(st.session_state.nome_completo, respostas, observacoes, supabase)
                    enviar_email(st.session_state.nome_completo, respostas)
                    st.success("Checklist enviado e salvo com sucesso!")
                except Exception as e:
                    st.error(f"Erro no envio: {e}")

    if st.button("Voltar ao Início", key="voltar_checklist"):
        st.session_state.etapa = 'nome'
        st.rerun()

# --- TELA 3: PAINEL ADMINISTRATIVO ---
elif st.session_state.etapa == 'admin_painel':
    st.title("⚙️ Painel Administrativo")

    st.subheader("Cadastrar Motorista")

    with st.form("form_cadastro_linha", clear_on_submit=True):
        col1, col2, col3, col4, col5, col_botao = st.columns([2, 1.1, 1.1, 1.2, 1.2, 1])
        with col1:
            novo_nome = st.text_input("Motorista")
        with col2:
            nova_placa = st.text_input("Placa")
        with col3:
            novo_chassi = st.text_input("Chassi")
        with col4:
            nova_validade_cnh = st.text_input("Val. CNH", placeholder="DD/MM/AAAA")
        with col5:
            nova_validade_renavam = st.text_input("Val. Renavam", placeholder="DD/MM/AAAA")
        with col_botao:
            st.write("")
            st.write("")
            enviado = st.form_submit_button("Enviar")

        if enviado:
            if not novo_nome.strip() or not nova_placa.strip():
                st.warning("⚠️ Preencha ao menos Motorista e Placa.")
            else:
                try:
                    dados = {
                        "Motorista": novo_nome.strip(),
                        "Placa": nova_placa.strip(),
                        "Chassi": novo_chassi.strip(),
                        "Val. CNH": formatar_data_para_banco(nova_validade_cnh),
                        "Val. Renavam": formatar_data_para_banco(nova_validade_renavam)
                    }
                    
                    supabase.table("Motoristas").insert(dados).execute()
                    st.success("✅ Motorista cadastrado com sucesso no banco de dados!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar no banco de dados: {e}")

    st.divider()
    st.subheader("Motoristas Cadastrados")

    try:
        res = supabase.table("Motoristas").select('id, "Motorista", "Placa", "Chassi", "Val. CNH", "Val. Renavam"').order("id", desc=True).execute()
        dados_banco = res.data

        if dados_banco:
            df_banco = pd.DataFrame(dados_banco)
            
            if "id" in df_banco.columns:
                df_banco = df_banco.drop(columns=["id"])

            st.dataframe(df_banco, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum motorista cadastrado no banco de dados ainda.")
    except Exception as e:
        st.error(f"Erro ao carregar motoristas do banco: {e}")

    if st.button("Voltar ao Início", key="voltar_admin"):
        st.session_state.etapa = 'nome'
        st.rerun()