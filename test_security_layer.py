# test_security_layer.py
from security_layer import redact_pii, prepare_safe_payload

def test_case(title: str, text: str, hard_block: bool):
    print("\n" + "="*80)
    print("TEST:", title)
    safe = prepare_safe_payload(text, hard_block=hard_block)
    print("pii_found:", safe.pii_found)
    print("blocked:", safe.blocked, "| reason:", safe.block_reason)
    print("text_out:", safe.text)

if __name__ == "__main__":
    # 1) Email + téléphone + code postal
    test_case(
        "Email + téléphone FR + CP",
        "Bonjour, contactez-moi à jean.dupont@gmail.com ou au 06 12 34 56 78. J'habite 75012.",
        hard_block=False
    )

    # 2) IBAN (doit être masqué, et bloqué si hard_block=True)
    test_case(
        "IBAN (redaction-only)",
        "Mon IBAN est FR76 3000 6000 0112 3456 7890 189, merci.",
        hard_block=False
    )
    test_case(
        "IBAN (hard block)",
        "Mon IBAN est FR76 3000 6000 0112 3456 7890 189, merci.",
        hard_block=True
    )

    # 3) NIR (num sécu FR approximatif)
    test_case(
        "NIR FR (hard block)",
        "Mon numéro de sécurité sociale est 180027501234567, aidez-moi.",
        hard_block=True
    )

    # 4) Numéro de carte (13-19 chiffres, masque + block si hard_block=True)
    test_case(
        "Carte bancaire (hard block)",
        "Voici ma carte 4111 1111 1111 1111, prenez le paiement.",
        hard_block=True
    )

    # 5) Cas normal assurance (ne doit pas détecter PII)
    test_case(
        "Cas normal remboursement",
        "Je n’ai pas été remboursé pour une consultation du 12/01. Pouvez-vous vérifier ?",
        hard_block=False
    )
