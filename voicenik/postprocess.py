"""Post-traitement du texte transcrit (sauts de ligne dictés, espaces)."""

import re

# « nouvelle ligne » / « à la ligne » dictés → vrai saut de ligne.
# La ponctuation qui précède est conservée, celle qui suit la commande est absorbée.
_NEWLINE = re.compile(
    r"\s*\b(?:nouvelle ligne|retour à la ligne|[àa] la ligne)\b[\s,.;]*",
    re.IGNORECASE,
)
_MULTISPACE = re.compile(r"[ \t]{2,}")


def apply(text: str) -> str:
    text = _NEWLINE.sub("\n", text)
    text = _MULTISPACE.sub(" ", text)
    lines = [line.strip() for line in text.split("\n")]
    return "\n".join(lines).strip()
