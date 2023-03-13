"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version
"""
"""mobileVers URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""


from django.contrib import admin
from django.urls import path, include
from application import views
from django.contrib.auth import views as auth_views  # import this
urlpatterns = [
    path('admin/', admin.site.urls),
    # For the no slash, I just put the homepage index file to be first
    path('', views.index, name='index'),
    # Add one of these every time I make a new app
    path('application/', include(('application.urls',
         'application'), namespace='application')),
    path('dashboard/', include(('dashboard.urls', 'dashboard'), namespace='dashboard')),


    path('accounts/', include('django.contrib.auth.urls')),
    # path('password_reset/', auth_views.PasswordResetView.as_view(template_name='dashboard/PasswordReset/passwordReset.html'), name='passwordReset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='dashboard/PasswordReset/passwordResetDone.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name="dashboard/PasswordReset/passwordResetConfirm.html"), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='dashboard/PasswordReset/passwordResetComplete.html'), name='password_reset_complete'),
]
