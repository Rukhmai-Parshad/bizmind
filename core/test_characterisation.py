"""Characterisation tests: public pages (updated in Milestone 3)."""
from django.test import TestCase


class PublicPagesTests(TestCase):
    def test_home_loads_without_login(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_about_contact_and_stats_pages_are_gone(self):
        # Milestone 3: About is merged into Home; Contact and the public /stats/
        # page (audit S6) were removed. They now show the 404 page.
        for url in ("/about/", "/contact/", "/stats/"):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 404)
                self.assertContains(response, "Page not found", status_code=404)
