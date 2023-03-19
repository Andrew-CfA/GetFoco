"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version
"""

import datetime

from unicodedata import decimal
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import JSONField

# Create custom user manager class (because django only likes to use usernames as usernames not email)
class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        
        #Create and save a SuperUser with the given email and password.
        
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)
    

class CaseInsensitiveFieldMixin:
    """
    Field mixin that uses case-insensitive lookup alternatives if they exist.
    
    This and associate case-insensitive index migration found in
    https://concisecoder.io/2018/10/27/case-insensitive-fields-in-django-models
    
    """
    LOOKUP_CONVERSIONS = {
        'exact': 'iexact',
        'contains': 'icontains',
        'startswith': 'istartswith',
        'endswith': 'iendswith',
        'regex': 'iregex',
    }
    def get_lookup(self, lookup_name):
        converted = self.LOOKUP_CONVERSIONS.get(lookup_name, lookup_name)
        return super().get_lookup(converted)


# Class to automatically save date data was entered into postgre
class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides selfupdating ``created`` and ``modified`` fields.
    """
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

# Class to automate generic timestamps in database data
class GenericTimeStampedModel(models.Model):
    """
    An abstract base class model that provides auto-updating ``created_at`` and
    ``modified_at`` fields.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

# Class to automate IQ-program-specific timestamps in database data
class IQProgramTimeStampedModel(models.Model):
    """
    An abstract base class model that provides auto-updating ``applied_at`` and
    ``enrolled_at`` fields.
    """
    applied_at = models.DateTimeField(auto_now_add=True)
    enrolled_at = models.DateTimeField()
    
    class Meta:
        abstract = True


class CIEmailField(CaseInsensitiveFieldMixin, models.EmailField):
    """
    Create an email field with case-insensitivity.
    """
    pass

# User model class
class User(AbstractUser):
    username = None
    email = CIEmailField(_('email address'), unique=True)
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    phone_number = PhoneNumberField()
    files = models.ManyToManyField('dashboard.Form', related_name="forms")
    address_files = models.ManyToManyField('dashboard.residencyForm', related_name="residencyforms")
    has_viewed_dashboard = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email  

# Addresses model attached to user (will delete as user account is deleted too)
class Addresses(TimeStampedModel):
    user_id = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    address = models.CharField(max_length=200, default="")
    address2 = models.CharField(max_length=200, blank=True, default="")

    # Try to get past the things that should be the same for every applicant
    city = models.CharField(max_length=64,)
    state = models.CharField(max_length=2,default="")

    zipCode = models.DecimalField(max_digits=5, decimal_places=0)    
    
    isInGMA = models.BooleanField(null=True, default=None)
    hasConnexion = models.BooleanField(null=True, default=None)
    is_verified = models.BooleanField(default=False)

# Address lookup model
class AddressesNew_rearch(GenericTimeStampedModel):
    address1 = models.CharField(max_length=200, default="")
    address2 = models.CharField(max_length=200, blank=True, default="")

    # Try to get past the things that should be the same for every applicant
    city = models.CharField(max_length=64,)
    state = models.CharField(max_length=2,default="")

    zip_code = models.DecimalField(max_digits=5, decimal_places=0)    
    
    is_in_gma = models.BooleanField(null=True, default=None)
    is_city_covered = models.BooleanField(null=True, default=None)
    has_connexion = models.BooleanField(null=True, default=None)
    is_verified = models.BooleanField(default=False)

    def clean(self):
        self.address1 = self.address1.upper()
        self.address2 = self.address2.upper()
        self.city = self.city.upper()
        self.state = self.state.upper()

    class Meta:
        # Create a composite unique key from the full address
        # This makes the full address searchable as well as ensuring uniqueness
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "address1",
                    "address2",
                    "city",
                    "state",
                    "zip_code",
                    ],
                name="unq_full_address",
            ),
        ]

# Addresses model attached to user (will delete as user account is deleted too)
class Addresses_rearch(GenericTimeStampedModel):
    # Default relation is the User primary key
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,   # set this to the primary key of this model
    )
    mailing_address = models.ForeignKey(
        AddressesNew_rearch,
        on_delete=models.DO_NOTHING,    # don't remove this value if address is deleted
        related_name='+',   # don't relate AddressesNew_rearch id with this field
    )
    eligibility_address = models.ForeignKey(
        AddressesNew_rearch,
        on_delete=models.DO_NOTHING,    # don't remove this value if address is deleted
        related_name='+',   # don't relate AddressesNew_rearch id with this field
    )


class AMI(TimeStampedModel):
    """ Model class to store the Area Median Income values.
    
    Note that these values are separated by number in household.
    
    The 'active' field designates if the record is currently in use; only
    'active' records should be displayed in the webapp.
    
    """
    
    householdNum = models.CharField(max_length=15, primary_key=True)
    active = models.BooleanField()
    
    ami = models.IntegerField()
    
    def __str__(self):
        return str(self.householdNum)
    
class AMI_rearch(GenericTimeStampedModel):
    """ Model class to store the Area Median Income values.
    
    Note that these values are separated by number in household and the 'valid
    year' (which is the year when the numbers were updated by the Census
    Bureau).
    
    The 'active' field designates if the record is currently in use; only
    'active' records should be used for calculations in the webapp.
    
    """
    
    # ``id`` is implicitly the primary key
    year_valid = models.IntegerField()
    number_persons_in_household = models.CharField(max_length=15)
    ami = models.IntegerField()

    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return str(self.number_persons_in_household)    
    
    class Meta:
        # Create a composite unique key for year_valid and individuals
        # This - along with an ``id`` field - is a workaround for Django not
        # supporting composite primary keys.
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "number_persons_in_household",
                    "year_valid",
                    ],
                name="unq_year_values",
            ),
        ]


choices = (
    ('More than 3 Years', 'More than 3 Years'),
    ('1 to 3 Years', '1 to 3 Years'),
    ('Less than a Year', 'Less than a Year'),
)

# Eligibility model class attached to user (will delete as user account is deleted too)
class Eligibility_rearch(GenericTimeStampedModel):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,   # set this to the primary key of this model
    )

    duration_at_address = models.CharField(choices=choices, max_length=200)
    number_persons_in_household = models.IntegerField(100, default=1)

    # Note that ami_year is the same value as 'year_valid' in AMI_rearch (but
    # there's not a way to reasonably associate them in Django)
    ami_year = models.IntegerField()

    # Define the min and max Gross Annual Household Income as a fraction of 
    # AMI (which is a function of number of individuals in household)
    ami_range_min = models.DecimalField(max_digits=3, decimal_places=2)
    ami_range_max = models.DecimalField(max_digits=3, decimal_places=2)

    is_income_verified = models.BooleanField(default=False)

    
class iqProgramQualifications(TimeStampedModel):
    """ Model class to store the IQ program qualifications.
    
    The program names specified here will be used in the remainder of the
    app's backend.
    
    """
    
    name = models.CharField(max_length=40, primary_key=True)
    percentAmi = models.DecimalField(max_digits=10, decimal_places=4)
    
    def __str__(self):
        return str(self.percentAmi)
    
class iqProgramQualifications_rearch(GenericTimeStampedModel):
    """ Model class to store the IQ program qualifications.
    
    The program names specified here will be used in the remainder of the
    app's backend.
    
    """
    
    # ``id`` is the implicity primary key
    program_name = models.CharField(max_length=40, unique=True)

    # Store the AMI for which users must be below in order to be eligible
    ami_threshold = models.DecimalField(max_digits=3, decimal_places=2)
    
    ## The following "friendly" fields will be viewable by users. None of them
    ## have a database-constrained length in order to maximize flexibility.

    ## TODO: remove the max_length input once updated to Django 4.1. In current
    ## Django version, max_length=None (the default) throws an exception but is
    ## fixed in 4.1 to associate with VARCHAR(MAX).
    ## max_length is currently set to a large value, but below Postgres's 
    ## VARCHAR(MAX).

    # Name of the program
    friendly_name = models.CharField(max_length=5000)
    # Program category (as defined by the Program Lead)
    friendly_category = models.CharField(max_length=5000)
    # Description of the program
    friendly_description = models.CharField(max_length=5000)
    # Supplmental information about the program (recommend leaving blank
    # (``''``) unless further info is necessary)
    friendly_supplemental_info = models.CharField(max_length=5000)
    # Hyperlink to learn more about the program
    learn_more_link = models.CharField(max_length=5000)
    # Estimated time period for the eligibility review (in readable text, e.g.
    # 'Two Weeks'). This should be manually updated periodically based on
    # program metrics.
    friendly_eligibility_review_period = models.CharField(max_length=5000)

    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return str(self.ami_threshold)
    
class iq_programs_rearch(IQProgramTimeStampedModel):
    """ Model class to store each user's program enrollment status.
    
    Note that the record for a program is created when a user applies (at which
    point ``applied_at`` is timestamped) and ``is_enrolled`` is set to ``True``
    and ``enrolled_at`` is timestamped when income verification is complete.
    
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
    )

    program = models.ForeignKey(
        iqProgramQualifications_rearch,
        on_delete=models.DO_NOTHING,    # don't update these values if the program is deleted
    )

    is_enrolled = models.BooleanField(default=False)
    

# Eligibility model class attached to user (will delete as user account is deleted too)
class Eligibility(TimeStampedModel):
    user_id = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
    )

    rent = models.CharField(choices=choices, max_length=200)
    #TODO: possibly add field for how many total individuals are in the household
    dependents = models.IntegerField(100, default=1)

    DEqualified = models.CharField(max_length=20)
    GenericQualified = models.CharField(max_length=20)
    ConnexionQualified = models.CharField(max_length=20)
    GRqualified = models.CharField(max_length=20)
    RecreationQualified = models.CharField(max_length=20)
    SPINQualified = models.CharField(max_length=20)

    #TODO 5/13/2021
    #insert other rebate flags here i.e.
    #xQualified = models.CharField(max_length=20)
    #utilitiesQualified = models.CharField(max_length=20)
    

    grossAnnualHouseholdIncome = models.CharField(max_length=20)    
    # Define the min and max Gross Annual Household Income as a fraction of 
    # AMI (which is a function of number of individuals in household)
    AmiRange_min = models.DecimalField(max_digits=5, decimal_places=4)
    AmiRange_max = models.DecimalField(max_digits=5, decimal_places=4)
    spin_privacy_acknowledgement = models.BooleanField(default=False)


class MoreInfo(TimeStampedModel):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    dependentInformation = JSONField(null=True,blank=True)
    #dependentsBirthdate = models.DateField(auto_now=False, auto_now_add=False, blank=True, null=True)
    #dependentsName = models.CharField(max_length=20)

class MoreInfo_rearch(GenericTimeStampedModel):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,   # set this to the primary key of this model
    )

    # Store the household info (individuals' names and birthdates) as JSON for
    # quick storage and reference
    household_info = JSONField(null=True,blank=True)
    created_at_init_temp = models.DateTimeField()
    modified_at_init_temp = models.DateTimeField()
    

# Programs model class attached to user (will delete as user account is deleted too)
class programs(TimeStampedModel): #incomeVerificationPrograms
    user_id = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    snap = models.BooleanField()
    freeReducedLunch = models.BooleanField()
    Identification = models.BooleanField()
    form1040 = models.BooleanField(default=False)
    ebb_acf = models.BooleanField()
    leap = models.BooleanField()
    medicaid = models.BooleanField(default=False)


class programs_rearch(GenericTimeStampedModel):
    """
    Model class to store the eligibility programs.
    
    """
    # ``id`` is the implicit primary key
    program_name = models.CharField(max_length=40, unique=True)

    # Store the AMI threshold that the users with each program are underneath
    ami_threshold = models.DecimalField(max_digits=3, decimal_places=2)

    # This is the friendly name displayed to the user

    # TODO: remove the max_length input once updated to Django 4.1. In current
    # Django version, max_length=None (the default) throws an exception but is
    # fixed in 4.1 to associate with VARCHAR(MAX).
    # max_length is currently set to a large value, but below Postgres's 
    # VARCHAR(MAX).

    friendly_program_name = models.CharField(max_length=5000)

def userfiles_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'user_{0:05}/{1}'.format(instance.user_id.id, filename)

class Dashboard_form_rearch(GenericTimeStampedModel):
    """
    Model class to store the eligibility programs.
    
    """
    # ``id`` is the implicit primary key
    user = models.ForeignKey(
        User,
        related_name='eligibility_files',
        on_delete=models.CASCADE,
    )

    program = models.ForeignKey(
        programs_rearch,
        on_delete=models.DO_NOTHING,  # don't remove the program ID if the program is deleted
        )

    # Upload the file(?) to the proper directory in Azure Blob Storage and store
    # the path
    document_path = models.FileField(max_length=5000, upload_to=userfiles_path)
    

class attestations(TimeStampedModel):
    user_id = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    completeAttestation = models.BooleanField(default=False)
    localAttestation = models.BooleanField(default=False)

# TODO: Should be deleted, but might need to ETL the data
# before the model is deleted
class addressVerification(TimeStampedModel):
    user_id = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    #Identification = models.BooleanField()
    Utility = models.BooleanField()
    #freeReducedLunch = models.BooleanField()

class addressLookup(TimeStampedModel):
    address = models.CharField(max_length=100) 

class futureEmails(TimeStampedModel):
    connexionCommunication = models.BooleanField(default=True, blank=True)


class EligibilityHistory(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(
        User,
        related_name='eligibility_history',
        on_delete=models.DO_NOTHING,  # don't remove the eligibility history if a user account is deleted
        )
    created = models.DateTimeField(auto_now_add=True)
    historical_eligibility = JSONField(null=True,blank=True)
