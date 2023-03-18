"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version
"""
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import reverse

# Grace User Authentication
from django.contrib.auth.backends import UserModel
from django.contrib.auth import get_user_model

from django.conf import settings

#below imports needed for blob storage
from azure.storage.blob import BlockBlobService

from py_models.qualification_status import QualificationStatus
from application.models import MoreInfo, Addresses, iqProgramQualifications
from decimal import Decimal


def blobStorageUpload(filename, file):
    blob_service_client = BlockBlobService(
        account_name=settings.BLOB_STORE_NAME,
        account_key=settings.BLOB_STORE_KEY,
        endpoint_suffix=settings.BLOB_STORE_SUFFIX,
        )
    
    blob_service_client.create_blob_from_bytes(
        container_name = settings.USER_FILES_CONTAINER,
        blob_name = filename,
        blob = file.read(),
    )

def authenticate(username=None, password=None):
    User = get_user_model()
    try: #to allow authentication through phone number or any other field, modify the below statement
        user = User.objects.get(email=username)
        print(user)
        print(password)
        print(user.password)
        print(user.check_password(password))
        if user.check_password(password):
            return user 
        return None
    except User.DoesNotExist:
        return None

def get_user(self, user_id):
    try:
        return UserModel.objects.get(id=user_id)
    except UserModel.DoesNotExist:
        return None

def files_to_string(file_list):
    list_string = ""
    counter = 0

    print(counter)
    # Get File_List into easy to read list to print out in template
    for key, value in file_list.items():
        # only add things to the list_string if its true
        if value == True:
            # Also add commas based on counter
            if counter == 5:
                list_string += "\n"
                counter = 4
            elif counter == 4:
                list_string += "\n"
                counter = 3
            elif counter == 3:
                list_string += "\n"
                counter = 2
            elif counter == 2:
                list_string += "\n"
                counter = 1
            elif counter == 1:
                list_string += "\n"
                counter = 0
            else:
                counter = 5
            list_string += key
    return list_string

# redirect user to whatever page they need to go to every time by checking which steps they've
# completed in the application process
def what_page(user,request):
    if user.is_authenticated:
        
        searchForUser = request.user.id
        
        #for some reason, none of these login correctly... reviewing this now
        try: #check if the addresses.is_verified==True
            if Addresses.objects.all().filter(user_id_id=searchForUser).exists() and Addresses.objects.get(user_id_id=searchForUser).is_verified:
                print("Address has been verified")
            else:
                print("Still need to verify address")
                raise AttributeError()
            
        except AttributeError:
            return "application:address"

        try: #check if finances is filled
            value = request.user.eligibility
        except AttributeError:
            return "application:finances"

        try: #check if dependents / birthdays are filled
            if(MoreInfo.objects.all().filter(user_id_id=searchForUser).exists()):
                print("MoreInfo exists")
            else:
                print("MoreInfo doesn't exist")
                return "application:moreInfoNeeded"
        except AttributeError or ObjectDoesNotExist:
            return "application:moreInfoNeeded"
        
        try: #check if programs is filled out
            value = request.user.programs
        except AttributeError or ObjectDoesNotExist:
            return "application:programs"

        try: #check if files are all uploaded
            file_list = get_users_eligiblity_programs(request)
            uploads_complete, file_list = check_user_file_upload_progress(request, file_list)

            if not uploads_complete:
                return "dashboard:files"
            else:
                print("files found")
        except AttributeError:
            return "dashboard:files"

        try: #check if ACP last four SSN is needed or not...
            if ((request.user.programs.ebb_acf) == True) and ((request.user.taxinformation.last4SSN) == "NULL"):
                return "application:filesInfoNeeded"
            else:
                print("last 4 ssn found")
        except:
            return "application:filesInfoNeeded"

        return "dashboard:dashboard"
    else:
        return "application:account"


def build_qualification_button(users_enrollment_status):
    # Create a dictionary to hold the button information
    return {
        'NOT QUALIFIED': {
            "text": "Can't Enroll",
            "color": "red",
            "textColor": "white"
        },
        'PENDING': {
            "text": "Applied",
            "color": "green",
            "textColor": "white"
        },
        'ACTIVE': {
            "text": "Enrolled!",
            "color": "blue",
            "textColor": "white"
        },
        '': {
            "text": "Quick Apply +",
            "color": "",
            "textColor": ""
        },
    }.get(users_enrollment_status, "")


def get_iq_programs(users_iq_program_statuses):
    programs = iqProgramQualifications.objects.all()
    for program in programs:
        iq_program = get_iq_program_info(users_iq_program_statuses, program.name)
        program.visibility = set_program_visibility(users_iq_program_statuses, program.name)
        program.button = build_qualification_button(iq_program['status_for_user'])
        program.status_for_user = iq_program['status_for_user']
        program.quick_apply_link = iq_program['quick_apply_link']
        program.learn_more_link = iq_program['learn_more_link']
        program.title = iq_program['title']
        program.description = iq_program['description']
        program.supplemental_info = iq_program['supplemental_info']
        program.eligibility_review_status = iq_program['eligibility_review_status']
        program.eligibility_review_time_period = iq_program['eligibility_review_time_period']
    return programs


def set_program_visibility(users_eligibility, program_name):
    if (users_eligibility.GenericQualified == QualificationStatus.PENDING.name or users_eligibility.GenericQualified == QualificationStatus.ACTIVE.name) and (users_eligibility.AmiRange_max <= iqProgramQualifications.objects.filter(name=program_name).values('percentAmi').first()['percentAmi']):
        return "block"
    else:
        return "none"


def get_iq_program_info(users_iq_program_status, program):
    return {
        'connexion': {
            'status_for_user': users_iq_program_status.ConnexionQualified,
            'quick_apply_link': reverse('application:ConnexionQuickApply'),
            'learn_more_link': 'https://www.fcgov.com/connexion/digital-equity',
            'title': 'Reduced-Rate Connexion',
            'subtitle': 'Connexion Assistance',
            'description': 'As Connexion comes online in neighborhoods across our community, the City of Fort Collins is committed to fast, affordable internet. Digital Access & Equity is an income-qualified rate of $19.95 per month for 1 gig-speed of internet plus wireless.',
            'supplemental_info': 'Applications accepted all year',
            'eligibility_review_status': "We are reviewing your application! Stay tuned here and check your email for updates." if users_iq_program_status.ConnexionQualified == 'PENDING' else "",
            'eligibility_review_time_period': "Estimated Notification Time: Two Weeks" if users_iq_program_status.ConnexionQualified == 'PENDING' else "",
        },
        'grocery': {
            'status_for_user': users_iq_program_status.GRqualified,
            'quick_apply_link': reverse('application:GRQuickApply'),
            'learn_more_link': 'https://www.fcgov.com/rebate/',
            'title': 'Grocery Tax Rebate',
            'subtitle': 'Food Assistance',
            'description': 'The Grocery Rebate Tax is an annual cash payment to low-income individuals and families living in the City of Fort Collins and its Growth Management Area. It provides your family with direct assistance in exchange for the taxes you spend on food.',
            'supplemental_info': 'Applications accepted all year',
            'eligibility_review_status': "We are reviewing your application! Stay tuned here and check your email for updates." if users_iq_program_status.GRqualified == 'PENDING' else "",
            'eligibility_review_time_period': "Estimated Notification Time: Two Weeks" if users_iq_program_status.GRqualified == 'PENDING' else "",
        },
        'recreation': {
            'status_for_user': users_iq_program_status.RecreationQualified,
            'quick_apply_link': reverse('application:RecreationQuickApply'),
            'learn_more_link': 'https://www.fcgov.com/recreation/reducedfeeprogram',
            'title': 'Recreation Reduced Fee',
            'subtitle': 'Recreation Assistance',
            'description': 'The Recreation Reduced Fee program provides income-eligible families and residents reduced cost access to recreation programs, classes, and facilities across the community.',
            'supplemental_info': 'Applications accepted all year',
            'eligibility_review_status': "We are reviewing your application! Stay tuned here and check your email for updates." if users_iq_program_status.RecreationQualified == 'PENDING' else "",
            'eligibility_review_time_period': "Estimated Notification Time: Two Weeks" if users_iq_program_status.RecreationQualified == 'PENDING' else "",
        },
        'spin': {
            'status_for_user': users_iq_program_status.SPINQualified,
            'quick_apply_link': "#",
            'learn_more_link': 'https://www.fcgov.com/fcmoves/spin',
            'title': 'Spin Access',
            'subtitle': 'Spin is Fort Collins\' e-bike and e-scooter share provider',
            'description': 'Through Spin Access, people with low income receive a discount for Spin rentals. No smartphone? With Spin Access, you can rent a Spin bike or scooter with text messaging. No credit/debit card? Contact FC Moves at rruhlen@fcgov.com or (970) 416-2040 to purchase Spin Cash cards.',
            'supplemental_info': 'Applications accepted all year',
            'eligibility_review_status': "We are reviewing your application! Stay tuned here and check your email for updates." if users_iq_program_status.SPINQualified == 'PENDING' else "",
            'eligibility_review_time_period': "Estimated Notification Time: Two Weeks" if users_iq_program_status.SPINQualified == 'PENDING' else "",
        },
    }.get(program)


def check_user_file_upload_progress(request, file_list):
    """Checks if user has uploaded all required documents
    params:
        request (object): Django request object
        file_list (dict): Dictionary of required documents and whether or not they have been uploaded
    Returns:
        uploads_complete (bool): True if all required documents have been uploaded, False otherwise
        file_list (dict): Dictionary of required documents and whether or not they have been uploaded
    """
    eligibility_programs = get_eligiblity_programs()
    # FYI: The array is order dependent. 0 = SNAP, 1 = PSD Reduced Lunch, 2 = ACP, 3 = ID, 4 = LEAP, etc. Feels like it
    # could be somewhat dangerous if the order of the programs in the database changes.
    checkAllForms = [not getattr(request.user.programs, program['eligibility_program']) for program in eligibility_programs]
    for i, group in enumerate(request.user.files.all()):
        for program in eligibility_programs:
            if group.document_title == program['document_title']:
                checkAllForms[i] = True
                file_list[program['document_description']] = False
                break

    uploads_complete = all(checkAllForms)
    return uploads_complete, file_list


def get_eligiblity_programs():
    """Returns a list of eligibility programs. This is just a shim for now
    and will eventually be replaced by a call to the database through Django's ORM
    Returns:
        list: List of eligibility programs
    """
    return [
        {
            'eligibility_program': 'snap',
            'document_title': 'SNAP',
            'document_description': 'SNAP Card',
            'get_ready_text': 'SNAP Card',
        },
        {
            'eligibility_program': 'freeReducedLunch',
            'document_title': 'Free and Reduced Lunch',
            'document_description': 'PSD Reduced Lunch Approval Letter',
            'get_ready_text': 'Poudre School District Letter (per child!)',
        },
        {
            'eligibility_program': 'ebb_acf',
            'document_title': 'ACP Letter',
            'document_description': 'Affordable Connectivity Program',
            'get_ready_text': 'Affordable Connectivity Program or Emergency Broadband Benefit Confirmation',
        },
        {
            'eligibility_program': 'Identification',
            'document_title': 'Identification',
            'document_description': 'Identification',
            'get_ready_text': 'Government Issued ID',
        },
        {
            'eligibility_program': 'leap',
            'document_title': 'LEAP Letter',
            'document_description': 'LEAP Letter',
            'get_ready_text': 'LEAP Letter',
        },
        {
            'eligibility_program': 'medicaid',
            'document_title': 'Medicaid',
            'document_description': 'Medicaid Card',
            'get_ready_text': 'Medicaid Card',
        },
    ]


def get_users_eligiblity_programs(request):
    """Returns a dictionary of eligibility programs and whether or not the user selected
    the programs they can upload documents for.
    params:
        request (object): Django request object
    Returns:
        file_list (dict): Dictionary of eligibility programs and whether or not the user selected them
    """
    eligibility_programs = get_eligiblity_programs()
    file_list = {}
    for program in eligibility_programs:
        file_list[program['document_description']] = getattr(request.user.programs, program['eligibility_program'])
    return file_list
