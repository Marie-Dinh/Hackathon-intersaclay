# test_pdf_security.py
from security_layer import extract_text_from_file, prepare_safe_payload

PDF_PATH = "..\..\datas\Test_PDF_Security.pdf"

if __name__ == "__main__":
    with open(PDF_PATH, "rb") as f:
        b = f.read()

    extracted = extract_text_from_file(b, "..\..\datas\Test_PDF_Security.pdf")
    print("\n=== EXTRACTED (head 500) ===")
    print(extracted[:500])

    safe = prepare_safe_payload(
        user_message="Voici ma demande, pièce jointe ci-dessous.",
        file_bytes=b,
        file_name="Test_PDF_Security.pdf",
        hard_block=False,  # mets True pour vérifier le blocage IBAN
    )

    print("\n=== SAFE PAYLOAD ===")
    print("pii_found:", safe.pii_found)
    print("blocked:", safe.blocked, "| reason:", safe.block_reason)
    print("\ntext_out (head 800):")
    print(safe.text[:800])
