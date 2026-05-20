import json
import tempfile
from types import SimpleNamespace

from gemini_audio_qa import GeminiAudioQAProcessor, QAProcessorScorecard


class FakeState(SimpleNamespace):
    pass


class FakeFile(SimpleNamespace):
    pass


def make_sample_output() -> dict:
    return {
        "saudacao_padrao_claro": True,
        "coleta_dados_pessoais": True,
        "coleta_endereco_completo": True,
        "fez_sondagem_necessidades": True,
        "oferta_completa_produtos": True,
        "aplicou_contra_argumentacao": True,
        "ofensa_ao_cliente": False,
        "falha_viabilidade_tecnica": False,
        "analise_sentimento_cliente": "satisfeito",
        "resumo_objecoes_cliente": "Cliente demonstrou interesse, mas pediu desconto.",
        "motivo_avaliacao": "Atendente fez sondagem completa, apresentou oferta relevante e controlou objeções.",
        "transcricao_dialogo": [
            {"papel": "Atendente", "fala": "Olá, muito bom dia! Falo da Claro, com quem tenho o prazer de conversar?"},
            {"papel": "Cliente", "fala": "Olá, bom dia. Aqui é o Jackson."},
            {"papel": "Atendente", "fala": "Olá seu Jackson, em que posso ajudar o senhor hoje?"},
            {"papel": "Cliente", "fala": "Queria saber os planos de internet para a minha rua."}
        ]
    }


def run_smoke_test() -> None:
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio:
        audio_path = temp_audio.name

    processor = GeminiAudioQAProcessor(api_key="TEST_API_KEY")
    sample_output = make_sample_output()

    fake_file = FakeFile(name="fake-file-123", state=FakeState(name="PROCESSING"))
    fake_done_file = FakeFile(name="fake-file-123", state=FakeState(name="ACTIVE"))
    file_checks = [fake_file, fake_done_file]

    processor.client.files.upload = lambda *, file, config=None: fake_file

    def fake_get(name: str, config=None):
        return file_checks.pop(0) if file_checks else fake_done_file

    processor.client.files.get = fake_get
    processor.client.models.generate_content = lambda *, model, contents, config=None: SimpleNamespace(text=json.dumps(sample_output))
    processor.client.files.delete = lambda *, name=None: None

    print("Executando smoke test local...")
    output, metadata = processor.process_audio_file(audio_path)
    scorecard = QAProcessorScorecard().calcular_score(output)

    print("Smoke test finalizado com sucesso.")
    print("JSON de saída validado:")
    print(json.dumps(output, indent=2, ensure_ascii=False))
    print("Metadados do áudio:")
    print(json.dumps(metadata, indent=2, ensure_ascii=False))
    print("Scorecard:")
    print(json.dumps(scorecard, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    run_smoke_test()
