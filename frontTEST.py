import streamlit as st
from classification import process
from config import ensure_api_key
import random
import datetime
from agent import AgentContext, init_agent, run_agent_sync
from retrieve_document import extract_text_from_pdf, extract_document
from project_types import TypeDocument, TypeTache
import traceback

# ---------------- CONFIG ----------------
st.set_page_config(page_title="AssurAI Winner Demo", layout="wide")

if "history" not in st.session_state:
    st.session_state.history = []

if "analysis" not in st.session_state:
    st.session_state.analysis = None

if "sent" not in st.session_state:
    st.session_state.sent = False

if "documents" not in st.session_state:
    st.session_state.documents = []

if "agent" not in st.session_state:
    st.session_state.agent = init_agent()

if "agent_deps" not in st.session_state:
    st.session_state.agent_deps = AgentContext(user_id="USER_001")


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

    # Agent qui classifie vers quel macro tâche on est (Contrats, Process, Demande)
    task_type = "document_contractuel"

    doc_type = "tableau_des_garanties"
    
    # Agent qui classifie le process à décrire

    # Agent qui check quelles demandes utilisés 

    if task_type==TypeTache.DOCUMENT_CONTRACTUEL:
        st.session_state.documents.append(extract_document(doc_type))
    elif task_type==TypeTache.PROCESSUS_INTERNE:
        raise ValueError(f"Not implemented yet for {task_type}")
    elif task_type==TypeTache.DEMANDES:
        raise ValueError(f"Not implemented yet for {task_type}")

    # context = "\n".join(st.session_state.documents) + "\nInput utilisateur:\n" + text

    context = "\Contexte utilisateur:\n" + text
    if audio:
        context += "\n[TRANSCRIPTION AUDIO CLIENT]"

    if file:
        context += f"\n[DOC FOURNI: {file.name}]"

    if not context.strip():
        st.warning("Veuillez fournir une information.")
        st.stop()

    file_bytes = None
    file_name = None
    if file:
        file_bytes = file.read()
        file_name = file.name

    # Call LLM + context
    with st.spinner("Analyse IA..."): 
        st.write(f"[DEBUG] sending_to_process | text_len={len(context)} | file={file.name if file else None} | bytes={len(file_bytes) if file_bytes else 0}")
        
        try:
            agent_result = run_agent_sync(st.session_state.agent, context, st.session_state.agent_deps).output
        except Exception as e:
            print(str(e))
            print(traceback.format_exc())
            
            agent_result = None
        
        if agent_result is not None:
            context += "\n Actions de l'agent :" + agent_result
            print("agent result added to context in first interaction")
            print(agent_result)
        result = process(context, file_bytes=file_bytes, file_name=file_name)
        st.write(f"[DEBUG] process_return | blocked={result.get('blocked')} | pii_found={result.get('pii_found')}")

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
            history_context = "\n".join(st.session_state.history)
            try:
                agent_result = run_agent_sync(st.session_state.agent, history_context, st.session_state.agent_deps).output
            except Exception as e:
                print(str(e))
                print(traceback.format_exc())
            
                agent_result = None
            
            if agent_result is not None:
                history_context += "\n Actions de l'agent :" + agent_result
                print("agent result added to context in complementary info")
                print(agent_result)
            result = process(history_context)

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
