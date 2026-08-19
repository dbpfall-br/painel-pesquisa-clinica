import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import hashlib
from datetime import datetime, timedelta

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Painel de Pesquisa Clínica v3.0",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CSS CUSTOMIZADO
# ============================================================
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }

    /* Ajuste de contraste para stMetric (KPIs) */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1d2e 0%, #252840 100%);
        border: 1px solid rgba(108, 99, 255, 0.2);
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    div[data-testid="stMetric"] label { 
        font-size: 0.85rem !important; 
        color: #A0A3B5 !important; 
        font-weight: 500 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] { 
        font-size: 2rem !important; 
        font-weight: 700 !important;
        color: #FFFFFF !important; 
    }

    .badge-ok   { background:#00c853; color:white;   padding:2px 8px; border-radius:10px; font-size:.75rem; font-weight:600; }
    .badge-warn { background:#ffab00; color:#1a1a1a; padding:2px 8px; border-radius:10px; font-size:.75rem; font-weight:600; }
    .badge-danger{ background:#ff1744; color:white;  padding:2px 8px; border-radius:10px; font-size:.75rem; font-weight:600; }
    .badge-done { background:#6C63FF; color:white;   padding:2px 8px; border-radius:10px; font-size:.75rem; font-weight:600; }

    /* Ajuste de contraste para a Barra Lateral (Sidebar) Escura */
    section[data-testid="stSidebar"] { 
        background: linear-gradient(180deg, #0E1117 0%, #151929 100%); 
    }
    
    /* Títulos em branco */
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] h4,
    section[data-testid="stSidebar"] h5,
    section[data-testid="stSidebar"] h6 { 
        color: #FAFAFA !important; 
    }
    
    /* Textos informativos, markdown e labels em cinza claro */
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] summary,
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li,
    section[data-testid="stSidebar"] .stMarkdown span { 
        color: #E2E8F0 !important; 
    }

    /* Garantir que botões mantenham texto escuro legível sobre seus fundos claros */
    section[data-testid="stSidebar"] button,
    section[data-testid="stSidebar"] button p,
    section[data-testid="stSidebar"] button span {
        color: #1A1D24 !important;
    }

    /* Garantir que inputs de texto e textareas mantenham texto escuro */
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] textarea { 
        color: #1A1D24 !important; 
    }

    /* Garantir que caixas de seleção (selectboxes/dropdowns) mantenham texto escuro */
    section[data-testid="stSidebar"] div[data-baseweb="select"] { 
        color: #1A1D24 !important; 
    }
    section[data-testid="stSidebar"] div[data-baseweb="select"] * { 
        color: #1A1D24 !important; 
    }

    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px 8px 0 0; padding: 8px 20px; }

    .estudo-header {
        background: linear-gradient(90deg, rgba(108,99,255,0.15) 0%, transparent 100%);
        border-left: 3px solid #6C63FF;
        padding: 6px 12px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 8px;
        font-weight: 700;
        font-size: 1rem;
    }
    
    .login-container {
        max-width: 450px;
        margin: 50px auto;
        padding: 40px;
        background-color: #1A1D26;
        border-radius: 12px;
        border: 1px solid rgba(108, 99, 255, 0.3);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# PERSISTÊNCIA EM JSON
# ============================================================
DATA_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DATA_FILE = os.path.join(DATA_DIR, "dados_clinicos.json")

VISITAS_PADRAO = [
    {"nome": "Visita 1", "dias": 7,  "janela": 3},
    {"nome": "Visita 2", "dias": 30, "janela": 5},
]

def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()

def carregar_dados():
    """Carrega dados do JSON, inicializando a estrutura e migrando se necessário."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
        
        # Garante estrutura de usuários
        if "usuarios" not in dados:
            dados["usuarios"] = {
                "admin": {
                    "senha_hash": hash_senha("admin123"),
                    "papel": "Administrador"
                },
                "coord": {
                    "senha_hash": hash_senha("coord123"),
                    "papel": "Coordenador"
                },
                "leitor": {
                    "senha_hash": hash_senha("leitor123"),
                    "papel": "Monitor/Leitor"
                }
            }
        
        # Garante estrutura de logs
        if "log_auditoria" not in dados:
            dados["log_auditoria"] = [
                {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "usuario": "Sistema",
                    "acao": "Atualização",
                    "detalhes": "Trilha de auditoria inicializada no banco de dados."
                }
            ]
            
        # Migração: Garante nome_entrada e visita_d0 em todos os estudos cadastrados
        if "estudos" in dados:
            for est_nome, est_info in dados["estudos"].items():
                if "nome_entrada" not in est_info:
                    est_info["nome_entrada"] = "Triagem"
                if "visita_d0" not in est_info:
                    est_info["visita_d0"] = est_info["nome_entrada"]

        return dados
    else:
        dados_padrao = {
            "estudos": {
                "Estudo Alfa": {
                    "nome_entrada": "Triagem",
                    "visita_d0": "Triagem",
                    "visitas": [
                        {"nome": "Visita 1 (Screening)", "dias": 7,  "janela": 3},
                        {"nome": "Visita 2 (Baseline)",  "dias": 30, "janela": 5},
                    ]
                },
                "Estudo Beta": {
                    "nome_entrada": "Triagem",
                    "visita_d0": "Triagem",
                    "visitas": [
                        {"nome": "Triagem",           "dias": 14, "janela": 5},
                        {"nome": "Avaliação Parcial", "dias": 45, "janela": 7},
                        {"nome": "Follow-up Final",   "dias": 90, "janela": 10},
                    ]
                },
            },
            "pacientes": [
                {"id": 1, "nome": "Voluntário A", "estudo": "Estudo Alfa", "d0": "2026-08-10", "fase_index": 0, "observacoes": ""},
                {"id": 2, "nome": "Voluntário B", "estudo": "Estudo Alfa", "d0": "2026-08-01", "fase_index": 1, "observacoes": ""},
                {"id": 3, "nome": "Voluntário C", "estudo": "Estudo Beta", "d0": "2026-07-15", "fase_index": 2, "observacoes": "Acompanhamento especial"},
            ],
            "usuarios": {
                "Admin": {
                    "senha_hash": hash_senha("Admin123"),
                    "papel": "Administrador"
                },
                "coord": {
                    "senha_hash": hash_senha("coord123"),
                    "papel": "Coordenador"
                },
                "leitor": {
                    "senha_hash": hash_senha("leitor123"),
                    "papel": "Monitor/Leitor"
                }
            },
            "log_auditoria": [
                {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "usuario": "Sistema",
                    "acao": "Inicialização",
                    "detalhes": "Banco de dados inicializado com sucesso."
                }
            ]
        }
        salvar_dados(dados_padrao)
        return dados_padrao

def salvar_dados(dados):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

# ============================================================
# SESSION STATE E LOGIN
# ============================================================
if "dados_carregados" not in st.session_state:
    dados = carregar_dados()
    st.session_state.estudos       = dados["estudos"]
    st.session_state.pacientes     = dados["pacientes"]
    st.session_state.usuarios      = dados["usuarios"]
    st.session_state.log_auditoria = dados["log_auditoria"]
    st.session_state.dados_carregados = True

def persistir():
    salvar_dados({
        "estudos": st.session_state.estudos,
        "pacientes": st.session_state.pacientes,
        "usuarios": st.session_state.usuarios,
        "log_auditoria": st.session_state.log_auditoria
    })

def registrar_log(acao: str, detalhes: str):
    user = st.session_state.get("usuario_logado", "Desconhecido")
    log_item = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "usuario": user,
        "acao": acao,
        "detalhes": detalhes
    }
    st.session_state.log_auditoria.insert(0, log_item)
    persistir()

# Fluxo de Autenticação
if "usuario_logado" not in st.session_state:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown("## 🔐 Login do Sistema")
    st.caption("Painel de Pesquisa Clínica - Controle de Acesso")
    
    usuario_input = st.text_input("Usuário:")
    senha_input   = st.text_input("Senha:", type="password")
    
    if st.button("Entrar", key="btn_login"):
        user = usuario_input.strip()
        # Busca insensível a maiúsculas/minúsculas
        user_key = None
        for u in st.session_state.usuarios:
            if u.lower() == user.lower():
                user_key = u
                break
                
        if user_key is not None:
            hash_digitado = hash_senha(senha_input)
            if hash_digitado == st.session_state.usuarios[user_key]["senha_hash"]:
                st.session_state.usuario_logado = user_key
                st.session_state.usuario_papel  = st.session_state.usuarios[user_key]["papel"]
                registrar_log("Login", f"Usuário realizou login com sucesso com o papel '{st.session_state.usuario_papel}'")
                st.success("Acesso concedido!")
                st.rerun()
            else:
                st.error("Senha incorreta.")
        else:
            st.error("Usuário não cadastrado.")
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ============================================================
# HELPERS DO APP
# ============================================================
HOJE = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

def get_visitas(estudo: str) -> list:
    return st.session_state.estudos.get(estudo, {}).get("visitas", [])

def get_nome_entrada(estudo: str) -> str:
    return st.session_state.estudos.get(estudo, {}).get("nome_entrada", "Triagem")

def get_visita_d0(estudo: str) -> str:
    return st.session_state.estudos.get(estudo, {}).get("visita_d0", get_nome_entrada(estudo))

def get_fases(estudo: str) -> list:
    nome_ent = get_nome_entrada(estudo)
    return [nome_ent] + [v["nome"] for v in get_visitas(estudo)] + ["Concluído"]

def calcular_status(data_alvo: datetime, janela: int):
    dias = (data_alvo - HOJE).days
    if dias < -janela:
        return "danger", dias, f"⚠️ {abs(dias)}d de atraso"
    elif dias < 0:
        return "warn",   dias, f"⏰ Na janela ({abs(dias)}d)"
    elif dias <= janela:
        return "warn",   dias, f"📅 Em {dias} dias"
    else:
        return "ok",     dias, f"✅ Em {dias} dias"

def proximo_id():
    return max((p["id"] for p in st.session_state.pacientes), default=0) + 1

# ============================================================
# HEADER PRINCIPAL
# ============================================================
col_t, col_d = st.columns([4, 1])
with col_t:
    st.markdown("# 🔬 Painel de Pesquisa Clínica")
    st.caption(f"Logado como: **{st.session_state.usuario_logado}** ({st.session_state.usuario_papel})")
with col_d:
    st.markdown(f"### 📅 {HOJE.strftime('%d/%m/%Y')}")
st.markdown("---")

# Papel do usuário logado
PAPEL = st.session_state.usuario_papel

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown(f"👤 **Usuário:** {st.session_state.usuario_logado}")
    st.markdown(f"💼 **Perfil:** {PAPEL}")
    
    if st.button("Logout 🚪", key="btn_logout", type="secondary"):
        registrar_log("Logout", "Usuário deslogou do sistema.")
        del st.session_state.usuario_logado
        del st.session_state.usuario_papel
        st.rerun()
        
    st.divider()

    lista_estudos = list(st.session_state.estudos.keys())

    # ── SESSÃO DROPBOX CONFIG (Apenas Administrador) ──────────
    if PAPEL == "Administrador":
        with st.expander("⚙️ Config", expanded=False):
            config_opcao = st.selectbox(
                "Ação:",
                [
                    "Criação de novos estudos",
                    "Exclusão de estudos",
                    "Exclusão de participantes",
                    "Auditoria de logs",
                    "Gestão de usuários"
                ],
                key="config_opcao_select"
            )
            
            if config_opcao == "Criação de novos estudos":
                st.markdown("### ➕ Novo Estudo")
                novo_estudo_nome = st.text_input("Nome do estudo:", key="novo_estudo_nome_cfg", placeholder="Ex: Estudo Gama")
                if st.button("Criar Estudo", key="btn_criar_estudo_cfg"):
                    nome = novo_estudo_nome.strip()
                    if not nome:
                        st.error("Informe um nome.")
                    elif nome in st.session_state.estudos:
                        st.error("Estudo já existe.")
                    else:
                        st.session_state.estudos[nome] = {
                            "nome_entrada": "Triagem",
                            "visita_d0": "Triagem",
                            "visitas": []
                        }
                        registrar_log("Criação de Estudo", f"Estudo '{nome}' criado com visitas padrão.")
                        persistir()
                        st.success(f"Estudo '{nome}' criado!")
                        st.rerun()
                        
                st.divider()
                st.markdown("### ✏️ Editar Protocolo")
                if lista_estudos:
                    estudo_editar = st.selectbox("Selecione o estudo:", lista_estudos, key="sel_estudo_editar_cfg")
                    if estudo_editar:
                        st.caption(f"Configurando visitas de: {estudo_editar}")
                        
                        est_info = st.session_state.estudos[estudo_editar]
                        nome_entrada_atual = est_info.get("nome_entrada", "Triagem")
                        visita_d0_atual = est_info.get("visita_d0", nome_entrada_atual)
                        visitas_atuais = get_visitas(estudo_editar)
                        
                        col_cfg1, col_cfg2 = st.columns(2)
                        
                        nome_entrada_options = ["Pré-Triagem", "Triagem", "Recrutado/TCLE", "Randomizado"]
                        default_ne_idx = nome_entrada_options.index(nome_entrada_atual) if nome_entrada_atual in nome_entrada_options else 1
                        
                        nome_entrada_edit = col_cfg1.selectbox(
                            "Nome do Dia de Entrada:",
                            nome_entrada_options,
                            index=default_ne_idx,
                            key=f"ne_{estudo_editar}_cfg"
                        )
                        
                        num_v = st.number_input(
                            "Quantidade de visitas no protocolo:", min_value=0, max_value=15,
                            value=len(visitas_atuais), key=f"nv_{estudo_editar}_cfg"
                        )

                        novas_visitas = []
                        for i in range(int(num_v)):
                            with st.expander(f"Visita {i+1}", expanded=(i < 1)):
                                nome_p  = visitas_atuais[i]["nome"]  if i < len(visitas_atuais) else f"Visita {i+1}"
                                dias_p  = visitas_atuais[i]["dias"]  if i < len(visitas_atuais) else (i+1)*14
                                jan_p   = visitas_atuais[i].get("janela", 3) if i < len(visitas_atuais) else 3

                                nome_v = st.text_input("Nome do Marco:", value=nome_p, key=f"vn_{estudo_editar}_{i}_cfg")
                                c1, c2 = st.columns(2)
                                dias_v = c1.number_input("Dias relativos ao D0:", value=dias_p, key=f"vd_{estudo_editar}_{i}_cfg")
                                jan_v  = c2.number_input("Janela ±dias:", min_value=0, value=jan_p, key=f"vj_{estudo_editar}_{i}_cfg")
                                novas_visitas.append({"nome": nome_v, "dias": int(dias_v), "janela": int(jan_v)})

                        # Escolha da visita D0 de referência
                        opcoes_d0 = [nome_entrada_edit] + [v["nome"] for v in novas_visitas]
                        default_d0_idx = 0
                        if visita_d0_atual in opcoes_d0:
                            default_d0_idx = opcoes_d0.index(visita_d0_atual)
                        
                        visita_d0_edit = col_cfg2.selectbox(
                            "Visita de Referência (D0):",
                            opcoes_d0,
                            index=default_d0_idx,
                            key=f"vd0_{estudo_editar}_cfg"
                        )

                        if st.button("💾 Salvar Protocolo", key=f"salvar_{estudo_editar}_cfg"):
                            st.session_state.estudos[estudo_editar]["nome_entrada"] = nome_entrada_edit
                            st.session_state.estudos[estudo_editar]["visita_d0"] = visita_d0_edit
                            st.session_state.estudos[estudo_editar]["visitas"] = novas_visitas
                            registrar_log("Edição de Protocolo", f"Protocolo do estudo '{estudo_editar}' foi atualizado. Entrada: {nome_entrada_edit}, D0: {visita_d0_edit}")
                            persistir()
                            st.success("Protocolo salvo!")
                            st.rerun()
                else:
                    st.info("Crie um estudo primeiro.")
                    
            elif config_opcao == "Exclusão de estudos":
                st.markdown("### 🗑️ Excluir Estudo")
                if lista_estudos:
                    estudo_excluir = st.selectbox("Selecione o estudo para excluir:", lista_estudos, key="sel_estudo_excluir_cfg")
                    pacientes_vinculados = [p for p in st.session_state.pacientes if p["estudo"] == estudo_excluir]
                    if pacientes_vinculados:
                        st.error(f"Não é possível excluir: {len(pacientes_vinculados)} participantes vinculados.")
                    else:
                        confirmar_est_excluir = st.checkbox(f"Confirmar exclusão definitiva de '{estudo_excluir}'?", key="chk_confirmar_est_excluir_cfg")
                        if st.button("Confirmar e Excluir Estudo", key=f"del_{estudo_excluir}_cfg", type="secondary", disabled=not confirmar_est_excluir):
                            del st.session_state.estudos[estudo_excluir]
                            registrar_log("Exclusão de Estudo", f"Estudo '{estudo_excluir}' foi excluído.")
                            persistir()
                            st.success(f"Estudo '{estudo_excluir}' excluído.")
                            st.rerun()
                else:
                    st.info("Nenhum estudo cadastrado.")
                    
            elif config_opcao == "Exclusão de participantes":
                st.markdown("### 🗑️ Excluir Participante")
                nomes_map = {f"{p['nome']} [{p['estudo']}] (ID:{p['id']})": p["id"] for p in st.session_state.pacientes}
                if nomes_map:
                    sel_remover = st.selectbox("Selecionar participante para remover:", list(nomes_map.keys()), key="sel_remover_cfg")
                    confirmacao_exclusao = st.checkbox("Confirmar exclusão definitiva do paciente?", key="chk_confirmacao_exclusao_cfg")
                    if st.button("❌ Confirmar e Remover", type="secondary", key="btn_remover_cfg", disabled=not confirmacao_exclusao):
                        id_rem = nomes_map[sel_remover]
                        nome_rem = [p["nome"] for p in st.session_state.pacientes if p["id"] == id_rem][0]
                        est_rem = [p["estudo"] for p in st.session_state.pacientes if p["id"] == id_rem][0]
                        
                        st.session_state.pacientes = [p for p in st.session_state.pacientes if p["id"] != id_rem]
                        registrar_log("Exclusão de Participante", f"Participante '{nome_rem}' (ID:{id_rem}) do estudo '{est_rem}' excluído permanentemente.")
                        persistir()
                        st.success("Participante removido com sucesso.")
                        st.rerun()
                else:
                    st.caption("Nenhum participante cadastrado.")
                    
            elif config_opcao == "Auditoria de logs":
                st.markdown("### 📝 Trilha de Auditoria")
                log_df = pd.DataFrame(st.session_state.log_auditoria)
                if not log_df.empty:
                    usuarios_log = ["Todos"] + sorted(log_df["usuario"].unique().tolist())
                    filtro_u = st.selectbox("Filtrar por Usuário:", usuarios_log, key="filtro_u_cfg")
                    pesquisa_d = st.text_input("Pesquisar logs:", key="pesquisa_d_cfg")
                    
                    filtered_log_df = log_df.copy()
                    if filtro_u != "Todos":
                        filtered_log_df = filtered_log_df[filtered_log_df["usuario"] == filtro_u]
                    if pesquisa_d.strip():
                        filtered_log_df = filtered_log_df[
                            filtered_log_df["detalhes"].str.contains(pesquisa_d, case=False, na=False) |
                            filtered_log_df["acao"].str.contains(pesquisa_d, case=False, na=False)
                        ]
                    
                    st.download_button(
                        "📥 Exportar Logs (CSV)",
                        filtered_log_df.to_csv(index=False, encoding="utf-8-sig"),
                        file_name=f"trilha_auditoria_{datetime.now().strftime('%Y%m%d%H%M')}.csv",
                        mime="text/csv",
                        key="btn_export_logs_cfg"
                    )
                    st.dataframe(filtered_log_df, hide_index=True, width="stretch")
                else:
                    st.info("Nenhum log registrado.")
                    
            elif config_opcao == "Gestão de usuários":
                st.markdown("### 👥 Gestão de Usuários")
                with st.form("form_novo_usuario_cfg", clear_on_submit=True):
                    novo_user = st.text_input("Username:", placeholder="Ex: joao.silva", key="new_user_cfg")
                    nova_senha = st.text_input("Senha:", type="password", key="new_pwd_cfg")
                    novo_papel = st.selectbox("Perfil:", ["Monitor/Leitor", "Coordenador", "Administrador"], key="new_role_cfg")
                    btn_criar_u = st.form_submit_button("➕ Criar Usuário")
                    
                    if btn_criar_u:
                        user_clean = novo_user.strip()
                        if not user_clean or not nova_senha:
                            st.error("Informe usuário e senha.")
                        elif user_clean in st.session_state.usuarios:
                            st.error("Este usuário já está cadastrado.")
                        else:
                            st.session_state.usuarios[user_clean] = {
                                "senha_hash": hash_senha(nova_senha),
                                "papel": novo_papel
                            }
                            registrar_log("Criação de Usuário", f"Criado usuário '{user_clean}' com perfil '{novo_papel}'")
                            persistir()
                            st.success(f"Usuário '{user_clean}' criado!")
                            st.rerun()
                
                st.divider()
                st.markdown("### 🗑️ Excluir Usuário")
                lista_usuarios = [u for u in st.session_state.usuarios.keys() if u != st.session_state.usuario_logado]
                if lista_usuarios:
                    user_excluir = st.selectbox("Selecionar usuário:", lista_usuarios, key="sel_user_excluir_cfg")
                    confirmar_user_excluir = st.checkbox("Confirmar exclusão definitiva?", key="chk_confirmar_user_excluir_cfg")
                    if st.button("Deletar Usuário", key="btn_excluir_user_cfg", disabled=not confirmar_user_excluir):
                        del st.session_state.usuarios[user_excluir]
                        registrar_log("Exclusão de Usuário", f"Excluído usuário '{user_excluir}'")
                        persistir()
                        st.success(f"Usuário '{user_excluir}' excluído.")
                        st.rerun()
                else:
                    st.caption("Nenhum outro usuário disponível.")
                
                st.divider()
                st.markdown("### Lista de Usuários")
                df_users = pd.DataFrame([
                    {"Usuário": u, "Perfil": info["papel"]} 
                    for u, info in st.session_state.usuarios.items()
                ])
                st.dataframe(df_users, hide_index=True, width="stretch")

    st.divider()

    # ── SEÇÃO 2: NOVO PARTICIPANTE ───────────────────────────
    if PAPEL == "Monitor/Leitor":
        st.markdown("## ➕ Novo Participante")
        st.info("🔒 Apenas Administradores e Coordenadores podem cadastrar novos participantes.")
    else:
        with st.expander("➕ Novo Participante", expanded=False):
            if lista_estudos:
                novo_estudo = st.selectbox("Estudo para o participante:", lista_estudos, key="sel_estudo_novo_paciente")
                nome_ent = get_nome_entrada(novo_estudo)
                
                with st.form("form_paciente", clear_on_submit=True):
                    novo_nome   = st.text_input("Identificação/Iniciais:", placeholder="Ex: J.S.M.")
                    nova_d0     = st.date_input(f"Data de {nome_ent}:", datetime.today())
                    nova_obs    = st.text_area("Observações:", height=60, placeholder="Anotações...")
                    submit      = st.form_submit_button("📥 Inserir Participante")

                    if submit:
                        if not novo_nome.strip():
                            st.error("Informe a identificação.")
                        else:
                            novo_p = {
                                "id": proximo_id(),
                                "nome": novo_nome.strip(),
                                "estudo": novo_estudo,
                                "d0": str(nova_d0),
                                "fase_index": 0,
                                "observacoes": nova_obs.strip()
                            }
                            st.session_state.pacientes.append(novo_p)
                            registrar_log("Cadastro de Participante", f"Cadastrado '{novo_nome.strip()}' (ID:{novo_p['id']}) no estudo '{novo_estudo}' com entrada em '{nova_d0}'")
                            persistir()
                            st.success(f"{novo_nome} adicionado!")
                            st.rerun()
            else:
                st.info("Crie um estudo antes de adicionar participantes.")

    st.divider()

    # ── SEÇÃO 3: FILTROS ─────────────────────────────────────
    st.markdown("## 🔍 Filtros de Visualização")
    estudos_disponiveis = sorted(set(p["estudo"] for p in st.session_state.pacientes)) if st.session_state.pacientes else []
    filtro_estudos = st.multiselect("Estudos:", estudos_disponiveis, default=estudos_disponiveis, key="filtro_estudos")
    
    # Participantes disponíveis com base nos estudos selecionados
    participantes_disponiveis = []
    if st.session_state.pacientes:
        participantes_disponiveis = sorted(list(set(
            p["nome"] for p in st.session_state.pacientes if p["estudo"] in filtro_estudos
        )))
    
    filtro_participantes = st.multiselect(
        "Participantes:",
        participantes_disponiveis,
        default=[],
        key="filtro_participantes",
        help="Deixe em branco para exibir todos os participantes dos estudos selecionados"
    )

# ============================================================
# PROCESSAMENTO DOS DADOS
# ============================================================
dados_processados = []
dados_timeline    = []

for p in st.session_state.pacientes:
    estudo    = p["estudo"]
    visitas   = get_visitas(estudo)
    fases     = get_fases(estudo)
    
    nome_entrada = get_nome_entrada(estudo)
    visita_d0    = get_visita_d0(estudo)
    
    data_entrada_dt = datetime.strptime(p["d0"], "%Y-%m-%d")
    fi              = min(p["fase_index"], len(fases) - 1)
    fase_atual      = fases[fi]

    # Calcular D0 de referência
    offset_d0 = 0
    if visita_d0 != nome_entrada:
        for v in visitas:
            if v["nome"] == visita_d0:
                offset_d0 = v["dias"]
                break
    
    d0_dt = data_entrada_dt + timedelta(days=offset_d0)

    info = {
        "ID": p["id"],
        "Participante": p["nome"],
        "Estudo": estudo,
        "D0": p["d0"],
        "Fase Atual": fase_atual,
        "Observações": p.get("observacoes", ""),
    }

    # Status
    if fase_atual == "Concluído":
        info["Status"] = "✅ Concluído"
        info["status_key"] = "done"
    else:
        visita_idx = fi - 1  # fase 0 = nome_entrada, fase 1 = visitas[0], etc.
        if 0 <= visita_idx < len(visitas):
            v_cfg = visitas[visita_idx]
            if v_cfg["nome"] == visita_d0:
                data_alvo = d0_dt
            else:
                data_alvo = d0_dt + timedelta(days=v_cfg["dias"])
                
            st_key, dias_r, texto = calcular_status(data_alvo, v_cfg["janela"])
            info["Status"] = texto
            info["Dias Restantes"] = dias_r
            info["status_key"] = st_key
        else:
            info["Status"] = f"📋 Em {nome_entrada}"
            info["status_key"] = "ok"

    # Prazos por visita
    for v in visitas:
        if v["nome"] == visita_d0:
            target_dt = d0_dt
        else:
            target_dt = d0_dt + timedelta(days=v["dias"])
        info[f"📅 {v['nome']}"] = target_dt.strftime("%d/%m/%Y")

    dados_processados.append(info)

    # Timeline — Dia de Entrada
    dados_timeline.append({
        "Participante": p["nome"],
        "Visita": f"{nome_entrada} (Inclusão)",
        "Início": data_entrada_dt,
        "Fim": data_entrada_dt + timedelta(days=1),
        "Estudo": estudo,
        "Status": "Concluído" if fi > 0 else "Atual"
    })
    # Timeline — visitas do protocolo deste estudo
    for idx_v, v in enumerate(visitas):
        if v["nome"] == visita_d0:
            data_alvo = d0_dt
        else:
            data_alvo = d0_dt + timedelta(days=v["dias"])
            
        janela = v.get("janela", 3)
        st_vis = "Concluído" if fi > idx_v + 1 else ("Atual" if fi == idx_v + 1 else "Pendente")
        dados_timeline.append({
            "Participante": p["nome"],
            "Visita": v["nome"],
            "Início": data_alvo - timedelta(days=janela),
            "Fim":    data_alvo + timedelta(days=janela + 1),
            "Estudo": estudo,
            "Status": st_vis
        })

df = pd.DataFrame(dados_processados) if dados_processados else pd.DataFrame()
df_timeline = pd.DataFrame(dados_timeline) if dados_timeline else pd.DataFrame()

# Aplicar filtros
if not df.empty:
    # 1. Filtro de Estudos
    if filtro_estudos:
        df_filtrado = df[df["Estudo"].isin(filtro_estudos)]
        df_tl       = df_timeline[df_timeline["Estudo"].isin(filtro_estudos)] if not df_timeline.empty else pd.DataFrame()
    else:
        df_filtrado = df
        df_tl       = df_timeline

    # 2. Filtro de Participantes (em conjunto com o de estudos)
    if filtro_participantes:
        df_filtrado = df_filtrado[df_filtrado["Participante"].isin(filtro_participantes)]
        if not df_tl.empty:
            df_tl   = df_tl[df_tl["Participante"].isin(filtro_participantes)]
else:
    df_filtrado = df
    df_tl       = df_timeline

# ============================================================
# KPIs
# ============================================================
total      = len(df_filtrado)
concluidos = len(df_filtrado[df_filtrado["status_key"] == "done"]) if total > 0 else 0
atrasados  = len(df_filtrado[df_filtrado["status_key"] == "danger"]) if total > 0 else 0
alertas    = len(df_filtrado[df_filtrado["status_key"] == "warn"]) if total > 0 else 0
compliance = round((total - atrasados) / total * 100, 1) if total > 0 else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("👥 Participantes", total)
k2.metric("✅ Concluídos", concluidos)
k3.metric("⚠️ Atrasados", atrasados,
          delta=f"-{atrasados}" if atrasados > 0 else "0", delta_color="inverse")
k4.metric("⏰ Em Alerta", alertas)
k5.metric("📊 Compliance", f"{compliance}%")
st.markdown("")

# ============================================================
# ABAS PRINCIPAIS
# ============================================================
abas_list = ["📅 Timeline", "📋 Kanban", "📈 Gráficos", "🔍 Tabela"]
abas = st.tabs(abas_list)

# ── TAB 1: TIMELINE ─────────────────────────────────────────
with abas[0]:
    st.subheader("Timeline de Visitas por Participante")

    if df_tl.empty:
        st.info("Nenhum dado com os filtros selecionados.")
    else:
        # Seletor de Modo de Visualização
        tipo_viz = st.radio(
            "Modo de Visualização:",
            ["Período Completo", "Filtrar por Semana"],
            horizontal=True,
            key="tipo_viz_timeline"
        )
        
        if tipo_viz == "Filtrar por Semana":
            # --- FILTRO POR AGENDA DE SEMANA ---
            col_sem, col_info_sem = st.columns([1, 2])
            with col_sem:
                data_sel = st.date_input("Selecionar semana (escolha qualquer dia):", value=HOJE, key="data_filtro_semana")
            
            # Ajusta para Segunda (início) e Domingo (fim) da semana escolhida
            if data_sel is None:
                data_sel = HOJE.date() if hasattr(HOJE, 'date') else HOJE
            
            # Se for datetime, converte para date para o weekday
            data_date = data_sel.date() if hasattr(data_sel, 'date') else data_sel
            inicio_semana = data_date - timedelta(days=data_date.weekday())
            fim_semana = inicio_semana + timedelta(days=6)
            
            inicio_dt = datetime.combine(inicio_semana, datetime.min.time())
            fim_dt = datetime.combine(fim_semana, datetime.max.time())
            
            with col_info_sem:
                st.markdown(f"🗓️ **Período da Agenda:** Semana de `{inicio_semana.strftime('%d/%m/%Y')}` a `{fim_semana.strftime('%d/%m/%Y')}`")
                st.caption("Exibindo apenas participantes e visitas (com suas respectivas janelas de tolerância) que ocorrem neste período.")

            # Filtro na base da timeline (janela intersecta a semana selecionada)
            df_tl_final = df_tl[
                (df_tl["Início"] <= fim_dt) & (df_tl["Fim"] >= inicio_dt)
            ]
            xaxis_config = dict(
                gridcolor="rgba(255,255,255,0.05)",
                range=[inicio_dt, fim_dt + timedelta(days=1)]
            )
            # Mostrar HOJE se estiver na semana
            show_today = inicio_dt <= HOJE <= fim_dt
        else:
            # Período completo
            df_tl_final = df_tl
            xaxis_config = dict(
                gridcolor="rgba(255,255,255,0.05)"
            )
            show_today = True

        if df_tl_final.empty:
            st.info("Nenhuma visita ou janela de tolerância agendada para o filtro selecionado.")
        else:
            color_map = {"Concluído": "#6C63FF", "Atual": "#ffab00", "Pendente": "#2a2d40"}

            fig_tl = px.timeline(
                df_tl_final,
                x_start="Início", x_end="Fim",
                y="Participante",
                color="Status",
                hover_data=["Visita", "Estudo"],
                color_discrete_map=color_map,
                category_orders={"Status": ["Concluído", "Atual", "Pendente"]}
            )
            
            # Linha vertical vermelha de HOJE
            if show_today:
                fig_tl.add_shape(
                    type="line", x0=HOJE, x1=HOJE, y0=0, y1=1, yref="paper",
                    line=dict(color="#ff1744", width=2, dash="dash")
                )
                fig_tl.add_annotation(
                    x=HOJE, y=1.05, yref="paper", text="HOJE",
                    showarrow=False, font=dict(color="#ff1744", size=11, weight="bold")
                )
                
            fig_tl.update_yaxes(autorange="reversed")
            fig_tl.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font_color="#FAFAFA",
                height=max(300, len(df_tl_final["Participante"].unique()) * 80),
                margin=dict(l=10, r=10, t=40, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=xaxis_config,
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)")
            )
            st.plotly_chart(fig_tl, width="stretch")

# ── TAB 2: KANBAN ───────────────────────────────────────────
with abas[1]:
    st.subheader("Fluxo de Monitoramento por Estudo")

    if df_filtrado.empty:
        st.info("Nenhum participante com os filtros selecionados.")
    else:
        estudos_no_kanban = df_filtrado["Estudo"].unique().tolist()

        for estudo_k in estudos_no_kanban:
            st.markdown(f'<div class="estudo-header">📁 {estudo_k}</div>', unsafe_allow_html=True)

            fases_k   = get_fases(estudo_k)
            df_estudo = df_filtrado[df_filtrado["Estudo"] == estudo_k]

            colunas   = st.columns(len(fases_k))
            for idx, fase in enumerate(fases_k):
                with colunas[idx]:
                    pac_na_fase = df_estudo[df_estudo["Fase Atual"] == fase]
                    st.markdown(f"**{fase}**")
                    st.caption(f"{len(pac_na_fase)} part.")
                    st.markdown("---")

                    for _, row in pac_na_fase.iterrows():
                        st_key = row.get("status_key", "ok")
                        status_txt = str(row.get("Status", ""))
                        if st_key == "done":
                            badge = "badge-done";   badge_txt = "Concluído"
                        elif st_key == "danger":
                            badge = "badge-danger"; badge_txt = status_txt
                        elif st_key == "warn":
                            badge = "badge-warn";   badge_txt = status_txt
                        else:
                            badge = "badge-ok";     badge_txt = status_txt or "No prazo"

                        with st.container(border=True):
                            st.markdown(f"**👤 {row['Participante']}**")
                            st.markdown(f'<span class="{badge}">{badge_txt}</span>', unsafe_allow_html=True)

                            nome_entrada = get_nome_entrada(estudo_k)
                            campo_prazo = f"📅 {fase}"
                            if campo_prazo in row and fase != nome_entrada and fase != "Concluído":
                                st.caption(f"📅 Prazo: {row[campo_prazo]}")
                            elif fase == nome_entrada:
                                st.caption(f"🗓️ Entrada: {row['D0']}")

                            obs = row.get("Observações", "")
                            if obs:
                                st.caption(f"📝 {obs}")

                            # Ações de Avançar e Retroceder (Apenas para Admin e Coordenador)
                            if PAPEL in ("Administrador", "Coordenador"):
                                col_prev, col_next = st.columns(2)
                                
                                # Botão de Retroceder (Voltar Visita / Corrigir engano)
                                with col_prev:
                                    if idx > 0:
                                        if st.button("⬅️ Corrigir", key=f"back_{row['ID']}_{estudo_k}_{idx}"):
                                            for pac in st.session_state.pacientes:
                                                if pac["id"] == row["ID"]:
                                                    pac["fase_index"] = idx - 1
                                            registrar_log("Correção de Fase", f"Participante '{row['Participante']}' retrocedeu de '{fase}' para '{fases_k[idx - 1]}'.")
                                            persistir()
                                            st.rerun()
                                            
                                # Botão de Avançar
                                with col_next:
                                    if fase != "Concluído":
                                        proxima = fases_k[idx + 1]
                                        if st.button(f"Avançar ➔", key=f"mv_{row['ID']}_{estudo_k}_{idx}"):
                                            for pac in st.session_state.pacientes:
                                                if pac["id"] == row["ID"]:
                                                    pac["fase_index"] = idx + 1
                                            registrar_log("Avanço de Fase", f"Participante '{row['Participante']}' avançou de '{fase}' para '{proxima}'.")
                                            persistir()
                                            st.rerun()
                            else:
                                st.caption("🔒 Visualização apenas")

            st.markdown("")  # Espaço entre estudos

# ── TAB 3: GRÁFICOS ─────────────────────────────────────────
with abas[2]:
    st.subheader("Visão Analítica")

    if df_filtrado.empty:
        st.info("Nenhum dado disponível.")
    else:
        g1, g2 = st.columns(2)

        with g1:
            st.markdown("##### 🥧 Participantes por Fase")
            df_fc = df_filtrado["Fase Atual"].value_counts().reset_index()
            df_fc.columns = ["Fase", "Quantidade"]
            fig_pizza = px.pie(df_fc, values="Quantidade", names="Fase", hole=0.4,
                               color_discrete_sequence=["#6C63FF","#00c853","#ffab00","#ff1744","#42a5f5","#ab47bc"])
            fig_pizza.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font_color="#FAFAFA", margin=dict(l=20,r=20,t=30,b=20)
            )
            fig_pizza.update_traces(textinfo="value+percent", textfont_size=13)
            st.plotly_chart(fig_pizza, width="stretch")

        with g2:
            st.markdown("##### 📊 Status dos Participantes")
            df_st = pd.DataFrame({
                "Status":    ["No Prazo", "Em Alerta", "Atrasado", "Concluído"],
                "Quantidade":[
                    len(df_filtrado[df_filtrado["status_key"] == "ok"]) if not df_filtrado.empty else 0,
                    len(df_filtrado[df_filtrado["status_key"] == "warn"]) if not df_filtrado.empty else 0,
                    len(df_filtrado[df_filtrado["status_key"] == "danger"]) if not df_filtrado.empty else 0,
                    len(df_filtrado[df_filtrado["status_key"] == "done"]) if not df_filtrado.empty else 0
                ]
            })
            fig_bar = px.bar(df_st, x="Status", y="Quantidade", color="Status", text="Quantidade",
                             color_discrete_map={"No Prazo":"#00c853","Em Alerta":"#ffab00","Atrasado":"#ff1744","Concluído":"#6C63FF"})
            fig_bar.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font_color="#FAFAFA", showlegend=False, margin=dict(l=20,r=20,t=30,b=20),
                xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)")
            )
            fig_bar.update_traces(textposition="outside", textfont_size=14)
            st.plotly_chart(fig_bar, width="stretch")

        if len(df_filtrado["Estudo"].unique()) > 1:
            st.markdown("##### 📁 Participantes por Estudo e Fase")
            df_ef = df_filtrado.groupby(["Estudo","Fase Atual"]).size().reset_index(name="Qtd")
            fig_ef = px.bar(df_ef, x="Estudo", y="Qtd", color="Fase Atual", barmode="group", text="Qtd",
                            color_discrete_sequence=["#6C63FF","#00c853","#ffab00","#ff1744","#42a5f5","#ab47bc"])
            fig_ef.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font_color="#FAFAFA", margin=dict(l=20,r=20,t=30,b=20),
                xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)")
            )
            fig_ef.update_traces(textposition="outside", textfont_size=12)
            st.plotly_chart(fig_ef, width="stretch")

# ── TAB 4: TABELA ───────────────────────────────────────────
with abas[3]:
    st.subheader("Visão Geral e Cronograma")

    if df_filtrado.empty:
        st.info("Nenhum participante registrado.")
    else:
        ci, cd = st.columns([3,1])
        ci.caption(f"Exibindo {len(df_filtrado)} de {len(df)} participantes")
        cd.download_button(
            "📥 Baixar CSV",
            df_filtrado.to_csv(index=False, encoding="utf-8-sig"),
            file_name=f"pesquisa_clinica_{HOJE.strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        st.dataframe(
            df_filtrado, hide_index=True, width="stretch",
            column_config={
                "ID":          st.column_config.NumberColumn("ID", width="small"),
                "Participante":st.column_config.TextColumn("Participante", width="medium"),
                "Status":      st.column_config.TextColumn("Status", width="medium"),
                "Estudo":      st.column_config.TextColumn("Estudo", width="medium"),
            }
        )

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.caption("🔬 Painel de Pesquisa Clínica v3.0 — IPES · Multi-usuários e Auditoria · Pronto para Nuvem")
