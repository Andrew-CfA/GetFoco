"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version
"""
from django.shortcuts import render, redirect, reverse
from django.core.exceptions import ObjectDoesNotExist

# Grace User Authentication
from django.contrib.auth.backends import ModelBackend, UserModel
from django.contrib.auth import get_user_model, login, authenticate, logout
from django.contrib.auth.hashers import check_password

from django.conf import settings

#below imports needed for blob storage
from azure.storage.blob import BlockBlobService

from .models import User


def blobStorageUpload(filename, file):
    blob_service_client = BlockBlobService(
        account_name=settings.ACCOUNT_NAME,
        account_key=settings.ACCOUNT_KEY,
        endpoint_suffix=settings.FILESTORE_ENDPOINT_SUFFIX,
        )
    
    blob_service_client.create_blob_from_bytes(
        container_name = settings.CONTAINER_NAME,
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

def files_to_string(file_list, request):
    list_string = ""
    counter = 0

    print(counter)
    # Get File_List into easy to read list to print out in template
    for key, value in file_list.items():
        # only add things to the list_string if its true
        if value == True:
            # Also add commas based on counter
            if counter == 4:
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
                counter = 4
            list_string += key
    return list_string

# redirect user to whatever page they need to go to every time by checking which steps they've
# completed in the application process
def what_page(user,request):
    if user.is_authenticated:
        #for some reason, none of these login correctly... reviewing this now
        try:
            value = request.user.addresses
        except AttributeError:
            return "application:address"

        try:
            value = request.user.eligibility
        except AttributeError:
            return "application:finances"
        
        try:
            value = request.user.programs
        except AttributeError or ObjectDoesNotExist:
            return "application:programs"
        
        try:
            print('Num files is', request.user.files.all()) #Check for all files per how many programs the client selected
            value = request.user.files.all()
            if not value.exists():
               print("object doesn't exist")
               return "dashboard:files"
            else:
                print("object exists")
        except AttributeError:
            return "dashboard:files"
        
        return "dashboard:dashboard"

    else:
        return "application:account"