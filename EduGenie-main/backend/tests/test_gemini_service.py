import backend.services.gemini_service as gemini_service


def test_default_model_name_uses_supported_gemini_model(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "dummy-key")
    monkeypatch.setattr(gemini_service, "_model", None)

    captured = {}

    def fake_configure(api_key):
        captured["api_key"] = api_key

    def fake_generative_model(model_name, system_instruction=None):
        captured["model_name"] = model_name
        captured["system_instruction"] = system_instruction
        return object()

    monkeypatch.setattr(gemini_service.genai, "configure", fake_configure)
    monkeypatch.setattr(gemini_service.genai, "GenerativeModel", fake_generative_model)

    gemini_service._get_model()

    assert captured["model_name"] == "gemini-3.5-flash"
    assert captured["api_key"] == "dummy-key"
