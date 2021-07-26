import csv
from usps import USPSApi, Address
import re

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

#address comparison function for finding if address is within N2N bounds
#TODO start thinking about SQL querys for this section and change it for database integration!
def addressCheck(address1):
    myex = re.compile(r"(DRIVE|DR)")
    final_str = re.sub(myex, '', address1)
    with open("compare.csv", "r") as csv_file:
        counter = 0
        csv_reader = csv.reader(csv_file, delimiter=',')
        for lines in csv_reader:
            column = lines[0] + " " + lines[1] + " " #+ lines[2]
            if final_str == column:
                print("True!")
                return True
            else:
                counter = counter + 1
                if counter == 77:
                    return False
                else:
                    continue


#1) open file csv containing AMI information
#2) compare dependents number to file, find right "row"
#3) take that value and compare to income level selection
#       current_user = request.user
#       record_data = programs.objects.get(user_id = current_user)
#       form = programForm(request.POST, instance = record_data)
def qualification(dependentNumber):
    with open("AMI.csv", "r") as csv_file:
        counter = 0
        csv_reader = csv.reader(csv_file, delimiter=',')
        for lines in csv_reader:
            dependentAmount = lines[0]
            AMINumber = lines[1]
            if dependentNumber == dependentAmount:
                print("AMI NUMBER IS: " + AMINumber)
                return int(AMINumber)
            else:
                counter = counter + 1
                if counter == 10:
                    return 0
                else:
                    continue

def validateUSPS(form):
    address = Address(
        name = " ",
        address_1 = form['address'],
        address_2 = form['address2'],
        city = form['city'],
        state = form['state'],
        zipcode = form['zipcode'],
    )
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
