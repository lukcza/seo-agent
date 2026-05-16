import os
from typing import Optional
# pyrefly: ignore [missing-import]
from unstructured.partition.pdf import partition_pdf
# pyrefly: ignore [missing-import]
import pytesseract
import unstructured_pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
unstructured_pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class TextReader:
    """
    Klasa odpowiedzialna za bezpieczne wczytywanie i zarządzanie plikami tekstowymi.
    """
    MAX_FILE_SIZE = 1024*1024*1024
    def __init__(self, default_encoding: str = "utf-8"):
        self.default_encoding = default_encoding

    def read_file(self, file_path: str, encoding: Optional[str] = None) -> Optional[str]:
        """
        Wczytuje całą zawartość pliku tekstowego i zwraca ją jako ciąg znaków (str).
        W przypadku błędu wyświetla odpowiedni komunikat i zwraca None.
        
        :param file_path: Ścieżka do pliku, który ma zostać wczytany.
        :param encoding: Opcjonalne kodowanie znaków (jeśli None, użyte zostanie domyślne).
        :return: Zawartość pliku jako str lub None w przypadku błędu.
        """
        enc = encoding or self.default_encoding
        
        # Sprawdzenie czy ścieżka nie jest pusta
        if not file_path or not file_path.strip():
            print("Błąd: Podana ścieżka pliku jest pusta.")
            return None

        # Sprawdzenie czy plik istnieje
        if not os.path.exists(file_path):
            print(f"Błąd: Plik o ścieżce '{file_path}' nie istnieje.")
            return None

        # Sprawdzenie czy to na pewno plik, a nie katalog
        if not os.path.isfile(file_path):
            print(f"Błąd: Wskazana ścieżka '{file_path}' nie jest plikiem.")
            return None
        if os.path.getsize(file_path) > self.MAX_FILE_SIZE:
            print(f"Błąd: Plik '{file_path}' jest za duży.")
            return None
        try:
            # Bezpieczne otwarcie pliku przy użyciu menedżera kontekstu (with)
            with open(file_path, "r", encoding=enc) as file:
                content = file.read()
                return content
        except FileNotFoundError:
            print(f"Błąd: Nie znaleziono pliku: {file_path}")
        except PermissionError:
            print(f"Błąd: Brak uprawnień do odczytu pliku: {file_path}")
        except UnicodeDecodeError:
            print(f"Błąd: Niepoprawne kodowanie znaku podczas próby odczytu pliku '{file_path}' za pomocą kodowania '{enc}'.")
        except Exception as e:
            print(f"Wystąpił nieoczekiwany błąd podczas odczytu pliku: {e}")
            
        return None

    def read_lines(self, file_path: str, encoding: Optional[str] = None) -> Optional[list[str]]:
        """
        Wczytuje plik linia po linii i zwraca je jako listę ciągów znaków.
        
        :param file_path: Ścieżka do pliku.
        :param encoding: Opcjonalne kodowanie znaków.
        :return: Lista linii (jako str) lub None w przypadku błędu.
        """
        content = self.read_file(file_path, encoding)
        if content is not None:
            # Dzielenie zawartości na pojedyncze linie, usuwając puste linie na końcu
            return content.splitlines()
        return None

class PDFConverter:
    """Klasa do konwersji plików PDF do czystego Markdown"""
    def convert_pdf_to_markdown(self, file_path: str, noise: Optional[list[str]] = None):
        elements = partition_pdf(
            filename=file_path,
            strategy="hi_res",
            languages=["eng"]
        )
        if noise is None:
            noise = [
                "Search Quality Rater Guidelines:",
                "An overview",
                "36/36",
                "Page",
                "improving search",
                "how search work"
            ]
        markdown = []
        for el in elements:
            el_type = type(el).__name__
            text = el.text.strip()
            if noise and any(phrase in text for phrase in noise) and len(text) < 60 or   text.endswith("/36"):
                continue     
            if(el_type == "Title"):
                markdown.append("# " + text)
            elif(el_type == "Header"):
                markdown.append("## " + text)
            elif(el_type == "ListItem"):
                markdown.append("* " + text)
            elif(el_type == "Table"):
                if "text_as_html" in el.metadata.to_dict():
                    markdown.append("\n" + el.metadata.text_as_html + "\n")
                else:
                    markdown.append("\n" + text + "\n") 
            elif(el_type == "NarrativeText"):
                markdown.append(text)
            else:
                if text: markdown.append(text)
        return "\n".join(markdown)
    def save_to_markdown(self, content: str, filename: str):
        try:
            with open(filename, "w", encoding="utf-8") as file:
                file.write(content)
                print(f"zapisano plik: {filename}.md")
        except Exception as e:
            print(f"Błąd podczas zapisywania pliku: {e}")
if __name__ == "__main__":
    converter = PDFConverter()
    print("konwertowanie pdf do markdown")
    markdown = converter.convert_pdf_to_markdown("hsw-sqrg.pdf")
    converter.save_to_markdown(markdown, "processed_guideliness.md")
    print("konwertowanie pdf do markdown zakończone")
    