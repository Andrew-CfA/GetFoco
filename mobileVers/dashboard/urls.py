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
from django.urls import path, include
from django.contrib import admin
from django.contrib.auth import views as auth_views #import this

from django.conf.urls.static import static
from django.conf import settings
from . import views

# Need to specify my urls to be used within this project
urlpatterns = [
    path('', views.feedback, name='index'), #path('', views.index, name='index'), #TODO need to rename this to feedback instead of index... because views.feedback contains the feedback code!
    # Pages for forms
    path('files', views.files, name='files'),
    path('filesContinued', views.filesContinued, name='filesContinued'),
    path('addressVerification', views.addressVerification, name='addressVerification'),
    path('login', views.login_user, name='login'),
    path('broadcast', views.broadcast, name='broadcast'),
    path('feedbackReceived', views.feedbackReceived, name="feedbackReceived"),
    path('manualVerifyIncome', views.manualVerifyIncome, name='manualVerifyIncome'),
    path('notifyRemaining', views.notifyRemaining, name='notifyRemaining'),
    path('underConstruction', views.underConstruction, name='underConstruction'),
    path('GetFOCO', views.dashboardGetFoco, name='dashboard'),
    path('qualifiedPrograms', views.qualifiedPrograms, name='qualifiedPrograms'),
    path('ProgramsList', views.ProgramsList, name='ProgramsList'),
    path('BagIt', views.BagIt, name='BagIt'),
    path('FAQ', views.FAQ, name='FAQ'),
    path('settings', views.settings, name='settings'),

    path("password_reset", views.password_reset_request, name="password_reset")
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) #this is needed to get file uploads to work! 
