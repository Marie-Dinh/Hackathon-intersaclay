import os
import random
from dotenv import load_dotenv
import anthropic

load_dotenv()

API_KEY = os.getenv("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=API_KEY)

MODEL = os.getenv("ANTHROPIC_MODEL") or os.getenv("CLAUDE_MODEL") or "claude-2"

# Profil
assure = {
    "nom": "Assuré",
    "age": 28,
    "habitation": "appartement",
    "zone": "urbaine",
    "sante": {
        "conditions_chroniques": False,
        "derniere_visite_medicale": 365
    }
}

# Météo fake
meteo = {
    "temperature": random.randint(-10,45),
    "pluie": random.randint(0,100),
    "vent": random.randint(0,120),
    "alerte": random.choice([True,False])
}

def score_risque():
    score=0
    if meteo["alerte"]: score+=3
    if meteo["temperature"]>40 or meteo["temperature"]<-5: score+=2
    if meteo["pluie"]>70: score+=2
    if meteo["vent"]>90: score+=1
    
    if assure["sante"]["conditions_chroniques"]:
        score+=2
        
    score+=min(assure["sante"]["derniere_visite_medicale"]/365,2)
    score+=1
    
    return round(score,2)

def demander_claude(question):
    
    contexte=f"""
Tu es une IA d'assurance préventive.

Profil client:
{assure}

Conditions météo:
{meteo}

Score de risque: {score_risque()}/10

Donne des conseils concrets et rassurants.
"""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=300,
            system=contexte,
            messages=[
                {"role": "user", "content": question}
            ]
        )
    except anthropic.NotFoundError:
        # Modèle introuvable: essayer un modèle de secours raisonnable
        fallback_model = "claude-2"
        if MODEL == fallback_model:
            return (
                f"Erreur: modèle '{MODEL}' introuvable. "
                "Définissez la variable d'environnement ANTHROPIC_MODEL avec un modèle valide."
            )
        try:
            response = client.messages.create(
                model=fallback_model,
                max_tokens=300,
                system=contexte,
                messages=[{"role": "user", "content": question}]
            )
        except Exception as e:
            return f"Erreur lors du fallback vers '{fallback_model}': {e}"
    except Exception as e:
        return f"Erreur lors de l'appel à l'API Claude: {e}"

    return response.content[0].text

print("\nAssistant prêt (exit pour quitter)\n")

while True:
    q=input("Vous: ")
    
    if q.lower()=="exit":
        break
        
    print("\nClaude:",demander_claude(q),"\n")
