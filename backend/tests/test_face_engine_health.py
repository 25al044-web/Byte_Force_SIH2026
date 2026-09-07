from app.services import face_matcher

def test_face_engine_ready_when_models_and_provider_loaded(monkeypatch):
    class App: models = {"detection": object(), "recognition": object()}
    class Ort:
        @staticmethod
        def get_available_providers(): return ["CPUExecutionProvider"]
    monkeypatch.setattr(face_matcher, "_get_face_app", lambda: App())
    monkeypatch.setitem(__import__("sys").modules, "onnxruntime", Ort)
    assert face_matcher.is_face_engine_ready()["ready"] is True

def test_face_engine_unavailable_on_initialization_failure(monkeypatch):
    monkeypatch.setattr(face_matcher, "_get_face_app", lambda: (_ for _ in ()).throw(RuntimeError("model failed")))
    assert face_matcher.is_face_engine_ready()["ready"] is False
