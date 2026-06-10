from voicenik.history import History


def test_ajout_et_ordre(tmp_path):
    history = History(path=tmp_path / "history.json")
    history.add("première")
    history.add("deuxième")
    entries = history.entries()
    assert [e["text"] for e in entries] == ["deuxième", "première"]
    assert all("timestamp" in e for e in entries)


def test_rotation_a_50_entrees(tmp_path):
    history = History(path=tmp_path / "history.json")
    for i in range(60):
        history.add(f"dictée {i}")
    entries = history.entries()
    assert len(entries) == 50
    assert entries[0]["text"] == "dictée 59"
    assert entries[-1]["text"] == "dictée 10"


def test_persistance(tmp_path):
    path = tmp_path / "history.json"
    History(path=path).add("texte persisté")
    rechargee = History(path=path)
    assert rechargee.entries()[0]["text"] == "texte persisté"


def test_fichier_corrompu(tmp_path):
    path = tmp_path / "history.json"
    path.write_text("{pas du json", encoding="utf-8")
    assert History(path=path).entries() == []
