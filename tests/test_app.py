import io
import unittest
import zipfile
from pathlib import Path

import app


class TextExtractionTests(unittest.TestCase):
    def test_clean_text_preserves_newlines_and_tabs(self):
        self.assertEqual(app.clean_text("A\x00B\nC\tD\x7f"), "AB\nC\tD")

    def test_plain_text_decoding(self):
        text, kind = app.text_of("Merhaba\nDünya".encode(), "notlar.txt")
        self.assertEqual(text, "Merhaba\nDünya")
        self.assertEqual(kind, "Metin/kod")

    def test_html_extraction_removes_script_and_tags(self):
        html = b"<html><script>secret()</script><p>Merhaba</p><p>Dunya</p></html>"
        text, kind = app.text_of(html, "page.html", "text/html")
        self.assertNotIn("secret", text)
        self.assertIn("Merhaba", text)
        self.assertIn("Dunya", text)
        self.assertEqual(kind, "Web/HTML")

    def test_zip_source_extraction(self):
        buff = io.BytesIO()
        with zipfile.ZipFile(buff, "w") as z:
            z.writestr("notes.txt", "İlk satır\nİkinci satır")
            z.writestr("__pycache__/ignored.py", "ignored")
        entries, errors = [], []
        app.add_zip(buff.getvalue(), "bundle.zip", entries, errors)
        self.assertEqual(errors, [])
        self.assertEqual(len(entries), 1)
        self.assertIn("İlk satır\nİkinci satır", entries[0]["text"])

    def test_pdf_generation_and_zip_report(self):
        result = app.create({
            "title": "Otomatik Test",
            "files": [("ornek.txt", "Başlık\nBu bir çevrimdışı test metnidir.".encode("utf-8"))],
            "offline": "1",
            "summaries": "1",
            "chapters": "1",
            "questions": "3",
            "includeoriginal": "1",
        })
        self.assertTrue(result["ok"])
        self.assertEqual(result["count"], 1)
        pdf_path = (app.OUT / Path(result["pdf"]).name)
        zip_path = (app.OUT / Path(result["zip"]).name)
        self.assertGreater(pdf_path.stat().st_size, 500)
        from pypdf import PdfReader
        extracted = "\n".join(page.extract_text() or "" for page in PdfReader(str(pdf_path)).pages)
        self.assertIn("Bu bir çevrimdışı test metnidir.", extracted)
        with zipfile.ZipFile(zip_path) as z:
            self.assertIn(pdf_path.name, z.namelist())
            self.assertIn("ISLEM_RAPORU.txt", z.namelist())
            self.assertIn("KAYNAK_ENVANTERI.csv", z.namelist())
            self.assertIn("orijinal_kaynaklar/ornek.txt", z.namelist())
            report = z.read("ISLEM_RAPORU.txt").decode("utf-8")
            self.assertIn("ornek.txt", report)

    def test_offline_mode_skips_urls_without_network(self):
        result = app.create({
            "title": "Çevrimdışı URL testi",
            "files": [("ornek.txt", b"yerel metin")],
            "urls": "https://example.invalid/file.pdf",
            "offline": "1",
            "questions": "3",
        })
        self.assertTrue(any("Çevrimdışı mod" in warning for warning in result["warnings"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
