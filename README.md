# Gemini Audio QA

Este script faz upload de um arquivo de áudio para o Gemini, solicita uma auditoria de QA focada em vendas e calcula uma nota final usando uma regra de scorecard orientada à conversão.

## Requisitos

- Python 3.11+ ou equivalente
- `google-genai` instalado

### Instalação

```bash
pip install google-genai pandas openpyxl
```

> Observação: `google-generativeai` está obsoleto. Use `google-genai` para novos projetos.

## Uso

```bash
python gemini_audio_qa.py caminho/para/chamada.mp3 --api-key SUA_API_KEY
```

### Opções úteis

- `--model gemini-3`
- `--api-base URL_DO_PROXY` para usar OpenClaw ou proxy
- `--output-json resultado.json` para gravar o payload final
- `--no-cleanup` para manter o arquivo de áudio no servidor do Gemini
- `--max-poll-seconds 180` para aumentar o timeout de processamento

## O que o script faz

1. Faz upload do arquivo de áudio para o Gemini
2. Aguarda processamento do arquivo
3. Envia áudio + prompt de auditoria de vendas para gerar JSON estruturado
4. Valida as chaves do contrato de vendas
5. Calcula a nota final usando pesos focados em sondagem, oferta e contra-argumentação
6. Exibe o payload final

## Saída

O script retorna um JSON com:

- `audio_path`
- `raw_ia_data`
- `scorecard`
  - `status_processamento`
  - `nota_final`
  - `classificacao`
  - `detalhamento`
  - `performance_sondagem_negociacao`
  - `resumo_objecoes_cliente`
  - `motivo_avaliacao`

## Contrato de dados esperado

O Gemini deve retornar um JSON com as chaves exatas:

- `saudacao_padrao_claro`
- `coleta_dados_pessoais`
- `coleta_endereco_completo`
- `fez_sondagem_necessidades`
- `oferta_completa_produtos`
- `aplicou_contra_argumentacao`
- `ofensa_ao_cliente`
- `falha_viabilidade_tecnica`
- `analise_sentimento_cliente`
- `resumo_objecoes_cliente`
- `motivo_avaliacao`

## Foco do scoring

O scorecard pesa fortemente:

- sondagem de necessidades
- oferta completa de produtos
- contra-argumentação do atendente

Penalidades críticas ocorrem quando há ofensa ao cliente ou falha de viabilidade técnica.

## Orquestrador em lote

Para rodar em escala diária e gerar relatórios BI, use `orquestrador_lote.py` junto com `gemini_audio_qa.py`.

### Dependências adicionais

- `pandas`
- `openpyxl` (opcional, para exportar XLSX)

```bash
pip install pandas openpyxl
```

### Uso em lote

```bash
python orquestrador_lote.py --audio-dir ./audios_para_auditoria --output-csv relatorio_consolidado_qa.csv --output-xlsx relatorio_consolidado_qa.xlsx --api-key SUA_CHAVE_API_AQUI
```

Se preferir, defina a variável de ambiente `GOOGLE_API_KEY` e não use `--api-key`.

### Modelo de operação

- O orquestrador varre `./audios_para_auditoria` em busca de MP3/WAV/M4A
- Cada áudio é processado com tolerância a falhas, mantendo o loop mesmo que um arquivo falhe
- O resultado é consolidado em um DataFrame do Pandas
- A saída é exportada como CSV e, opcionalmente, XLSX para análise BI
