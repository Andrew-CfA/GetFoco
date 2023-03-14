"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version
"""
from concurrent.futures.process import _python_exit
import json
from django.core.serializers.json import DjangoJSONEncoder
from multiprocessing.sharedctypes import Value
from django.conf import settings as django_settings
from django.shortcuts import render, redirect, reverse
from django.contrib.auth import login, logout
from django.forms.models import modelformset_factory
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.password_validation import validate_password
from django.contrib import messages
from django.http import QueryDict
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from dashboard.backend import get_iq_program_info
from .forms import FilesInfoForm, UserForm, AddressForm, EligibilityForm, programForm, addressLookupForm, futureEmailsForm, MoreInfoForm, attestationForm, UserUpdateForm, EligibilityUpdateForm
from .backend import addressCheck, validateUSPS, enroll_connexion_updates, get_dependant_info, model_to_dict
from .models import AMI, MoreInfo, iqProgramQualifications, User, Eligibility, EligibilityHistory

from py_models.qualification_status import QualificationStatus

import logging, re
import usaddress
from decimal import Decimal

from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from py_models.decorators import set_update_mode



formPageNum = 6

class GAHIBuilder:
    """
    
    This class builds and displays the Gross Annual Household Income
    brackets.
    
    The idea behind this class is that it links the min and max AMI range
    values to the applicant without actually linking the `application_ami`
    table. The fields in this table are supposed to be added to and the old
    values marked inactive, but that may not happen properly and doing it
    this way ensures the AMI range values won't be messed up if that table
    isn't updated properly.
    
    """
    
    # Run the program AMI qualifications here (when the site loads) instead
    # of on class instantiation, to save time
    amiCutoffs = iqProgramQualifications.objects.all().values(
        'percentAmi'
        ).distinct()    # distince() returns only the unique values (no dups)
    # List of floats of ami percentages (prepend zero for the bottom end)
    amiCutoffPc = [Decimal('0')]+sorted(
        [x['percentAmi'] for x in list(amiCutoffs)]
        )

    def __init__(self, request):
        """
        Take the lookup AMI value and program AMI limits and output the
        selections to the user.

        Parameters
        ----------
        ami : int
            Area Median Income, a lookup value from the application_ami table
            based on the user-input household size in the webapp.

        Returns
        -------
        List of elements for the user to select for Gross Annual Household
        Income.

        """
        
        self.list = []
        self.valid = False  # default to invalid result
        
        dependentsStr = request.GET.get('dependents')
        try:
            try:
                # Return the AMI value for the number entered
                ami = AMI.objects.filter(
                    householdNum=dependentsStr,
                    active=True,
                    ).order_by('ami').first().ami
            except AttributeError:  # catch error of 'dependents' value not found
                # If number in household is invalid, display that instead of a
                # dropdown (if dependents cannot be converted to int, a
                # ValueError will be raised before the if statement).
                dependents = int(dependentsStr)
                if dependents < 1:
                    raise ValueError
                else:
                    print(dependents,'individuals in household')
                    
                    # Find the max defined number in household, and compare it
                    # to the input - anything greater than max will have the
                    # 'Each Additional' value added
                    maxHousehold = int(
                        AMI.objects.filter(
                            active=True,
                            ).order_by('-householdNum')[1].householdNum
                        )
                    ami = AMI.objects.filter(
                        householdNum=maxHousehold,
                        active=True,
                        ).order_by('ami').first().ami + \
                        (dependents - maxHousehold) * \
                            AMI.objects.filter(
                                householdNum='Each Additional',
                                active=True,
                                ).order_by('ami').first().ami
                    # print('Base is',AMI.objects.filter(householdNum=maxHousehold,active=True).order_by('ami').first().ami,'Additional is',(dependents - maxHousehold)*AMI.objects.filter(householdNum='Each Additional',active=True).order_by('ami').first().ami)
                
        # Catch invalid dependents
        except ValueError:
            print("Invalid number of individuals")
            self.list.append(
                GAHIVal(
                    'INVALID',
                    'Enter a whole number for individuals in household',
                    ),
                )
            
        else:
            self.valid = True
            print('AMI is',ami) 
            
            # Transform percentages to values using the calculated AMI
            amiCutoffVals = [ami*x for x in self.amiCutoffPc]
            print('AMI cutoffs are',amiCutoffVals)
            
            # Build the list, using each distinct monetary cutoff.
            # Database values are "<low %>^<high %>"
            # Display values are "$<low value> ~ $<high value>", except at the
            # top and bottom ends
            maxIdx = len(self.amiCutoffPc)
            for idx,itm in enumerate(amiCutoffVals):
                if idx == 0:
                    self.list.append(
                        GAHIVal(
                            f"{self.amiCutoffPc[idx]}^{self.amiCutoffPc[idx+1]}",
                            f"Below ${amiCutoffVals[idx+1]:06,.0f}",
                            ),
                        )
                elif idx == maxIdx-1:
                    self.list.append(
                        GAHIVal(
                            f"{self.amiCutoffPc[idx]}^1",
                            f"Over ${itm:06,.0f}",
                            ),
                        )
                else:
                    # Add $1 to the low end of each range to improve clarity
                    # (range ends will now not overlap)
                    # Adding to the low end means applicants at the edge of the
                    # range will select the lower range and increase their
                    # available benefits.
                    self.list.append(
                        GAHIVal(
                            f"{self.amiCutoffPc[idx]}^{self.amiCutoffPc[idx+1]}",
                            f"${itm+1:06,.0f} ~ ${amiCutoffVals[idx+1]:06,.0f}",
                            ),
                        )
                
        # print(self.list)
        
class GAHIVal:
    """ Class to store the text and passable value for each GAHI amount. """
    
    def __init__(self, val, text):

        self.val = val
        self.text = text
        
# Use the following tag mapping for USPS standards for all functions
tag_mapping = {
   'Recipient': 'recipient',
   'AddressNumber': 'address_2',
   'AddressNumberPrefix': 'address_2',
   'AddressNumberSuffix': 'address_2',
   'StreetName': 'address_2',
   'StreetNamePreDirectional': 'address_2',
   'StreetNamePreModifier': 'address_2',
   'StreetNamePreType': 'address_2',
   'StreetNamePostDirectional': 'address_2',
   'StreetNamePostModifier': 'address_2',
   'StreetNamePostType': 'address_2',
   'CornerOf': 'address_2',
   'IntersectionSeparator': 'address_2',
   'LandmarkName': 'address_2',
   'USPSBoxGroupID': 'address_2',
   'USPSBoxGroupType': 'address_2',
   'USPSBoxID': 'address_2',
   'USPSBoxType': 'address_2',
   'BuildingName': 'address_1',
   'OccupancyType': 'address_1',
   'OccupancyIdentifier': 'address_1',
   'SubaddressIdentifier': 'address_1',
   'SubaddressType': 'address_1',
   'PlaceName': 'city',
   'StateName': 'state',
   'ZipCode': 'zipcode',
}
        
# first index page we come into
def index(request):
    if request.method == "POST": 
        form = addressLookupForm(request.POST or None)
        if form.is_valid():
            try:
                form.save()
                
                # Use usaddress to try to parse the input text into an address
                
                # Clean the data
                # Remove 'fort collins' - the multi-word city can confuse the
                # parser
                addressStr = form.cleaned_data['address'].lower().replace('fort collins','')
                
                rawAddressDict, addressType = usaddress.tag(
                    addressStr,
                    tag_mapping,
                    )
                
                # Only continue to validation, etc if a 'Street Address' is
                # found by usaddress
                if addressType != 'Street Address':
                    raise NameError("The address cannot be parsed")
                    
                print(
                    'Address parsing found',
                    rawAddressDict,
                    )
                
                # Help out parsing with educated guesses
                # if 'state' not in rawAddressDict.keys():
                rawAddressDict['state'] = 'CO'
                # if 'city' not in rawAddressDict.keys():
                rawAddressDict['city'] = 'Fort Collins'
                    
                print(
                    'Updated address parsing is', 
                    rawAddressDict,
                    )
                    
                # Ensure the necessary keys for USPS validation are included
                uspsKeys = [
                    'name',
                    'address_1',
                    'address_2',
                    'city',
                    'state',
                    'zipcode']
                rawAddressDict.update(
                    {key:'' for key in uspsKeys if key not in rawAddressDict.keys()}
                    )
                
                # Validate to USPS address
                addressDict = validateUSPS(rawAddressDict)
                
                # Check for IQ and Connexion services
                isInGMA, hasConnexion = addressCheck(addressDict)
                
                if isInGMA:
                    # Connexion status unknown, but since isInGMA==True, it
                    # will be available at some point
                    if not hasConnexion:    # this covers both None and False
                        # Write a dictionary to the session var with 'address'
                        # and 'zipCode' for use when quick-applying for Connexion
                        request.session['address_dict'] = {
                            'address': addressDict['AddressValidateResponse']['Address']['Address2'],
                            'zipCode': addressDict['AddressValidateResponse']['Address']['Zip5'],
                            }
                        return redirect(reverse("application:quickComingSoon"))
                        
                    else:  # hasConnexion==True is the only remaining option
                        return redirect(reverse("application:quickAvailable"))
                    
                else:
                    return redirect(reverse("application:quickNotAvailable"))

            except:
                #TODO implement look into logs!
                logging.warning("insert valid zipcode")
                return(redirect(reverse("application:quickNotFound")))
    
    else:
        # Check if the app_status query parameter is present
        # If so, check if it is 'in_progress'
        # If it's in progress, redirect to the application:index page
        if 'app_status' in request.GET:
            if request.GET['app_status'] == 'in_progress':
                # Set the app_status session variable to 'in_progress'
                request.session['app_status'] = 'in_progress'
                return redirect(reverse("application:index"))

        form = addressLookupForm() 
    
    
        # Check if the user is logged in and has the 'app_status' session var
        # set to 'in_progress'
        in_progress_app_saved = False
        if request.user.is_authenticated and 'app_status' in request.session:
            if request.session['app_status'] == 'in_progress':
                in_progress_app_saved = True

        logout(request)
        return render(
            request,
            'application/index.html',
            {
                'form': form,
                'is_prod': django_settings.IS_PROD,
                'in_progress_app_saved': in_progress_app_saved,
                },
            )

def address(request):

    if request.method == "POST": 
        try:
            existing = request.user.addresses
            form = AddressForm(request.POST,instance = existing)
        except ObjectDoesNotExist:
            form = AddressForm(request.POST or None)

        print(form.data)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user_id = request.user
            instance.save()            
            return redirect(reverse("application:addressCorrection"))
    else:
        form = AddressForm()

    return render(
        request,
        'application/address.html',
        {
            'form':form,
            'step':2,
            'request.user':request.user,
            'formPageNum':formPageNum,
            'Title': "Address",
            'is_prod': django_settings.IS_PROD,
            },
        )


def addressCorrection(request):
    try:
        q = QueryDict('', mutable=True)
        q.update({"address": request.user.addresses.address, 
            "address2": request.user.addresses.address2, 
            "city": request.user.addresses.city,
            "state": request.user.addresses.state,
            "zipcode": str(request.user.addresses.zipCode),})

        q_orig = QueryDict('', mutable=True)
        q_orig.update({"address": request.user.addresses.address, 
            "address2": request.user.addresses.address2, 
            "city": request.user.addresses.city,
            "state": request.user.addresses.state,
            "zipcode": str(request.user.addresses.zipCode),})
        
        # Loop through maxLoopIdx+1 times to try different methods of
        # parsing the address
        # Loop 0: as-entered > usaddress > USPS API
        # Loop 1: as-entered with apt/suite keywords replaced with 'unit' >
            # usaddress > USPS API
        # Loop 2: an-entered with keyword replacements > USPS API
        maxLoopIdx = 2
        idx = 0     # starting idx
        flag_needMoreInfo = False   # flag for previous iter needing more info
        while 1:
            print("Start loop {}".format(idx))

            try:
                if idx in (0,1):
                    addressStr = "{ad1} {ad2}, {ct}, {st} {zp}".format(
                        ad1=q['address'].replace('#',''),
                        ad2=q['address2'].replace('#',''),
                        ct=q['city'],
                        st=q['state'],
                        zp=q['zipcode'])

                    try:
                        rawAddressDict, addressType = usaddress.tag(
                            addressStr,
                            tag_mapping,
                            )

                    # Go directly to the QueryDict version if there's a usaddress
                    # issue
                    except usaddress.RepeatedLabelError:
                        print('Error in usaddress labels - continuing as loop 2')
                        idx = 2
                        raise AttributeError

                    # Ensure the necessary keys for USPS validation are included
                    uspsKeys = [
                        'name',
                        'address_1',
                        'address_2',
                        'city',
                        'state',
                        'zipcode']
                    rawAddressDict.update(
                        {key:'' for key in uspsKeys if key not in rawAddressDict.keys()}
                        )

                # Validate to USPS address - use usaddress first, then try
                # with input QueryDict
                try:
                    if idx == 2:
                        print('Input QueryDict:', q)
                        dict_address = validateUSPS(q)   
                    else:
                        print('rawAddressDict:', rawAddressDict)
                        dict_address = validateUSPS(rawAddressDict)        
                    validationAddress = dict_address['AddressValidateResponse']['Address']
                    print('USPS Validation return:', validationAddress)
                    
                except KeyError:
                    if idx == maxLoopIdx:
                        if flag_needMoreInfo:
                            raise TypeError(str_needMoreInfo)
                        raise
                    idx+=1
                    raise AttributeError

                # Ensure 'Address1' is a valid key
                if 'Address1' not in validationAddress.keys():
                    validationAddress['Address1'] = ''
                
                # Kick back to the user if the USPS API needs more information
                if 'ReturnText' in validationAddress.keys():
                    if idx == maxLoopIdx:
                        print('Address not found - end of loop')
                        raise TypeError(validationAddress['ReturnText'])

                    # Continue checking, but flag that this was a result from 
                    # the USPS API and store the text
                    else:
                        flag_needMoreInfo = True
                        str_needMoreInfo = validationAddress['ReturnText']

                else:   # success!
                    break

                if idx == maxLoopIdx:   # this is just here for safety
                    break
                else:
                    idx+=1
                    raise AttributeError

            except AttributeError:
                # Use AttributeError to skip to the end of the loop
                # Note that idx has already been iterated before this point
                print('AttributeError raised with idx', idx)
                if q['address2'] != '':  
                    if idx == 1:
                        # For loop 1: if 'ReturnText' is not found and address2 is
                        # not None, remove possible keywords and try again
                        # Note that this will affect later loop iterations
                        print('Address not found - try to remove/replace keywords')
                        removeList = ['apt', 'unit', '#']
                        for wrd in removeList:
                            q['address2'] = q['address2'].lower().replace(wrd, '')

                        q['address2'] = 'Unit {}'.format(q['address2'].lstrip())

                else:
                    # This whole statement updates address2, so if it's blank,
                    # iterate through idx prematurely
                    idx = 2
        
        program_string_2 = [validationAddress['Address2'], 
                            validationAddress['Address1'],
                            validationAddress['City'] + " "+ validationAddress['State'] +" "+  str(validationAddress['Zip5'])]
        print('program_string_2', program_string_2)
        
    except TypeError as msg:
        print("More address information is needed from user")
        # Only pass to the user for the 'more information is needed' case
        # --This is all that has been tested--
        msg = str(msg)
        if 'more information is needed' in msg:
            program_string_2 = [
                msg.replace('Default address: ',''),
                "Please press 'back' and re-enter.",
                ]
            
        else:
            print("Some other issue than 'more information is needed'")
            program_string_2 = [
                "Sorry, we couldn't verify this address through USPS.",
                "Please press 'back' and re-enter.",
                ]

    except KeyError or RelatedObjectDoesNotExist:
        program_string_2 = [
            "Sorry, we couldn't verify this address through USPS.",
            "Please press 'back' and re-enter.",
            ]
        print("USPS couldn't figure it out!")
        
    else:
        request.session['usps_address_validate'] = dict_address
        print(q)
        print(dict_address)                   
        
        # If validation was successful and all address parts are case-insensitive
        # exact matches between entered and validation, skip addressCorrection()
        
        # Run the QueryDict 'q' to get just dict
        # If just a string input was used (loop idx == 2), use '-' for blanks
        if idx == 2:
            q_orig = {key: q_orig[key] if q[key]!='' else '-' for key in q_orig.keys()}
        else:
            q_orig = {key: q_orig[key] for key in q_orig.keys()}
        if 'usps_address_validate' in request.session.keys() and \
            dict_address['AddressValidateResponse']['Address']['Address2'].lower() == q_orig['address'].lower() and \
                dict_address['AddressValidateResponse']['Address']['Address1'].lower() == q_orig['address2'].lower() and \
                    dict_address['AddressValidateResponse']['Address']['City'].lower() == q_orig['city'].lower() and \
                        dict_address['AddressValidateResponse']['Address']['State'].lower() == q_orig['state'].lower() and \
                            str(dict_address['AddressValidateResponse']['Address']['Zip5']).lower() == q_orig['zipcode'].lower():         
            
            print('Exact (case-insensitive) address match!')
            return redirect(reverse("application:takeUSPSaddress"))
    
    print('Address match not found - proceeding to addressCorrection')
                        
    program_string = [request.user.addresses.address, request.user.addresses.address2, request.user.addresses.city + " " + request.user.addresses.state + " " + str(request.user.addresses.zipCode)]
    return render(
        request,
        'application/addressCorrection.html',
        {
            'step':2,
            'formPageNum':formPageNum,
            'program_string': program_string,
            'program_string_2': program_string_2,
            'Title': "Address Correction",
            'is_prod': django_settings.IS_PROD,
            },
        )

def takeUSPSaddress(request):
    try:
        # Use the session var created in addressCorrection(), then remove it
        dict_address = request.session['usps_address_validate']
        del request.session['usps_address_validate']
        
        # Check for and store GMA and Connexion status
        isInGMA, hasConnexion = addressCheck(dict_address)

        instance = request.user.addresses
        instance.user_id = request.user
        instance.address = dict_address['AddressValidateResponse']['Address']['Address2']
        instance.address2 = dict_address['AddressValidateResponse']['Address']['Address1']
        instance.city = dict_address['AddressValidateResponse']['Address']['City']
        instance.state = dict_address['AddressValidateResponse']['Address']['State']
        instance.zipCode = int(dict_address['AddressValidateResponse']['Address']['Zip5'])
        
        # Record the service area and Connexion status
        instance.isInGMA = isInGMA
        instance.hasConnexion = hasConnexion
        
        # Final step: mark the address record as 'verified'
        instance.is_verified = True
        
        instance.save()
    except KeyError or TypeError or RelatedObjectDoesNotExist:
        
        print("USPS couldn't figure it out!")
        # HTTP_REFERER sends this button press back to the same page
        # (e.g. removes the button functionality)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    else:
        return redirect(reverse("application:inServiceArea"))



def inServiceArea(request):
    if request.user.addresses.isInGMA:
        return redirect(reverse("application:finances")) #TODO figure out to clean?
    else:
        print("address not in GMA")
        return redirect(reverse("application:notAvailable")) 

@set_update_mode
def account(request):
    if request.method == "POST": 
        # maybe also do some password requirements here too
        try:
            existing = request.user
            # Check if the update_mode exists in the POST data.
            update_mode = request.POST.get('update_mode')
            if update_mode:
                form = UserUpdateForm(request.POST,instance = existing)
            else:
                form = UserForm(request.POST,instance = existing)
        except AttributeError or ObjectDoesNotExist:
            form = UserForm(request.POST or None)
        if form.is_valid() and update_mode:
            form.save()
            return JsonResponse({"redirect":f"{reverse('dashboard:settings')}?page_updated=account"})
        elif form.is_valid():
            passwordCheck = form.passwordCheck()
            passwordCheckDuplicate = form.passwordCheckDuplicate()
            #AJAX data function below, sends data to AJAX function in account.html. If client makes a mistake in password, AJAX lets them know, no page refresh
            if passwordCheck != None: #if passwordCheck finds an error like too common a password, no numbers, etc.
                data = {
                    'result':"error",
                    'message': passwordCheck
                }
                return JsonResponse(data)
            #AJAX data function below, sends data to AJAX function in account.html. If client makes a mistake in password, AJAX lets them know, no page refresh
            elif str(passwordCheckDuplicate) != str(form.cleaned_data['password']): #Checks if password is the same as the "Enter Password Again" Field
                data = {
                    'result':"error",
                    'message': passwordCheckDuplicate
                }
                return JsonResponse(data)
            try:
                user = form.save()
                login(request,user)
                print("userloggedin")
                data = {
                'result':"success",
                }
                return JsonResponse(data)
            except AttributeError:
                print("user error, login not saved, user is: " + str(user))

            return redirect(reverse("application:address"))

        else:
            #AJAX data function below, sends data to AJAX function in account.html, if clients make a mistake via email or phone number, page lets them know and DOESN'T refresh web page
            #let's them know via AJAX
            errorMessages = dict(form.errors.items())       
            if "email" in errorMessages:
                data ={
                    'result':"error",
                    'message': errorMessages["email"]
                    }
            elif "phone_number" in errorMessages:
                data = {
                    'result':"error",
                    'message':  errorMessages["phone_number"]
                    }
            return JsonResponse(data)
    else:
        if request.session.get('update_mode'):
            # Query the users table for the user's data
            user = User.objects.get(id=request.user.id)
            form = UserUpdateForm(instance=user)
        else:
            form = UserForm()

    return render(
        request,
        'application/account.html',
        {
            'form':form,
            'step':1,
            'formPageNum':formPageNum,
            'Title': "Account",
            'is_prod': django_settings.IS_PROD,
            'update_mode': request.session.get('update_mode'),
            },
        )
def filesInfoNeeded(request):
    '''
    can be used in the future for more information that may be needed from client pertaining to IQ programs
    i.e. ACP requires last 4 digits of SSN
    '''
    if request.method =="POST":
        try:
            existing = request.user.MoreInfo
            form = FilesInfoForm(request.POST,instance = existing)
        except AttributeError or ObjectDoesNotExist:
            form = FilesInfoForm(request.POST or None)
        if form.is_valid():
            try:
                instance = form.save(commit=False)
                instance.user_id = request.user
                instance.last4SSN = form.cleaned_data['last4SSN']
                instance.save()
                return redirect(reverse("dashboard:broadcast"))
            except IntegrityError:
                print("User already has information filled out for this section")
                return redirect(reverse("application:filesInfoNeeded"))
        else:
            print(form.data)
    else:
        form = FilesInfoForm()
     
    return render(
        request,
        "application/filesInfoNeeded.html",
        {
            'step':5,
            'form':form,
            'formPageNum':6,
            'Title': "IQ Program Info Needed",
            'is_prod': django_settings.IS_PROD,
            },
        )
     
@set_update_mode
def moreInfoNeeded(request):
    if request.method =="POST":
        # Check if the update_mode exists in the POST data.
        update_mode = request.POST.get('update_mode')
        try:
            if update_mode:
                existing = MoreInfo.objects.get(user_id=request.user.id)
                form = MoreInfoForm(request.POST,instance=existing)
            else:
                existing = request.user.MoreInfo
                form = MoreInfoForm(request.POST,instance=existing)
        except AttributeError or ObjectDoesNotExist:
            form = MoreInfoForm(request.POST or None)
        
        try:
            instance = form.save(commit=False)
            instance.user_id = request.user
            instance.dependentInformation = str(form.data)
            instance.save()
            if update_mode:
                return redirect(f"{reverse('dashboard:settings')}?page_updated=financial")
            return redirect(reverse("application:programs"))
        except IntegrityError:
            print("User already has information filled out for this section")
            return redirect(reverse("application:programs"))
    else:
        dependant_info = None
        # We're only checking if the query parameter even exists, not its value
        # if there is a query parameter, we're in update mode and we want to show the form
        # with user's existing data. If there is no query parameter, the user is just now
        # starting the application.
        if request.session.get('update_mode'):
            # Query the users table for the user's data
            more_info = MoreInfo.objects.get(user_id=request.user.id)
            dependant_info = get_dependant_info(more_info)
            form = MoreInfoForm(instance=more_info)
        else:
            form = MoreInfoForm()
     
        return render(
            request,
            "application/moreInfoNeeded.html",
            {
                'step':3,
                'dependent': str(request.user.eligibility.dependents),
                'list':list(range(request.user.eligibility.dependents)),
                'form':form,
                'formPageNum':6,
                'Title': "More Info Needed",
                'is_prod': django_settings.IS_PROD,
                'update_mode': request.session.get('update_mode'),
                'form_data': json.dumps(dependant_info) if dependant_info else None,
                },
            )


def load_gahi_selector(request):
    """ Load the Gross Annual Household Income selection list. """
    
    print('Loaded GAHI selector!')
    gahi = GAHIBuilder(request)
    return render(
        request,
        'hr/income_dropdown_list_options.html',
        {
            'gahiList': gahi.list,
            'valid': gahi.valid,
            },
        )

@set_update_mode
def finances(request):
    if request.method == "POST":
        # Check if the update_mode exists in the POST data.
        update_mode = request.POST.get('update_mode')
        try:
            existing = request.user.eligibility
            if update_mode:
                previous_max_ami = existing.AmiRange_max
                form = EligibilityUpdateForm(request.POST,instance = existing)
            else:
                form = EligibilityForm(request.POST,instance = existing)
        except AttributeError or ObjectDoesNotExist:
            form = EligibilityForm(request.POST or None)

        instance = form.save(commit=False)
        instance.user_id = request.user       
        
        # Parse the 'value' (carat-delimited) from the GAHIBuilder output
        instance.AmiRange_min, instance.AmiRange_max = [
            Decimal(x) for x in form.cleaned_data['grossAnnualHouseholdIncome'].split('^')
            ]

        # The gist of this if/else block is that we want to keep a user's program
        # statuses the same if they are in a PENDING or ACTIVE state. However, if
        # they are NOTQUALIFIED, we want to set them to an empty string so that they 
        # can enroll in programs again.
        if update_mode:
            # Save the user's current eligibility data to the database in the
            # eligibility history table.
            users_eligibility = model_to_dict(Eligibility.objects.get(user_id=request.user.id))
            eligibility_history = EligibilityHistory.objects.create(
                user_id=request.user,
                # Convert the eligibility object to a dictionary and then to a JSON string
                # and set it to the historical_eligibility field
                historical_eligibility=json.dumps(users_eligibility, cls=DjangoJSONEncoder)                                
            )
            eligibility_history.save()

            # Loop through all of the attributes in the request.user.eligibility object
            # and set them to "" if they contain the word "Qualified", have a NOTQUALIFED
            # status and the new AmiRange_max is less than the old AmiRange_max.
            if instance.AmiRange_max < previous_max_ami:
                instance.GenericQualified = QualificationStatus.PENDING.name
                for attr in dir(request.user.eligibility):
                    if "qualified" in attr.lower() and "GenericQualified" != attr:
                        if getattr(request.user.eligibility, attr) == QualificationStatus.NOTQUALIFIED.name:
                            setattr(request.user.eligibility, attr, "")
        else:
            # Ensure AmiRange_max < 1 (that's all we need for GenericQualified)
            if instance.AmiRange_max < Decimal('1'):
                print("GAHI is below program AMI ranges")
                instance.GenericQualified = QualificationStatus.PENDING.name
            else:
                print("GAHI is greater than program AMI ranges")
                instance.GenericQualified = QualificationStatus.NOTQUALIFIED.name             
            
        print("SAVING")
        instance.save()

        # auto apply grocery rebate people if their AMI is <=30%
        if ((request.user.eligibility.AmiRange_max <= Decimal('0.3') and request.user.eligibility.GRqualified != QualificationStatus.ACTIVE.name)):
            # Update the current model so the dashboard displays correctly
            request.user.eligibility.GRqualified = QualificationStatus.PENDING.name

            # Update the database
            Eligibility.objects.filter(user_id_id=request.user.id).update(GRqualified=QualificationStatus.PENDING.name)

        if update_mode:
            return redirect(f'{reverse("application:moreInfoNeeded")}?update_mode=1')
        else:
            return redirect(reverse("application:moreInfoNeeded"))

    else:
        if request.session.get('update_mode'):
            # Query the users table for the user's data
            eligibility = Eligibility.objects.get(user_id=request.user.id)
            form = EligibilityUpdateForm(instance=eligibility)
        else:
            form = EligibilityForm()

    return render(
        request,
        'application/finances.html',
        {
            'form':form,
            'step':3,
            'formPageNum':formPageNum,
            'Title': "Finances",
            'is_prod': django_settings.IS_PROD,
            'update_mode': request.session.get('update_mode'),
            },
        )


def IQProgramQuickApply(request, iq_program):
    iq_program = get_iq_program_info(request.user.eligibility, iq_program)

    print(iq_program['status_for_user'])
    #print(request.user.eligibility.GRQualified)
    
    # Calculate if within the qualification range
    qualifyAmiPc = iqProgramQualifications.objects.filter(name=iq_program['program_name']).values(
        'percentAmi'
        ).first()['percentAmi']
    print(f'{iq_program["program_name"]} max AMI %:',qualifyAmiPc)

    setattr(request.user.eligibility, iq_program['eligibility_column_name'], QualificationStatus.PENDING.name)
    if iq_program['program_name'] == 'spin':
        setattr(request.user.eligibility, 'spin_privacy_acknowledgement', True)
    elif iq_program['program_name'] == 'connexion':
        addr = request.user.addresses
        ## Check for Connexion services
        # Recreate the relevant parts of addressDict as if from validateUSPS()
        addressDict = {
            'AddressValidateResponse': {
                'Address': {
                    'Address2': addr.address,
                    'Zip5': addr.zipCode,
                    },
                },
            }
        _, hasConnexion = addressCheck(addressDict)
        # Connexion status unknown, but since isInGMA==True at this point in
        # the application, Connexion will be available at some point
        if not hasConnexion:    # this covers both None and False
            return redirect(reverse("application:comingSoon"))
        
    request.user.eligibility.save()

    return render(
        request,
        "application/quickApply.html",
        {
            'programName': iq_program['program_name'].title(),
            'Title': f"{iq_program['program_name'].title()} Quick Apply Complete",
            'is_prod': django_settings.IS_PROD,
            },
        )


def attestation(request):
    if request.method == "POST": 
        try:
            existing = request.user.attestations
            form = attestationForm(request.POST,instance = existing)
        except AttributeError or ObjectDoesNotExist:
            form = attestationForm(request.POST or None)
        if form.is_valid():
            print(form.data)
            print(request.session)
            try:
                instance = form.save(commit=False)
                instance.user_id = request.user
                instance.save()
                return redirect(reverse("dashboard:broadcast"))
            except IntegrityError:
                print("User already has information filled out for this section")
            return redirect(reverse("application:available"))
    else:
        form = attestationForm()

    return render(
        request,
        "application/attestation.html",
        {
            'form':form,
            'step':6,
            'formPageNum':formPageNum,
            'Title': "Attestation",
            'is_prod': django_settings.IS_PROD,
            },
        )



def programs(request):
    if request.method == "POST": 
        try:
            existing = request.user.programs
            form = programForm(request.POST,instance = existing)
        except AttributeError or ObjectDoesNotExist:
            form = programForm(request.POST or None)
        if form.is_valid():
            print(form.data)
            print(request.session)
            try:
                instance = form.save(commit=False)
                instance.user_id = request.user
                instance.save()    
                return redirect(reverse("dashboard:files"))
            except IntegrityError:
                print("User already has information filled out for this section")
            #enter upload code here for client to upload images
            return redirect(reverse("application:available"))
    else:
        form = programForm()

    return render(
        request,
        'application/programs.html',
        {
            'form':form,
            'step':4,
            'formPageNum':formPageNum,
            'Title': "Programs",
            'is_prod': django_settings.IS_PROD,
            },
        )









def notAvailable(request):
    return render(
        request,
        'application/notAvailable.html',
        {
            'Title': "Address Not in Service Area",
            'is_prod': django_settings.IS_PROD,
            },
        )

def quickAvailable(request):
    return render(
        request,
        'application/quickAvailable.html',
        {
            'Title': "Quick Connexion Available",
            'is_prod': django_settings.IS_PROD,
            },
        )

def quickNotAvailable(request):
    return render(
        request,
        'application/quickNotAvailable.html',
        {
            'Title': "Quick Connexion Not Available",
            'is_prod': django_settings.IS_PROD,
            },
        ) 

def quickNotFound(request):
    return render(
        request,
        'application/quickNotFound.html',
        {
            'Title': "Quick Connexion Not Found",
            'is_prod': django_settings.IS_PROD,
            },
        ) 

def quickComingSoon(request): 
    
    if request.method == "POST": 
        form = futureEmailsForm(request.POST or None)
        if form.is_valid():
            try:
                form.save()
            except AttributeError:
                print("Error Email Saving")
            else:
                request.session['connexion_communication'] = form.cleaned_data['connexionCommunication']
                return redirect(reverse("application:account"))
                
    
    form = futureEmailsForm()
    return render(
        request,
        'application/quickComingSoon.html',
        {
            'form':form,
            'model_url': reverse("application:quickComingSoon"),
            'Title': "Quick Connexion Coming Soon",
            'is_prod': django_settings.IS_PROD,
            },
        )

def comingSoon(request): 

    if request.method == "POST": 
        form = futureEmailsForm(request.POST or None)
        if form.is_valid():
            try:
                form.save()
                
                doEnroll = form.cleaned_data['connexionCommunication']
                enrollFailure = False
                if doEnroll is True:
                    try:
                        enroll_connexion_updates(request)
                    except AssertionError:
                        enrollFailure = True
                        
                return render(
                    request,
                    "application/quickApply.html",
                    {
                        'programName': 'Reduced-Rate Connexion',
                        'enroll_failure': enrollFailure,
                        'is_enrolled': doEnroll,
                        'Title': "Reduced-Rate Connexion Quick Apply Complete",
                        'is_prod': django_settings.IS_PROD,
                        },
                    )

            except AttributeError:
                print("Error Email Saving")
    
    # If this application was started with quickComingSoon and the address
    # entered there matches the application, skip to quickApply.html
    if 'address_dict' in request.session.keys() and 'connexion_communication' in request.session.keys():
        addr = request.user.addresses
        if request.session['address_dict']['address'] == addr.address and request.session['address_dict']['zipCode'] == str(addr.zipCode):
            
            doEnroll = request.session['connexion_communication']
            enrollFailure = False
            if doEnroll is True:
                try:
                    enroll_connexion_updates(request)
                except AssertionError:
                    enrollFailure = True
                    
            # Remove the session vars after use
            del request.session['address_dict']
            del request.session['connexion_communication']
                    
            return render(
                request,
                "application/quickApply.html",
                {
                    'programName': 'Reduced-Rate Connexion',
                    'enroll_failure': enrollFailure,
                    'is_enrolled': doEnroll,
                    'Title': "Reduced-Rate Connexion Quick Apply Complete",
                    'is_prod': django_settings.IS_PROD,
                    },
                )
        
    form = futureEmailsForm()
    return render(
        request,
        'application/comingSoon.html',
        {
            'form':form,
            'model_url': reverse("application:comingSoon"),
            'Title': "Reduced-Rate Connexion Communication",
            'is_prod': django_settings.IS_PROD,
            },
        )

def privacyPolicy(request):
    # check if user is logged in
    user_logged_in = False
    if request.user.is_authenticated:
        user_logged_in = True

    return render(
        request,
        'application/privacyPolicy.html',
        {
            'is_prod': django_settings.IS_PROD,
            'user_logged_in': user_logged_in,
            },
        )

def dependentInfo(request):
    return render(
        request,
        'application/dependentInfo.html',
        {
            'is_prod': django_settings.IS_PROD,
            },
        )

def mayQualify(request):
    return render(
        request,
        'application/mayQualify.html',
        {
            'step':3,
            'formPageNum':formPageNum,
            'Title': "May Qualify for Programs",
            'is_prod': django_settings.IS_PROD,
            },
        )


def getReady(request):
     return render(
         request,
         'application/getReady.html',
         {
            'step':0,
            'formPageNum':formPageNum,
            'Title': "Ready some Necessary Documents",
            'is_prod': django_settings.IS_PROD,
            },
         )