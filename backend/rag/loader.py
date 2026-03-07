import os
import pandas as pd
from langchain_community.document_loaders.text import TextLoader
from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_community.document_loaders.unstructured import UnstructuredFileLoader

def load_document(file_path: str) -> str:
    """
    Loads a document from the given file path and returns its text content.
    Supports .pdf, .txt, .md, .xlsx, and .xls files.
    """
    _, extension = os.path.splitext(file_path)
    extension = extension.lower()

    try:
        if extension == ".pdf":
            loader = PyPDFLoader(file_path)
        elif extension in [".txt", ".md"]:
            loader = TextLoader(file_path, encoding="utf-8")
        elif extension in [".xlsx", ".xls"]:
            # Load all sheets from the Excel file. `sheet_name=None` gets all sheets.
            all_sheets_df = pd.read_excel(file_path, sheet_name=None)
            full_text_content = []
            for sheet_name, df in all_sheets_df.items():
                # Convert each row to a structured string with headers to preserve context in chunks
                df = df.fillna("")
                row_strings = []
                for _, row in df.iterrows():
                    # Create a string like: "Sheet_Category: Books | Author: Name | Title: ..."
                    row_items = [f"Sheet_Category: {sheet_name}"] + [f"{str(col).strip()}: {str(val).strip()}" for col, val in row.items() if str(val).strip() != ""]
                    row_strings.append(" | ".join(row_items))
                full_text_content.append("\n".join(row_strings))
            return "\n\n---\n\n".join(full_text_content)
        else:
            # A generic fallback for other file types
            loader = UnstructuredFileLoader(file_path)

        documents = loader.load()
        
        return "\n\n".join([doc.page_content for doc in documents if doc.page_content])

    except Exception as e:
        print(f"Error loading document {file_path}: {e}")
        return "" # Return empty string on failure