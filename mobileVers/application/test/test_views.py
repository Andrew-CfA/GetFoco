from unittest.main import TestProgram
from django.test import TestCase, Client
from django.urls import reverse
from application.models import *
import json


class TestViews(TestCase):

    def setUp(self):
        self.client = Client()
        self.index_url = reverse("application:index")
        self.address_url = reverse("application:address")

    def test_index_GET(self):
        print("Test - index.view GET()")
        response = self.client.get(self.index_url)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'application/index.html')

    def test_address_GET(self):
        print("Test - address.view GET()")
        response = self.client.get(self.address_url)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'application/address.html')
