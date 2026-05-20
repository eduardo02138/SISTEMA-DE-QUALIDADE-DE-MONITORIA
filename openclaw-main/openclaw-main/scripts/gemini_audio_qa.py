from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
    import google.generativeai as genai
except ImportError as exc:
    raise SystemExit(
        "Missing dependency: install google-generativeai first. "
        "Example: pip install google-generativeai"
    ) from exc


EXPECTED_QA_KEYS: List[str] = [
    "compliance_saudacao",
    "confirmacao_dados_seguranca",
    "problema_resolvido",
    "empatia_cordialidade",
    "ofensa_ao_cliente",
    "viola_lgpd",
    "tempo_espera_abusivo",
    "analise_sentimento_cliente",
    "motivo_avaliacao",
]

DEFAULT_SENTIMENTS: List[str] = ["satisfeito", "neutro", "irritado", "furioso"]


@dataclass
class QAProcessorScorecard:
    pesos_criterios: Dict[str, float] = None
    penalidades_criticas: Dict[str, Any] = None
    multiplicador_sentimento: Dict[str, float] = None

    def __post_init__(self) -> None:
        self.pesos_criterios = self.pesos_criterios or {
            "compliance_saudacao": 15.0,
            "confirmacao_dados_seguranca": 25.0,
            "problema_resolvido": 40.0,
            "empatia_cordialidade": 20.0,
        }

        self.penalidades_criticas = self.penalidades_criticas or {
            "ofensa_ao_cliente": "FATAL",
            "viola_lgpd": "FATAL",
            "tempo_espera_abusivo": 30.0,
        }

        self.multiplicador_sentimento = self.multiplicador_sentimento or {
            "satisfeito": 1.05,
            "neutro": 1.00,
            "irritado": 0.85,
            "furioso": 0.70,
        }

    def calcular_score(self, llm_json_output: Dict[str, Any]) -> Dict[str, Any]:
        nota_base = 0.0
        detalhamento_pontos: Dict[str, float] = {}

        for criterio, peso in self.pesos_criterios.items():
            cumpriu = bool(llm_json_output.get(criterio, False))
            pontos_ganhos = peso * float(cumpriu)
            nota_base += pontos_ganhos
            detalhamento_pontos[criterio] = pontos_ganhos

        sentimento = str(llm_json_output.get("analise_sentimento_cliente", "neutro")).lower()
        multiplicador = self.multiplicador_sentimento.get(sentimento, 1.0)
        nota_ajustada = nota_base * multiplicador

        for falha, punicao in self.penalidades_criticas.items():
            if bool(llm_json_output.get(falha, False)):
                if punicao == "FATAL":
                    return self._gerar_relatorio(
                        0.0,
                        detalhamento_pontos,
                        f"Zerado por falha crítica: {falha}",
                    )
                nota_ajustada -= float(punicao)

        nota_final = max(0.0, min(nota_ajustada, 100.0))
        return self._gerar_relatorio(nota_final, detalhamento_pontos, "Avaliação concluída com sucesso.")

    def _gerar_relatorio(self, nota: float, detalhamento: Dict[str, float], status: str) -> Dict[str, Any]:
        return {
            "status_processamento": status,
            "nota_final": round(nota, 2),
            "classificacao": self._classificar_desempenho(nota),
            "detalhamento": detalhamento,
        }

    def _classificar_desempenho(self, nota: float) -> str:
        if nota >= 90:
            return "Excelente (Nível de Premiação)"
        if nota >= 75:
            return "Aceitável (Dentro da Meta)"
        if nota >= 50:
            return "Atenção (Requer Treinamento)"
        return "Crítico (Risco Operacional)"


class GeminiAudioQAProcessor:
    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-1.5-pro",
        api_base_url: Optional[str] = None,
        max_poll_seconds: int = 180,
        cleanup_audio_file: bool = True,
    ) -> None:
        if not api_key:
            raise ValueError("A chave de API deverá ser fornecida via --api-key ou variável de ambiente.")

        self.api_key = api_key
        self.model_name = model_name
        self.api_base_url = api_base_url
        self.max_poll_seconds = max_poll_seconds
        self.cleanup_audio_file = cleanup_audio_file
        self._configure_genai()

    def _configure_genai(self) -> None:
        if self.api_base_url:
            genai.configure(api_key=self.api_key, api_base=self.api_base_url)
        else:
            genai.configure(api_key=self.api_key)

    def process_audio_file(self, audio_path: str) -> Dict[str, Any]:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {audio_path}")

        audio_file = self._upload_audio(audio_path)
        try:
            processed_file = self._wait_for_file_processing(audio_file)
            result = self._generate_audit_json(processed_file)
            return self._validate_output(result)

        finally:
            if self.cleanup_audio_file and hasattr(audio_file, "name"):
                self._delete_audio_file(audio_file.name)

    def _upload_audio(self, path: str) -> Any:
        print(f"Upload do arquivo de áudio para o Gemini: {path}")
        return genai.upload_file(path=path)

    def _wait_for_file_processing(self, audio_file: Any) -> Any:
        start = time.monotonic()
        while True:
            if getattr(audio_file, "state", None) is None:
                return audio_file

            state_name = getattr(audio_file.state, "name", None)
            if state_name == "PROCESSING":
                elapsed = time.monotonic() - start
                if elapsed > self.max_poll_seconds:
                    raise TimeoutError("Tempo de espera excedido enquanto o áudio era processado.")
                print("Arquivo em processamento no servidor...")
                time.sleep(5)
                audio_file = genai.get_file(audio_file.name)
                continue

            if state_name == "FAILED":
                raise RuntimeError("O servidor falhou ao processar o arquivo de áudio.")

            return audio_file

    def _generate_audit_json(self, audio_file: Any) -> Dict[str, Any]:
        prompt = self._build_prompt()
        model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={"response_mime_type": "application/json"},
        )

        print("Enviando áudio ao Gemini para auditoria...")
        response = model.generate_content([audio_file, prompt])

        text = getattr(response, "text", None) or getattr(response, "content", None)
        if text is None:
            raise RuntimeError("Resposta inesperada do Gemini: campo de texto ausente.")

        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "O Gemini retornou conteúdo que não pôde ser convertido em JSON.\n"
                f"Resposta bruta: {text[:1024]}"
            ) from exc

    def _delete_audio_file(self, file_name: str) -> None:
        try:
            genai.delete_file(file_name)
        except Exception as exc:
            print(f"Aviso: falha ao excluir arquivo temporário no Gemini: {exc}")

    def _build_prompt(self) -> str:
        return """
Atue como um auditor automatizado de Quality Assurance (QA) para atendimento ao cliente.

Você receberá um arquivo de áudio contendo uma gravação de chamada. Ouça o áudio e identifique duas vozes distintas: o Atendente e o Cliente.

Avalie os critérios abaixo e retorne APENAS um JSON válido com as chaves exatas e valores corretos:

{
  "compliance_saudacao": false,
  "confirmacao_dados_seguranca": false,
  "problema_resolvido": false,
  "empatia_cordialidade": false,
  "ofensa_ao_cliente": false,
  "viola_lgpd": false,
  "tempo_espera_abusivo": false,
  "analise_sentimento_cliente": "satisfeito",
  "motivo_avaliacao": "Justifique brevemente sua análise aqui"
}

Regras adicionais:
1. Use APENAS as chaves listadas acima.
2. "analise_sentimento_cliente" deve ser um dos valores: satisfeito, neutro, irritado ou furioso.
3. "motivo_avaliacao" deve ser uma justificativa curta e objetiva.
4. Não inclua texto adicional fora do JSON.
""".strip()

    def _validate_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(output, dict):
            raise ValueError("A saída do Gemini não é um objeto JSON.")

        missing_keys = [key for key in EXPECTED_QA_KEYS if key not in output]
        if missing_keys:
            raise ValueError(
                f"A saída do Gemini não contém as chaves obrigatórias: {missing_keys}. "
                f"Chaves recebidas: {list(output.keys())}"
            )

        sentiment = str(output.get("analise_sentimento_cliente", "")).lower()
        if sentiment not in DEFAULT_SENTIMENTS:
            raise ValueError(
                "O valor de 'analise_sentimento_cliente' é inválido. "
                f"Valores permitidos: {DEFAULT_SENTIMENTS}. Recebido: {sentiment}"
            )

        return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pipeline Gemini audio -> JSON + scorecard de QA."
    )
    parser.add_argument("audio_path", help="Caminho para o arquivo de áudio de chamada.")
    parser.add_argument(
        "--api-key",
        default=os.environ.get("GENAI_API_KEY") or os.environ.get("GOOGLE_API_KEY"),
        help="Chave da API Gemini. Também pode ser lida de GENAI_API_KEY ou GOOGLE_API_KEY.",
    )
    parser.add_argument(
        "--api-base",
        default=os.environ.get("GENAI_API_BASE"),
        help="URL base da API Gemini/OpenClaw, se necessário.",
    )
    parser.add_argument(
        "--model",
        default="gemini-1.5-pro",
        help="Modelo Gemini a ser utilizado. Ex: gemini-1.5-pro",
    )
    parser.add_argument(
        "--output-json",
        default=None,
        help="Arquivo JSON de saída para gravar o payload resultante.",
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Não exclui o arquivo de áudio temporário na nuvem após processamento.",
    )
    parser.add_argument(
        "--max-poll-seconds",
        type=int,
        default=180,
        help="Tempo máximo em segundos para aguardar o upload/processamento do áudio.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    processor = GeminiAudioQAProcessor(
        api_key=args.api_key,
        model_name=args.model,
        api_base_url=args.api_base,
        max_poll_seconds=args.max_poll_seconds,
        cleanup_audio_file=not args.no_cleanup,
    )

    raw_output = processor.process_audio_file(args.audio_path)
    scorecard = QAProcessorScorecard().calcular_score(raw_output)

    final_payload = {
        "audio_path": os.path.abspath(args.audio_path),
        "raw_ia_data": raw_output,
        "scorecard": scorecard,
    }

    output_text = json.dumps(final_payload, ensure_ascii=False, indent=2)
    print(output_text)

    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as out_file:
            out_file.write(output_text)
        print(f"Resultado gravado em: {args.output_json}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        raise SystemExit(1)
