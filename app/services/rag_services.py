import os
from google import genai
from dotenv import load_dotenv
from app.core.database import SEODatabaseManager
from app.core.reader import PDFConverter
# pyrefly: ignore [missing-import]
from langchain_text_splitters import MarkdownTextSplitter, RecursiveCharacterTextSplitter

load_dotenv()

class RAGServices:
    def __init__(self):
        self.db_manager = SEODatabaseManager()
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

    def chunk_document(self, document:str, chunk_size:int=1000, chunk_overlap:int=200) -> list[str]:
        text_splitter = MarkdownTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        return text_splitter.split_text(document)            

    def vectorize_chunks(self, chunks:list[str]) -> list[list[float]]:
        response = self.client.models.embed_content(
            model='gemini-embedding-2',
            contents=chunks
        )
        return [item.values for item in response.embeddings]

if __name__ == "__main__":
    rag_services = RAGServices()
    pdf_converter = PDFConverter()
    document = "./processed_guideliness.md"
    try:
        with open(document, "r", encoding="utf-8") as file:
            document = file.read()
    except FileNotFoundError:
        print(f"Błąd: Nie znaleziono pliku: {document}")
        exit(1)
    except Exception as e:
        print(f"Błąd: Wystąpił nieoczekiwany błąd podczas odczytu pliku: {e}")
        exit(1)
    chunks = rag_services.chunk_document(document)
    embeddings = rag_services.vectorize_chunks(chunks)
    for embedding in embeddings:
            print(embedding)
            print("-" * 100)