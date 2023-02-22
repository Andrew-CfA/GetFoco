FROM ubuntu:20.04
#Layer for python and gdal support
RUN apt-get update && apt-get install -y software-properties-common curl \
    && add-apt-repository ppa:ubuntugis/ubuntugis-unstable && apt-get update \
    && apt-get install -y python3-pip libssl-dev libffi-dev python3-gdal \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3 10 \
    && update-alternatives --install /usr/bin/pip    pip    /usr/bin/pip3    10 \
    && rm -rf /var/lib/apt/lists/*
# #Begin of mandatory layers for Microsoft ODBC Driver 13 for Linux
# RUN apt-get update && apt-get install -y apt-transport-https wget
# RUN sh -c 'echo "deb [arch=amd64] https://apt-mo.trafficmanager.net/repos/mssql-ubuntu-xenial-release/ xenial main" > /etc/apt/sources.list.d/mssqlpreview.list'
# RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 417A0893
# RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys B02C46DF417A0893
# #changed from --keyserver apt-mo.trafficmanager.net
# RUN apt-get update -y
# RUN apt-get -y install unixodbc-dev
# RUN apt-get update -y


# RUN su
# RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -

# RUN curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
# RUN exit


# RUN apt-get update -y
# RUN ACCEPT_EULA=Y apt-get install -y msodbcsql17
# RUN apt-get install -y locales
# RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen
# RUN locale-gen
#End of mandatory layers for Microsoft ODBC Driver 13 for Linux
RUN apt-get remove -y curl


#Layers for the django app
RUN mkdir /code
WORKDIR /code
ADD . /code/
RUN apt-get install libmagic1
RUN pip install pip --upgrade
RUN pip install -r requirements.txt
RUN pip install gunicorn
RUN pip install whitenoise


RUN python manage.py collectstatic --noinput --settings=mobileVers.settings.dev
#--settings=mobileVers.settings.production

COPY init.sh /usr/local/bin/

RUN chmod u+x /usr/local/bin/init.sh

#Layer for exposing the app through
EXPOSE 8000

WORKDIR /code

ENTRYPOINT [ "init.sh" ]