import dataclasses

from voicenik.config import Settings, load_settings, save_settings


def test_valeurs_par_defaut():
    settings = Settings()
    assert settings.language == "fr"
    assert settings.hotkey == "ctrl+space"
    assert settings.mode == "push_to_talk"
    assert "Kubernetes" in settings.vocabulary


def test_aller_retour(tmp_path):
    path = tmp_path / "config.json"
    original = dataclasses.replace(Settings(), hotkey="f9", mode="toggle", model="small")
    save_settings(original, path)
    assert load_settings(path) == original


def test_fichier_absent(tmp_path):
    assert load_settings(tmp_path / "absent.json") == Settings()


def test_fichier_corrompu(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("###", encoding="utf-8")
    assert load_settings(path) == Settings()


def test_cles_inconnues_ignorees(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"hotkey": "f9", "ancienne_option": true}', encoding="utf-8")
    assert load_settings(path).hotkey == "f9"
