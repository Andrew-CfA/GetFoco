"""
Get FoCo is a platform for application and administration of income-
qualified programs offered by the City of Fort Collins.
Copyright (C) 2019

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from . import views

# Need to specify my urls to be used within this project
urlpatterns = [
    path('', views.index, name='index'),
    # Pages for forms
    path('address', views.address, name='address'),
    path('account', views.account, name='account'),
    path('finances', views.finances, name='finances'),
    path('programs', views.programs, name='programs'),
    path('attestation', views.attestation, name='attestation'),
    path('moreInfoNeeded', views.moreInfoNeeded, name='moreInfoNeeded'),
    path('filesInfoNeeded', views.filesInfoNeeded, name='filesInfoNeeded'),
    

    # Available/NotAvailable Digital Equity in your area
    # path('available', views.available, name='available'),
    path('notAvailable', views.notAvailable, name='notAvailable'),
    path('quickAvailable', views.quickAvailable, name='quickAvailable'),
    path('quickNotAvailable', views.quickNotAvailable, name='quickNotAvailable'),
    path('quickComingSoon', views.quickComingSoon, name='quickComingSoon'),
    path('quickNotFound', views.quickNotFound, name='quickNotFound'),
    path('addressCorrection', views.addressCorrection, name='addressCorrection'),
    path('inServiceArea', views.inServiceArea, name='inServiceArea'),
    path('GRQuickApply', views.GRQuickApply, name='GRQuickApply'),
    path('takeUSPSaddress', views.takeUSPSaddress, name='takeUSPSaddress'),
    # Grocery Rebate Dependent Pages
    path('callUs', views.callUs, name='callUs'),
    # Recreation Dependent Pages
    path('RecreationQuickApply', views.RecreationQuickApply, name='RecreationQuickApply'),
    path('ConnexionQuickApply', views.ConnexionQuickApply, name='ConnexionQuickApply'),
    path('SPINQuickApply', views.SPINQuickApply, name='SPINQuickApply'),
    # ETC. pages
    path('comingSoon', views.comingSoon, name='comingSoon'),
    path('mayQualify', views.mayQualify, name='mayQualify'),
    path('privacyPolicy', views.privacyPolicy, name='privacyPolicy'),
    path('dependentInfo', views.dependentInfo, name='dependentInfo'),
    path('getReady', views.getReady, name='getReady'),

    path('ajax/load-gahi/', views.load_gahi_selector, name='ajax_load_gahi'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) #this is needed to get file uploads to work! 
