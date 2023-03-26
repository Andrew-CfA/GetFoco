from django.test import SimpleTestCase
from django.urls import reverse, resolve
from application.views import *

class TestUrls(SimpleTestCase):

    def test_index_resolved(self):
        url = reverse("application:index")
        print("Test - Index url")
        self.assertEquals(resolve(url).func, index)

    def test_address_resolved(self):
        url = reverse("application:address")
        print("Test - addresses url")
        self.assertEquals(resolve(url).func, address)

    def test_account_resolved(self):
        url = reverse("application:account")
        print("Test - account url")
        self.assertEquals(resolve(url).func, account)

    def test_finances_resolved(self):
        url = reverse("application:finances")
        print("Test - finances url")
        self.assertEquals(resolve(url).func, finances)

    def test_programs_resolved(self):
        url = reverse("application:programs")
        print("Test - programs url")
        self.assertEquals(resolve(url).func, programs)
    

    def test_notAvailable_resolved(self):
        url = reverse("application:notAvailable")
        print("Test - notAvailable url")
        self.assertEquals(resolve(url).func, notAvailable)


    def test_addressCorrection_resolved(self):
        url = reverse("application:addressCorrection")
        print("Test - addressCorrection url")
        self.assertEquals(resolve(url).func, addressCorrection)

    def test_takeUSPSaddress_resolved(self):
        url = reverse("application:takeUSPSaddress")
        print("Test - takeUSPSaddress url")
        self.assertEquals(resolve(url).func, takeUSPSaddress)

    def test_privacyPolicy_resolved(self):
        url = reverse("application:privacyPolicy")
        print("Test - privacyPolicy url")
        self.assertEquals(resolve(url).func, privacyPolicy)

    def test_dependentInfo_resolved(self):
        url = reverse("application:dependentInfo")
        print("Test - dependentInfo url")
        self.assertEquals(resolve(url).func, dependentInfo)