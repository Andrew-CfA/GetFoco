"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version
"""
import json
from django.shortcuts import render, redirect, reverse
from django.core.serializers.json import DjangoJSONEncoder

from application.models import iqProgramQualifications
from .forms import FileForm, FeedbackForm, TaxForm, addressVerificationForm, AddressForm
from django.conf import settings as django_settings  

from .backend import authenticate, files_to_string, get_iq_program, set_users_gr_qualification_status, what_page, blobStorageUpload, build_qualification_button, set_program_visibility
from django.contrib.auth import get_user_model, login, authenticate
from application.backend import broadcast_email, broadcast_sms, broadcast_email_pw_reset

from django.db import IntegrityError

from py_models.qualification_status import QualificationStatus
import logging


from django.shortcuts import render, redirect
from django.core.mail import BadHeaderError
from django.http import HttpResponse
from django.contrib.auth.forms import PasswordResetForm
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes

import magic, datetime


#Step 4 of Application Process
def files(request):
    file_list = {
        "Affordable Connectivity Program": request.user.programs.ebb_acf,
        "Identification": request.user.programs.Identification,
        "LEAP Letter": request.user.programs.leap,
        "Medicaid Card": request.user.programs.medicaid,
        "PSD Reduced Lunch Approval Letter": request.user.programs.freeReducedLunch,
        "SNAP Card": request.user.programs.snap,
    }
    '''
    Variables:
    fileNames - used to name the files in the database and file upload
    fileAmount - number of file uploads per income verified documentation
    '''
    if request.method == "POST":
         # Check the user's session variables to see if they have a first_time_file_upload variable
        # If they don't have it, create the variable and set it to True
        if 'first_time_file_upload' not in request.session:
            request.session['first_time_file_upload'] = True
        else:
            request.session['first_time_file_upload'] = False
        form = FileForm(request.POST, request.FILES)
        if form.is_valid():
            print(form)
            if request.user.is_authenticated:
                instance = form.save(commit=False)
                instance.user_id = request.user
                fileNames=[]
                fileAmount = 0
                #process is as follows:
                # 1) file is physically saved from the buffer
                # 2) file is then SCANNED using magic
                # 3) file is then deleted or nothing happens if magic sees it's ok

                #update, magic no longer needs to scan from saved file, can now scan from buffer! so with this in mind
                '''
                1) For loop #1 file(s) scanned first
                2) For Loop #2 file saved if file(s) are valid
                '''
                for f in request.FILES.getlist('document'):
                    #fileValidation found below
                    #filetype = magic.from_file("mobileVers/" + instance.document.url)
                    filetype = magic.from_buffer(f.read())
                    logging.info(filetype)
                    if "PNG" in filetype:
                        pass
                    elif "JPEG" in filetype:
                        pass
                    elif "JPG" in filetype:
                        pass
                    elif "PDF" in filetype:
                        pass
                    else:
                        logging.error("File is not a valid file type. file is: " + filetype)
                        if instance.document_title == "LEAP Letter":
                            file_list = "LEAP Letter"
                        if instance.document_title == "SNAP":
                            file_list = "SNAP Card"
                        if instance.document_title == "Free and Reduced Lunch":
                            file_list = "PSD Reduced Lunch Approval Letter"
                        if instance.document_title == "ACP Letter":
                            file_list = "Affordable Connectivity Program"
                        if instance.document_title == "Identification":
                            file_list = "Identification"
                        if instance.document_title == "Medicaid":
                            file_list = "Medicaid Card"
                        return render(
                            request,
                            'dashboard/files.html',
                            {
                                "message": "File is not a valid file type. Please upload either  JPG, PNG, OR PDF.",
                                'form':form,
                                'programs': file_list,
                                'program_string': file_list,
                                'step':5,
                                'formPageNum':6,
                                'Title': "Files",
                                'file_upload': json.dumps({'success_status': False}),
                                'is_prod': django_settings.IS_PROD,
                                },
                            )
                    
                for f in request.FILES.getlist('document'):
                    fileAmount += 1
                    instance.document.save( datetime.datetime.now().isoformat() + "_" + str(fileAmount) + "_" + str(f),f) # this line allows us to save multiple files: format = iso format (f,f) = (name of file, actual file)
                    fileNames.append(str(instance.document))
                    file_upload = request.user
                    file_upload.files.add(instance)
                    #Below is blob / storage code for Azure! Files automatically uploaded to the storage
                    f.seek(0)
                    blobStorageUpload(str(instance.document.url), f)
            
                #below the code to update the database to allow for MULTIPLE files AND change the name of the database upload!
                instance.document = str(fileNames)
                instance.save()
                
                
                # Check if the user needs to upload another form
                Forms = request.user.files
                checkAllForms = [not(request.user.programs.snap),not(request.user.programs.freeReducedLunch),not(request.user.programs.ebb_acf),not(request.user.programs.Identification),not(request.user.programs.leap),not(request.user.programs.medicaid),]
                for group in Forms.all():
                    if group.document_title == "SNAP":
                        checkAllForms[0] = True
                        file_list["SNAP Card"] = False
                    if group.document_title == "Free and Reduced Lunch":
                        checkAllForms[1] = True
                        file_list["PSD Reduced Lunch Approval Letter"] = False
                    if group.document_title == "ACP Letter":
                        checkAllForms[2] = True
                        file_list["Affordable Connectivity Program"] = False
                    if group.document_title == "Identification":
                        checkAllForms[3] = True
                        file_list["Identification"] = False
                    if group.document_title == "LEAP Letter":
                        checkAllForms[4] = True
                        file_list["LEAP Letter"] = False
                    if group.document_title == "Medicaid":
                        checkAllForms[5] = True
                        file_list["Medicaid Card"] = False
                if False in checkAllForms:
                    return render(
                        request,
                        'dashboard/files.html',
                        {
                            'form':form,
                            'programs': file_list,
                            'program_string': files_to_string(file_list),
                            'step':5,
                            'formPageNum':6,
                            'Title': "Files",
                            'file_upload': json.dumps({'success_status': True}),
                            'is_prod': django_settings.IS_PROD,
                            },
                        )
                
                # if affordable connectivity program is chosen
                elif request.user.programs.ebb_acf == True:
                    return redirect(reverse("application:filesInfoNeeded"))
                else:
                    return redirect(reverse("dashboard:broadcast")) 
            else:
                print("notautnehticated")
                # TODO: Change this link
                return render(
                    request,
                    'dashboard/layout.html',
                    {
                        'is_prod': django_settings.IS_PROD,
                        },
                    )
    else:
        print(request.user)
        # Check the user's session variables to see if they have a first_time_file_upload variable
        # If they don't have it, create the variable and set it to True
        if 'first_time_file_upload' not in request.session:
            request.session['first_time_file_upload'] = True
        else:
            request.session['first_time_file_upload'] = False
        form = FileForm()
    print(file_list)
    return render(
        request,
        'dashboard/files.html',
        {
            'form':form,
            'programs': file_list,
            'program_string': files_to_string(file_list),
            'step':5,
            'formPageNum':6,
            'Title': "Files",
            'file_upload': json.dumps({'success_status': None}),
            'is_prod': django_settings.IS_PROD,
            },
        )



def addressVerification(request):
    if request.method == "POST":
        try:
            existing = request.user.addressverification
            form = addressVerificationForm(request.POST,instance = existing)
        except AttributeError or ObjectDoesNotExist:
            form = addressVerificationForm(request.POST or None)
        if form.is_valid():
            print(form.data)
            print(request.session)
            try:
                instance = form.save(commit=False)
                instance.user_id = request.user
                instance.save()
                return redirect(reverse("dashboard:filesContinued"))
            except IntegrityError:
                print("User already has information filled out for this section")
            return redirect(reverse("application:available"))

    else:
        form = addressVerificationForm()

    return render(
        request,
        'dashboard/addressVerification.html',
        {
            'form':form,
            'step':1,
            'formPageNum':"2 - Recreation Reduced Fee",
            'Title': "Address Verification",
            'is_prod': django_settings.IS_PROD,
            },
        )

#    else:
#        return redirect(reverse(page))
    #return render(request, 'application/programs.html',)






def filesContinued(request):
    file_list = {   #"Identification": request.user.addressverification.Identification,
                    "Utility Bill": request.user.addressverification.Utility,
                    #"PSD Reduced Lunch Approval Letter": request.user.addressverification.freeReducedLunch,
    }

    if request.method == "POST":   
        form = AddressForm(request.POST, request.FILES)
        if form.is_valid():
            print(form)  
            if request.user.is_authenticated:
                instance = form.save(commit=False)
                instance.user_id = request.user
                fileList = []
                fileNames=[]
                fileAmount = 0
                '''
                1) For loop #1 file(s) scanned first
                2) For Loop #2 file saved if file(s) are valid
                '''

                for f in request.FILES.getlist('document'):
                    #fileValidation found below
                    #filetype = magic.from_file("mobileVers/" + instance.document.url)
                    filetype = magic.from_buffer(f.read())
                    logging.info(filetype)
                    if "PNG" in filetype:
                        pass
                    elif "JPEG" in filetype:
                        pass
                    elif "JPG" in filetype:
                        pass
                    elif "PDF" in filetype:
                        pass
                    else:
                        logging.error("File is not a valid file type. file is: " + filetype)
                        if instance.document_title == "Utility":
                            file_list = "Utility Bill"
                        return render(request,'dashboard/filesContinued.html',
                            {
                                "message": "File is not a valid file type. Please upload either  JPG, PNG, OR PDF.",
                                'form':form,
                                'programs': file_list,
                                'program_string': file_list,
                                'step':2,
                                'formPageNum':2,
                                'Title': "Files Continued",
                                'is_prod': django_settings.IS_PROD,
                                },
                            )

                for f in request.FILES.getlist('document'):
                    fileAmount += 1
                    fileList.append(str(fileAmount))
                    instance.document.save( datetime.datetime.now().isoformat() + "_" + str(fileAmount) + "_" + str(f),f) # this line allows us to save multiple files: format = iso format (f,f) = (name of file, actual file)
                    fileNames.append(str(instance.document))
                    file_upload = request.user
                    file_upload.address_files.add(instance)
                    #Below is blob / storage code for Azure! Files automatically uploaded to the storage
                    f.seek(0)
                    blobStorageUpload(str(instance.document.url), f)

                #below the code to update the database to allow for MULTIPLE files AND change the name of the database upload!
                #instance.document = str(request.user.email)+  str(fileList) this saves with email appeneded to number of files
                instance.document = str(fileNames) 
                instance.save()
                
                # Check if the user needs to upload another form
                Forms = request.user.address_files
                checkAllForms = [not(request.user.addressverification.Utility)] #not(request.user.addressverification.Identification), ,not(request.user.addressverification.freeReducedLunch),
                for group in Forms.all():
                    if group.document_title == "Utility":
                        checkAllForms[0] = True
                        file_list["Utility Bill"] = False
                ''' 
                    if group.document_title == "Identification":
                        checkAllForms[0] = True
                        file_list["Identification"] = False
                    if group.document_title == "Free and Reduced Lunch": 
                        checkAllForms[2] = True
                        file_list["PSD Reduced Lunch Approval Letter"] = False'''

                if False in checkAllForms:
                    return render(
                        request,
                        'dashboard/filesContinued.html',
                        {
                            'form':form,
                            'programs': file_list,
                            'program_string': files_to_string(file_list),
                            'step':2,
                            'formPageNum':2,
                            'Title': "Files Continued",
                            'is_prod': django_settings.IS_PROD,
                            },
                        )
                return redirect(reverse("application:RecreationQuickApply")) 
            else:
                print("notautnehticated")
                # TODO: Change this link
                return render(
                    request,
                    'dashboard/layout.html',
                    {
                        'is_prod': django_settings.IS_PROD,
                        },
                    )
    else:
        form = AddressForm()
    print(file_list)
    return render(
        request,
        'dashboard/filesContinued.html',
        {
            'form':form,
            'programs': file_list,
            'program_string': files_to_string(file_list),
            'step':2,
            'formPageNum':"2 - Recreation Reduced Fee",
            'Title': "Files Continued",
            'is_prod': django_settings.IS_PROD,
            },
        )

def broadcast(request):
    print(request.user.files.all()[0])
    current_user = request.user
    try:    
        broadcast_email(current_user.email)
    except:
        logging.error("there was a problem with sending the email / sendgrid")
        #TODO store / save for later: client getting feedback that SendGrid may be down 
    phone = str(current_user.phone_number)
    try:
        broadcast_sms(phone)
    except:
        logging.error("Twilio servers may be down")
        #TODO store / save for later: client getting feedback that twilio may be down 
    return render(
        request,
        'dashboard/broadcast.html',
        {
            'program_string': current_user.email,
            'step':6,
            'formPageNum':6,
            'Title': "Broadcast",
            'is_prod': django_settings.IS_PROD,
            },
        )


def index(request):
    #active_program_count = Program.objects..wherecurrent_user.
    return render(request, 'dashboard/index.html', #{
   #     "active_program_count": active_program_count}
    )
    #return render(request, 'dashboard/index.html', {
    #    'program_string':current_user.email
    #})


def settings(request):
    # Get the success query string parameter
    page_updated = request.GET.get('page_updated')
    if page_updated:
        request.session['page_updated'] = page_updated
        return redirect(reverse('dashboard:settings'))

    if 'page_updated' in request.session:
        page_updated = request.session.get('page_updated')
        del request.session['page_updated']
    else:
        page_updated = None

    return render(
        request,
        'dashboard/settings.html',
        {
            "name": request.user.first_name,
            "lastName": request.user.last_name,
            "email": request.user.email,
            "address": request.user.addresses.address,
            "address2": request.user.addresses.address2,
            "zipCode": request.user.addresses.zipCode,
            "state": request.user.addresses.state,
            "password": request.user.password,
            "phoneNumber": request.user.phone_number,
            'is_prod': django_settings.IS_PROD,
            "routes": {
                    "account": reverse('application:account'),
                    "finances": reverse('application:finances'),
                },
            "page_updated": json.dumps({'page_updated': page_updated}, cls=DjangoJSONEncoder),
            },
        )


def password_reset_request(request):
    User = get_user_model()
    if request.method == "POST":
        password_reset_form = PasswordResetForm(request.POST)
        if password_reset_form.is_valid():
            data = password_reset_form.cleaned_data['email']
            associated_users = User.objects.filter(Q(email=data))
            if associated_users.exists():
                for user in associated_users:
                    subject = "Password Reset Requested"
                    email_template_name = "dashboard/PasswordReset/password_reset_email.txt"
                    c = {
                        "email":user.email,
                        'domain':'getfoco.fcgov.com', #'getfoco.azurewebsites.net' | '127.0.0.1:8000'
                        'site_name': 'Get FoCo',
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "user": user,
                        'token': default_token_generator.make_token(user),
                        'protocol': 'http',
					}
                    email = render_to_string(email_template_name, c)
                    try:
#                        send_mail(subject, email, 'admin@example.com' , [user.email], fail_silently=False)
                        broadcast_email_pw_reset(user.email, email)
                    except BadHeaderError:
                        return HttpResponse('Invalid header found.')
                    return redirect ("/password_reset/done/")
    password_reset_form = PasswordResetForm()

    return render(
        request,
        "dashboard/PasswordReset/passwordReset.html",
        {
            "password_reset_form":password_reset_form,
            'Title': "Password Reset Request",
            'is_prod': django_settings.IS_PROD,
            },
        )


def login_user(request):
    if request.method == "POST":
        # Try to log in user
        email = request.POST["email"]
        password = request.POST["password"]
        user = authenticate(username=email, password=password)
        # Check if the authentication was successful
        if user is not None:
            login(request, user)
            # Push user to correct page
            #update application_user "modified" per login
            obj = request.user
            obj.modified = datetime.datetime.now(datetime.timezone.utc)
            obj.save()
            # Push user to correct page
            page = what_page(request.user, request)
            print(page)
            if page == "dashboard:dashboard":
                return redirect(reverse("dashboard:dashboard"))
            else:
                return redirect(reverse("dashboard:notifyRemaining"))

        else:
            return render(
                request,
                "dashboard/login.html",
                {
                    "message": "Invalid username and/or password",
                    'Title': "Login",
                    'is_prod': django_settings.IS_PROD,
                    },
                )
    
    # If it turns out user is already logged in but is trying to log in again,
    # run through what_page() to find the correct place
    if request.method == "GET" and request.user.is_authenticated:
        page = what_page(request.user, request)
        print(page)
        if page == "dashboard:dashboard":
            return redirect(reverse("dashboard:dashboard"))
        else:
            return redirect(reverse("dashboard:notifyRemaining"))

    # Just give back log in page if none of the above is true
    else:
        return render(
            request,
            "dashboard/login.html",
            {
                'Title': "Login",
                'is_prod': django_settings.IS_PROD,
                },
            )

def notifyRemaining(request):    
    page = what_page(request.user, request)
    return render(
        request,
        "dashboard/notifyRemaining.html",
        {
            "next_page": page,
            'Title': "Notify Remaining Steps",
            'is_prod': django_settings.IS_PROD,
            },
        )


def qualifiedPrograms(request):
    # Query the database for all programs
    programs = iqProgramQualifications.objects.all()
    for program in programs:
        iq_program = get_iq_program(request.user.eligibility, program.name)
        program.visibility = set_program_visibility(request.user.eligibility, program.name)
        program.button = build_qualification_button(iq_program['status_for_user'])
        program.status_for_user = iq_program['status_for_user']
        program.quick_apply_link = iq_program['quick_apply_link']
        program.learn_more_link = iq_program['learn_more_link']
        program.title = iq_program['title']
        program.subtitle = iq_program['subtitle']
        program.supplemental_info = iq_program['supplemental_info']

    # NOTE: This same function is called in the dashboardGetFoco view function. To me this logic should be executed a user
    # has after provides their financial information. This would happen after they initially fill out their application, 
    # after they updated it from their settings, or when they go through the renewal process.
    set_users_gr_qualification_status(request)

    order_by = request.GET.get('order_by')
    if order_by and order_by == 'eligible':
        programs = sorted(programs, key=lambda x: (x.status_for_user, x.status_for_user))
    elif order_by:
        programs = sorted(programs, key=lambda x: (x.status_for_user.lower() != order_by, x.status_for_user))

    return render(
        request,
        'dashboard/qualifiedPrograms.html',
        {
            "Title": "Qualified Programs",
            "dashboard_color": "white",
            "program_list_color": "var(--yellow)",
            "FAQ_color": "white",
            "Settings_color": "white",
            "Privacy_Policy_color": "white",
            "iq_programs": programs,
            'is_prod': django_settings.IS_PROD,
        },
    )

 
def feedback(request):
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse("dashboard:feedbackReceived"))
        else:
            print("form is not valid")
    else:
        form = FeedbackForm()
    if request.user.eligibility.GenericQualified == QualificationStatus.PENDING.name or request.user.eligibility.GenericQualified == QualificationStatus.ACTIVE.name:
        text = "Based on your information, you may qualify! Be on the lookout for an email or phone call."
        text2 = "Based on your information you may also qualify for the city's Grocery Rebate Tax program!"
        text3 = "By clicking on the link below, we can send your information over and quick apply for you."
        text4 = "Click here to quick apply for Grocery Rebate Tax Program"
        text5 = ""
        text6 = "Click here to quick apply for Recreation"
        text7 = "The Get FoCo Office is working on a timeline to respond to applications within the next two weeks."
    else:
        text = "Based on your info, you may be over the pre-tax income limit. At this time you do not qualify. If your income changes, please apply again."
        text2 = ""
        text3 = ""
        text4 = ""
        text5 = "Grocery Rebate Tax Program"
        text6 = "Utilities Income-Qualified Assistance Program"
        text7 = "The Get FoCo Office is working on a timeline to respond to applications within the next two weeks."
    
    if request.user.eligibility.GRqualified == QualificationStatus.PENDING.name or request.user.eligibility.GRqualified == QualificationStatus.ACTIVE.name:
        text2 = "Thank you for quick applying for the Grocery Rebate Tax Program."
        text3 = "Expect an update within 3 weeks - check your email!"
        text4 = ""


    return render(
        request,
        'dashboard/index.html',
        context={
            "program_string": text,
            "program_string2": text2,
            "program_string3": text3,
            "program_string4": text4,
            "program_string5": text5,
            "program_string6": text6,
            "program_string7": text7,
            'Title': "Feedback",
            'is_prod': django_settings.IS_PROD,
            },
        )


def manualVerifyIncome(request):
    if request.method == "POST": 
        try:
            existing = request.user.TaxInformation
            form = TaxForm(request.POST,instance = existing)
        except AttributeError or ObjectDoesNotExist:
            form = TaxForm(request.POST or None)
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
        else:
            form = TaxForm()
    return render(
        request,
        "dashboard/manualVerifyIncome.html",
        {
            'step':5,
            'formPageNum':6,
            'Title': "Input Income",
            'is_prod': django_settings.IS_PROD,
            },
        )

def feedbackReceived(request):
    return render(
        request,
        "dashboard/feedbackReceived.html",
        {
            'Title': "Feedback Received",
            'is_prod': django_settings.IS_PROD,
            },
        )

def underConstruction(request):
    return render(
        request,
        "dashboard/underConstruction.html",
        {
            'Title': "Under Construction",
            'is_prod': django_settings.IS_PROD,
            },
        )
    

# Everything under here is for new dashboard
def dashboardGetFoco(request):
    QProgramNumber = 0
    ActiveNumber = 0
    PendingNumber = 0

    programs = iqProgramQualifications.objects.all()
    for program in programs:
        iq_program = get_iq_program(request.user.eligibility, program.name)
        program.visibility = set_program_visibility(request.user.eligibility, program.name)
        program.button = build_qualification_button(iq_program['status_for_user'])
        program.status_for_user = iq_program['status_for_user']
        program.quick_apply_link = iq_program['quick_apply_link']
        program.learn_more_link = iq_program['learn_more_link']
        program.title = iq_program['title']
        program.description = iq_program['description']
        program.supplemental_info = iq_program['supplemental_info']
        program.eligibility_review_status = iq_program['eligibility_review_status']
        program.eligibility_review_time_period = iq_program['eligibility_review_time_period']

        # If the program's visibility is 'block' or the status is `ACTIVE` or `PENDING`, it means the user is eligible for the program
        # so we'll count it for their total number of programs they qualify for
        if program.visibility == "block" or program.status_for_user == 'ACTIVE' or program.status_for_user == 'PENDING':
            QProgramNumber += 1

    # NOTE: This same function is called in the qualifiedPrograms view function. To me this logic should be executed a user
    # has after provides their financial information. This would happen after they initially fill out their application, 
    # after they updated it from their settings, or when they go through the renewal process.
    set_users_gr_qualification_status(request)

    for program in programs:
        # If a program's status_for_user is 'PENDING' add 1 to the pending number and subtract 1 from the QProgramNumber
        if program.status_for_user == 'PENDING':
            PendingNumber += 1
            QProgramNumber -= 1
        # If a program's status_for_user is 'ACTIVE' add 1 to the active number and subtract 1 from the QProgramNumber
        elif program.status_for_user == 'ACTIVE':
            ActiveNumber += 1
            QProgramNumber -= 1
        # If a program's status_for_user is 'NOT QUALIFIED' subtract 1 to the QProgramNumber
        elif program.status_for_user == 'NOT QUALIFIED':
            QProgramNumber -= 1

    # By default we assume the user has viewed the dashboard, but if they haven't
    # we set the proxy_viewed_dashboard flag to false and update the user
    # in the database to say that they have viewed the dashboard. This obviates
    # the need to create some AJAX call to a Django template to update the database 
    # when the user views the dashboard.
    proxy_viewed_dashboard = True
    if request.user.has_viewed_dashboard == False:
        proxy_viewed_dashboard = False
        request.user.has_viewed_dashboard = True
        request.user.save()

    return render(
        request,
        'dashboard/dashboard_GetFoco.html',
        {
            "Title": "Get FoCo Dashboard",
            "dashboard_color": "var(--yellow)",
            "program_list_color": "white",
            "FAQ_color": "white",
            "Settings_color": "white",
            "Privacy_Policy_color": "white",
            "Bag_It_color": "white",
            "iq_programs": programs,
            "QProgramNumber":QProgramNumber,
            "PendingNumber":PendingNumber,
            "ActiveNumber":ActiveNumber,
            "clientName": request.user.first_name,
            "clientEmail": request.user.email,

            'is_prod': django_settings.IS_PROD,
            'max_ami': request.user.eligibility.AmiRange_max,
            'eligibility': request.user.eligibility.GenericQualified,
            'proxy_viewed_dashboard': proxy_viewed_dashboard,
        },
    )

def ProgramsList(request):
        # Query the database for all programs
    programs = iqProgramQualifications.objects.all()
    for program in programs:
        iq_program = get_iq_program(request.user.eligibility, program.name)
        program.visibility = set_program_visibility(request.user.eligibility, program.name)
        program.button = build_qualification_button(iq_program['status_for_user'])
        program.status_for_user = iq_program['status_for_user']
        program.quick_apply_link = iq_program['quick_apply_link']
        program.learn_more_link = iq_program['learn_more_link']
        program.title = iq_program['title']
        program.subtitle = iq_program['subtitle']
        program.description = iq_program['description']
        program.supplemental_info = iq_program['supplemental_info']

    return render(
        request,
        'dashboard/ProgramsList.html',
        {
            "page_title": "Programs List",
            "dashboard_color": "white",
            "program_list_color": "var(--yellow)",
            "FAQ_color": "white",
            "Settings_color": "white",
            "Privacy_Policy_color": "white",
            "Bag_It_color": "white",
            'Title': "Programs List",
            'is_prod': django_settings.IS_PROD,
            'iq_programs': programs,
            },
        )

def BagIt(request):
    return render(
        request,
        'dashboard/BagIt.html',
        {
            "page_title": "Bag It",
            "dashboard_color": "white",
            "program_list_color": "white",
            "FAQ_color": "white",
            "Settings_color": "white",
            "Privacy_Policy_color": "white",
            "Bag_It_color": "var(--yellow)",
            'Title': "Bag It",
            'lastName': request.user.last_name,
            'date': datetime.datetime.now().date(),
            'is_prod': django_settings.IS_PROD,
            },
        )


def FAQ(request):
    return render(
        request,
        'dashboard/FAQ.html',
        {
            "page_title": "FAQ",
            "dashboard_color": "white",
            "program_list_color": "white",
            "FAQ_color": "var(--yellow)",
            "Settings_color": "white",
            "Privacy_Policy_color": "white",
            "Bag_It_color": "white",
            'Title': "FAQ",
            'is_prod': django_settings.IS_PROD,
            },
        )
