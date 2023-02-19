from django.test import SimpleTestCase
from django.urls import reverse, resolve
from dashboard.views import *

class TestUrls(SimpleTestCase):

    def test_index_resolved(self):

        # NOTES: Only let authenticated users enter!!!!
        # NOTES: have two cases, one authenticated user, one non authenticated

        url = reverse("dashboard:index")
        print("Test - Index url")
        self.assertEquals(resolve(url).func, feedback)

    def test_files_resolved(self):
        url = reverse("dashboard:files")
        print("Test - files url")
        self.assertEquals(resolve(url).func, files)

    def test_filesContinued_resolved(self):
        url = reverse("dashboard:filesContinued")
        print("Test - filesContinued url")
        self.assertEquals(resolve(url).func, filesContinued)

    def test_addressVerification_resolved(self):
        url = reverse("dashboard:addressVerification")
        print("Test - addressVerification url")
        self.assertEquals(resolve(url).func, addressVerification)

    def test_login_resolved(self):
        url = reverse("dashboard:login")
        print("Test - login url")
        self.assertEquals(resolve(url).func, login_user)
    
    def test_broadcast_resolved(self):
        url = reverse("dashboard:broadcast")
        print("Test - broadcast url")
        self.assertEquals(resolve(url).func, broadcast)

    def test_feedbackReceived_resolved(self):
        url = reverse("dashboard:feedbackReceived")
        print("Test - feedbackReceived url")
        self.assertEquals(resolve(url).func, feedbackReceived)

    def test_manualVerifyIncome_resolved(self):
        url = reverse("dashboard:manualVerifyIncome")
        print("Test - manualVerifyIncome url")
        self.assertEquals(resolve(url).func, manualVerifyIncome)

    def test_notifyRemaining_resolved(self):
        url = reverse("dashboard:notifyRemaining")
        print("Test - notifyRemaining url")
        self.assertEquals(resolve(url).func, notifyRemaining)

    def test_underConstruction_resolved(self):
        url = reverse("dashboard:underConstruction")
        print("Test - underConstruction url")
        self.assertEquals(resolve(url).func, underConstruction)

    def test_dashboard_resolved(self):
        url = reverse("dashboard:dashboard")
        print("Test - dashboard url")
        self.assertEquals(resolve(url).func, dashboardGetFoco)

    def test_qualifiedPrograms_resolved(self):
        url = reverse("dashboard:qualifiedPrograms")
        print("Test - qualifiedPrograms url")
        self.assertEquals(resolve(url).func, qualifiedPrograms)

    def test_ProgramsList_resolved(self):
        url = reverse("dashboard:ProgramsList")
        print("Test - ProgramsList url")
        self.assertEquals(resolve(url).func, ProgramsList)
        