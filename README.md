# VoiceNik — Dictée vocale 100 % locale pour Windows

Appuyez sur **Ctrl + Espace**, parlez, relâchez : le texte transcrit est injecté
à la position du curseur, dans n'importe quelle application (navigateur, VS Code,
IntelliJ, terminal, messagerie…). La transcription est réalisée entièrement en
local par [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — aucune
donnée ne quitte votre PC.

## Fonctionnalités

- 🎙️ Raccourci clavier global configurable (par défaut `Ctrl+Espace`)
- ✋ Deux modes : **push-to-talk** (maintenir la touche) ou **toggle** (appui / appui)
- 🇫🇷 Excellent support du français, ponctuation automatique
- 🧠 Vocabulaire technique configurable (Kubernetes, GitLab, Angular, Spring Boot…)
- ↩️ Dites « nouvelle ligne » ou « à la ligne » pour insérer un saut de ligne
- ⚡ GPU NVIDIA (CUDA, modèle `large-v3-turbo`) avec repli automatique CPU (`int8`)
- 📋 Injection instantanée par collage (presse-papiers restauré ensuite) ou frappe simulée
- 🖥️ Icône de zone de notification (état du micro en couleur) + pastille discrète animée
- 🕘 Historique des 50 dernières dictées, copiables en un clic
- 🚀 Lancement automatique au démarrage de Windows (optionnel)

## Installation (depuis les sources)

Prérequis : Python ≥ 3.10 sous Windows.

```powershell
cd voiceNik
pip install -e ".[cuda]"        # ou pip install -e .  (CPU uniquement)
```

Premier lancement :

```powershell
python -m voicenik
```

Le modèle Whisper est téléchargé une seule fois dans `%APPDATA%\VoiceNik\models\`
(~1,6 Go pour `large-v3-turbo`). Ensuite, tout fonctionne **hors ligne**.

## Utilisation

1. L'icône VoiceNik apparaît dans la zone de notification (bleue = prêt).
2. Placez le curseur où vous voulez écrire, dans n'importe quelle application.
3. **Maintenez `Ctrl+Espace`** et parlez : un son doux retentit et une pastille
   « Écoute… » (point rouge animé) apparaît centrée en haut de l'écran.
4. Relâchez : second son doux, la pastille passe en « Transcription… »
   (icône orange + spinner), puis le texte apparaît au curseur.

Clic sur l'icône de notification → fenêtre **Paramètres** : microphone, modèle,
langue, raccourci, mode push-to-talk/toggle, méthode d'injection, vocabulaire,
bouton de test, historique.

> ⚠️ `Ctrl+Espace` est aussi le raccourci d'autocomplétion de VS Code / IntelliJ.
> Tant que VoiceNik tourne, il intercepte cette combinaison. Changez le raccourci
> dans les paramètres (ex. `ctrl+alt+space` ou `f9`) si vous préférez.

## Configuration

Fichiers dans `%APPDATA%\VoiceNik\` :

| Fichier | Rôle |
|---|---|
| `config.json` | paramètres (modifiables aussi via la fenêtre Paramètres) |
| `history.json` | 50 dernières dictées |
| `voicenik.log` | journal (latence de chaque dictée incluse) |
| `models\` | modèles Whisper téléchargés |

Modèles disponibles : `large-v3-turbo` (recommandé avec GPU), `medium`, `small`
(recommandé en CPU), `base`.

## Tests

```powershell
pip install -e ".[dev]"
pytest
```

## Construire l'exécutable

```powershell
pip install -e ".[cuda,dev]"
pyinstaller packaging/voicenik.spec
```

Résultat : `dist\VoiceNik\VoiceNik.exe` (dossier autonome à copier où vous voulez ;
mode *onedir* choisi pour un démarrage < 2 s). Cochez « Lancer VoiceNik au
démarrage de Windows » dans les paramètres pour l'enregistrer dans le registre
(`HKCU\...\Run`, aucun droit administrateur requis).

## Limitations connues

- Les applications lancées **en administrateur** ne reçoivent ni le raccourci ni
  le texte si VoiceNik n'est pas lui-même élevé (protection Windows UIPI).
- En mode « collage », seul le **texte** du presse-papiers est restauré (pas les
  images ou fichiers copiés).
- La toute première dictée après le lancement peut attendre la fin du chargement
  du modèle (quelques secondes).

## Architecture du code

```
voicenik/
├── __main__.py        point d'entrée, instance unique, journalisation
├── app.py             machine à états (idle → recording → transcribing)
├── hotkey.py          raccourci global, modes push-to-talk / toggle
├── audio.py           capture micro 16 kHz (sounddevice)
├── transcriber.py     faster-whisper, CUDA→CPU automatique, vocabulaire
├── postprocess.py     « nouvelle ligne » → \n, nettoyage
├── injector.py        collage Ctrl+V (presse-papiers restauré) ou frappe
├── history.py         50 dernières dictées (JSON)
├── autostart.py       clé Run du registre
├── config.py          paramètres JSON (%APPDATA%\VoiceNik)
├── assets/            sons de notification (start.wav, stop.wav)
└── ui/                tray (pystray), overlay et paramètres (tkinter)
```

`scripts/generate_sounds.py` régénère les sons de notification (glissandos
sinusoïdaux doux) si vous voulez les personnaliser.
