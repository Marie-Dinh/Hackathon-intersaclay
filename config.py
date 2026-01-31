# config.py
import os
import sys
from dotenv import load_dotenv

load_dotenv()  # charge .env AVANT de lire les variables

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
print(f"[CONFIG] model={CLAUDE_MODEL} key_present={bool(ANTHROPIC_API_KEY)}", file=sys.stderr)


def ensure_api_key() -> bool:
    if not ANTHROPIC_API_KEY:
        msg = (
            "❌ Aucune clé Claude / Anthropic détectée.\n\n"
            "Définis ANTHROPIC_API_KEY dans .env ou en variable d'environnement.\n"
            "Exemples :\n"
            "  - Linux / macOS : export ANTHROPIC_API_KEY=\"ta_cle_ici\"\n"
            "  - Windows (PowerShell) : setx ANTHROPIC_API_KEY \"ta_cle_ici\"\n"
        )
        print(msg, file=sys.stderr)
        return False
    return True
