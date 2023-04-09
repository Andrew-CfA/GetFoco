FROM ubuntu:20.04
#Layer for python and gdal support
RUN apt-get update && apt-get install -y software-properties-common curl \
    && add-apt-repository ppa:ubuntugis/ubuntugis-unstable && apt-get update \
    && apt-get install -y python3-pip libssl-dev libffi-dev python3-gdal \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3 10 \
    && update-alternatives --install /usr/bin/pip    pip    /usr/bin/pip3    10 \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get remove -y curl

# Layers for the django app

# RUN pip installs first, for caching
# Note that updates to requirements.txt don't need to be replicated here, because requirements.txt
# will add/update packages later in this script
RUN apt-get install libmagic1
RUN pip install pip --upgrade
RUN pip install django==3.1.7
RUN pip install sendgrid==6.6.0
RUN pip install django-formwizard~=1.0
RUN pip install django-formtools~=2.2
RUN pip install matplotlib~=3.3.3
RUN pip install mpld3~=0.5.2
RUN pip install usps-api
RUN pip install usaddress~=0.5.10
RUN pip install twilio
RUN pip install django-phonenumber-field[phonenumbers]
RUN pip install django-environ
RUN pip install psycopg2-binary
RUN pip install django-crispy-forms
RUN pip install python-magic
RUN pip install azure-storage-blob==2.1.0
RUN pip install gunicorn
RUN pip install whitenoise

# Then ADD code and 
# RUN requirements.txt for completeness (this will ignore previously-installed packages or update
# them if requirements.txt has different versions)
RUN mkdir /code
WORKDIR /code
ADD . /code/
RUN pip install -r requirements.txt


RUN python manage.py collectstatic --noinput --settings=mobileVers.settings.dev
#--settings=mobileVers.settings.production

COPY init.sh /usr/local/bin/

RUN chmod u+x /usr/local/bin/init.sh

#Layer for exposing the app through
EXPOSE 8000

WORKDIR /code

ENTRYPOINT [ "init.sh" ]