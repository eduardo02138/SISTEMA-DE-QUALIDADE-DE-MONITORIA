import argparse
import glob
import os
import time
from typing import Any, Dict, List, Optional

import pandas as pd

from gemini_audio_qa import GeminiAudioQAProcessor, QAProcessorScorecard

# ==========================================
# CONFIGURAÇÕES DO AMBIENTE
# ==========================================
DIRETORIO_AUDIOS_PADRAO = "./audios_para_auditoria"
ARQUIVO_SAIDA_CSV_PADRAO = "relatorio_consolidado_qa.csv"
ARQUIVO_SAIDA_XLSX_PADRAO = "relatorio_consolidado_qa.xlsx"
CHAVE_API_AMBIENTE = os.environ.get("GOOGLE_API_KEY", "")


def listar_arquivos_de_audio(diretorio: str) -> List[str]:
    extensoes = ("*.mp3", "*.wav", "*.m4a")
    arquivos_alvo: List[str] = []
    for ext in extensoes:
        arquivos_alvo.extend(glob.glob(os.path.join(diretorio, ext)))
    return sorted(arquivos_alvo, key=str.lower)


def processar_lote(
    diretorio: str,
    api_key: str,
    model_name: str = "gemini-3",
    delay_segundos: float = 2.0,
) -> pd.DataFrame:
    arquivos_alvo = listar_arquivos_de_audio(diretorio)
    total_arquivos = len(arquivos_alvo)
    print(f"Iniciando lote: {total_arquivos} arquivos encontrados em '{diretorio}'.\n")

    if total_arquivos == 0:
        return pd.DataFrame()

    processor_ia = GeminiAudioQAProcessor(api_key=api_key, model_name=model_name)
    motor_notas = QAProcessorScorecard()
    dados_consolidados: List[Dict[str, Any]] = []

    for indice, caminho_audio in enumerate(arquivos_alvo, start=1):
        nome_arquivo = os.path.basename(caminho_audio)
        print(f"[{indice}/{total_arquivos}] Processando: {nome_arquivo}...")

        linha_registro: Dict[str, Any] = {
            "Nome do Arquivo": nome_arquivo,
            "Caminho do Arquivo": caminho_audio,
            "Duracao Audio (segundos)": None,
            "Modelo Efetivo Usado": None,
            "Status": "Pendente",
            "Nota Final": None,
            "Classificacao": None,
            "Sentimento Cliente": None,
            "Performance Vendas (Sondagem/Oferta)": None,
            "Resumo Objecoes": None,
            "Motivo Avaliacao IA": None,
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
            linha_registro[f"Check: {criterio}"] = "Não"
            linha_registro[f"Pontos: {criterio}"] = 0.0

        try:
            raw_output, metadata = processor_ia.process_audio_file(caminho_audio)
            scorecard = motor_notas.calcular_score(raw_output)

            linha_registro.update(
                {
                    "Status": scorecard.get("status_processamento", "Concluído"),
                    "Nota Final": scorecard.get("nota_final", 0.0),
                    "Classificacao": scorecard.get("classificacao", "N/A"),
                    "Sentimento Cliente": raw_output.get(
                        "analise_sentimento_cliente", "Não Identificado"
                    ),
                    "Performance Vendas (Sondagem/Oferta)": scorecard.get(
                        "performance_sondagem_negociacao", 0.0
                    ),
                    "Resumo Objecoes": scorecard.get("resumo_objecoes_cliente", ""),
                    "Motivo Avaliacao IA": scorecard.get("motivo_avaliacao", ""),
                    "Duracao Audio (segundos)": metadata.get("duration_seconds"),
                    "Modelo Efetivo Usado": metadata.get("modelo_efetivo"),
                }
            )

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
                valor = raw_output.get(criterio, False)
                linha_registro[f"Check: {criterio}"] = "Sim" if bool(valor) else "Não"
                linha_registro[f"Pontos: {criterio}"] = round(
                    scorecard.get("detalhamento", {}).get(criterio, 0.0), 2
                )

            print(
                f" -> Sucesso. Nota: {linha_registro['Nota Final']} | {linha_registro['Classificacao']}"
            )

        except Exception as exc:
            erro_msg = str(exc)
            print(f" -> ERRO: {erro_msg}")
            linha_registro["Status"] = f"Falha Técnica: {erro_msg}"
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
                linha_registro[f"Pontos: {criterio}"] = 0.0

        dados_consolidados.append(linha_registro)

        # Salva o relatório individual na pasta 'relatorio' para resiliência on-the-fly
        try:
            pasta_relatorio = "relatorio"
            os.makedirs(pasta_relatorio, exist_ok=True)
            caminho_saida_individual = os.path.join(
                pasta_relatorio, f"relatorio_{nome_arquivo}.csv"
            )
            df_individual = pd.DataFrame([linha_registro])
            df_individual.to_csv(caminho_saida_individual, index=False, encoding="utf-8-sig")
            print(f" -> Relatório individual salvo em: {caminho_saida_individual}")

            # Salva o arquivo de transcrição de diálogo (.txt) de forma estruturada
            if "raw_output" in locals() and isinstance(raw_output, dict) and "transcricao_dialogo" in raw_output:
                caminho_transcricao = os.path.join(
                    pasta_relatorio, f"transcricao_{nome_arquivo}.txt"
                )
                dialogo = raw_output["transcricao_dialogo"]
                with open(caminho_transcricao, "w", encoding="utf-8") as f_txt:
                    f_txt.write("=== TRANSCRIÇÃO DE AUDITORIA ===\n")
                    f_txt.write(f"Gravação: {nome_arquivo}\n")
                    f_txt.write(f"Data de Auditoria: {time.strftime('%d/%m/%Y %H:%M:%S')}\n\n")
                    for fala_dict in dialogo:
                        papel = fala_dict.get("papel", "Desconhecido")
                        fala = fala_dict.get("fala", "")
                        f_txt.write(f"{papel}: {fala}\n")
                print(f" -> Arquivo de transcrição salvo em: {caminho_transcricao}")
        except Exception as r_exc:
            print(f" -> Erro ao salvar arquivos individuais para {nome_arquivo}: {r_exc}")

    df_final = pd.DataFrame(dados_consolidados)
    return df_final


def salvar_relatorio(
    df: pd.DataFrame,
    arquivo_csv: str,
    arquivo_xlsx: Optional[str] = None,
) -> None:
    df.to_csv(arquivo_csv, index=False, encoding="utf-8-sig")
    print(f"Relatório CSV salvo em: {arquivo_csv}")

    if arquivo_xlsx:
        try:
            df.to_excel(arquivo_xlsx, index=False, engine="openpyxl")
            print(f"Relatório Excel salvo em: {arquivo_xlsx}")
        except Exception as exc:
            print(f"Aviso: falha ao exportar para XLSX ({arquivo_xlsx}): {exc}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Processador em lote de arquivos de áudio para auditoria Gemini QA."
    )
    parser.add_argument(
        "--audio-dir",
        default=DIRETORIO_AUDIOS_PADRAO,
        help="Diretório de entrada para os áudios (mp3, wav, m4a).",
    )
    parser.add_argument(
        "--output-csv",
        default=ARQUIVO_SAIDA_CSV_PADRAO,
        help="Caminho do arquivo CSV de saída.",
    )
    parser.add_argument(
        "--output-xlsx",
        default=None,
        help="Caminho opcional do arquivo XLSX de saída.",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Chave de API do Google Gemini (pode ser lida de GOOGLE_API_KEY).",
    )
    parser.add_argument(
        "--model",
        default="gemini-3",
        help="Modelo Gemini a ser usado para a avaliação. Alias gemini-3 mapeia para gemini-3-pro-preview.",
    )
    parser.add_argument(
        "--delay-segundos",
        type=float,
        default=2.0,
        help="Delay entre chamadas para reduzir risco de rate limit.",
    )
    args = parser.parse_args()

    api_key = args.api_key or CHAVE_API_AMBIENTE
    if not api_key:
        raise SystemExit(
            "Nenhuma chave de API fornecida. Defina GOOGLE_API_KEY ou use --api-key."
        )

    if not os.path.exists(args.audio_dir):
        os.makedirs(args.audio_dir, exist_ok=True)
        print(
            f"Criei a pasta '{args.audio_dir}'. Coloque seus áudios lá e rode novamente."
        )
        raise SystemExit(0)

    df_resultados = processar_lote(
        args.audio_dir,
        api_key=api_key,
        model_name=args.model,
        delay_segundos=args.delay_segundos,
    )

    if df_resultados.empty:
        print("Nenhum arquivo de áudio encontrado. Nada foi exportado.")
        raise SystemExit(0)

    salvar_relatorio(df_resultados, args.output_csv, args.output_xlsx)

    print("\n=======================================================")
    print("Lote finalizado!")
    print(df_resultados[["Nome do Arquivo", "Nota Final", "Classificacao"]].head(10).to_string(index=False))
    print("=======================================================")
