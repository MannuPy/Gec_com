"""
Encodage phonétique simplifié adapté au français (RF-08).

Objectif : permettre la recherche de produits avec tolérance aux fautes de
frappe et aux variations orthographiques courantes (ex. « visserie » /
« vissérie », « marteau » / « marto »), en réduisant chaque mot à un
squelette phonétique comparable, dans l'esprit de Soundex/Metaphone mais
adapté aux digrammes et sons du français.

Le code obtenu est stocké dans `Product.name_phonetic` (un code par mot du
nom, séparés par des espaces — cf. `app/models/catalog.py`) et recalculé
automatiquement à chaque création/modification de produit. La recherche
(`GET /products?search=...`) compare le code phonétique du terme recherché à
ce champ en complément de la recherche `ILIKE` classique.
"""
import re
import unicodedata

# Substitutions ordonnées : digrammes/sons composés du français ramenés à une
# forme canonique. L'ordre est important (les motifs les plus longs/specifiques
# d'abord) pour eviter qu'une regle generale ne masque un cas particulier.
_REPLACEMENTS = [
    ("eau", "o"),
    ("au", "o"),
    ("ai", "e"),
    ("ei", "e"),
    ("oeu", "eu"),
    ("oe", "e"),
    ("ph", "f"),
    ("th", "t"),
    ("qu", "k"),
    ("ch", "x"),
    ("gu", "g"),
    ("ge", "je"),
    ("gi", "ji"),
    ("gy", "ji"),
    ("ce", "se"),
    ("ci", "si"),
    ("cy", "si"),
    ("c", "k"),
    ("y", "i"),
    ("z", "s"),
    ("x", "ks"),
    ("w", "v"),
    ("h", ""),
]


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _encode_word(word: str) -> str:
    cleaned = _strip_accents(word.lower())
    cleaned = cleaned.replace("ç", "s")
    cleaned = re.sub(r"[^a-z]", "", cleaned)
    if not cleaned:
        return ""

    for src, dst in _REPLACEMENTS:
        cleaned = cleaned.replace(src, dst)

    # Réduit les lettres consécutives identiques (ex. "tt" -> "t", "ss" -> "s")
    collapsed: list[str] = []
    for ch in cleaned:
        if not collapsed or collapsed[-1] != ch:
            collapsed.append(ch)

    return "".join(collapsed)


def phonetic_code(text: str | None) -> str:
    """
    Calcule le code phonétique d'un texte (un code par mot, séparés par des
    espaces). Retourne une chaîne vide si `text` est vide/None.

    >>> phonetic_code("Visserie")
    'viseri'
    >>> phonetic_code("Vissérie")
    'viseri'
    >>> phonetic_code("Marteau Stanley")
    'marto stanle'
    """
    if not text:
        return ""

    words = re.split(r"\s+", text.strip())