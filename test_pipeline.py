from classification import process

if __name__ == "__main__":
    user_message = (
        "Bonjour, je n’ai pas été remboursé pour une consultation du 12/01. "
        "Pouvez-vous vérifier ? Je suis assez inquiet car j’ai avancé les frais."
    )

    result = process(user_message)

    print("\n=== REPLY (texte client) ===\n")
    print(result["reply"])

    print("\n=== CLASSIFICATION (JSON) ===\n")
    print(result["classification"])
