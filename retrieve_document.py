import pdfplumber
from pathlib import Path
from project_types import TypeDocument

ROOT_FOLDER = Path(__file__).resolve().parent

DOCUMENT_PATHS = {
    TypeDocument.TABLEAU_DES_GARANTIES: ROOT_FOLDER / "data" / "espace_client" / "tableau_garantie.pdf",
    TypeDocument.CONTRAT: ROOT_FOLDER / "data" / "espace_client" / "contrat.pdf",
    TypeDocument.CONDITIONS_GENERALES: ROOT_FOLDER / "data" / "espace_client" / "conditions_generales.pdf",
    TypeDocument.CONDITIONS_PARTICULIERES: ROOT_FOLDER / "data" / "espace_client" / "conditions_particulieres.pdf",
    TypeDocument.REGLES_DE_REMBOURSEMENT: ROOT_FOLDER / "data" / "espace_client" / "regles_remboursement.pdf",
    TypeDocument.GUIDE_CLIENT: ROOT_FOLDER / "data" / "espace_client" / "guide_client.pdf",
    TypeDocument.NOTICE_INFORMATION: ROOT_FOLDER / "data" / "espace_client" / "notice_information.pdf",
}


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extracts text from a PDF file using pdfplumber.
    Returns full text as a single string.
    """
    text_content = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_content.append(page_text)

    return "\n".join(text_content)



def extract_document(doc_type: TypeDocument) -> str:
    """
    Extracts text from a health insurance document
    based on its document type.
    """
    if doc_type not in DOCUMENT_PATHS:
        raise ValueError(f"Unsupported document type: {doc_type}")

    pdf_path = DOCUMENT_PATHS[doc_type]

    if not pdf_path.exists():
        raise FileNotFoundError(f"Document not found at: {pdf_path}")

    return extract_text_from_pdf(pdf_path)

