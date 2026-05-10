import unittest
from unittest.mock import mock_open, patch
import os

from app.core.reader import TextReader


class TestTextReader(unittest.TestCase):
    def setUp(self):
        """Metoda uruchamiana przed każdym testem."""
        self.reader = TextReader(default_encoding="utf-8")

    @patch("os.path.exists")
    @patch("os.path.isfile")
    @patch("os.path.getsize")
    def test_read_file_success(self, mock_getsize, mock_isfile, mock_exists):
        """Test poprawnego wczytania zawartości pliku."""
        # Konfiguracja mocków dla systemu plików
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_getsize.return_value = 100

        file_content = "Witaj świecie!\nTo jest test."
        
        with patch("builtins.open", mock_open(read_data=file_content)) as mock_file:
            result = self.reader.read_file("test.txt")
            
            self.assertEqual(result, file_content)
            mock_file.assert_called_once_with("test.txt", "r", encoding="utf-8")

    def test_read_file_empty_path(self):
        """Test zachowania dla pustej ścieżki pliku."""
        result = self.reader.read_file("   ")
        self.assertIsNone(result)

    @patch("os.path.exists")
    def test_read_file_not_exists(self, mock_exists):
        """Test zachowania, gdy plik nie istnieje."""
        mock_exists.return_value = False
        
        result = self.reader.read_file("non_existent.txt")
        self.assertIsNone(result)

    @patch("os.path.exists")
    @patch("os.path.isfile")
    def test_read_file_is_directory(self, mock_isfile, mock_exists):
        """Test zachowania, gdy podana ścieżka prowadzi do katalogu, a nie pliku."""
        mock_exists.return_value = True
        mock_isfile.return_value = False
        
        result = self.reader.read_file("some_directory")
        self.assertIsNone(result)

    @patch("os.path.exists")
    @patch("os.path.isfile")
    @patch("os.path.getsize")
    @patch("builtins.open")
    def test_read_file_permission_error(self, mock_open_func, mock_getsize, mock_isfile, mock_exists):
        """Test obsługi błędu braku uprawnień (PermissionError)."""
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_getsize.return_value = 100
        mock_open_func.side_effect = PermissionError("Brak uprawnień")

        result = self.reader.read_file("protected.txt")
        self.assertIsNone(result)

    @patch("os.path.exists")
    @patch("os.path.isfile")
    @patch("os.path.getsize")
    @patch("builtins.open")
    def test_read_file_unicode_decode_error(self, mock_open_func, mock_getsize, mock_isfile, mock_exists):
        """Test obsługi błędu kodowania znaków (UnicodeDecodeError)."""
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_getsize.return_value = 100
        mock_open_func.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid byte")

        result = self.reader.read_file("binary_file.bin")
        self.assertIsNone(result)

    @patch("os.path.exists")
    @patch("os.path.isfile")
    @patch("os.path.getsize")
    def test_read_lines_success(self, mock_getsize, mock_isfile, mock_exists):
        """Test wczytywania pliku linia po linii (read_lines)."""
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_getsize.return_value = 100

        file_content = "Linia 1\nLinia 2\nLinia 3"
        
        with patch("builtins.open", mock_open(read_data=file_content)):
            lines = self.reader.read_lines("test.txt")
            
            self.assertEqual(lines, ["Linia 1", "Linia 2", "Linia 3"])
            self.assertEqual(len(lines), 3)


if __name__ == "__main__":
    unittest.main()
