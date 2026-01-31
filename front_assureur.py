import streamlit as st
import anthropic
import os
from dotenv import load_dotenv
import random

load_dotenv()

# -------- CONFIG CLAUDE --------
client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

MODEL = "claude-3-haiku-20240307"



# -------- BASE CLIENTS --------
assures = [
    {
        "nom":"Emilie",
        "age":28,
        "assurance":"Habitation",
        "historique_sinistre":1,
        "message":"J’ai eu un dégât des eaux dans ma salle de bain hier soir, l’eau venait du plafond."
    },
    {
        "nom":"Paul",
        "age":52,
        "assurance":"Auto",
        "historique_sinistre":4,
        "message":"On a rayé toute ma voiture sur le parking cette nuit, je n’ai rien vu."
    },
    {
        "nom":"Lina",
        "age":35,
        "assurance":"Santé",
        "historique_sinistre":0,
        "message":"Je demande un remboursement pour des soins dentaires urgents."
    },
]

# -------- SCORE FRAUDE --------
def score_fraude(a):
    s=0
    
    if a["historique_sinistre"]>=3:
        s+=4
        
    if "nuit" in a["message"]:
        s+=2
        
    if "rien vu" in a["message"]:
        s+=2
        
    s+=random.randint(0,2)
    
    return min(s,10)

# -------- UI --------
st.title("🛡️ Dashboard Assureur 🛡️")

# Sélection assuré
nom = st.selectbox(
    "Choisir un de vos assurés",
    [a["nom"] for a in assures]
)

assure = next(a for a in assures if a["nom"]==nom)


st.markdown("""
<style>

/* Selectbox fond bleu foncé */
div[data-baseweb="select"] > div {
    background-color: #2649AB !important;
    color: white !important;
    border-radius: 10px;
}

/* Texte à l'intérieur */
div[data-baseweb="select"] span {
    color: black !important;
}

/* Menu déroulant */
ul {
    background-color: #0f172a !important;
    color: white !important;
}

li {
    color: white !important;
}

</style>
""", unsafe_allow_html=True)

# -------- PROFIL --------
st.subheader("👤 Profil assuré")

col1,col2=st.columns(2)

with col1:
    st.write("Nom:",assure["nom"])
    st.write("Age:",assure["age"])

with col2:
    st.write("Type d'assurance:",assure["assurance"])
    st.write("Sinistres passés:",assure["historique_sinistre"])

st.subheader("📂 Dossier assuré")

if st.button("Afficher le dossier de l’assuré"):

    st.markdown("### 🧾 Informations détaillées")

    st.write("**Nom :**", assure["nom"])
    st.write("**Âge :**", assure["age"])
    st.write("**Type d'assurance :**", assure["assurance"])
    st.write("**Historique sinistres :**", assure["historique_sinistre"])

    st.markdown("### 💬 Dernière déclaration")

    st.info(assure["message"])

    st.markdown("### 🔎 Analyse rapide")

    if assure["historique_sinistre"] >= 3:
        st.warning("Client avec historique de sinistres élevé → Vérification conseillée")
    else:
        st.success("Profil client standard")



# -------- MESSAGE CLIENT --------
st.subheader("💬 Déclaration client")

st.info(assure["message"])

# -------- SCORE FRAUDE --------
fraude = score_fraude(assure)

st.subheader("🚨 Risque de fraude")

if fraude>=7:
    st.error(f"Risque ÉLEVÉ : {fraude}/10")
elif fraude>=4:
    st.warning(f"Risque MODÉRÉ : {fraude}/10")
else:
    st.success(f"Risque FAIBLE : {fraude}/10")

# -------- RÉSUMÉ IA --------
st.subheader("🤖 Résumé intelligent")

if st.button("Générer résumé IA"):

    prompt=f"""
Tu es analyste en assurance.

Résume la déclaration client en 3 lignes claires.

Client:
{assure}
"""

    resp = client.messages.create(
        model=MODEL,
        max_tokens=300,
        messages=[
            {"role":"user","content":prompt}
        ]
    )

    st.write(resp.content[0].text)



st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #0f172a, #1e3a8a, #0ea5e9);
        background-attachment: fixed;
    }

    /* Texte en blanc pour contraste */
    h1, h2, h3, h4, h5, h6, p, label, div {
        color: white !important;
    }

    /* Boîtes stylées */
    .stSelectbox, .stTextInput, .stButton>button {
        border-radius: 10px;
    }

    /* Cards effet glassmorphism */
    .stAlert {
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        border: 1px solid rgba(255,255,255,0.2);
    }
    </style>
    """,
    unsafe_allow_html=True
)
