from voicenik import postprocess


def test_nouvelle_ligne_devient_saut_de_ligne():
    assert postprocess.apply("Bonjour. Nouvelle ligne Merci") == "Bonjour.\nMerci"


def test_a_la_ligne():
    assert postprocess.apply("Premier point à la ligne deuxième point") == (
        "Premier point\ndeuxième point"
    )


def test_retour_a_la_ligne():
    assert postprocess.apply("titre retour à la ligne contenu") == "titre\ncontenu"


def test_ponctuation_apres_commande_absorbee():
    assert postprocess.apply("Fin. Nouvelle ligne, suite") == "Fin.\nsuite"


def test_espaces_multiples_reduits():
    assert postprocess.apply("un  deux   trois") == "un deux trois"


def test_texte_sans_commande_inchange():
    text = "Déploie le pod Kubernetes sur GitLab, puis redémarre Spring Boot."
    assert postprocess.apply(text) == text


def test_texte_vide():
    assert postprocess.apply("") == ""
