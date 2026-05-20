# ⚡ Telecom QA - Sistema de Qualidade de Monitoria

Sistema inteligente de auditoria e monitoria de qualidade para operações de telecomunicações, utilizando a potência da IA do **Google Gemini** para transformar áudios de chamadas em dados estruturados e insights acionáveis.

---

## 📊 Painel Interativo (Dashboard Premium)

O projeto conta com um **Painel Interativo** moderno e intuitivo desenvolvido em Streamlit, projetado para oferecer uma experiência de auditoria de alto nível.

### ✨ Diferenciais do Painel:
- **Estética Glassmorphism:** Interface escura com efeitos de transparência e desfoque, proporcionando um visual premium e profissional.
- **Navegação Estilo YouTube:** Menu lateral robusto e fluido para alternar rapidamente entre a visão geral e os relatórios individuais.
- **Auditoria em Tempo Real:** Aba dedicada para upload e processamento imediato de novos áudios via API do Gemini.
- **Transcrição Literal (Ipsis Litteris):** Visualização de diálogos palavra por palavra, garantindo que nenhum detalhe da ligação seja perdido.
- **KPIs Visuais:** Gráficos interativos (Plotly) que mostram a aderência aos scripts, sentimento do cliente e eficácia de vendas.

---

## 🚀 Funcionalidades Principais

1.  **Auditoria Automatizada:** O sistema ouve o áudio e preenche automaticamente um checklist de conformidade (saudação, sondagem, oferta, contra-argumentação).
2.  **Análise de Sentimento:** Identifica se o cliente terminou a ligação Satisfeito, Neutro ou Irritado.
3.  **Resiliência API:** Mecanismo de retentativa automática (retry) para lidar com picos de demanda da API (Erro 503).
4.  **Processamento em Lote:** Script de orquestração para processar centenas de áudios de uma só vez.
5.  **Extração de Dados:** Identificação automática de nomes, telefones e endereços mencionados durante a chamada.

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python 3.12+
- **IA:** Google Gemini (via `google-genai`)
- **Interface:** Streamlit
- **Gráficos:** Plotly Express
- **Processamento de Áudio:** FFmpeg & Mutagen
- **Dados:** Pandas

---

## ⚙️ Como Iniciar o Painel

1.  Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```
2.  Inicie o Dashboard:
    ```bash
    streamlit run frontend/dashboard.py
    ```
3.  No navegador, insira sua **Chave de API do Gemini** na aba "Auditar Novo Áudio" e comece a auditoria!

---

## 📁 Estrutura do Repositório

- `frontend/dashboard.py`: Código fonte da interface visual.
- `gemini_audio_qa.py`: Motor de inteligência e integração com Gemini.
- `orquestrador_lote.py`: Script para processamento massivo de arquivos.
- `relatorio/`: Pasta onde os resultados e transcrições são salvos.

---
*Desenvolvido para elevar o padrão de qualidade em monitorias de telecomunicações.*
