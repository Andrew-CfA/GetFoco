# Architecture

Here you will find high-level architecture of Get FoCo.
Getting to know Get FoCo starts here!

## Top Level

Get FoCO is a web-app that allows residents of Fort Collins to create accounts with their financial information and income verification (SNAP, EBT, PSD Letter, ACP Letter) which then is used by Get FoCo to see what kind of income qualified programs they may qualify for.

It is a 6 step process

Step 1
Client creates their account with email, phone number, etc.

Step 2
Client uploads their address information to see if they qualify for location based IQ Programs

Step 3
Client inputs their financial information such as gross annual AMI and number of people in household - the system uses this information to double check programs they may qualify for

Step 4
Client inputs which income verification programs they may be a part of (if any) - this is used to validate clients' income which, again, is used to double check which programs they may qualify for.

Step 5
Client uploads their income verification proof, i.e. a picture or pdf of a SNAP card, etc.

Step 6
Final step! Client is then emailed to verify account creation and finally...

Dashboard
Using the information from steps 1 - 6, the dashboard uses logic and facts to figure out which IQ programs a client may qualify for - at the dashboard these programs are shown and clients are able to click on "quick-apply" to apply for programs.

## Code Map
Here you will find brief explanations of files, directories and data structures.

### '.github/workflows'
Future workflow GitHub implementation.

### '.vscode/settings.json'
settings.json file for vscode. May no longer be needed.

### 'mobileVers/'
Files not in folders are all crucial Docker files or files django necessary files.

### 'mobileVers/Dockerfile'
Crucial Docker file holding instructions to containerize Get FoCo using Docker, subsequent files, entrypoint.sh and init.sh are utilized in tandem to create a pleasant Docker containerizing experience.

### 'mobileVers/application/backend.py'
Here you'll find some useful backend logic / functions used in the main application, most of these functions are used to 
supplement the application and to keep views.py clutter to a minimum! Functions include USPS, address and Twilio.

### 'mobileVers/application/forms.py'
Here you'll find important forms information for the "application" part of the webpage. These forms hold steps 1-4 of the application.

### 'mobileVers/application/models.py'
Here you'll find models used for the database in tandem with the forms to create critical tables for the database. This models file pertains to the 'application' portion of Get FoCo.

### 'mobileVers/application/tests.py'
Here is an example tests file, tests need to be implemented still.

### 'mobileVers/application/static'
Holds static images used to make Get FoCo look good.