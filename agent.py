import json
import asyncio
from project_types import TypeDocument
from retrieve_document import extract_document
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel
from typing import List, Optional, Annotated
from dataclasses import dataclass

import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("ANTHROPIC_API_KEY")
model = os.getenv("CLAUDE_MODEL", "anthropic:claude-3-haiku-20240307")


class DecisionRemboursement(BaseModel):
    acte: Optional[str]
    date: Optional[str]
    montant: Optional[float]
    instructions: Optional[str] = None


class AgentContext(BaseModel):
    user_id: str
    decision_remboursement: DecisionRemboursement | None = None
    doc_type: TypeDocument | None = None
    

def recuperer_document_contexte(
    ctx: RunContext[AgentContext]
) -> dict:
    """
    Récupère le contrat d’assurance de l’utilisateur correspondant au type fourni, sous forme de chaîne de caractère.
    """
    doc_type = ctx.deps.doc_type
    return extract_document(doc_type)

def extraire_type_document(
    ctx: RunContext[AgentContext],
    texte: str
) -> TypeDocument:
    """
    Extrait une le type de document en lien avec le texte utilisateur.

    Il s'agit de tous type de documents permettant de répondre à la question posé.
    Pour les demandes de remboursement, il s'agit du tableau de garantie.
    Toute demande d'information sont liées aux documents du client.

    Les types possibles sont : 
    TABLEAU_DES_GARANTIES
    CONTRAT
    CONDITIONS_GENERALES
    CONDITIONS_PARTICULIERES
    REGLES_DE_REMBOURSEMENT
    GUIDE_CLIENT
    NOTICE_INFORMATION

    RÈGLES STRICTES :
    - Tu dois retourner un objet conforme au schéma TypeDocument
    - Tu dois toujours retourner une valeur autre que None
    """

def enregistrer_type_document(
    ctx: RunContext[AgentContext],
    doc_type: TypeDocument
) -> dict:
    """
    Enregistre le type du document dans le contexte.
    """
    ctx.deps.doc_type = doc_type
    return {"status": "type de document enregistree"}

# def calcule_montant_estimee(
#     ctx: RunContext[AgentContext],
#     montant: TypeDocument,

# ) -> dict:
# """
#     Calcule le montant estimee à partir du montant.
# """

def create_ticket(
    ctx: RunContext[AgentContext]
) -> dict:
    """
    Crée le ticket de remboursement en fonction des informations saisies
    """
    
    user_id = ctx.deps.user_id
    decision_remboursement = ctx.deps.decision_remboursement
    doc_type = ctx.deps.doc_type

    if decision_remboursement is None:
        raise RuntimeError("Décision absente")

    if not decision_remboursement.acte or not decision_remboursement.montant:
        raise RuntimeError("Décision incomplète")


    # if decision_remboursement.eligible:
    output = {
        "ticket_id": "ticket_001",
        "acte": decision_remboursement.acte,
        "date": decision_remboursement.date,
        "montant": decision_remboursement.montant,
        "instructions": decision_remboursement.instructions,
        "document_utiliser": doc_type
    }    

    # Save
    with open('data/ticket.json', 'w') as f:
        json.dump(output, f, indent=4)
    # else:
    #     output = {
    #         "msg": "Certaines informations sont manquantes"
    #         }
    
    return output

def enregistrer_decision_remboursement(
    ctx: RunContext[AgentContext],
    decision: DecisionRemboursement
) -> dict:
    """
    Enregistre la décision de remboursement dans le contexte.
    """
    ctx.deps.decision_remboursement = decision
    return {"status": "decision_enregistree"}


def extraire_demande_remboursement(
    ctx: RunContext[AgentContext],
    texte: str
) -> DecisionRemboursement:
    """
    Extrait une demande de remboursement depuis le texte utilisateur.

    L'acte est en lien avec le type de consultation.
    Les instructions sont les instructions à faire pour compléter le ticket.

    RÈGLES STRICTES :
    - Tu dois retourner un objet conforme au schéma DecisionRemboursement
    - Si une information est absente, mets null
    - N'invente JAMAIS une valeur
    """

def init_agent()->Agent:
    return Agent(
        model=model,
        deps_type=AgentContext,
        tools=[
            extraire_demande_remboursement,
            enregistrer_decision_remboursement,
            extraire_type_document,
            enregistrer_type_document,
            recuperer_document_contexte,
            create_ticket,
        ],
        system_prompt="""
        Tu es un expert en remboursement d’assurance santé en France.
        Tu dois exraire les informations donné par l'utilisateur et modifier ton contexte à partir de ces entrées.
        Tu dois déterminer le type de document et extraire le document en lien avec la demande si c'est nécessaire.
        Les demandes de remboursements utilisent les tableaux de garanties pour calculer le montant estimé.
        Tu dois créer le ticket.
        """
    )




def run_agent_sync(agent, text, deps):
    return asyncio.run(agent.run(text, deps=deps))
