from django.shortcuts import render, redirect, reverse
from django.contrib.auth import login, logout
from django.forms.models import modelformset_factory
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.password_validation import validate_password
from django.contrib import messages

from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from .forms import UserForm, AddressForm, EligibilityForm, programForm, addressLookupForm, futureEmailsForm, MoreInfoForm, attestationForm
from .backend import addressCheck, validateUSPS, enroll_connexion_updates
from .models import AMI, MoreInfo, iqProgramQualifications
from django.http import QueryDict

from py_models.qualification_status import QualificationStatus

import logging
import usaddress
from decimal import Decimal

from django.http import HttpResponseRedirect 


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
                    self.list.append(
                        GAHIVal(
                            f"{self.amiCutoffPc[idx]}^{self.amiCutoffPc[idx+1]}",
                            f"${itm:06,.0f} ~ ${amiCutoffVals[idx+1]:06,.0f}",
                            ),
                        )
                
        # print(self.list)
        
class GAHIVal:
    """ Class to store the text and passable value for each GAHI amount. """
    
    def __init__(self, val, text):

        self.val = val
        self.text = text
        
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
                
                # Use the following tag mapping for USPS standards
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
    
    form = addressLookupForm() 
    logout(request)
    return render(request, 'application/index.html', {
            'form':form,
        })

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

    return render(request, 'application/address.html', {
        'form':form,
        'step':2,
        'request.user':request.user,
        'formPageNum':formPageNum,
        'Title': "Address"
        })


def addressCorrection(request):
    try:
        q = QueryDict('', mutable=True)
        q.update({"address": request.user.addresses.address, 
            "address2": request.user.addresses.address2, 
            "city": request.user.addresses.city,
            "state": request.user.addresses.state,
            "zipcode": str(request.user.addresses.zipCode),})
        dict_address = validateUSPS(q)
        print(dict_address['AddressValidateResponse']['Address'])
        
        # Kick back to the user if the USPS API needs more information
        if 'ReturnText' in dict_address['AddressValidateResponse']['Address'].keys():
            raise TypeError()
        
        program_string_2 = [dict_address['AddressValidateResponse']['Address']['Address2'], 
                            dict_address['AddressValidateResponse']['Address']['Address1'],
                            dict_address['AddressValidateResponse']['Address']['City'] + " "+ dict_address['AddressValidateResponse']['Address']['State'] +" "+  str(dict_address['AddressValidateResponse']['Address']['Zip5'])]
        
    except KeyError or TypeError or RelatedObjectDoesNotExist:
        program_string_2 = ["Sorry, we couldn't verify this address through USPS.", "Please press 'back' and re-enter."]
        print("USPS couldn't figure it out!")
        
    else:
        request.session['usps_address_validate'] = dict_address
        print(q)
        print(dict_address)                   
        
    # If validation was successful and all address parts are case-insensitive
    # exact matches between entered and validation, skip addressCorrection()
    
    # Rewrite any blank values in q to match '-' from USPS API
    q = {key: q[key] if q[key]!='' else '-' for key in q.keys()}
    if 'usps_address_validate' in request.session.keys() and \
        dict_address['AddressValidateResponse']['Address']['Address2'].lower() == q['address'].lower() and \
            dict_address['AddressValidateResponse']['Address']['Address1'].lower() == q['address2'].lower() and \
                dict_address['AddressValidateResponse']['Address']['City'].lower() == q['city'].lower() and \
                    dict_address['AddressValidateResponse']['Address']['State'].lower() == q['state'].lower() and \
                        str(dict_address['AddressValidateResponse']['Address']['Zip5']).lower() == q['zipcode'].lower():         
        
        print('Exact (case-insensitive) address match!')
        return redirect(reverse("application:takeUSPSaddress"))
    
    else:
        print('Address match not found - proceeding to addressCorrection')
                            
        program_string = [request.user.addresses.address, request.user.addresses.address2, request.user.addresses.city + " " + request.user.addresses.state + " " + str(request.user.addresses.zipCode)]
        return render(request, 'application/addressCorrection.html',  {
            'step':2,
            'formPageNum':formPageNum,
            'program_string': program_string,
            'program_string_2': program_string_2,
            'Title': "Address Correction"
        })

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
        
        instance.isInGMA = isInGMA
        instance.hasConnexion = hasConnexion
        
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


def account(request):
    if request.method == "POST": 
        # maybe also do some password requirements here too
        try:
            existing = request.user
            form = UserForm(request.POST,instance = existing)
        except AttributeError or ObjectDoesNotExist:
            form = UserForm(request.POST or None)
        if form.is_valid():
            # Add Error MESSAGE IF THEY DIDN"T WRITE CORRECT THINGS TO SUBMIT
            # Make sure password isn't getting saved twice
            passwordCheck = form.passwordCheck()
            passwordCheckDuplicate = form.passwordCheckDuplicate()
            if passwordCheck != None:
                return render(request, 'application/account.html', {
                'form':form,
                'step':1,
                'formPageNum':formPageNum,
                'Title': "Account",
                'passwordError': passwordCheck
                })   
            else:
                logging.info("password passes all validation checks...")
                

            if str(passwordCheckDuplicate) == str(form.cleaned_data['password']):
                logging.info("password is the same password entered twice...")
            else:
                logging.error("passwords are not the same...")
                return render(request, 'application/account.html', {
                'form':form,
                'step':1,
                'formPageNum':formPageNum,
                'Title': "Account",
                'passwordError': passwordCheckDuplicate
                })   
            try:
                user = form.save()
                login(request,user)
                print("userloggedin")
            except AttributeError:
                print("user error, login not saved, user is: " + str(user))
            return redirect(reverse("application:address"))
    else:
        form = UserForm()

    return render(request, 'application/account.html', {
    'form':form,
    'step':1,
    'formPageNum':formPageNum,
    'Title': "Account",
    })
#    else:
#        return redirect(reverse(page))

def moreInfoNeeded(request):
    if request.method =="POST":
        try:
            existing = request.user.MoreInfo
            form = MoreInfoForm(request.POST,instance = existing)
        except AttributeError or ObjectDoesNotExist:
            form = MoreInfoForm(request.POST or None)
        if form.is_valid():
            try:
                instance = form.save(commit=False)
                instance.user_id = request.user
                instance.dependentInformation = str(form.data)
                instance.save()
                # If GenericQualified is 'ACTIVE',
                # go to the financial information page
                #if instance.GenericQualified == QualificationStatus.ACTIVE.name:
                    #return redirect(reverse("application:mayQualify"))
                #else:
                return redirect(reverse("application:programs"))
            except IntegrityError:
                print("User already has information filled out for this section")
                return redirect(reverse("application:programs"))
        else:
            print(form.data)
    else:
        form = MoreInfoForm()
     
    """householdNum = AMI.objects.filter(
            householdNum=request.user.eligibility.dependents_id,
            active=True,
            ).values('householdNum').first()['householdNum']"""
    return render(request, "application/moreInfoNeeded.html",{
        'step':3,
        #"""'dependent': householdNum,
        #'list':list(range(householdNum)),"""
        'dependent': str(request.user.eligibility.dependents),
        'list':list(range(request.user.eligibility.dependents)),
        'form':form,
        'formPageNum':6,
        'Title': "More Info Needed"
    })
     
    '''"""householdNum = AMI.objects.filter(
            householdNum=request.user.eligibility.dependents_id,
            active=True,
            ).values('householdNum').first()['householdNum']"""
    return render(request, "application/moreInfoNeeded.html",{
        'step':1,
        #"""'dependent': householdNum,
        #'list':list(range(householdNum)),"""
        'dependent': str(request.user.eligibility.dependents),
        'list':list(range(request.user.eligibility.dependents)),
        'form':form,
        'formPageNum':3,
    })'''


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

def finances(request):
    if request.method == "POST":
        try:
            existing = request.user.eligibility
            form = EligibilityForm(request.POST,instance = existing)
        except AttributeError or ObjectDoesNotExist:
            form = EligibilityForm(request.POST or None)
        if form.is_valid():
            print(form.data)
            instance = form.save(commit=False)
            instance.user_id = request.user       
            
            # Parse the 'value' (carat-delimited) from the GAHIBuilder output
            instance.AmiRange_min, instance.AmiRange_max = [
                Decimal(x) for x in form.cleaned_data['grossAnnualHouseholdIncome'].split('^')
                ]
            
            # Ensure AmiRange_max < 1 (that's all we need for GenericQualified)
            if instance.AmiRange_max < Decimal('1'):
                print("GAHI is below program AMI ranges")
                instance.GenericQualified = QualificationStatus.ACTIVE.name
            else:
                print("GAHI is greater than program AMI ranges")
                instance.GenericQualified = QualificationStatus.NOTQUALIFIED.name                  
                
            print("SAVING")
            instance.save()
            # If GenericQualified is 'ACTIVE', go to the financial information page
            #TODO talk to the team about if they make too much money... if they do do we want them to still go through the application or to go to contact us page?
            if instance.GenericQualified == QualificationStatus.ACTIVE.name:
                return redirect(reverse("application:moreInfoNeeded"))
            else:
                return redirect(reverse("application:moreInfoNeeded"))
        else:
            print(form.data)
    else:
        form = EligibilityForm()

    return render(request, 'application/finances.html', {
        'form':form,
        'step':3,
        'formPageNum':formPageNum,
        'Title': "Finances"
    })

def ConnexionQuickApply(request):
    obj = request.user.eligibility
    addr = request.user.addresses
    print(obj.ConnexionQualified)
    #print(request.user.eligibility.GRQualified)
    
    # Calculate if within the qualification range
    qualifyAmiPc = iqProgramQualifications.objects.filter(name='connexion').values(
        'percentAmi'
        ).first()['percentAmi']
    print(obj.AmiRange_max)
    print('Connexion max AMI %:',qualifyAmiPc)
    if obj.GenericQualified == QualificationStatus.ACTIVE.name and obj.AmiRange_max <= qualifyAmiPc:
        obj.ConnexionQualified = QualificationStatus.PENDING.name
        print(obj.ConnexionQualified)
        obj.save()
        
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
        isInGMA, hasConnexion = addressCheck(addressDict)
        # Connexion status unknown, but since isInGMA==True at this point in
        # the application, Connexion will be available at some point
        if not hasConnexion:    # this covers both None and False
            return redirect(reverse("application:comingSoon"))
        else:  # hasConnexion==True is the only remaining option
            return render(
                request,
                "application/quickApply.html",
                {'programName': 'Reduced-Rate Connexion',
                'Title': "Reduced-Rate Connexion Quick Apply Complete"},
                )
    else:
        obj.ConnexionQualified = QualificationStatus.NOTQUALIFIED.name
        print(obj.ConnexionQualified)
        obj.save()
        
        return render(
            request,
            'application/notQualify.html',
            {'programName': 'Reduced-Rate Connexion',
            'Title': "Reduced-Rate Connexion Not Qualified"},
            )

def GRQuickApply(request):
    obj = request.user.eligibility
    print(obj.GRqualified)
    #print(request.user.eligibility.GRQualified)
    
    
    # Calculate if within the qualification range
    qualifyAmiPc = iqProgramQualifications.objects.filter(name='grocery').values(
        'percentAmi'
        ).first()['percentAmi']  
    print('Grocery max AMI %:',qualifyAmiPc)
    if obj.GenericQualified == QualificationStatus.ACTIVE.name and obj.AmiRange_max <= qualifyAmiPc:
        obj.GRqualified = QualificationStatus.PENDING.name
        obj.save()
        return render(
            request,
            "application/quickApply.html",
            {'programName': 'Grocery Tax Rebate',
            'Title': "Grocery Tax Rebate Quick Apply Complete"},
            )
    else:
        obj.GRqualified = QualificationStatus.NOTQUALIFIED.name
        obj.save()
        return render(
            request,
            "application/notQualify.html",
            {'programName': 'Grocery Tax Rebate',
            'Title': "Grocery Tax Rebate Not Qualified"},
            )
    print(obj.GRqualified)

def RecreationQuickApply(request):
    obj = request.user.eligibility
    print(obj.RecreationQualified)
    #print(request.user.eligibility.GRQualified)
    
    # Calculate if within the qualification range
    qualifyAmiPc = iqProgramQualifications.objects.filter(name='recreation').values(
        'percentAmi'
        ).first()['percentAmi']
    print('Recreation max AMI %:',qualifyAmiPc)
    if obj.GenericQualified == QualificationStatus.ACTIVE.name and obj.AmiRange_max <= qualifyAmiPc:
        obj.RecreationQualified = QualificationStatus.PENDING.name
        obj.save()
        return render(
            request,
            "application/quickApply.html",
            {'programName': 'Recreation',
            'Title': "Recreation Quick Apply Complete"},
            )
    else:
        obj.RecreationQualified = QualificationStatus.NOTQUALIFIED.name        
        print(obj.RecreationQualified)
        obj.save()
        return render(
            request,
            "application/notQualify.html",
            {'programName': 'Recreation',
            'Title': "Recreation Not Qualified"},
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

    return render(request, "application/attestation.html",{
        'form':form,
        'step':6,
        'formPageNum':formPageNum,
        'Title': "Attestation"
    })



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

    return render(request, 'application/programs.html', {
    'form':form,
    'step':4,
    'formPageNum':formPageNum,
    'Title': "Programs"
    })

#    else:
#        return redirect(reverse(page))
    #return render(request, 'application/programs.html',)








def notAvailable(request):
    return render(request, 'application/notAvailable.html',{'Title': "Address Not in GMA"})

def quickAvailable(request):
    return render(request, 'application/quickAvailable.html', {'Title': "Quick Connexion Available"})

def quickNotAvailable(request):
    return render(request, 'application/quickNotAvailable.html', {'Title': "Quick Connexion Not Available"}) 

def quickNotFound(request):
    return render(request, 'application/quickNotFound.html',{'Title': "Quick Connexion Not Found"}) 

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
    return render(request, 'application/quickComingSoon.html', {
            'form':form,
            'model_url': reverse("application:quickComingSoon"),
            'Title': "Quick Connexion Coming Soon"
        })

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
                        'Title': "Reduced-Rate Connexion Quick Apply Complete"
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
                    'Title': "Reduced-Rate Connexion Quick Apply Complete"
                    },
                )
        
    form = futureEmailsForm()
    return render(request, 'application/comingSoon.html', {
            'form':form,
            'model_url': reverse("application:comingSoon"),
            'Title': "Reduced-Rate Connexion Communication"
        })

def privacyPolicy(request):
    return render(request, 'application/privacyPolicy.html',)

def dependentInfo(request):
    return render(request, 'application/dependentInfo.html',)

def mayQualify(request):
    return render(request, 'application/mayQualify.html',{
        'step':3,
        'formPageNum':formPageNum,
        'Title': "May Qualify for Programs"
    })

# TODO: The 'CallUs' page should no longer be referenced elsewhere - ensure this is true and remove this function
# (also remove from urls.py)
def callUs(request):
    return render(request, 'application/callUs.html',{
        'step':3,
        'formPageNum':formPageNum,
    })


def getReady(request):
     return render(request, 'application/getReady.html',{
        'step':0,
        'formPageNum':formPageNum,
        'Title': "Ready some Necessary Documents"
    })