import csv
from usps import USPSApi, Address
import re
import requests
from django import http  # used for type checks

import urllib.parse
import requests

#Andrew backend code for Twilio
from twilio.rest import Client
from django.conf import settings    
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def broadcast_sms(phone_Number):
    message_to_broadcast = ("We have received your application for GetYourConnection! We'll keep in touch")
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
        
        # Below this point are status messages from Connexion lookup tool at
        # https://www.fcgov.com/connexion/ as of 2021-06-11.
        # statusMsg is currently unused here - for reference only
        if statusInput in (
                'on hold',
                'in design',
                'design approved',
                'proofing complete'
                ):
            statusMsg = 'In Design\n\nYou are currently in the design phase. This is the earliest stage of the build process and involves infrastructure identification, conduit and boring need identification, as well as scheduling consideration. We are unable to give you an approximate date for service at this stage. If you would like to be notified when service is available at your address, please complete the <a href="/connexion/residential#service-availability"> service availability notification form </a>.'
            
        elif statusInput in (
                'in construction',
                'gig',
                'accepted',
                ):
            statusMsg = 'In Construction\n\nThis is the building phase of the process. Once you see construction in your neighborhood and receive a door hanger announcing construction, service is typically available within 6-9 months. For any construction-related questions or concerns email <a href="mailto:fcresidents@aeg.cc">fcresidents@aeg.cc</a> or call 970-207-7873. If you would like to be notified when service is available at your address, please complete the <a href="/connexion/residential#service-availability">service availability notification form</a>.'
            
        elif statusInput in (
                'released',
                'out of warranty',
                ):
            statusMsg = 'Service Available\n\nCongratulations!! Service is available in your neighborhood. If you would like to learn more about our products and services, please <a href="https://www.fcgov.com/connexion/support#customer-service">contact our Customer Service Team</a>. <br><br>If you live in a multi-family dwelling unit, service may not be immediately available. Townhomes, apartments, and condos require permission prior to Connexion service being available. Please contact your property owner or homeowners association for permission for Connexion to provide service.'
            
        
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
        
    print (address)
    usps = USPSApi(settings.USPS_SID, test=True)
    validation = usps.validate_address(address)
    outDict = validation.result
    try:
        print(outDict['AddressValidateResponse']['Address']['Address2'])
        print(outDict)
        return outDict
    
    except KeyError:
        print("Wrong address info added")
        raise


def broadcast_email(email):
    TEMPLATE_ID = settings.TEMPLATE_ID
    message = Mail(
        from_email='ahernandez@codeforamerica.org',
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
