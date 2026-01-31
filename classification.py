# claude_agent.py
from typing import Optional, Dict, Any, List
import os
import json
from security_layer import prepare_safe_payload
import logging; logging.basicConfig(level=logging.INFO); log = logging.getLogger("assurai")

from anthropic import Anthropic  # pip install anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL


def build_claude_client() -> Optional[Anthropic]:
    """Crée un client Claude (Anthropic). Utilise ANTHROPIC_API_KEY si présent."""
    api_key = ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY")
    log.info("build_claude_client | model=%s | key_present=%s", CLAUDE_MODEL, bool(api_key))  # debug config

    if not api_key:
        return None
    return Anthropic(api_key=api_key)  # conforme à l'exemple officiel


def _extract_text(message) -> str:
    """Concatène tous les blocs texte de la réponse Claude."""
    parts: List[str] = []
    for block in getattr(message, "content", []) or []:
        if getattr(block, "type", None) == "text":
            parts.append(getattr(block, "text", "") or "")
    return "\n".join([p for p in parts if p]).strip()


# 1) Réponse "client" (texte naturel)
SYSTEM_PROMPT_RESPONSE = """
Tu es un assistant de relation client dans l'assurance.
Objectif : aider l’assuré à clarifier sa demande et proposer les prochaines étapes.

Règles :
- Français, ton pro, simple, rassurant.
- Concis et actionnable (liste d’étapes si utile).
- Ne pas inventer d’infos.
- Si infos manquantes : poser 2 à 4 questions ciblées.
- Ne retourne pas de JSON ici.
"""


def generate_customer_reply(user_message: str) -> str:
    """1er appel : génère la réponse destinée au client."""
    client = build_claude_client()
    log.info("generate_customer_reply | input_len=%d", len(user_message))  # taille entrée (sans contenu)
    if client is None:
        return "⚠️ Impossible d'appeler Claude : clé API manquante."

    msg = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=500,
        system=SYSTEM_PROMPT_RESPONSE,  # system prompt côté Claude Messages API
        messages=[{"role": "user", "content": user_message}],
        temperature=0.3,
    )
    log.info("generate_customer_reply | ok | blocks=%d", len(getattr(msg, "content", []) or []))  # réponse reçue
    return _extract_text(msg)


# 2) Classification (JSON strict via output_config.format / json_schema)
SYSTEM_PROMPT_CLASSIFIER = """
Tu es un classifieur de demandes d'assurés.
Retourne UNIQUEMENT un JSON conforme au schéma fourni.
Si incertain : AUTRE/INCONNU + confiance faible.
"""


CLASSIFICATION_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "motif": {
            "type": "string",
            "enum": [
                "REMBOURSEMENT_SANTE",
                "DEVIS",
                "COTISATIONS",
                "ATTESTATION",
                "ARRET_TRAVAIL_PREVOYANCE",
                "RETRAITE_INFO",
                "CHANGEMENT_SITUATION",
                "RECLAMATION",
                "AUTRE",
            ],
        },
        "domaine": {"type": "string", "enum": ["SANTE", "PREVOYANCE", "RETRAITE", "MULTI", "INCONNU"]},
        "intention": {"type": "string", "enum": ["INFORMATION", "ACTION", "SUIVI", "CONTESTATION", "ENVOI_DOCUMENTS"]},
        "priorite": {"type": "string", "enum": ["HAUTE", "NORMALE", "BASSE"]},
        "ton_client": {"type": "string", "enum": ["CALME", "INQUIET", "MECONTENT", "URGENT"]},
        "actions_recommandees": {
            "type": "array",
            "items": {"type": "string", "enum": ["ORIENTER_SELFCARE", "CREER_TICKET_GESTION", "DEMANDER_PIECES", "DEMANDER_INFOS", "ESCALADER_URGENCE"]},
        },
        "infos_a_collecter": {"type": "array", "items": {"type": "string"}},
        "resume_1_phrase": {"type": "string"},
        "confiance": {"type": "number"},
    },
    "required": [
        "motif",
        "domaine",
        "intention",
        "priorite",
        "ton_client",
        "actions_recommandees",
        "infos_a_collecter",
        "resume_1_phrase",
        "confiance",
    ],
    "additionalProperties": False,
}


def classify(text_to_classify: str) -> Dict[str, Any]:
    """2e appel : classification JSON garantie par le schéma."""
    client = build_claude_client()
    if client is None:
        return {
            "motif": "AUTRE",
            "domaine": "INCONNU",
            "intention": "INFORMATION",
            "priorite": "NORMALE",
            "ton_client": "CALME",
            "actions_recommandees": ["DEMANDER_INFOS"],
            "infos_a_collecter": [],
            "resume_1_phrase": "Clé API manquante : classification non réalisée.",
            "confiance": 0.0,
        }
    log.info("classify | input_len=%d | schema_keys=%d", len(text_to_classify), len(CLASSIFICATION_SCHEMA.get("properties", {})))  # debug schema
    msg = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=300,
        system=SYSTEM_PROMPT_CLASSIFIER,
        messages=[{"role": "user", "content": f"Texte à classifier :\n{text_to_classify}"}],
        temperature=0.0,
        # Structured outputs (JSON Schema) => JSON valide dans response.content[0].text
        output_config={
            "format": {
                "type": "json_schema",
                "schema": CLASSIFICATION_SCHEMA,
            }
        },
    )

    raw_json = _extract_text(msg)
    log.info("classify | raw_json=%s", raw_json[:300].replace("\n", "\\n"))  # tronqué (évite fuite)
    #print("DEBUG raw_json:", repr(raw_json))
    data = json.loads(raw_json)

# Validation simple / garde-fou : forcer confiance dans [0, 1]
    try:
        c = float(data.get("confiance", 0.0))
    except (TypeError, ValueError):
        c = 0.0
    data["confiance"] = max(0.0, min(1.0, c))

    log.info("classify | result | motif=%s domaine=%s confiance=%.2f", data.get("motif"), data.get("domaine"), float(data.get("confiance", 0.0)))  # sortie structurée
    return data


def process(user_message: str, file_bytes: bytes = None, file_name: str = None) -> Dict[str, Any]:
    log.info("process | start | msg_len=%d", len(user_message))  # début pipeline

    """
    Pipeline complet : sécurisation -> réponse -> classification.
    Le LLM ne voit jamais les PII brutes (redaction).
    """
    safe = prepare_safe_payload(
        user_message=user_message,
        file_bytes=file_bytes,
        file_name=file_name,
        hard_block=False,  # mets True si tu veux bloquer IBAN/NIR/carte
    )
    log.info("security | pii_found=%s | blocked=%s", getattr(safe, "pii_found", None), getattr(safe, "blocked", None))  # privacy-by-design


    # Si tu veux bloquer en cas de données très sensibles :
    if safe.blocked:
        return {
            "reply": "⚠️ Votre message contient des données très sensibles (IBAN/NIR/carte). "
                     "Merci de les retirer avant de continuer.",
            "classification": {
                "motif": "AUTRE",
                "domaine": "INCONNU",
                "intention": "INFORMATION",
                "priorite": "NORMALE",
                "ton_client": "CALME",
                "actions_recommandees": ["DEMANDER_INFOS"],
                "infos_a_collecter": [],
                "resume_1_phrase": "Blocage sécurité: données sensibles détectées.",
                "confiance": 0.0,
            },
            "pii_found": safe.pii_found,
            "blocked": True,
            "block_reason": safe.block_reason,
        }

    reply = generate_customer_reply(safe.text)
    classification = classify(f"DEMANDE CLIENT:\n{safe.text}\n\nREPONSE ASSISTANT:\n{reply}")

    return {
        "reply": reply,
        "classification": classification,
        "pii_found": safe.pii_found,
        "blocked": False,
        "block_reason": None,
    }
