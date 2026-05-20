from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import time
import wave
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Sobrescrita de print para evitar UnicodeEncodeError em consoles Windows
def print(*args, **kwargs):
    import builtins
    try:
        builtins.print(*args, **kwargs)
    except UnicodeEncodeError:
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                encoding = sys.stdout.encoding or 'utf-8'
                safe_args.append(arg.encode(encoding, errors='replace').decode(encoding))
            else:
                safe_args.append(arg)
        try:
            builtins.print(*safe_args, **kwargs)
        except Exception:
            safe_args_ascii = [
                arg.encode('ascii', errors='replace').decode('ascii') if isinstance(arg, str) else arg
                for arg in args
            ]
            builtins.print(*safe_args_ascii, **kwargs)

try:
    import google.genai as genai
except ImportError as exc:
    raise SystemExit(
        "Missing dependency: install google-genai first. "
        "Example: pip install google-genai"
    ) from exc

try:
    from mutagen._file import File as MutagenFile
except ImportError:
    MutagenFile = None  # type: ignore[assignment]

EXPECTED_QA_KEYS: List[str] = [
    "saudacao_padrao_claro",
    "coleta_dados_pessoais",
    "coleta_endereco_completo",
    "fez_sondagem_necessidades",
    "oferta_completa_produtos",
    "aplicou_contra_argumentacao",
    "ofensa_ao_cliente",
    "falha_viabilidade_tecnica",
    "analise_sentimento_cliente",
    "resumo_objecoes_cliente",
    "motivo_avaliacao",
    "transcricao_dialogo",
    # Campos estruturados adicionais para extração de dados do cliente
    "cliente_nome",
    "telefone_1",
    "telefone_2",
    "endereco_completo",
    "endereco_detalhado",
]

DEFAULT_SENTIMENTS: List[str] = ["satisfeito", "neutro", "irritado", "furioso"]
MODEL_ALIASES: Dict[str, str] = {
    "gemini-3": "gemini-3-pro-preview",
    "gemini-3-pro": "gemini-3-pro-preview",
    "gemini-3-flash": "gemini-3-flash-preview",
    "gemini-3.1-pro": "gemini-3.1-pro-preview",
}
MODEL_FALLBACKS: List[str] = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-3-flash-preview",
    "gemini-3-pro-preview",
    "gemini-3.1-pro-preview",
]


@dataclass
class QAProcessorScorecard:
    pesos_criterios: Dict[str, float] = field(default_factory=dict)
    penalidades_criticas: Dict[str, Any] = field(default_factory=dict)
    multiplicador_sentimento: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.pesos_criterios = self.pesos_criterios or {
            "saudacao_padrao_claro": 5.0,
            "coleta_dados_pessoais": 15.0,
            "coleta_endereco_completo": 15.0,
            "fez_sondagem_necessidades": 25.0,
            "oferta_completa_produtos": 15.0,
            "aplicou_contra_argumentacao": 25.0,
        }

        self.penalidades_criticas = self.penalidades_criticas or {
            "ofensa_ao_cliente": "FATAL",
            "falha_viabilidade_tecnica": 40.0,
        }

        self.multiplicador_sentimento = self.multiplicador_sentimento or {
            "satisfeito": 1.10,
            "neutro": 1.00,
            "irritado": 0.80,
            "furioso": 0.50,
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
        result = self._gerar_relatorio(nota_final, detalhamento_pontos, "Avaliação concluída com sucesso.")
        result["performance_sondagem_negociacao"] = (
            detalhamento_pontos.get("fez_sondagem_necessidades", 0.0)
            + detalhamento_pontos.get("aplicou_contra_argumentacao", 0.0)
        )

        if "resumo_objecoes_cliente" in llm_json_output:
            result["resumo_objecoes_cliente"] = llm_json_output["resumo_objecoes_cliente"]
        if "motivo_avaliacao" in llm_json_output:
            result["motivo_avaliacao"] = llm_json_output["motivo_avaliacao"]

        return result

    def _gerar_relatorio(self, nota: float, detalhamento: Dict[str, float], status: str) -> Dict[str, Any]:
        result = {
            "status_processamento": status,
            "nota_final": round(nota, 2),
            "classificacao": self._classificar_desempenho(nota),
            "detalhamento": detalhamento,
        }

        # Exiba o resumo de objeções e a motivação do auditor, quando disponíveis.
        return result

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
        model_name: str = "gemini-3",
        api_base_url: Optional[str] = None,
        max_poll_seconds: int = 180,
        cleanup_audio_file: bool = True,
    ) -> None:
        if not api_key:
            raise ValueError("A chave de API deverá ser fornecida via --api-key ou variável de ambiente.")

        self.api_key = api_key
        self.requested_model_name = model_name
        self.model_name = self._normalize_model_name(model_name)
        self.effective_model: Optional[str] = None
        self.api_base_url = api_base_url
        self.max_poll_seconds = max_poll_seconds
        self.cleanup_audio_file = cleanup_audio_file
        self.client = self._build_client()

    def _normalize_model_name(self, model_name: str) -> str:
        normalized = model_name.strip().lower()
        return MODEL_ALIASES.get(normalized, normalized)

    def _build_client(self) -> genai.Client:
        if self.api_base_url:
            http_options = genai.types.HttpOptions(base_url=self.api_base_url)
            return genai.Client(api_key=self.api_key, http_options=http_options)

        return genai.Client(api_key=self.api_key)

    def _get_model_candidates(self) -> List[str]:
        candidates = [self.model_name]
        for fallback in MODEL_FALLBACKS:
            if fallback not in candidates:
                candidates.append(fallback)
        return candidates

    def _is_model_not_found_error(self, message: str) -> bool:
        text = message.lower()
        return "not found" in text or "not supported for generatecontent" in text

    def _is_quota_error(self, message: str) -> bool:
        text = message.lower()
        return "resource_exhausted" in text or "quota" in text or "rate limit" in text

    def _otimizar_audio_local(self, caminho_bruto: str) -> Optional[str]:
        import subprocess
        import uuid
        
        diretorio = os.path.dirname(caminho_bruto) or "."
        nome_base = os.path.splitext(os.path.basename(caminho_bruto))[0]
        
        # Gera um nome de arquivo temporário limpo em ASCII puro para evitar qualquer erro de encoding
        caminho_otimizado = os.path.join(diretorio, f"opt_temp_{uuid.uuid4().hex}.mp3")

        print(f"[{nome_base}] Otimizando áudio localmente via FFmpeg...")
        
        # Parâmetros recomendados para inteligência de voz:
        # -ar 16000: Taxa de amostragem perfeitamente adequada para voz e IA (16kHz)
        # -ac 1: Converte estéreo para mono (reduz tamanho à metade)
        # -b:a 64k: Bitrate ideal para clareza vocal com alto poder de compressão
        comando = [
            "ffmpeg", "-y", "-i", caminho_bruto,
            "-ar", "16000", "-ac", "1", "-b:a", "64k",
            caminho_otimizado
        ]

        try:
            # Executa silenciosamente no background
            subprocess.run(comando, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, check=True)
            print(f"[{nome_base}] Compressão local FFmpeg concluída! Pronto para upload rápido.")
            return caminho_otimizado
        except FileNotFoundError:
            print("⚠️ AVISO: FFmpeg não foi encontrado no PATH do sistema. Utilizando o áudio bruto (mais lento).")
            return None
        except Exception as e:
            print(f"⚠️ AVISO: Falha na compressão do áudio: {e}. Utilizando o áudio bruto.")
            if os.path.exists(caminho_otimizado):
                try:
                    os.remove(caminho_otimizado)
                except Exception:
                    pass
            return None

    def process_audio_file(self, audio_path: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {audio_path}")

        # Tenta otimizar localmente o áudio para acelerar o upload e processamento
        caminho_otimizado = self._otimizar_audio_local(audio_path)
        caminho_trabalho = caminho_otimizado if caminho_otimizado else audio_path

        metadata = {
            "audio_path": audio_path,
            "duration_seconds": self._get_audio_duration(caminho_trabalho),
            "modelo_requisitado": self.requested_model_name,
            "modelo_efetivo": None,
        }

        audio_file = self._upload_audio(caminho_trabalho)
        try:
            processed_file = self._wait_for_file_processing(audio_file)
            result = self._generate_audit_json(processed_file)
            validated = self._validate_output(result)
            metadata["modelo_efetivo"] = self.effective_model or self.model_name
            return validated, metadata

        finally:
            # Limpa o arquivo na nuvem
            if self.cleanup_audio_file and hasattr(audio_file, "name"):
                self._delete_audio_file(audio_file.name)
            
            # Limpa o arquivo local temporário otimizado, caso tenha sido gerado
            if caminho_otimizado and os.path.exists(caminho_otimizado):
                try:
                    os.remove(caminho_otimizado)
                    print(f" -> Arquivo temporário otimizado {caminho_otimizado} removido localmente.")
                except Exception as clean_err:
                    print(f"Aviso: falha ao remover arquivo temporário otimizado: {clean_err}")

    def _upload_audio(self, path: str) -> Any:
        print(f"Upload do arquivo de áudio para o Gemini: {path}")
        
        # Detecta se o nome do arquivo contém caracteres não-ASCII (acentuação/especiais)
        basename = os.path.basename(path)
        has_non_ascii = any(ord(c) > 127 for c in basename)
        
        upload_path = path
        temp_ascii_path = None
        
        if has_non_ascii:
            import shutil
            import uuid
            # Cria uma cópia com nome limpo em ASCII puro para evitar UnicodeEncodeError no httpx
            ext = os.path.splitext(path)[1]
            diretorio = os.path.dirname(path) or "."
            temp_name = f"temp_upload_{uuid.uuid4().hex}{ext}"
            temp_ascii_path = os.path.join(diretorio, temp_name)
            shutil.copy(path, temp_ascii_path)
            upload_path = temp_ascii_path
            print(f" -> Nome contém caracteres não-ASCII. Utilizando cópia segura: {upload_path}")

        mime_type, _ = mimetypes.guess_type(upload_path)
        if not mime_type:
            extension = os.path.splitext(upload_path)[1].lower().lstrip('.')
            mime_type = {
                "mp3": "audio/mpeg",
                "wav": "audio/wav",
                "m4a": "audio/mp4",
                "aac": "audio/aac",
                "flac": "audio/flac",
            }.get(extension, "application/octet-stream")

        config = genai.types.UploadFileConfig(mime_type=mime_type)
        try:
            with open(upload_path, "rb") as audio_stream:
                return self.client.files.upload(file=audio_stream, config=config)
        finally:
            if temp_ascii_path and os.path.exists(temp_ascii_path):
                try:
                    os.remove(temp_ascii_path)
                    print(f" -> Cópia temporária {temp_ascii_path} removida localmente.")
                except Exception:
                    pass

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
                audio_file = self.client.files.get(name=audio_file.name)
                continue

            if state_name == "FAILED":
                raise RuntimeError("O servidor falhou ao processar o arquivo de áudio.")

            return audio_file

    def _generate_audit_json(self, audio_file: Any) -> Dict[str, Any]:
        prompt = self._build_prompt()
        config = genai.types.GenerateContentConfig(response_mime_type="application/json")

        print("Enviando áudio ao Gemini para auditoria...")
        response = self._generate_with_model_fallback(audio_file, prompt, config)

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

    def _generate_with_model_fallback(
        self,
        audio_file: Any,
        prompt: str,
        config: Any,
    ) -> Any:
        last_error = None
        max_retries = 3
        
        for model in self._get_model_candidates():
            for attempt in range(max_retries):
                print(f"Tentando gerar conteúdo com o modelo: {model} (Tentativa {attempt + 1}/{max_retries})")
                try:
                    response = self.client.models.generate_content(
                        model=model,
                        contents=[audio_file, prompt],
                        config=config,
                    )
                    self.model_name = model
                    self.effective_model = model
                    print(f"Modelo aceito: {model}")
                    return response
                except Exception as exc:
                    message = str(exc).lower()
                    last_error = exc
                    
                    # Verifica se é um erro transiente que justifica retry (503 ou 429)
                    is_transient = "503" in message or "unavailable" in message or "429" in message or "rate limit" in message or "exhausted" in message
                    
                    if is_transient and attempt < max_retries - 1:
                        wait_time = (2 ** attempt) + 1  # 2s, 3s, 5s...
                        print(f" -> Erro temporário ({message}). Aguardando {wait_time}s para nova tentativa...")
                        time.sleep(wait_time)
                        continue
                    
                    # Se não for transiente ou se esgotaram as tentativas, tenta o próximo modelo
                    print(f" -> Erro ao tentar gerar com {model}: {message}")
                    if attempt < max_retries - 1:
                        print(" -> Tentando próximo modelo da lista de fallback...")
                    break

        raise RuntimeError(
            "Falha ao gerar conteúdo no Gemini. Nenhum modelo de fallback teve sucesso após múltiplas tentativas. "
            f"Último erro: {last_error}"
        )

    def _get_audio_duration(self, path: str) -> Optional[float]:
        extension = os.path.splitext(path)[1].lower().lstrip('.')
        if extension in ("wav", "wave"):
            try:
                with wave.open(path, "rb") as audio_wave:
                    frames = audio_wave.getnframes()
                    rate = audio_wave.getframerate()
                    return round(frames / float(rate), 2)
            except Exception:
                return None

        if MutagenFile is not None:
            try:
                audio = MutagenFile(path)
                if audio is not None and hasattr(audio, "info") and getattr(audio.info, "length", None):
                    return round(float(audio.info.length), 2)
            except Exception:
                return None

        return None

    def _delete_audio_file(self, file_name: str) -> None:
        try:
            self.client.files.delete(name=file_name)
        except Exception as exc:
            print(f"Aviso: falha ao excluir arquivo temporário no Gemini: {exc}")

    def _build_prompt(self) -> str:
        return """
Você é um Auditor Sênior de Qualidade de Atendimento, Vendas e Retenção.

Sua tarefa é ouvir o áudio desta chamada com extrema atenção e realizar duas ações cruciais:
1. TRANSCREVER O DIÁLOGO FIELMENTE E LITERALMENTE (IPSIS LITTERIS): Transcreva a gravação de forma literal, palavra por palavra, exatamente como é falada no áudio.
   - RIGOR ABSOLUTO: A transcrição deve ser IDENTICA ao áudio. Se o áudio diz "tá", transcreva "tá", não "está". Se o áudio tem gagueiras ou hesitações (ex: "é... é... então"), transcreva EXATAMENTE assim.
   - NÃO RESUMA: É expressamente proibido resumir falas. Se uma fala durar 1 minuto, transcreva o minuto inteiro palavra por palavra.
   - NÃO CRIE DIÁLOGOS: Não invente falas que não existem. Se você não ouve o cliente, NÃO transcreva nada para o cliente.
   - SEPARAÇÃO DE CANAIS: Identifique claramente quem está falando. 
   - GRAVAÇÕES DE CANAL ÚNICO / VLOGS DO YOUTUBE: Se a gravação for de apenas um lado da conversa, transcreva EXATAMENTE tudo o que é falado.
     - Se a voz do cliente NÃO for ouvida fisicamente no áudio, você NÃO deve incluir respostas fictícias para o "Cliente". Deixe apenas as falas que de fato saem das caixas de som/áudio.
2. AVALIAR O DESEMPENHO: Avalie a aderência do atendente às etapas do funil de atendimento e vendas com base exclusivamente nas falas que de fato ocorreram.

Pense passo a passo antes de responder. Considere:
- Saudação Padrão: O atendente se identificou corretamente?
- Sondagem: Fez perguntas investigativas reais?
- Oferta Completa: Apresentou o produto com detalhes?
- Contra-argumentação: Contornou objeções de forma consultiva?

Retorne APENAS um JSON válido com as chaves exatas abaixo:

{
  "saudacao_padrao_claro": false,
  "coleta_dados_pessoais": false,
  "coleta_endereco_completo": false,
  "fez_sondagem_necessidades": false,
  "oferta_completa_produtos": false,
  "aplicou_contra_argumentacao": false,
  "ofensa_ao_cliente": false,
  "falha_viabilidade_tecnica": false,
  "analise_sentimento_cliente": "neutro",
  "resumo_objecoes_cliente": "String descrevendo a principal barreira de compra apresentada pelo cliente.",
  "motivo_avaliacao": "Justificativa técnica detalhada e verídica da sua análise, baseada apenas no conteúdo real do áudio.",
  "transcricao_dialogo": [
    {"papel": "Atendente", "fala": "Fala literal..."},
    {"papel": "Cliente", "fala": "Fala literal..."}
  ]
}

Regras importantes:
1. Use APENAS as chaves listadas acima.
2. "analise_sentimento_cliente" deve ser satisfeito, neutro, irritado ou furioso.
3. A chave "transcricao_dialogo" deve ser a transcrição sequencial mais fiel possível ao áudio real.
4. Não inclua nenhum texto explicativo fora do JSON.
""".strip()

    def _consolidate_json_list(self, outputs: List[Any]) -> Dict[str, Any]:
        if not outputs:
            raise ValueError("A saída do Gemini retornou uma lista vazia.")
        
        # Se houver apenas um item, apenas extrai ele
        if len(outputs) == 1:
            if isinstance(outputs[0], dict):
                return outputs[0]
            else:
                raise ValueError("O item na lista de saída do Gemini não é um objeto JSON.")
                
        # Consolida múltiplos segmentos em um único dicionário coerente
        consolidated: Dict[str, Any] = {
            "saudacao_padrao_claro": False,
            "coleta_dados_pessoais": False,
            "coleta_endereco_completo": False,
            "fez_sondagem_necessidades": False,
            "oferta_completa_produtos": False,
            "aplicou_contra_argumentacao": False,
            "ofensa_ao_cliente": False,
            "falha_viabilidade_tecnica": False,
            "analise_sentimento_cliente": "neutro",
            "resumo_objecoes_cliente": "",
            "motivo_avaliacao": "",
            "transcricao_dialogo": []
        }
        
        sentiments_priority = {"furioso": 4, "irritado": 3, "neutro": 2, "satisfeito": 1}
        max_sentiment_val = 0
        max_sentiment = "neutro"
        
        objecoes = []
        motivos = []
        
        for idx, out in enumerate(outputs):
            if not isinstance(out, dict):
                continue
                
            # Booleanos: união lógica OR (se cumpriu em qualquer trecho, considera cumprido)
            # Para os itens negativos (ofensa e falha viabilidade), OR também é correto para penalizar se ocorrer em algum trecho
            for key in [
                "saudacao_padrao_claro",
                "coleta_dados_pessoais",
                "coleta_endereco_completo",
                "fez_sondagem_necessidades",
                "oferta_completa_produtos",
                "aplicou_contra_argumentacao",
                "ofensa_ao_cliente",
                "falha_viabilidade_tecnica"
            ]:
                if bool(out.get(key, False)):
                    consolidated[key] = True
            
            # Sentimento: adota o mais severo/expressivo
            sent = str(out.get("analise_sentimento_cliente", "neutro")).lower()
            sent_val = sentiments_priority.get(sent, 2)
            if sent_val > max_sentiment_val:
                max_sentiment_val = sent_val
                max_sentiment = sent
                
            # Objeções
            obj = out.get("resumo_objecoes_cliente", "").strip()
            if obj and obj.lower() not in ("sem objeções", "n/a", "sem objecoes"):
                objecoes.append(f"[Trecho {idx+1}] {obj}")
                
            # Motivos
            mot = out.get("motivo_avaliacao", "").strip()
            if mot:
                motivos.append(f"[Trecho {idx+1}] {mot}")
                
            # Transcrição: concatena os diálogos sequencialmente
            dialog = out.get("transcricao_dialogo", [])
            if isinstance(dialog, list):
                consolidated["transcricao_dialogo"].extend(dialog)

            # Campos de contato/cliente: adota o primeiro valor não vazio encontrado
            for ckey in ["cliente_nome", "telefone_1", "telefone_2", "endereco_completo"]:
                val = out.get(ckey) or (out.get("raw_ia_data") or {}).get(ckey) if isinstance(out, dict) else None
                if val and not consolidated.get(ckey):
                    consolidated[ckey] = val

            # Endereço detalhado: se presente como dict, tenta preencher os campos
            ed = out.get("endereco_detalhado") or (out.get("raw_ia_data") or {}).get("endereco_detalhado") if isinstance(out, dict) else None
            if isinstance(ed, dict) and not consolidated.get("endereco_detalhado"):
                consolidated["endereco_detalhado"] = ed
                
        consolidated["analise_sentimento_cliente"] = max_sentiment
        consolidated["resumo_objecoes_cliente"] = "; ".join(objecoes) if objecoes else "Sem objeções"
        consolidated["motivo_avaliacao"] = " | ".join(motivos) if motivos else "Chamada auditada."
        
        return consolidated

    def _validate_output(self, output: Any) -> Dict[str, Any]:
        # Se a saída for uma lista, tenta consolidar
        if isinstance(output, list):
            output = self._consolidate_json_list(output)

        # Se após a consolidação ainda não for dicionário, falha
        if not isinstance(output, dict):
            raise ValueError("A saída do Gemini não pôde ser convertida em um dicionário JSON válido.")

        # Desembrulha caso esteja aninhado sob uma única chave raiz (ex: {"auditoria": {...}} ou {"resultado": {...}})
        if not all(k in output for k in ["saudacao_padrao_claro", "transcricao_dialogo"]):
            for val in output.values():
                if isinstance(val, dict) and all(k in val for k in ["saudacao_padrao_claro", "transcricao_dialogo"]):
                    output = val
                    break

        # Preenche de forma proativa chaves ausentes com valores padrão (tolerância a falhas pequenas da IA)
        for key in EXPECTED_QA_KEYS:
            if key not in output:
                if key in [
                    "saudacao_padrao_claro",
                    "coleta_dados_pessoais",
                    "coleta_endereco_completo",
                    "fez_sondagem_necessidades",
                    "oferta_completa_produtos",
                    "aplicou_contra_argumentacao",
                    "ofensa_ao_cliente",
                    "falha_viabilidade_tecnica"
                ]:
                    output[key] = False
                elif key == "analise_sentimento_cliente":
                    output[key] = "neutro"
                elif key == "resumo_objecoes_cliente":
                    output[key] = "Sem objeções"
                elif key == "motivo_avaliacao":
                    output[key] = "Avaliação estruturada gerada pela IA."
                elif key == "transcricao_dialogo":
                    output[key] = []
                elif key == "cliente_nome":
                    output[key] = ""
                elif key == "telefone_1":
                    output[key] = ""
                elif key == "telefone_2":
                    output[key] = ""
                elif key == "endereco_completo":
                    output[key] = ""
                elif key == "endereco_detalhado":
                    output[key] = {}

        # Valida campo sentimento
        sentiment = str(output.get("analise_sentimento_cliente", "")).lower()
        if sentiment not in DEFAULT_SENTIMENTS:
            output["analise_sentimento_cliente"] = "neutro"

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

    raw_output, metadata = processor.process_audio_file(args.audio_path)
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
