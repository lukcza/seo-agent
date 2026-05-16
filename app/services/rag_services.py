import json
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
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    def chunk_document(self, document:str, chunk_size:int=1000, chunk_overlap:int=200) -> list[str]:
        text_splitter = MarkdownTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        return text_splitter.split_text(document)            

    def vectorize_chunks(self, chunks:list[str]) -> list[list[float]]:
        response = self.client.models.embed_content(
            model='gemini-embedding-2',
            contents=chunks
        )
        return [item.values for item in response.embeddings]
    def query_knowledge(self, query: str, top_k: int = 3) -> list[str]:
        """Szuka w bazie wiedzy fragmentów pasujących do zapytania."""
        query_embedding = self.client.models.embed_content(
            model='text-embedding-004',
            contents=[query]
        ).embeddings[0].values
        knowledge = self.db_manager.get_rag_knowledge()
        scored_chunks = []
        for item in knowledge:
            chunk_emb = json.loads(item["embedding"])
            score = sum(a*b for a,b in zip(query_embedding, chunk_emb))
            scored_chunks.append((score, item["chunk_text"]))
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        relevant_text =  "\n\n".join([chunk[0] for chunk in scored_chunks[:top_k]])
        return relevant_text
    def setup_knowledge_base(self, document:str) -> None:
        """Tworzy bazę wiedzy z dokumentu."""
        self.db_manager.clear_rag_knowledge()
        chunks = self.chunk_document(document)
        embeddings = self.vectorize_chunks(chunks)
        for chunk, embedding in zip(chunks, embeddings):
            self.db_manager.save_rag_chunk(document, chunk, embedding)
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
    rag_services.setup_knowledge_base(document)