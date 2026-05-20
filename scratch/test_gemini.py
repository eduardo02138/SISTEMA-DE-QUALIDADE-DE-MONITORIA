import os
import sys

# Ensure the parent directory is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gemini_audio_qa import GeminiAudioQAProcessor

def test_robustness():
    print("Initializing QA Processor...")
    processor = GeminiAudioQAProcessor(
        api_key="mock_key",
        model_name="gemini-2.5-flash",
        cleanup_audio_file=True
    )

    # 1. Test case: Output is a list of two segment dicts
    print("\nTest Case 1: List of segment dictionaries")
    mock_list_output = [
        {
            "saudacao_padrao_claro": True,
            "coleta_dados_pessoais": True,
            "analise_sentimento_cliente": "satisfeito",
            "resumo_objecoes_cliente": "Preço alto",
            "motivo_avaliacao": "O cliente achou caro mas gostou do plano.",
            "transcricao_dialogo": [{"papel": "Atendente", "fala": "Olá!"}]
        },
        {
            "saudacao_padrao_claro": False,
            "coleta_dados_pessoais": False,
            "fez_sondagem_necessidades": True,
            "ofensa_ao_cliente": True,
            "analise_sentimento_cliente": "furioso",
            "resumo_objecoes_cliente": "Fidelidade",
            "motivo_avaliacao": "O atendente se irritou.",
            "transcricao_dialogo": [{"papel": "Cliente", "fala": "Não quero!"}]
        }
    ]
    
    validated = processor._validate_output(mock_list_output)
    print("Validated output keys:", list(validated.keys()))
    
    # Assertions
    assert validated["saudacao_padrao_claro"] == True, "Should be True (OR operation)"
    assert validated["coleta_dados_pessoais"] == True, "Should be True (OR operation)"
    assert validated["fez_sondagem_necessidades"] == True, "Should be True (OR operation)"
    assert validated["ofensa_ao_cliente"] == True, "Should be True (OR operation)"
    assert validated["analise_sentimento_cliente"] == "furioso", "Should pick the worst sentiment"
    assert "Preço alto" in validated["resumo_objecoes_cliente"], "Should concatenate objections"
    assert "Fidelidade" in validated["resumo_objecoes_cliente"], "Should concatenate objections"
    assert len(validated["transcricao_dialogo"]) == 2, "Should concatenate transcript list"
    print(" -> Case 1 PASSED!")

    # 2. Test case: Output is a single dictionary wrapped in a list
    print("\nTest Case 2: Dictionary wrapped in a single-element list")
    mock_wrapped = [
        {
            "saudacao_padrao_claro": True,
            "transcricao_dialogo": [{"papel": "Atendente", "fala": "Teste"}]
        }
    ]
    validated = processor._validate_output(mock_wrapped)
    assert validated["saudacao_padrao_claro"] == True
    assert validated["analise_sentimento_cliente"] == "neutro", "Should backfill default sentiment"
    assert validated["resumo_objecoes_cliente"] == "Sem objeções", "Should backfill default objections"
    print(" -> Case 2 PASSED!")

    # 3. Test case: Nested under a root key
    print("\nTest Case 3: Nested under single root key")
    mock_nested = {
        "auditoria": {
            "saudacao_padrao_claro": True,
            "transcricao_dialogo": []
        }
    }
    validated = processor._validate_output(mock_nested)
    assert validated["saudacao_padrao_claro"] == True
    print(" -> Case 3 PASSED!")

    print("\nALL UNIT TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_robustness()
