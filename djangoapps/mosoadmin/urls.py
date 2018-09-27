# -*- coding:utf-8 -*-
"""
Urls for mosoadmin dashboard feature
"""

from django.conf.urls import patterns, url
from django.conf import settings
from mosoadmin import views


urlpatterns = patterns(
    '',
    url(r'^$', views.CreateUser.as_view()),
    url(r'^createuser/?$', views.CreateUser.as_view(), name="createuser"),
    url(r'^createschool/?$', views.CreateSchool.as_view(), name="createschool"),
    url(r'^manageusers/?$', views.ManageUsers.as_view(), name="manageusers"),

    url(r'^createcontract/?$', views.Createcontract.as_view(), name="createcontract"),
    url(r'^createcontractitem/(?P<contract_id>\d+)/?$', views.create_contractitem, name="createcontractitem"),

    url(r'^courses/?$', views.CourseEnroll.as_view(), name="mosoadmin_courses"),

    # api
    url(r'^mosousers/?$', views.get_mosousers, name='mosousers'),


)
