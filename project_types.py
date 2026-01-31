from enum import Enum

class TypeDocument(str, Enum):
    """
    Types de documents d'assurance santé pris en charge
    """

    TABLEAU_DES_GARANTIES = "tableau_des_garanties"
    CONTRAT = "contrat"
    CONDITIONS_GENERALES = "conditions_generales"
    CONDITIONS_PARTICULIERES = "conditions_particulieres"
    REGLES_DE_REMBOURSEMENT = "regles_de_remboursement"
    GUIDE_CLIENT = "guide_client"
    NOTICE_INFORMATION = "notice_information"


class TypeTache(str, Enum):
    """
    Types de tâches macro
    """

    DOCUMENT_CONTRACTUEL = "document_contractuel"
    PROCESSUS_INTERNE = "processus_interne"
    DEMANDES = "demandes"