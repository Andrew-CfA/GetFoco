# All of the forms built from models are here 
from django import forms
from django.db.models.fields import CharField, DateField, TextField
from django.forms import widgets
from django.contrib.auth.password_validation import validate_password

from .models import User, Addresses, Eligibility, programs, choices, addressLookup, futureEmails, attestations, MoreInfo

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

# form for basic finance eligibility

class DateInput(forms.DateInput):
    input_type ='date'
class MoreInfoForm(forms.ModelForm):
    dependentsName = forms.CharField(label='First & Last Name of Individual')
    dependentsBirthdate = forms.DateField(label="Their Birthdate", widget=forms.widgets.DateInput(attrs={'type': 'date'}))
    class Meta:
        model = MoreInfo
        fields = ['dependentsName','dependentsBirthdate','dependentInformation']
        widgets = {'dependentInformation': forms.HiddenInput(),}

 

# programs they are available for
class programForm(forms.ModelForm):
    class Meta:
        model = programs
        fields = ['snap', 'freeReducedLunch', 'Identification', 'form1040', 'EBB_ACF'] #EBB_ACF = Emergency Broadband Benefit AKA Affordable Connectivity Program
        labels  = { 
            'snap':'Supplemental Nutrition Assistance Program (SNAP)',
            'freeReducedLunch': 'Poudre School District Free and Reduced Lunch',
            'Identification':'Identification Card',
            'form1040':'1040 Form',
            ''
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