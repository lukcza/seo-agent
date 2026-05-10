import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import os
import json

# pyrefly: ignore [missing-import]
import google.generativeai as genai
from app.services.prompter import get_seo_data, verify_seo_data
from app.models.seo import SEOData


class TestPrompter(unittest.IsolatedAsyncioTestCase):

    async def test_get_seo_data_empty_content(self):
        """Test whether ValueError is raised for empty content."""
        with self.assertRaises(ValueError) as context:
            await get_seo_data("")
        self.assertEqual(str(context.exception), "Content cannot be empty")

        with self.assertRaises(ValueError) as context:
            await get_seo_data("   ")
        self.assertEqual(str(context.exception), "Content cannot be empty")

        with self.assertRaises(ValueError) as context:
            await get_seo_data(None)
        self.assertEqual(str(context.exception), "Content cannot be empty")

    @patch("app.services.prompter.genai")
    async def test_get_seo_data_success(self, mock_genai):
        """Test successful API call and returned text."""
        mock_client = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_client

        mock_response = MagicMock()
        mock_response.text = '{"title": "SEO Title", "description": "SEO Desc", "keywords": "test", "content": "SEO Content"}'
        
        mock_client.generate_content_async = AsyncMock(return_value=mock_response)

        test_content = "Przykładowy tekst do analizy SEO."
        result = await get_seo_data(test_content)
        mock_genai.GenerativeModel.assert_called_once()
        args, kwargs = mock_genai.GenerativeModel.call_args
        self.assertEqual(args[0], 'gemini-2.5-flash')
        mock_genai.GenerationConfig.assert_called_once_with(
            response_mime_type="application/json",
            temperature=0.5
        )
        self.assertIsInstance(result, SEOData)
        self.assertEqual(result.title, "SEO Title")
        self.assertEqual(result.description, "SEO Desc")
        self.assertEqual(result.keywords, "test")
        self.assertEqual(result.content, "SEO Content")

    @patch("app.services.prompter.genai")
    async def test_get_seo_data_api_error(self, mock_genai):
        """Test error handling when Gemini API raises an exception."""
        mock_client = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_client
        mock_client.generate_content_async = AsyncMock(side_effect=Exception("API Connection Error"))

        result = await get_seo_data("Przykładowy tekst")
        self.assertIsNone(result)

    def test_verify_seo_data_valid(self):
        """Test verify_seo_data with valid JSON and expected lengths."""
        valid_json = json.dumps({
            "title": "A Great Title Under Sixty Characters",
            "description": "A wonderful, descriptive meta description that is well under the limit of one hundred and sixty characters to ensure good SEO performance.",
            "keywords": "seo, testing, python",
            "content": "This is the actual page content."
        })
        seo_obj = SEOData.from_json(valid_json)
        self.assertTrue(verify_seo_data(seo_obj))

    def test_verify_seo_data_missing_keys(self):
        """Test verify_seo_data with missing fields."""
        invalid_json = json.dumps({
            "title": "A Great Title",
            "keywords": "seo, testing, python",
            "content": "Missing description"
        })
        seo_obj = SEOData.from_json(invalid_json)
        self.assertFalse(verify_seo_data(seo_obj))

    def test_verify_seo_data_too_long_fields(self):
        """Test verify_seo_data with field lengths exceeding limits."""
        # Walidacja limitu długości tytułu (> 60 znaków)
        too_long_title = json.dumps({
            "title": "A" * 61,
            "description": "Short description",
            "keywords": "seo",
            "content": "Content"
        })
        seo_obj = SEOData.from_json(too_long_title)
        self.assertFalse(verify_seo_data(seo_obj))

        # Walidacja limitu długości opisu (> 160 znaków)
        too_long_desc = json.dumps({
            "title": "Short title",
            "description": "B" * 161,
            "keywords": "seo",
            "content": "Content"
        })
        seo_obj = SEOData.from_json(too_long_desc)
        self.assertFalse(verify_seo_data(seo_obj))

        # Walidacja limitu długości słów kluczowych (> 50 znaków)
        too_long_keywords = json.dumps({
            "title": "Short title",
            "description": "Short description",
            "keywords": "C" * 51,
            "content": "Content"
        })
        seo_obj = SEOData.from_json(too_long_keywords)
        self.assertFalse(verify_seo_data(seo_obj))


if __name__ == "__main__":
    unittest.main()
