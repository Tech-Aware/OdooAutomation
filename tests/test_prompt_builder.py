from generate_post.prompt_builder import build_user_prompt


def test_build_user_prompt_fills_fields():
    info = {
        "objet": "Fête du village",
        "date": "14 juillet",
        "horaires": "18h-23h",
        "lieu": "Place du village",
    }
    prompt = build_user_prompt(info)
    assert "Fête du village" in prompt
    assert "14 juillet" in prompt
    assert "18h-23h" in prompt
    assert "Place du village" in prompt
    # fields not provided are omitted entirely
    assert "- Programme : " not in prompt
