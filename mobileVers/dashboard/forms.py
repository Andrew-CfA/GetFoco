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
from django import forms
from .models import Form, Feedback, TaxInformation, residencyForm
from application.models import addressVerification
from django.forms import ClearableFileInput

 
class FileForm(forms.ModelForm):
    class Meta:
        model = Form
        fields = ['document_title','document',]
        labels  = { 
            'document_title':'Program', 
            'document':'Document Upload',
        }
        widgets = {
            'document': ClearableFileInput(attrs={'multiple': True}),
        }
        
 
class AddressForm(forms.ModelForm):
    class Meta:
        model = residencyForm
        fields = ['document_title','document',]
        labels  = { 
            'document_title':'Program', 
            'document':'Document Upload',
        }
        widgets = {
            'document': ClearableFileInput(attrs={'multiple': True}),
        }



# identification forms that they have currently
class addressVerificationForm(forms.ModelForm):
    class Meta:
        model = addressVerification
        fields = ['Utility']#'Identification','freeReducedLunch'
        labels  = { 
            'Utility':'Utility Bill',
            #'Identification':'Identification Card',
            #'freeReducedLunch':'Free and Reduced Lunch',
        } 
        



class TaxForm(forms.ModelForm):
    class Meta:
        model = TaxInformation
        fields = ['TaxBoxAmount',]
        labels  = { 
            'TaxBoxAmount':'Amount of Box 11',
        }



'''need to complete below , tie this and models.py to index.html stars rating and also bug when star is pressed twice...'''
class FeedbackForm(forms.ModelForm):
    #starRating = forms.ChoiceField(widget=forms.RadioSelect(), label="starRating")
    feedbackComments = forms.CharField(max_length = 500, required=False) 
    starRating = forms.CharField(max_length=1, required=False)
    class Meta:
        model = Feedback
        fields = ['feedbackComments','starRating']
        labels  = { 
            'starRating':'Rating in Stars',
            'feedbackComments':'Feedback and Comments by Clients', 
        } 