from django.test import Client, TestCase


class StaticURLTests(TestCase):

    def setUp(self):
        self.guest_client = Client()

    def test_about_author_page(self):
        response = self.guest_client.get('/about/author/')
        self.assertEqual(response.status_code, 200)

    def test_about_tech_page(self):
        response = self.guest_client.get('/about/tech/')
        self.assertEqual(response.status_code, 200)
