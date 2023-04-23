"""
Get FoCo is a platform for application and administration of income-
qualified programs offered by the City of Fort Collins.
Copyright (C) 2019

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
# All of the forms built from models are here 
import json
from django import forms
from django.contrib.auth.password_validation import validate_password

from dashboard.models import TaxInformation

from .models import HouseholdMembers, User, Addresses, Eligibility, programs, choices, addressLookup, futureEmails, attestations

# form for user account creation
class UserForm(forms.ModelForm):
    password2 = forms.CharField(label='Enter Password Again',
                               widget=forms.PasswordInput())
    class Meta:
        model = User
        fields = ['first_name','last_name', 'email','phone_number','password'] #password between email and phone number
        labels  = { 
            'first_name':'First Name', 
            'last_name':'Last Name', 
            'password':'Password', 
            'email':'Email',
            'phone_number':'Phone Number',
        }

    def passwordCheck(self):
        password = self.cleaned_data['password']
        try:
            validate_password(password, user = None, password_validators=None)
        except Exception as e:
            return str(e)
    
    def passwordCheckDuplicate(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            return 'Passwords don\'t match.'
        return cd['password']

    def save(self, commit=True):
        user = super(UserForm, self).save(commit=False)
        user.set_password(user.password) # set password properly before commit
        if commit:
            user.save()
        return user


# form for user account creation
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name','last_name', 'email','phone_number']
        labels  = { 
            'first_name':'First Name', 
            'last_name':'Last Name', 
            'email':'Email',
            'phone_number':'Phone Number',
        }
    
    # Save function that will update the user's
    # first name, last name, email, and phone number
    def save(self, commit=True):
        user = super(UserUpdateForm, self).save(commit=False)
        if commit:
            user.save()
        return user


# form for addresses
class AddressForm(forms.ModelForm):
    class Meta:
        model = Addresses
        fields = ['address', 'address2', 'city', 'state', 'zipCode']
        labels  = { 
            'user_id': 'user_id',
            'address':'Street Address',
            'address2':'Apt, Suite, etc.',
            'city':'City', 
            'state':'State', 
            'zipCode':'Zip Code',
        }
        #widgets = {
            #'zipCode':TextField(attrs={'type':'number'}),
            #'document': ClearableFileInput(attrs={'multiple': True}),
            #=forms.widgets.DateInput(attrs={'type': 'date'})
        #} 

# form for basic finance eligibility
class EligibilityForm(forms.ModelForm):
    rent = forms.ChoiceField(choices=choices,widget=forms.RadioSelect(),label="Rent")
    class Meta:
        model = Eligibility
        fields = ['rent','dependents', 'grossAnnualHouseholdIncome']
        labels  = {
            'rent':'Rent',
            'dependents':'Number of Dependents', 
            'grossAnnualHouseholdIncome':'Adjusted Gross Annual Household Income',
        } 

class EligibilityUpdateForm(forms.ModelForm):
    class Meta:
        model = Eligibility
        fields = ['dependents', 'grossAnnualHouseholdIncome']
        labels  = {
            'dependents':'Number of Dependents', 
            'grossAnnualHouseholdIncome':'Adjusted Gross Annual Household Income',
        } 

# form for basic finance eligibility

class DateInput(forms.DateInput):
    input_type ='date'


class HouseholdMembersForm(forms.ModelForm):
    name = forms.CharField(label='First & Last Name of Individual')
    birthdate = forms.DateField(label="Their Birthdate", widget=forms.widgets.DateInput(attrs={'type': 'date'}))
    class Meta:
        model = HouseholdMembers
        fields = ['name', 'birthdate']


class FilesInfoForm(forms.ModelForm):
    last4SSN = forms.DecimalField(label='Because you uploaded an Affordable Connectivity Program confirmation, please enter the last four digits of your SSN')
    class Meta:
        model = TaxInformation
        fields = ['last4SSN']


# programs they are available for
class programForm(forms.ModelForm):
    class Meta:
        model = programs
        fields = ['ebb_acf', 'Identification', 'leap', 'medicaid', 'freeReducedLunch', 'snap'] #ebb_acf = Emergency Broadband Benefit AKA Affordable Connectivity Program
        labels  = { 
            'snap':'Supplemental Nutrition Assistance Program (SNAP)',
            'medicaid':'Medicaid',
            'freeReducedLunch': 'Poudre School District Free and Reduced Lunch',
            'Identification':'Identification Card',
            'ebb_acf':'Affordable Connectivity Program (ACP)',
            'leap':'Low-income Energy Assistance Program (LEAP)',
        } 

class attestationForm(forms.ModelForm):
    class Meta:
        model = attestations
        fields = ['localAttestation', 'completeAttestation',]
        labels  = { 
            'localAttestation':'I am lawfully present in the United States and/or am ONLY applying on behalf on my children (under 18 years of age) who are lawfully present.',
            'completeAttestation':'I verify the information stated on this application is true.',
        } 

class addressLookupForm(forms.ModelForm):
    class Meta:
        model = addressLookup
        fields = ['address']
        labels  = { 
            'address':'Address', 
        } 

class futureEmailsForm(forms.ModelForm):
    class Meta:
        model = futureEmails
        fields = ['connexionCommunication']
        labels  = {
            'connexionCommunication':'Subscribe me to service updates! By checking this box, I agree to receive communications from Fort Collins Connexion. I understand I may opt out at any time.'
        } 