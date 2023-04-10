"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version
"""
# All of the forms built from models are here 
from django import forms
from django.contrib.auth.password_validation import validate_password

from .models import HouseholdMembers, User, Addresses, addressLookup, futureEmails, Eligibility_rearch, programs_rearch

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

class EligibilityForm(forms.ModelForm):
    choices = (
        ('More than 3 Years', 'More than 3 Years'),
        ('1 to 3 Years', '1 to 3 Years'),
        ('Less than a Year', 'Less than a Year'),
    )
    duration_at_address = forms.ChoiceField(choices=choices, widget=forms.RadioSelect())
    household_income = forms.ChoiceField()
    class Meta:
        model = Eligibility_rearch
        fields = ['duration_at_address','number_persons_in_household',]
        labels  = {
            'duration_at_address':'How long have you lived at this address?',
            'number_persons_in_household': 'How many individuals are in your household?', 
        }

class EligibilityUpdateForm(forms.ModelForm):
    class Meta:
        model = Eligibility_rearch
        fields = ['number_persons_in_household',]
        labels  = {
            'number_persons_in_household': 'How many individuals are in your household?', 
        } 


class DateInput(forms.DateInput):
    input_type ='date'


class HouseholdMembersForm(forms.ModelForm):
    name = forms.CharField(label='First & Last Name of Individual')
    birthdate = forms.DateField(label="Their Birthdate", widget=forms.widgets.DateInput(attrs={'type': 'date'}))
    class Meta:
        model = HouseholdMembers
        fields = ['name', 'birthdate']




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