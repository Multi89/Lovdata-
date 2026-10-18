from __future__ import annotations

from typing import Literal, TypedDict


ExplanationLevel = Literal["lett", "vanlig", "professor"]


class StyleGuide(TypedDict):
    level: ExplanationLevel
    label: str
    audience: str
    instructions: list[str]
    required_sections: list[str]


_STYLE_GUIDES: dict[ExplanationLevel, StyleGuide] = {
    "lett": {
        "level": "lett",
        "label": "Lett forklart",
        "audience": "Person uten juridisk utdanning",
        "instructions": [
            "Skriv på enkelt norsk med korte avsnitt.",
            "Forklar juridiske ord første gang de brukes.",
            "Start med hva regelen betyr i praksis for brukeren.",
            "Skill tydelig mellom rettigheter, plikter, frister og mulige neste steg.",
            "Ikke gi en sikker konklusjon når kildene eller faktum er uklare.",
        ],
        "required_sections": [
            "Kort forklart",
            "Hvilke regler som gjelder",
            "Hva dette kan bety i praksis",
            "Kilder",
        ],
    },
    "vanlig": {
        "level": "vanlig",
        "label": "Vanlig juridisk forklaring",
        "audience": "Allmenn leser som ønsker både forklaring og presisjon",
        "instructions": [
            "Skriv tydelig og presist uten unødvendig fagspråk.",
            "Oppgi hovedregel, viktige vilkår, unntak og relevante frister.",
            "Skill mellom lov, forskrift, rettspraksis og andre kilder.",
            "Vis usikkerhet og hvilke fakta som kan endre vurderingen.",
        ],
        "required_sections": [
            "Konklusjon",
            "Regelgrunnlag",
            "Vurdering",
            "Praktiske neste steg",
            "Kilder",
        ],
    },
    "professor": {
        "level": "professor",
        "label": "Professor / juridisk faglig nivå",
        "audience": "Jurist, student eller fagperson",
        "instructions": [
            "Bruk juridisk metode og presis rettskildeterminologi.",
            "Identifiser rettsspørsmålet og skill mellom de lege lata og eventuell de lege ferenda.",
            "Drøft ordlyd, systematikk, formål, forarbeider, rettspraksis og reelle hensyn når kildene finnes.",
            "Vurder rettskildenes vekt, innbyrdes forhold, tidsmessige gyldighet og eventuell motstrid.",
            "Skill klart mellom sikker rett, tolkningsalternativer og faktumavhengige vurderinger.",
            "Bruk paragrafhenvisninger og dokument-ID-er, men unngå lange ordrette sitater.",
        ],
        "required_sections": [
            "Problemstilling",
            "Rettslig utgangspunkt",
            "Rettskildebildet",
            "Drøftelse",
            "Konklusjon",
            "Kilder",
        ],
    },
}


def get_style_guide(level: ExplanationLevel) -> StyleGuide:
    return _STYLE_GUIDES[level]
