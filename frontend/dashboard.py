import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import glob
import sys
import html
from datetime import datetime
import json

# Adiciona o diretório raiz ao path do sistema para permitir importações corretas de módulos irmãos
diretorio_script = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(diretorio_script)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# ==========================================
# CONFIGURAÇÃO DE PÁGINA E ESTILO
# ==========================================
st.set_page_config(
    page_title="Painel de Qualidade - Telecom QA",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injeção de CSS personalizado para estética premium e Glassmorphism (Menu Estilo YouTube)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

/* Configurações básicas */
html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Outfit', sans-serif;
    background-color: #0B0F19;
    color: #E2E8F0;
}

[data-testid="stHeader"] {
    background-color: rgba(11, 15, 25, 0.85);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
}

[data-testid="stSidebar"] {
    background-color: #0F172A;
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}

/* Cabeçalho da barra lateral */
.sidebar-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #FFFFFF;
    margin-bottom: 1.5rem;
    background: linear-gradient(135deg, #6366F1 0%, #A855F7 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Custom button navigation styling - YouTube style sidebar menu */
div[data-testid="stSidebar"] div[data-testid="stButton"] button {
    background: rgba(30, 41, 59, 0.15) !important;
    border: 1px solid rgba(255, 255, 255, 0.03) !important;
    border-radius: 12px !important;
    padding: 0.6rem 0.8rem !important;
    color: #94A3B8 !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    cursor: pointer !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    text-align: left !important;
    width: 100% !important;
    margin-bottom: 2px !important;
}

div[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
    background: rgba(99, 102, 241, 0.12) !important;
    border-color: rgba(99, 102, 241, 0.25) !important;
    color: #E2E8F0 !important;
    transform: translateX(4px);
}

div[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="primary"] {
    background: linear-gradient(135deg, #6366F1 0%, #A855F7 100%) !important;
    border: none !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25) !important;
}

/* KPI Cards com Glassmorphism */
.kpi-container {
    display: flex;
    gap: 1.5rem;
    width: 100%;
    margin-bottom: 2rem;
}

.kpi-card {
    flex: 1;
    background: rgba(30, 41, 59, 0.45);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 10px 30px 0 rgba(0, 0, 0, 0.25);
    transition: all 0.3s ease;
}

.kpi-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 35px 0 rgba(99, 102, 241, 0.18);
    border-color: rgba(99, 102, 241, 0.35);
}

.kpi-title {
    font-size: 0.85rem;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

.kpi-value {
    font-size: 2.25rem;
    font-weight: 700;
    line-height: 1.1;
    background: linear-gradient(135deg, #FFFFFF 0%, #94A3B8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Classes dinâmicas para as métricas */
.val-excelente {
    background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
}

.val-alerta {
    background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
}

.val-critico {
    background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
}

/* Ficha de Auditoria */
.sheet-card {
    background: rgba(15, 23, 42, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    padding: 2rem;
    margin-top: 1.5rem;
    box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.15);
}

.sheet-section-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #F8FAFC;
    border-bottom: 2px solid rgba(99, 102, 241, 0.2);
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
}

.badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
}

.badge-excelente {
    background-color: rgba(16, 185, 129, 0.15);
    color: #10B981;
    border: 1px solid rgba(16, 185, 129, 0.3);
}

.badge-alerta {
    background-color: rgba(245, 158, 11, 0.15);
    color: #F59E0B;
    border: 1px solid rgba(245, 158, 11, 0.3);
}

.badge-critico {
    background-color: rgba(239, 68, 68, 0.15);
    color: #EF4444;
    border: 1px solid rgba(239, 68, 68, 0.3);
}

/* Abas Customizadas */
div[data-testid="stHorizontalBlock"] {
    background: rgba(15, 23, 42, 0.3);
    border-radius: 8px;
    padding: 0.5rem;
}

/* Customização dos containers padrão Streamlit */
div[data-testid="stVerticalBlock"] > div:has(div.kpi-card) {
    padding: 0px !important;
}

/* Container de Navegação Premium */
.navigation-card {
    background: rgba(30, 41, 59, 0.25);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15);
}

/* Transcription bubbles */
.transcription-line {
    display: flex;
    gap: 0.75rem;
    align-items: flex-start;
    margin-bottom: 0.6rem;
}
.transcription-avatar {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
    flex: 0 0 44px;
}
.avatar-assistant { background: linear-gradient(135deg,#6366F1,#A855F7); color: white; }
.avatar-user { background: linear-gradient(135deg,#10B981,#059669); color: white; }
.transcription-bubble {
    padding: 0.8rem 1rem;
    border-radius: 12px;
    max-width: 85%;
    font-size: 0.95rem;
    line-height: 1.35;
    color: #E2E8F0;
}
.bubble-assistant { background: rgba(99,102,241,0.12); border: 1px solid rgba(99,102,241,0.18); }
.bubble-user { background: rgba(16,185,129,0.08); border: 1px solid rgba(16,185,129,0.12); }
.bubble-meta { font-weight:700; display:block; margin-bottom:4px; color:#F8FAFC }
</style>
""", unsafe_allow_html=True)

# ==========================================
# CARREGAMENTO E AGREGAÇÃO DE DADOS (ETL MULTI-ARQUIVO)
# ==========================================
# Ajusta paths para apontar ao root do repositório
diretorio_script = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(diretorio_script)
pasta_relatorio = os.path.join(repo_root, "relatorio")
caminho_consolidado = os.path.join(repo_root, "relatorio_consolidado_qa.csv")

@st.cache_data(ttl=15) # Cache curto para ver atualizações rápidas
def carregar_dados_relatorio() -> pd.DataFrame:
    lista_dfs = []
    
    # 1. Tenta carregar arquivos individuais da pasta 'relatorio'
    if os.path.exists(pasta_relatorio):
        arquivos_csv = glob.glob(os.path.join(pasta_relatorio, "*.csv"))
        for arq in arquivos_csv:
            try:
                temp_df = pd.read_csv(arq, encoding='utf-8-sig')
                if not temp_df.empty:
                    lista_dfs.append(temp_df)
            except Exception:
                pass
                
    if lista_dfs:
        df_merged = pd.concat(lista_dfs, ignore_index=True)
        # Se houver duplicados por nome do arquivo (ex: reprocessamentos), mantém a última versão
        if "Nome do Arquivo" in df_merged.columns:
            df_merged = df_merged.drop_duplicates(subset=["Nome do Arquivo"], keep="last")
        return df_merged
        
    # 2. Se a pasta estiver vazia, tenta ler o consolidado da raiz (fallback)
    if os.path.exists(caminho_consolidado):
        try:
            df_root = pd.read_csv(caminho_consolidado, encoding='utf-8-sig')
            return df_root
        except Exception:
            pass
            
    return pd.DataFrame()

# Obtém informações de modificação do arquivo ou diretório
if os.path.exists(pasta_relatorio) and os.listdir(pasta_relatorio):
    # Pega o arquivo mais recentemente modificado na pasta relatorio
    arquivos = glob.glob(os.path.join(pasta_relatorio, "*.csv"))
    recente = max(arquivos, key=os.path.getmtime)
    mtime = os.path.getmtime(recente)
    dt_modificacao = datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M:%S")
elif os.path.exists(caminho_consolidado):
    mtime = os.path.getmtime(caminho_consolidado)
    dt_modificacao = datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M:%S")
else:
    dt_modificacao = "Sem relatórios cadastrados"

df = carregar_dados_relatorio()

# ==========================================
# GERAÇÃO DA LISTA DE PÁGINAS (MENU DE NAVEGAÇÃO LATERAL)
# ==========================================
paginas = ["📊 Visão Geral Consolidada", "📤 Auditar Novo Áudio"]
lista_audios: list[str] = []
classificacoes_disponiveis: list[str] = []
sentimentos_disponiveis: list[str] = []
if not df.empty:
    if "Nome do Arquivo" in df.columns:
        lista_audios = sorted(df["Nome do Arquivo"].unique())
        paginas_audios = [f"📞 {audio}" for audio in lista_audios]
        # Insere as gravações individuais entre o Painel Consolidado e a Auditoria
        paginas = ["📊 Visão Geral Consolidada"] + paginas_audios + ["📤 Auditar Novo Áudio"]

# ==========================================
# BARRA LATERAL - ESTILO MENU YOUTUBE
# ==========================================
with st.sidebar:
    st.markdown('<div class="sidebar-title">⚡ Telecom QA</div>', unsafe_allow_html=True)
    st.markdown(f"<p style='color: #94A3B8; font-size: 0.8rem; margin-top: -10px; margin-bottom: 1.5rem;'>Última alteração ativa:<br><b>{dt_modificacao}</b></p>", unsafe_allow_html=True)

    st.markdown("<p style='font-size: 0.8rem; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; border-bottom: 1px solid rgba(255,255,255,0.03); padding-bottom: 0.25rem;'>Navegação</p>", unsafe_allow_html=True)

    if "pagina_ativa" not in st.session_state or st.session_state["pagina_ativa"] not in paginas:
        st.session_state["pagina_ativa"] = "📊 Visão Geral Consolidada"

    # Navegação via botões (YouTube Style) - Mais estável que st.radio para listas dinâmicas
    for p in paginas:
        is_active = (st.session_state["pagina_ativa"] == p)
        if st.button(
            p, 
            key=f"btn_nav_{p}", 
            use_container_width=True, 
            type="primary" if is_active else "secondary",
            help=f"Ir para: {p}"
        ):
            if st.session_state["pagina_ativa"] != p:
                st.session_state["pagina_ativa"] = p
                st.rerun()
    
    pagina_selecionada = st.session_state["pagina_ativa"]

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Atualizar Relatório", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ==========================================
# RENDERIZAÇÃO DE RELATÓRIO INDIVIDUAL (SEQUENCIAL / PAGINA UNICA DETALHADA)
# ==========================================
def renderizar_avaliacao_individual(audio_selecionado):
    if df.empty:
        st.error("❌ Não há dados disponíveis para esta avaliação.")
        return
        
    # Recupera o registro específico
    registro_filtrado = df[df["Nome do Arquivo"] == audio_selecionado]
    if registro_filtrado.empty:
        st.error(f"❌ Não foi possível encontrar o registro para o áudio '{audio_selecionado}'.")
        return
        
    registro = registro_filtrado.iloc[0]
    
    # Cabeçalho do Relatório de Qualidade
    st.markdown(f"""
    <div style="margin-bottom: 1.5rem; padding: 1.5rem; background: rgba(30, 41, 59, 0.45); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px;">
        <h1 style="font-weight: 800; font-size: 2.1rem; margin-bottom: 0.25rem; background: linear-gradient(135deg, #F59E0B 0%, #EF4444 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-top: 0px;">
            📋 Detalhamento da Auditoria
        </h1>
        <p style="color: #94A3B8; font-size: 0.95rem; margin: 0;">
            Gravação Analisada: <b>{audio_selecionado}</b>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Scorecard KPIs
    nota_final = registro.get("Nota Final", 0.0)
    vendas_score = registro.get("Performance Vendas (Sondagem/Oferta)", 0.0)
    sentimento = str(registro.get("Sentimento Cliente", "Não Identificado")).title()
    classif = registro.get("Classificacao", "N/A")
    
    classe_nota = "val-excelente" if nota_final >= 75 else ("val-alerta" if nota_final >= 50 else "val-critico")
    classe_venda = "val-excelente" if vendas_score >= 70 else ("val-alerta" if vendas_score >= 40 else "val-critico")
    
    if sentimento.lower() in ["satisfeito", "feliz"]:
        classe_sent = "val-excelente"
    elif sentimento.lower() in ["neutro"]:
        classe_sent = "val-alerta"
    else:
        classe_sent = "val-critico"
        
    if "Excelente" in classif:
        badge_class = "badge-excelente"
    elif "Aceitável" in classif:
        badge_class = "badge-excelente"
    elif "Atenção" in classif:
        badge_class = "badge-alerta"
    else:
        badge_class = "badge-critico"
        
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">⭐ Nota Final</div>
            <div class="kpi-value {classe_nota}">{nota_final:.1f}<span style="font-size: 1rem; font-weight: normal; color: #94A3B8;">/100</span></div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">💼 Eficácia de Vendas</div>
            <div class="kpi-value {classe_venda}">{vendas_score:.1f}<span style="font-size: 1rem; font-weight: normal; color: #94A3B8;">/100</span></div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">❤️ Sentimento Cliente</div>
            <div class="kpi-value {classe_sent}">{sentimento}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">⚠️ Risco da Operação</div>
            <div style="margin-top: 0.5rem;"><span class="badge {badge_class}" style="font-size: 0.95rem; padding: 0.4rem 1rem;">{classif}</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)

    # -----------------------------
    # Dados coletados (nome, telefones, endereço)
    # -----------------------------
    def _buscar_em_registro(chaves_possiveis):
        for k in chaves_possiveis:
            if k in registro and pd.notna(registro.get(k)):
                return str(registro.get(k))
        return None

    # Tenta localizar JSON bruto associado (salvo por pipeline ou auditoria manual)
    dados_brutos = {}
    json_candidates = [
        os.path.join(pasta_relatorio, f"relatorio_{audio_selecionado}.json"),
        os.path.join(pasta_relatorio, f"{os.path.splitext(audio_selecionado)[0]}.json"),
    ]
    for jc in json_candidates:
        try:
            if os.path.exists(jc):
                with open(jc, "r", encoding="utf-8") as jf:
                    dados_brutos = json.load(jf)
                break
        except Exception:
            dados_brutos = {}

    # Normaliza possíveis localizações dos campos nos dados brutos
    cliente_nome = (
        _buscar_em_registro(["Nome Cliente", "Nome do Cliente", "cliente_nome", "nome_cliente"]) 
        or (dados_brutos.get("raw_ia_data") or dados_brutos).get("cliente_nome") if isinstance(dados_brutos, dict) else None
    )

    telefone_1 = (
        _buscar_em_registro(["Telefone 1", "Telefone 01", "telefone_1", "contato_1"]) 
        or (dados_brutos.get("raw_ia_data") or dados_brutos).get("telefone_1") if isinstance(dados_brutos, dict) else None
    )
    telefone_2 = (
        _buscar_em_registro(["Telefone 2", "Telefone 02", "telefone_2", "contato_2"]) 
        or (dados_brutos.get("raw_ia_data") or dados_brutos).get("telefone_2") if isinstance(dados_brutos, dict) else None
    )

    endereco = None
    endereco_keys = ["Endereco", "Endereço", "endereco", "endereco_completo"]
    for k in endereco_keys:
        if k in registro and pd.notna(registro.get(k)):
            endereco = str(registro.get(k))
            break
    if not endereco and isinstance(dados_brutos, dict):
        raw = dados_brutos.get("raw_ia_data") or dados_brutos
        endereco = raw.get("endereco") or raw.get("address") or raw.get("endereco_completo")

    # Se endereco for dict, extrai campos
    rua = numero = bairro = cidade = complemento = None
    if isinstance(endereco, dict):
        rua = endereco.get("rua") or endereco.get("street")
        numero = endereco.get("numero") or endereco.get("number")
        bairro = endereco.get("bairro") or endereco.get("neighborhood")
        cidade = endereco.get("cidade") or endereco.get("city")
        complemento = endereco.get("complemento") or endereco.get("complement")
        endereco_text = ", ".join([p for p in [rua, numero, complemento, bairro, cidade] if p])
    else:
        endereco_text = endereco if endereco else None

    # Renderiza o bloco de dados coletados
    st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='padding:0.8rem; border-radius:12px; background: rgba(15,23,42,0.35); border:1px solid rgba(255,255,255,0.03);'>
        <h3 style='margin:0 0 0.5rem 0;'>🧾 Dados coletados na ligação</h3>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns([2,3])
    with col_a:
        st.markdown(f"**Nome do cliente**: <br><b>{cliente_nome or 'Não coletado'}</b>", unsafe_allow_html=True)
        st.markdown(f"**Telefone 1**: <br><b>{telefone_1 or 'Não coletado'}</b>", unsafe_allow_html=True)
        st.markdown(f"**Telefone 2**: <br><b>{telefone_2 or 'Não coletado'}</b>", unsafe_allow_html=True)
    with col_b:
        st.markdown(f"**Endereço**: <br><b>{endereco_text or 'Não coletado'}</b>", unsafe_allow_html=True)
        st.markdown(f"**Cidade / Bairro**: <br><b>{(cidade or 'Não coletado')} / {(bairro or 'Não coletado')}</b>", unsafe_allow_html=True)
        st.markdown(f"**Rua / Nº / Complemento**: <br><b>{(rua or 'Não coletado')} / {(numero or 'Não coletado')} / {(complemento or 'Não coletado')}</b>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ----------------------------------------------------
    # SEÇÃO A: RELATÓRIO DE QUALIDADE E ÁUDIO
    # ----------------------------------------------------
    st.markdown("""
    <div style="margin-top: 2rem; margin-bottom: 1.25rem; border-bottom: 2px solid rgba(99, 102, 241, 0.2); padding-bottom: 0.5rem;">
        <h3 style="font-weight: 700; margin: 0; color: #F8FAFC;">
            📋 Relatório de Qualidade e Áudio
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<p style="font-weight: 600; font-size: 1.05rem; color: #E2E8F0; margin-bottom: 0.5rem;">🎵 Ouvir Gravação do Áudio</p>', unsafe_allow_html=True)
    
    caminhos_possiveis = [
        os.path.join(repo_root, "temp_audios", audio_selecionado),
        os.path.join("temp_audios", audio_selecionado),
        os.path.join("C:\\Users\\eduar\\Downloads", audio_selecionado),
        audio_selecionado
    ]
    audio_localizado = None
    for cam in caminhos_possiveis:
        if os.path.exists(cam):
            audio_localizado = cam
            break
            
    if audio_localizado:
        st.audio(audio_localizado, format="audio/mp3")
    else:
        st.warning("⚠️ Arquivo de áudio físico não encontrado no diretório local. Se desejar reproduzir o áudio no painel, carregue o arquivo abaixo:")
        upload_ouvir = st.file_uploader(
            f"Carregar áudio '{audio_selecionado}':", 
            type=["mp3", "wav", "m4a"], 
            key=f"ouvir_{audio_selecionado}"
        )
        if upload_ouvir:
            st.audio(upload_ouvir)
    
    # Checklist de Conformidade
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p style="font-weight: 600; font-size: 1.05rem; color: #E2E8F0; margin-bottom: 0.5rem;">📋 Checklist de Conformidade e Aderência</p>', unsafe_allow_html=True)
    
    col_chk1, col_chk2 = st.columns(2)
    
    checklists_1 = [
        ("saudacao_padrao_claro", "Saudação Padrão Claro"),
        ("coleta_dados_pessoais", "Coleta de Dados Pessoais (CPF/Email)"),
        ("coleta_endereco_completo", "Coleta de Endereço Completo"),
        ("fez_sondagem_necessidades", "Realizou Sondagem de Necessidades"),
    ]
    
    checklists_2 = [
        ("oferta_completa_produtos", "Oferta Completa de Produtos"),
        ("aplicou_contra_argumentacao", "Aplicou Contra-Argumentação"),
        ("ofensa_ao_cliente", "Ofensa ao Cliente (Critério Zero)"),
        ("falha_viabilidade_tecnica", "Falha de Viabilidade Técnica (Critério Zero)"),
    ]
    
    def render_chk_item(chave, rotulo):
        col_check_name = f"Check: {chave}"
        if col_check_name in registro:
            val = registro[col_check_name]
        else:
            val = "Não" # fallback
            
        if chave in ["ofensa_ao_cliente", "falha_viabilidade_tecnica"]:
            if val == "Sim":
                st.markdown(f"<div style='padding: 0.6rem 1rem; border-radius: 12px; background-color: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.25); margin-bottom: 0.5rem; color: #FCA5A5;'>🚨 <b>{rotulo}:</b> Ocorreu (Violação do Critério Zero!)</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='padding: 0.6rem 1rem; border-radius: 12px; background-color: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.25); margin-bottom: 0.5rem; color: #A7F3D0;'>✅ <b>{rotulo}:</b> Sem Ocorrência (OK)</div>", unsafe_allow_html=True)
        else:
            if val == "Sim":
                st.markdown(f"<div style='padding: 0.6rem 1rem; border-radius: 12px; background-color: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.25); margin-bottom: 0.5rem; color: #A7F3D0;'>✅ <b>{rotulo}:</b> Aderente (Sim)</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='padding: 0.6rem 1rem; border-radius: 12px; background-color: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.25); margin-bottom: 0.5rem; color: #FCA5A5;'>❌ <b>{rotulo}:</b> Não Aderente (Não)</div>", unsafe_allow_html=True)

    with col_chk1:
        for chave, rotulo in checklists_1:
            render_chk_item(chave, rotulo)
            
    with col_chk2:
        for chave, rotulo in checklists_2:
            render_chk_item(chave, rotulo)

    st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)

    # ----------------------------------------------------
    # SEÇÃO B: DIAGNÓSTICO E JUSTIFICATIVA IA
    # ----------------------------------------------------
    st.markdown("""
    <div style="margin-top: 2rem; margin-bottom: 1.25rem; border-bottom: 2px solid rgba(16, 185, 129, 0.2); padding-bottom: 0.5rem;">
        <h3 style="font-weight: 700; margin: 0; color: #F8FAFC;">
            🤖 Diagnóstico e Justificativa IA
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    col_dia1, col_dia2 = st.columns(2)
    with col_dia1:
        st.markdown(f"""
        <div class="sheet-card" style="margin-top: 0px; height: 100%;">
            <div class="sheet-section-title">💡 Resumo das Objeções do Cliente</div>
            <p style="color: #CBD5E1; font-size: 0.95rem; line-height: 1.6; margin: 0;">{registro.get("Resumo Objecoes", "Nenhuma objeção registrada.")}</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_dia2:
        st.markdown(f"""
        <div class="sheet-card" style="margin-top: 0px; height: 100%;">
            <div class="sheet-section-title">🧠 Justificativa Detalhada da IA</div>
            <p style="color: #CBD5E1; font-size: 0.95rem; line-height: 1.6; margin: 0;">{registro.get("Motivo Avaliacao IA", "Sem justificativa adicional.")}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)

    # ----------------------------------------------------
    # SEÇÃO C: DIÁLOGO E TRANSCRIÇÃO
    # ----------------------------------------------------
    st.markdown("""
    <div style="margin-top: 2rem; margin-bottom: 1.25rem; border-bottom: 2px solid rgba(168, 85, 247, 0.2); padding-bottom: 0.5rem;">
        <h3 style="font-weight: 700; margin: 0; color: #F8FAFC;">
            💬 Diálogo e Transcrição
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Localizador robusto de arquivos de transcrição (imune a divergências de acentuação/Unicode NFC/NFD)
    def localizar_transcricao_robusta(pasta, audio_nome):
        import unicodedata
        if not os.path.exists(pasta):
            return None
            
        def normalizar(s):
            return unicodedata.normalize('NFKD', str(s)).lower().strip()
            
        audio_norm = normalizar(audio_nome)
        audio_norm_sem_ext = normalizar(os.path.splitext(audio_norm)[0])
        
        # 1. Procura correspondência nos arquivos físicos da pasta
        arquivos_txt = glob.glob(os.path.join(pasta, "*.txt"))
        for arq in arquivos_txt:
            basename = os.path.basename(arq)
            basename_norm = normalizar(basename)
            if (audio_norm in basename_norm) or (audio_norm_sem_ext in basename_norm):
                return arq
                
        # 2. Fallback de segurança para caminho direto
        caminho_direto = os.path.join(pasta, f"transcricao_{audio_nome}.txt")
        if os.path.exists(caminho_direto):
            return caminho_direto
            
        return None

    caminho_transcricao = localizar_transcricao_robusta(pasta_relatorio, audio_selecionado)
    if caminho_transcricao:
        try:
            with open(caminho_transcricao, "r", encoding="utf-8") as f_txt:
                linhas = f_txt.readlines()
            
            for linha in linhas:
                linha = linha.strip()
                if not linha:
                    continue
                if linha.startswith("===") or linha.startswith("Gravação:") or linha.startswith("Data de Auditoria:"):
                    continue

                if ":" in linha:
                    partes = linha.split(":", 1)
                    papel = partes[0].strip()
                    fala = partes[1].strip()

                    papel_norm = papel.lower()
                    safe_fala = html.escape(fala)
                    safe_papel = html.escape(papel)

                    if papel_norm in ["atendente", "vendedor", "operador"]:
                        avatar_html = '<div class="transcription-avatar avatar-assistant">💁</div>'
                        bubble_html = (
                            f'<div class="transcription-bubble bubble-assistant">'
                            f'<span class="bubble-meta">Atendente</span>'
                            f'{safe_fala}'
                            f'</div>'
                        )
                    elif papel_norm in ["cliente", "consumidor"]:
                        avatar_html = '<div class="transcription-avatar avatar-user">👤</div>'
                        bubble_html = (
                            f'<div class="transcription-bubble bubble-user">'
                            f'<span class="bubble-meta">Cliente</span>'
                            f'{safe_fala}'
                            f'</div>'
                        )
                    else:
                        avatar_html = '<div class="transcription-avatar avatar-user">💬</div>'
                        bubble_html = (
                            f'<div class="transcription-bubble bubble-user">'
                            f'<span class="bubble-meta">{safe_papel}</span>'
                            f'{safe_fala}'
                            f'</div>'
                        )

                    html_line = f'<div class="transcription-line">{avatar_html}{bubble_html}</div>'
                    st.markdown(html_line, unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="transcription-line"><div class="transcription-bubble bubble-user">{html.escape(linha)}</div></div>', unsafe_allow_html=True)
        except Exception as err_chat:
            st.error(f"Erro ao ler arquivo de transcrição: {err_chat}")
    else:
        st.info("ℹ️ Nenhuma transcrição de diálogo (.txt) encontrada para este áudio na pasta de relatórios.")

# ==========================================
# ROTEAMENTO E RENDERIZAÇÃO DAS PÁGINAS
# ==========================================

if pagina_selecionada == "📊 Visão Geral Consolidada":
    # ----------------------------------------------------
    # ROTA: VISÃO GERAL CONSOLIDADA (COM FILTROS)
    # ----------------------------------------------------
    col_header_title, col_header_btn = st.columns([8, 3])

    with col_header_title:
        st.markdown(f"""
        <div style="margin-bottom: 1rem;">
            <h1 style="font-weight: 800; font-size: 2.3rem; margin-bottom: 0.25rem; background: linear-gradient(135deg, #6366F1 0%, #A855F7 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-top: 0px;">
                ⚡ Inteligência de QA em Telecomunicações
            </h1>
            <p style="color: #94A3B8; font-size: 0.95rem; margin: 0;">
                Última alteração ativa: <b>{dt_modificacao}</b>
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_header_btn:
        st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)
        if st.button("🔄 Atualizar Relatório", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # Filtros Analíticos
    classificacao_filtro = []
    sentimento_filtro = []
    nota_minima = 0.0
    busca_termo = ""

    if not df.empty:
        if "Sentimento Cliente" in df.columns:
            df["Sentimento Cliente"] = df["Sentimento Cliente"].fillna("Não Identificado").str.lower()
            sentimentos_disponiveis = sorted(df["Sentimento Cliente"].unique())
        if "Classificacao" in df.columns:
            df["Classificacao"] = df["Classificacao"].fillna("N/A")
            classificacoes_disponiveis = sorted(df["Classificacao"].unique())
        
        with st.expander("🔍 Filtros Analíticos e Pesquisa", expanded=True):
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                classificacao_filtro = st.multiselect(
                    "Classificação do Risco:",
                    options=classificacoes_disponiveis,
                    default=classificacoes_disponiveis
                )
            with col_f2:
                sentimento_filtro = st.multiselect(
                    "Sentimento do Cliente:",
                    options=sentimentos_disponiveis,

            
                    default=sentimentos_disponiveis
                )
            with col_f3:
                nota_minima = st.slider(
                    "Nota Final Mínima:",
                    min_value=0.0,
                    max_value=100.0,
                    value=0.0,
                    step=5.0
                )
                busca_termo = st.text_input("🔍 Buscar no Relatório:", placeholder="Ex: preço, script, seguro...")

    # Aplicação dos Filtros nos dados
    if not df.empty:
        df_filtrado = df[
            (df["Classificacao"].isin(classificacao_filtro)) &
            (df["Sentimento Cliente"].isin(sentimento_filtro)) &
            (df["Nota Final"] >= nota_minima)
        ]
        
        if busca_termo:
            termo = busca_termo.lower()
            mascara_busca = (
                df_filtrado["Nome do Arquivo"].str.lower().str.contains(termo, na=False) |
                df_filtrado["Resumo Objecoes"].str.lower().str.contains(termo, na=False) |
                df_filtrado["Motivo Avaliacao IA"].str.lower().str.contains(termo, na=False)
            )
            df_filtrado = df_filtrado[mascara_busca]
    else:
        df_filtrado = pd.DataFrame()

    # Painel Consolidado
    st.markdown("""
    <div style="margin-top: 1.5rem; margin-bottom: 1rem;">
        <h2 style="font-weight: 800; font-size: 1.75rem; margin-bottom: 0.25rem; background: linear-gradient(135deg, #818CF8 0%, #C084FC 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            📊 Visão Geral Consolidada
        </h2>
        <p style="color: #94A3B8; font-size: 0.95rem; margin-top: 0px; margin-bottom: 0px;">
            Painel analítico consolidado das interações monitoradas e avaliações extraídas.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if df.empty:
        st.warning("⚠️ Nenhum registro de auditoria localizado ainda nas pastas `relatorio/` ou na raiz.")
        st.info("💡 Clique em **'📤 Auditar Novo Áudio'** no menu lateral esquerdo para processar seu primeiro arquivo em tempo real!")
    elif len(df_filtrado) == 0:
        st.warning("⚠️ Nenhum registro encontrado com os filtros aplicados. Tente ajustar as seleções do filtro acima.")
    else:
        # KPIs
        total_interacoes = len(df_filtrado)
        nota_media = df_filtrado["Nota Final"].mean()
        vendas_media = df_filtrado["Performance Vendas (Sondagem/Oferta)"].mean()

        bons_sentimentos = df_filtrado[df_filtrado["Sentimento Cliente"].isin(["satisfeito", "neutro"]) ]
        taxa_satisfacao = (len(bons_sentimentos) / total_interacoes * 100) if total_interacoes > 0 else 0.0

        classe_nota = "val-excelente" if nota_media >= 75 else ("val-alerta" if nota_media >= 50 else "val-critico")
        classe_venda = "val-excelente" if vendas_media >= 70 else ("val-alerta" if vendas_media >= 40 else "val-critico")
        classe_satisfacao = "val-excelente" if taxa_satisfacao >= 70 else ("val-alerta" if taxa_satisfacao >= 40 else "val-critico")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">📋 Total Analisado</div>
                <div class="kpi-value">{total_interacoes} <span style="font-size: 1rem; color: #94A3B8; font-weight: normal;">chamadas</span></div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">⭐ Nota Final Média</div>
                <div class="kpi-value {classe_nota}">{nota_media:.1f}<span style="font-size: 1rem; font-weight: normal;">/100</span></div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">💼 Eficácia de Vendas</div>
                <div class="kpi-value {classe_venda}">{vendas_media:.1f}<span style="font-size: 1rem; font-weight: normal;">/100</span></div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">❤️ Sentimento Positivo/Neutro</div>
                <div class="kpi-value {classe_satisfacao}">{taxa_satisfacao:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        # Gráficos
        col_graf1, col_graf2 = st.columns(2)

        with col_graf1:
            st.markdown('<p style="font-weight: 600; font-size: 1.1rem; color: #E2E8F0; margin-bottom: 0.5rem;">Distribuição do Sentimento do Cliente</p>', unsafe_allow_html=True)
            contagem_sentimento = df_filtrado["Sentimento Cliente"].value_counts().reset_index()
            contagem_sentimento.columns = ["Sentimento", "Contagem"]
            contagem_sentimento["Sentimento"] = contagem_sentimento["Sentimento"].str.title()

            fig_pie = px.pie(
                contagem_sentimento, 
                names="Sentimento", 
                values="Contagem", 
                hole=0.45,
                color="Sentimento",
                color_discrete_map={
                    "Satisfeito": "#10B981",
                    "Neutro": "#64748B",
                    "Irritado": "#F59E0B",
                    "Furioso": "#EF4444",
                    "Não Identificado": "#475569"
                }
            )
            fig_pie.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Outfit, sans-serif", size=12, color="#E2E8F0"),
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
                margin=dict(t=10, b=50, l=10, r=10)
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_graf2:
            st.markdown('<p style="font-weight: 600; font-size: 1.1rem; color: #E2E8F0; margin-bottom: 0.5rem;">Aderência aos Padrões Operacionais (% de Sim)</p>', unsafe_allow_html=True)
            colunas_check = [col for col in df_filtrado.columns if col.startswith("Check:")]
            dados_check = []

            for col in colunas_check:
                taxa_sucesso = (df_filtrado[col] == "Sim").mean() * 100
                nome_limpo = col.replace("Check: ", "").replace("_", " ").title()
                dados_check.append({"Critério": nome_limpo, "Aderência (%)": taxa_sucesso})

            df_check = pd.DataFrame(dados_check).sort_values("Aderência (%)", ascending=True)

            fig_bar = px.bar(
                df_check, 
                x="Aderência (%)", 
                y="Critério", 
                orientation='h',
                color="Aderência (%)",
                color_continuous_scale=["#EF4444", "#F59E0B", "#10B981"],
                range_color=[0, 100]
            )
            fig_bar.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Outfit, sans-serif", size=11, color="#E2E8F0"),
                coloraxis_showscale=False,
                xaxis=dict(range=[0, 105], showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(showgrid=False),
                margin=dict(t=10, b=10, l=10, r=10)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        # Correlação de Vendas
        st.markdown('<p style="font-weight: 600; font-size: 1.1rem; color: #E2E8F0; margin-bottom: 0.5rem;">Correlação: Eficácia de Vendas vs. Nota Final</p>', unsafe_allow_html=True)
        fig_scatter = px.scatter(
            df_filtrado,
            x="Performance Vendas (Sondagem/Oferta)",
            y="Nota Final",
            color="Classificacao",
            hover_name="Nome do Arquivo",
            size=[10] * len(df_filtrado),
            color_discrete_map={
                "Excelente (Nível de Premiação)": "#10B981",
                "Aceitável (Dentro da Meta)": "#3B82F6",
                "Atenção (Requer Treinamento)": "#F59E0B",
                "Crítico (Risco Operacional)": "#EF4444"
            },
            labels={"Performance Vendas (Sondagem/Oferta)": "Eficácia de Vendas", "Nota Final": "Nota da Auditoria"}
        )
        fig_scatter.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(15, 23, 42, 0.3)',
            font=dict(family="Outfit, sans-serif", size=11, color="#E2E8F0"),
            xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", range=[-5, 105]),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", range=[-5, 105]),
            legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
            margin=dict(t=10, b=50, l=10, r=10)
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        # Tabela Consolidada
        with st.expander("📋 Ver Tabela Consolidada de Auditoria Completa", expanded=False):
            st.dataframe(
                df_filtrado[[
                    "Nome do Arquivo", 
                    "Nota Final", 
                    "Classificacao", 
                    "Sentimento Cliente", 
                    "Performance Vendas (Sondagem/Oferta)"
                ]],
                column_config={
                    "Nome do Arquivo": "Ficheiro Analisado",
                    "Nota Final": st.column_config.NumberColumn("Nota Final (Audit)", format="%.1f"),
                    "Classificacao": "Classificação do Risco",
                    "Sentimento Cliente": "Sentimento do Cliente",
                    "Performance Vendas (Sondagem/Oferta)": st.column_config.NumberColumn("Nota Vendas", format="%.1f")
                },
                use_container_width=True,
                hide_index=True
            )

elif pagina_selecionada == "📤 Auditar Novo Áudio":
    # ----------------------------------------------------
    # ROTA: PROCESSAR E AUDITAR NOVO ÁUDIO (REAL-TIME IA)
    # ----------------------------------------------------
    st.markdown("""
    <div style="margin-bottom: 1.5rem; padding: 1.5rem; background: rgba(30, 41, 59, 0.45); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px;">
        <h1 style="font-weight: 800; font-size: 2.1rem; margin-bottom: 0.25rem; background: linear-gradient(135deg, #10B981 0%, #3B82F6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-top: 0px;">
            📤 Auditar Nova Ligação via IA
        </h1>
        <p style="color: #94A3B8; font-size: 0.95rem; margin: 0;">
            Carregue gravações de chamadas de vendas para que o Gemini audite as regras e pontuações em tempo real.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.info("💡 Os relatórios de auditoria gerados aqui serão salvos de forma independente na pasta `relatorio/` e incorporados ao painel principal instantaneamente.")

    if "mensagens_sucesso" in st.session_state and st.session_state["mensagens_sucesso"]:
        for msg in st.session_state["mensagens_sucesso"]:
            st.success(msg)
        del st.session_state["mensagens_sucesso"]

    if "mensagens_erro" in st.session_state and st.session_state["mensagens_erro"]:
        for msg in st.session_state["mensagens_erro"]:
            st.error(msg)
        del st.session_state["mensagens_erro"]

    # Parâmetros
    st.subheader("Parâmetros do Gemini")
    col_par1, col_par2 = st.columns(2)

    with col_par1:
        chave_padrao = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GENAI_API_KEY") or ""
        sessao_key = st.session_state.get("gemini_key", chave_padrao)

        gemini_key = st.text_input(
            "Chave de API do Google Gemini:",
            type="password",
            value=sessao_key,
            help="Defina sua chave de API para habilitar as chamadas ao Gemini."
        )

        if gemini_key:
            st.session_state["gemini_key"] = gemini_key

    with col_par2:
        modelo_selecionado = st.selectbox(
            "Modelo Gemini:",
            options=[
                "gemini-2.5-flash", 
                "gemini-2.5-pro", 
                "gemini-1.5-flash",
                "gemini-1.5-pro",
                "gemini-3-flash-preview", 
                "gemini-3-pro-preview", 
                "gemini-3.1-pro-preview"
            ],
            index=0,
            help="O orquestrador tentará usar este modelo com fallbacks automáticos se houver limitações ou cotas excedidas."
        )

    st.markdown("---")
    st.subheader("Upload da Gravação de Áudio")
    uploaded_files = st.file_uploader(
        "Selecione um ou mais arquivos de áudio para auditoria:",
        type=["mp3", "wav", "m4a"],
        accept_multiple_files=True
    )

    if st.button("🚀 Iniciar Auditoria via IA", type="primary", use_container_width=True):
        if not gemini_key:
            st.error("❌ Por favor, digite sua Chave de API do Gemini para continuar.")
        elif not uploaded_files:
            st.error("❌ Por favor, selecione pelo menos um arquivo de áudio para auditar.")
        else:
            try:
                from gemini_audio_qa import GeminiAudioQAProcessor, QAProcessorScorecard
            except ImportError as imp_err:
                st.error(f"❌ Não foi possível carregar o módulo `gemini_audio_qa.py`: {imp_err}")
                st.stop()

            mensagens_sucesso = []
            mensagens_erro = []

            with st.status("⚙️ Processando auditoria via IA...", expanded=True) as status:
                for uploaded_file in uploaded_files:
                    status.write(f"🔄 **{uploaded_file.name}**: Iniciando processamento...")

                    temp_dir = os.path.join(repo_root, "temp_audios")
                    os.makedirs(temp_dir, exist_ok=True)
                    temp_path = os.path.join(temp_dir, uploaded_file.name)

                    with open(temp_path, "wb") as f_temp:
                        f_temp.write(uploaded_file.getbuffer())

                    status.write(f"📂 **{uploaded_file.name}**: Áudio temporário salvo localmente com sucesso.")

                    try:
                        processor_ia = GeminiAudioQAProcessor(
                            api_key=gemini_key,
                            model_name=modelo_selecionado,
                            cleanup_audio_file=True
                        )

                        status.write(f"🤖 **{uploaded_file.name}**: O Gemini está escutando e auditando a ligação...")
                        raw_output, metadata = processor_ia.process_audio_file(temp_path)
                        scorecard = QAProcessorScorecard().calcular_score(raw_output)

                        linha_registro = {
                            "Nome do Arquivo": uploaded_file.name,
                            "Caminho do Arquivo": os.path.abspath(temp_path),
                            "Duracao Audio (segundos)": metadata.get("duration_seconds"),
                            "Modelo Efetivo Usado": metadata.get("modelo_efetivo"),
                            "Status": scorecard.get("status_processamento", "Concluído"),
                            "Nota Final": scorecard.get("nota_final", 0.0),
                            "Classificacao": scorecard.get("classificacao", "N/A"),
                            "Sentimento Cliente": raw_output.get("analise_sentimento_cliente", "Não Identificado"),
                            "Performance Vendas (Sondagem/Oferta)": scorecard.get("performance_sondagem_negociacao", 0.0),
                            "Resumo Objecoes": scorecard.get("resumo_objecoes_cliente", ""),
                            "Motivo Avaliacao IA": scorecard.get("motivo_avaliacao", ""),
                        }

                        for criterio in [
                            "saudacao_padrao_claro",
                            "coleta_dados_pessoais",
                            "coleta_endereco_completo",
                            "fez_sondagem_necessidades",
                            "oferta_completa_produtos",
                            "aplicou_contra_argumentacao",
                            "ofensa_ao_cliente",
                            "falha_viabilidade_tecnica",
                        ]:
                            val_crit = raw_output.get(criterio, False)
                            linha_registro[f"Check: {criterio}"] = "Sim" if bool(val_crit) else "Não"
                            linha_registro[f"Pontos: {criterio}"] = round(
                                scorecard.get("detalhamento", {}).get(criterio, 0.0), 2
                            )

                        os.makedirs(pasta_relatorio, exist_ok=True)
                        saida_path = os.path.join(pasta_relatorio, f"relatorio_{uploaded_file.name}.csv")
                        pd.DataFrame([linha_registro]).to_csv(saida_path, index=False, encoding="utf-8-sig")

                        if isinstance(raw_output, dict) and "transcricao_dialogo" in raw_output:
                            caminho_transcricao = os.path.join(
                                pasta_relatorio, f"transcricao_{uploaded_file.name}.txt"
                            )
                            dialogo = raw_output["transcricao_dialogo"]
                            try:
                                with open(caminho_transcricao, "w", encoding="utf-8") as f_txt:
                                    f_txt.write("=== TRANSCRIÇÃO DE AUDITORIA ===\n")
                                    f_txt.write(f"Gravação: {uploaded_file.name}\n")
                                    f_txt.write(f"Data de Auditoria: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
                                    for fala_dict in dialogo:
                                        papel = fala_dict.get("papel", "Desconhecido")
                                        fala = fala_dict.get("fala", "")
                                        f_txt.write(f"{papel}: {fala}\n")
                                status.write(f"📝 **{uploaded_file.name}**: Transcrição estruturada salva em `{caminho_transcricao}`.")
                            except Exception as txt_err:
                                status.write(f"⚠️ **{uploaded_file.name}**: Falha ao salvar transcrição TXT: {txt_err}")

                        mensagens_sucesso.append(
                            f"✅ **{uploaded_file.name}**: Auditoria concluída! Nota: **{linha_registro['Nota Final']}/100** ({linha_registro['Classificacao']})"
                        )

                    except Exception as err_api:
                        erro_str = str(err_api)
                        mensagens_erro.append(f"❌ **{uploaded_file.name}**: Erro ao chamar a API do Gemini: {erro_str}")
                        status.write(f"❌ **{uploaded_file.name}**: Erro no processamento.")

                status.update(label="✅ Processamento de auditoria concluído!", state="complete")

            st.session_state["mensagens_sucesso"] = mensagens_sucesso
            st.session_state["mensagens_erro"] = mensagens_erro
            st.cache_data.clear()
            st.rerun()

else:
    # ----------------------------------------------------
    # ROTA: RELATÓRIO DE LIGAÇÃO INDIVIDUAL (PÁGINA DEDICADA DE ACORDO COM O MENU DO SIDEBAR)
    # ----------------------------------------------------
    audio_nome = pagina_selecionada.replace("📞 ", "")
    renderizar_avaliacao_individual(audio_nome)
