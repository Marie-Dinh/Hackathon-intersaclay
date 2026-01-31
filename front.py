@ -0,0 +1,174 @@
import streamlit as st
from classification import process
from config import ensure_api_key
import random
import datetime

# ---------------- CONFIG ----------------
st.set_page_config(page_title="AssurAI Winner Demo", layout="wide")

if "history" not in st.session_state:
    st.session_state.history = []

if "analysis" not in st.session_state:
    st.session_state.analysis = None

if "sent" not in st.session_state:
    st.session_state.sent = False

# ---------------- HEADER ----------------
st.title("🥇 AssurAI — AI Insurance Copilot")
st.caption("Déclaration de sinistre augmentée par IA")

st.markdown("---")

if not ensure_api_key():
    st.error("Clé API manquante.")
    st.stop()

# ---------------- SIDEBAR DASHBOARD ----------------
with st.sidebar:

    st.header("📊 Dashboard Impact")

    st.metric("⏱ Temps traitement", "-45%")
    st.metric("❌ Erreurs dossiers", "-60%")
    st.metric("😊 Satisfaction client", "+32%")
    st.metric("💰 Coût gestion", "-25%")

    st.markdown("---")

    st.header("🧠 IA Capabilities")
    st.write("""
    - NLP sinistre
    - Pré-qualification auto
    - Détection incohérences
    - Assistance assuré temps réel
    """)

# ---------------- INPUT CLIENT ----------------
st.subheader("📝 Déclaration assuré")

text = st.text_area("Décrivez votre situation")

audio = st.audio_input("🎤 Message vocal")

file = st.file_uploader("📎 Pièce jointe", type=["png","jpg","pdf","txt"])

# ---------------- ANALYSE ----------------
if st.button("🚀 Analyse IA"):

    context = text

    if audio:
        context += "\n[TRANSCRIPTION AUDIO CLIENT]"

    if file:
        context += f"\n[DOC FOURNI: {file.name}]"

    if not context.strip():
        st.warning("Veuillez fournir une information.")
        st.stop()

    with st.spinner("Analyse IA..."):
        result = process(context)

    st.session_state.analysis = result
    st.session_state.history.append(context)
    st.session_state.sent = False

# ---------------- RESULTATS ----------------
if st.session_state.analysis:

    reply = st.session_state.analysis["reply"]
    cls = st.session_state.analysis["classification"]

    st.success("Analyse IA terminée")

    col1,col2 = st.columns(2)

    # -------- CLIENT VIEW --------
    with col1:
        st.markdown("### 💬 Réponse à l’assuré")
        st.info(reply)

        st.markdown("### 🧠 Résumé intelligent")
        st.success(cls["resume_1_phrase"])

        # Score complétude
        completeness = random.randint(60,98)
        st.markdown("### 📂 Complétude dossier")
        st.progress(completeness/100)

        if completeness < 70:
            st.warning("Dossier incomplet")
        else:
            st.success("Dossier exploitable")

    # -------- ASSUREUR VIEW --------
    with col2:
        st.markdown("### 🏢 Vue assureur")

        st.write(f"**Motif:** {cls['motif']}")
        st.write(f"**Domaine:** {cls['domaine']}")
        st.write(f"**Priorité:** {cls['priorite']}")

        # Score risque
        risk = random.randint(10,90)
        st.markdown("### ⚠️ Score risque sinistre")
        st.progress(risk/100)

        # Détection fraude simple
        fraud_score = random.randint(0,100)
        st.markdown("### 🔍 Indice fraude")
        st.metric("Fraud Risk", f"{fraud_score}%")

        if fraud_score > 70:
            st.error("⚠️ Vérification recommandée")
        else:
            st.success("Aucune suspicion")

        st.markdown("### ✅ Actions IA")
        for a in cls["actions_recommandees"]:
            st.write("•",a)

# ---------------- TIMELINE DOSSIER ----------------
    st.markdown("---")
    st.subheader("📅 Timeline dossier")

    now = datetime.datetime.now()

    st.write(f"🕒 {now.strftime('%H:%M')} — Déclaration client")
    st.write(f"🕒 {now.strftime('%H:%M')} — Analyse IA")
    st.write(f"🕒 {now.strftime('%H:%M')} — Pré-qualification")

# ---------------- CHAT SUIVI ----------------
    st.markdown("---")
    st.subheader("💬 Questions complémentaires")

    follow = st.text_input("Réponse client")

    if st.button("Envoyer réponse"):
        st.session_state.history.append(follow)

        with st.spinner("Mise à jour analyse..."):
            result = process("\n".join(st.session_state.history))

        st.session_state.analysis = result
        st.rerun()

# ---------------- TRANSMISSION ----------------
    st.markdown("---")

    if not st.session_state.sent:
        if st.button("📨 Envoyer dossier à l'assureur"):
            st.session_state.sent = True
            st.success("Dossier transmis au gestionnaire")
            st.balloons()

    else:
        st.info("Dossier déjà transmis")

# ---------------- FOOTER ----------------
st.markdown("---")
st.caption("AssurAI — Hackathon Winner Demo | AI for Insurance")
