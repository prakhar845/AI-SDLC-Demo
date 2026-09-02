import os
import sys
import unittest

class TestLandingPage(unittest.TestCase):
    def setUp(self):
        # Locate and load the HTML file
        self.file_path = "index.html"
        self.assertTrue(os.path.exists(self.file_path), "CRITICAL: index.html does not exist in the root directory!")
        
        with open(self.file_path, "r", encoding="utf-8") as f:
            self.html_content = f.read().lower()

    def test_structural_integrity(self):
        """Ensures the core HTML skeletal tags are present."""
        self.assertIn("<!doctype html>", self.html_content, "Missing standard HTML5 doctype declaration.")
        self.assertIn("<html", self.html_content, "Missing opening <html> tag.")
        self.assertIn("</html>", self.html_content, "Missing closing </html> tag.")

    def test_seo_and_accessibility(self):
        """Checks for required SEO and accessibility elements."""
        self.assertIn("<title>", self.html_content, "Missing <title> tag for SEO/Accessibility.")
        
    def test_no_empty_hyperlinks(self):
        """Prevents dead links from being merged to production."""
        self.assertNotIn('href=""', self.html_content, "QA Failure: Found an empty href attribute (href=\"\").")
        self.assertNotIn("href=''", self.html_content, "QA Failure: Found an empty href attribute (href='').")

if __name__ == '__main__':
    print("Starting Automated QA Execution Gate...")
    
    # Run tests and evaluate the result
    loader = unittest.defaultTestLoader
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(loader.loadTestsFromTestCase(TestLandingPage))
    
    # If any test fails, exit with a status code of 1 to block the GitHub PR
    if not result.wasSuccessful():
        print("\n❌ QA Gate Failed. Please fix the above errors.")
        sys.exit(1)
    else:
        print("\n✅ QA Gate Passed. All assertions successful.")
        sys.exit(0)
