import os
from typing import Optional


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
