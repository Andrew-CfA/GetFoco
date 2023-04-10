"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version
"""

'''
Here you'll find some useful backend logic / functions used in the main application, most of these functions are used to 
supplement the application and to keep views.py clutter to a minimum!
'''
import ast
import json
from usps import USPSApi, Address
import re
import requests
from django import http  # used for type checks
import datetime

import urllib.parse
import requests

#Andrew backend code for Twilio
from twilio.rest import Client
from django.conf import settings    
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.core.serializers.json import DjangoJSONEncoder


def broadcast_sms(phone_Number):
    message_to_broadcast = ("Thank you for creating an account with Get FoCo! Be sure to review the programs you qualify for on your dashboard and click on Quick Apply to finish the application process!")
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    client.messages.create(to=phone_Number,
                            from_=settings.TWILIO_NUMBER,
                            body=message_to_broadcast)


def addressCheck(address_dict):
    """
    Check for address GMA and Connexion statuses.

    Parameters
    ----------
    instance : dict
        Post-USPS-validation dictionary. Usable data for this script are in
        ['AddressValidateResponse']['Address'][...].

    Returns
    -------
    bool
        Whether the address is in the GMA (True, False).
    bool
        The status of Connexion service (True, False, None).

    """
    
    try:
        # Gather the coordinate string for future queries
        # Parse the 'instance' data for proper 'address_parts'
        address_parts = "{}, {}".format(
            address_dict['AddressValidateResponse']['Address']['Address2'],
            address_dict['AddressValidateResponse']['Address']['Zip5'],
            )
        coordString = address_lookup(address_parts)
        
    except NameError:   # NameError specifies that the address is not found
                        # in City lookups and is therefore not in the IQ
                        # service area           
        return (False, False)
    
    else:
        # Alternatively:
            # hasConnexion = connexion_lookup(address_lookup(address_parts))
        hasConnexion = connexion_lookup(coordString)
        print('No Connexion for you') if hasConnexion is None else print('Connexion available') if hasConnexion else print('Connexion coming soon')
        
        # Alternatively:
            # isInGMA = gma_lookup(address_lookup(address_parts))
        isInGMA = gma_lookup(coordString)
        print('Is in GMA!') if isInGMA else print('Outside of GMA')

        return (isInGMA, hasConnexion)
    

def address_lookup(address_parts):
    """
    Look up the coordinates for an address to input into future queries.

    Parameters
    ----------
    address_parts : str
        The address parts to use for the lookup (specifically in the format
        <address_2>, <zip code>) (e.g. "300 LAPORTE AVE, 80521", sans quotes).

    Raises
    ------
    requests.exceptions.HTTPError
        An issue with the lookup endpoint.
    NameError
        Address not found in City lookups - address is not in IQ service area.

    Returns
    -------
    str
        Formatted string of x,y coordinates for the address, to input in
        future queries.

    """
    
    url = 'https://gisweb.fcgov.com/arcgis/rest/services/Geocode/Fort_Collins_Area_Address_Point_Geocoding_Service/GeocodeServer/findAddressCandidates'
    
    payload={
        'f': 'pjson',
        'Street': address_parts,
        }
    
    # Gather response
    response = requests.get(url, params=payload)
    if response.status_code!=requests.codes.ok:
        raise requests.exceptions.HTTPError(response.reason,response.content)
        
    # Parse response
    outVal = response.json()
    
    # Ensure candidate(s) exist and they have a decent match score
    # Because this is how the Sales Tax lookup is architected, it should be
    # safe to assume these are returned sorted, with best candidate first
    if len(outVal['candidates']) > 0 and outVal['candidates'][0]['score'] > 85:
        # Define the coordinate string to be used in future queries
        coordString = '{x},{y}'.format(
            x=outVal['candidates'][0]['location']['x'],
            y=outVal['candidates'][0]['location']['y'],
            )
        
    else:
        raise NameError("Matching address not found")
    
    return coordString 


def connexion_lookup(coord_string):
    """
    Look up the Connexion service status given the coordinate string.

    Parameters
    ----------
    coord_string : str
        Formatted <x>,<y> string of coordinates from address_lookup().
        
    Raises
    ------
    requests.exceptions.HTTPError
        An issue with the lookup endpoint.
    IndexError
        Address not found in Connexion lookups - Connexion is likely to be
        unavailable at this address.

    Returns
    -------
    bool
        Boolean 'status', designating True for 'service available' or False
        for 'service will be available, but not yet' OR None for 'unavailable'
        (probably)
    
    TODO: Switch this to an enum if we want to keep this structure

    """
    
    url = 'https://gisweb.fcgov.com/arcgis/rest/services/FDH_Boundaries_ForPublic/MapServer/0/query'
    
    payload={
        'f': 'pjson',
        'geometryType': 'esriGeometryPoint',
        'geometry': coord_string,
        }
    
    # Gather response
    response = requests.post(url, params=payload)
    if response.status_code!=requests.codes.ok:
        raise requests.exceptions.HTTPError(response.reason,response.content)
        
    # Parse response
    outVal = response.json()
    
    try:
        statusInput = outVal['features'][0]['attributes']['INVENTORY_STATUS_CODE']
        
    except (IndexError, KeyError):
        return None
    
    else:
        statusInput = statusInput.lower()
        
        # If we made it to this point, Connexion will be or is currently
        # available
        if statusInput in (
                'released',
                'out of warranty',                
                ):      # this is the 'available' case
            return True
        
        else:
            return False
         
        
def gma_lookup(coord_string):
    """
    Look up the GMA location given the coordinate string.

    Parameters
    ----------
    coord_string : str
        Formatted <x>,<y> string of coordinates from address_lookup().
        
    Raises
    ------
    requests.exceptions.HTTPError
        An issue with the lookup endpoint.    

    Returns
    -------
    Boolean 'status', designating True for an address within the GMA, or False
    otherwise.

    """
    
    url = 'https://gisweb.fcgov.com/arcgis/rest/services/FCMaps/MapServer/26/query'
    
    payload={
        # Manually stringify 'geometry' - requests and json.dumps do this
        # incorrectly
        'geometry': """{"points":[["""+coord_string+"""]],"spatialReference":{"wkid":102653}}""",
        'geometryType': 'esriGeometryMultipoint',
        'inSR': 2231,
        'spatialRel': 'esriSpatialRelIntersects',
        'where': '',
        'returnGeometry': 'false',
        'outSR': 2231,
        'outFields': '*',
        'f': 'pjson',
        }
    
    # Gather response
    response = requests.get(url, params=payload)
    if response.status_code!=requests.codes.ok:
        raise requests.exceptions.HTTPError(response.reason,response.content)    
        
    # Parse response
    outVal = response.json()

    if len(outVal['features']) > 0:
        return True
    else:
        return False
    
def enroll_connexion_updates(request):
    """
    Enroll a user in Connexion service update emails.

    Parameters
    ----------
    request : django.core.handlers.wsgi.WSGIRequest
        User request for the calling page, to be passed through to this
        function.

    Raises
    ------
    AssertionError
        Designates a failure when writing to the Connexion-update service.

    Returns
    -------
    None. No return designates a successful write to the service.

    """
    
    usr = request.user
    addr = request.user.addresses
    
    print(usr.email)
    print(usr.phone_number.national_number)
    print("{ad}, {zc}".format(ad=addr.address, zc=addr.zipCode))

    url = "https://www.fcgov.com/webservices/codeforamerica/"
    params = {
        'email': usr.email,
        # Retrieve just the 10-digit phone number
        'phone': usr.phone_number.national_number,
        # Create an address string recognized by the City system
        'address': "{ad}, {zc}".format(ad=addr.address, zc=addr.zipCode),
        }
    payload = urllib.parse.urlencode(params)
    
    headers = {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.post(url, data=payload, headers=headers)
    
    # raise AssertionError('error test')
    
    # This seems to rely on the 'errors' return rather than status code, so
    # need to verify both (kick back an error if either are not good)
    if response.status_code != requests.codes.okay or response.json()['errors'] != '':
        print(response.json()['errors'])
        raise AssertionError('subscription request could not be completed')

def validateUSPS(inobj):
    if isinstance(inobj, http.request.QueryDict):
        # Combine fields into Address
        address = Address(
            name = " ",
            address_1 = inobj['address'],
            address_2 = inobj['address2'],
            city = inobj['city'],
            state = inobj['state'],
            zipcode = inobj['zipcode'],
        )
        
    elif isinstance(inobj, dict):
        address = Address(**inobj)
        
    else:
        raise AttributeError('Unknown validation input')

    usps = USPSApi(settings.USPS_SID, test=True)
    validation = usps.validate_address(address)
    outDict = validation.result
    try:
        print(outDict['AddressValidateResponse']['Address']['Address2'])
        print(outDict)
        return outDict
    
    except KeyError:
        print("Address could not be found - no guesses")
        raise


def broadcast_email(email):
    TEMPLATE_ID = settings.TEMPLATE_ID
    message = Mail(
        from_email='getfoco@fcgov.com',
        to_emails=email)
    
    message.template_id = TEMPLATE_ID
    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)

def broadcast_email_pw_reset(email, content):
    TEMPLATE_ID_PW_RESET = settings.TEMPLATE_ID_PW_RESET
    message = Mail(
        subject='Password Reset Requested',
        from_email='getfoco@fcgov.com',
        to_emails=email,
        )
    message.dynamic_template_data = {
        'subject': 'Password Reset Requested',
        'html_content': content,
    }
    message.template_id = TEMPLATE_ID_PW_RESET
    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)


def model_to_dict(model):
    """
    Convert a model object to a dictionary. If a property is a datetime object,
    it will be converted to a string. If there is a nested model, it will be
    excluded from the dictionary.
    :param model: model object
    """
    model_dict = {}
    for field in model._meta.get_fields():
        if field.is_relation:
            continue
        value = getattr(model, field.name)
        if isinstance(value, datetime.datetime):
            value = value.strftime('%Y-%m-%d %H:%M:%S')
        model_dict[field.name] = value
    return model_dict


def serialize_household_members(request):
    """
    Serialize the household members from the request body. Into a list of dictionaries.
    then convert the list of dictionaries into json, so it can be stored in the users
    household_info. Each dictionary should have a 'name' and 'birthdate
    :param request: request object
    """
    # Parse the form data from the request body into a dictionary
    data = urllib.parse.parse_qs(request.body.decode('utf-8'))

    # Extract the household member data and exclude csrfmiddlewaretoken
    household_members_data = {k: v for k, v in data.items() if k != 'csrfmiddlewaretoken'}
    
    # Create a list of dictionaries with 'name' and 'birthdate' keys
    household_members = [{'name': data['name'][i], 'birthdate': data['birthdate'][i]} for i in range(len(household_members_data['name']))]

    household_info = json.loads(json.dumps({'persons_in_household': household_members}, cls=DjangoJSONEncoder))
    return household_info
