# security_layer.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Tuple
import re
import io

try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None


# --- Regex PII FR utiles (hackathon) ---
RE_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
RE_PHONE_FR = re.compile(r"\b(?:\+33\s?|0)(?:[1-9])(?:[\s.-]?\d{2}){4}\b")
RE_IBAN = re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}\s?[A-Z0-9]{1,4}\b", re.IGNORECASE)
RE_NIR_FR = re.compile(r"\b[12]\d{2}(?:0[1-9]|1[0-2])(?:\d{2}|2[ABab])\d{3}\d{3}\d{2}\b")  # approx
RE_CARD = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
RE_POSTCODE_FR = re.compile(r"\b\d{5}\b")

# Nom / prénom (patterns structurés, faibles faux positifs)
RE_NOM_LABEL = re.compile(r"(?im)\bnom\s*:\s*[A-ZÀ-ÖØ-Ý][A-Za-zÀ-ÖØ-öø-ÿ' -]{1,40}\b")
RE_PRENOM_LABEL = re.compile(r"(?im)\bpr[ée]nom\s*:\s*[A-ZÀ-ÖØ-Ý][A-Za-zÀ-ÖØ-öø-ÿ' -]{1,40}\b")

# Civilités + Nom (ex: "Monsieur Dupont", "Mme Martin")
RE_CIVILITE_NOM = re.compile(r"(?i)\b(m\.|mr|monsieur|mme|madame|mlle|mademoiselle)\s+[A-ZÀ-ÖØ-Ý][A-Za-zÀ-ÖØ-öø-ÿ' -]{1,40}\b")

# "Je m'appelle Prénom Nom" (assez fiable)
RE_JE_MAPPELLE = re.compile(r"(?i)\bje\s+m[' ]appelle\s+[A-ZÀ-ÖØ-Ý][A-Za-zÀ-ÖØ-öø-ÿ' -]{1,40}(?:\s+[A-ZÀ-ÖØ-Ý][A-Za-zÀ-ÖØ-öø-ÿ' -]{1,40})?\b")


@dataclass
class SafePayload:
    text: str
    pii_found: List[str]
    blocked: bool
    block_reason: Optional[str] = None


def redact_pii(text: str) -> Tuple[str, List[str]]:
    found: List[str] = []

    def sub(pattern: re.Pattern, repl: str, label: str, s: str) -> str:
        if pattern.search(s):
            found.append(label)
        return pattern.sub(repl, s)

    t = text
    t = sub(RE_EMAIL, "[EMAIL]", "email", t)
    t = sub(RE_PHONE_FR, "[TEL]", "telephone", t)
    t = sub(RE_IBAN, "[IBAN]", "iban", t)
    t = sub(RE_NIR_FR, "[NIR]", "nir", t)
    t = sub(RE_CARD, "[NUM_CARTE]", "carte_bancaire", t)
    t = sub(RE_POSTCODE_FR, "[CODE_POSTAL]", "code_postal", t)

    t = sub(RE_NOM_LABEL, "Nom : [NOM]", "nom", t)
    t = sub(RE_PRENOM_LABEL, "Prénom : [PRENOM]", "prenom", t)
    t = sub(RE_CIVILITE_NOM, "[CIVILITE] [NOM]", "nom", t)
    t = sub(RE_JE_MAPPELLE, "Je m'appelle [PRENOM] [NOM]", "nom_prenom", t)


    print(f"[SEC] redact_pii | found={sorted(set(found))}")
    return t, sorted(set(found))


def should_block(pii_found: List[str]) -> Tuple[bool, Optional[str]]:
    # Politique hackathon : on peut soit bloquer, soit juste masquer.
    # Ici on bloque si très sensible.
    high_risk = {"iban", "nir", "carte_bancaire"}
    hit = high_risk.intersection(set(pii_found))
    if hit:
        return True, f"Données sensibles détectées: {', '.join(sorted(hit))}"
    return False, None


def extract_text_from_file(file_bytes: bytes, file_name: str, max_pages: int = 2, max_chars: int = 3000) -> str:
    name = (file_name or "").lower()
    print(f"[SEC] extract_text_from_file | file={name} | bytes={len(file_bytes)} | PdfReader={'OK' if PdfReader else 'None'}")


    if name.endswith(".txt"):
        return file_bytes.decode("utf-8", errors="ignore")[:max_chars]

    if name.endswith(".pdf"):
        if PdfReader is None:
            return "[PDF non lu: PyPDF2 non installé]"
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            chunks = []
            for p in reader.pages[:max_pages]:
                page_text = p.extract_text() or ""
                if page_text.strip():
                    chunks.append(page_text)
            joined = "\n".join(chunks).strip()
            print(f"[SEC] pdf_extract | chars={len(joined)} | pages_used={min(max_pages, len(reader.pages))}")
            return joined[:max_chars] if joined else "[PDF lu mais texte vide]"
        except Exception:
            return "[PDF non lu: erreur extraction]"

    # Images: OCR volontairement désactivé pour éviter dépendances/instabilité
    if name.endswith((".png", ".jpg", ".jpeg")):
        return "[Image fournie: OCR désactivé en démo]"

    return "[Pièce jointe non supportée]"


def prepare_safe_payload(
    user_message: str,
    file_bytes: Optional[bytes] = None,
    file_name: Optional[str] = None,
    hard_block: bool = False,
    max_chars: int = 8000,
) -> SafePayload:
    base = (user_message or "").strip()[:max_chars]

    if file_bytes and file_name:
        extracted = extract_text_from_file(file_bytes, file_name)
        base = base + f"\n\n[EXTRAIT_PIECE_JOINTE: {file_name}]\n" + extracted

    redacted, pii = redact_pii(base)

    blocked, reason = (should_block(pii) if hard_block else (False, None))
    print(f"[SEC] prepare_safe_payload | pii_found={pii} | blocked={blocked} | text_len={len(redacted)}")
    return SafePayload(text=redacted, pii_found=pii, blocked=blocked, block_reason=reason)
