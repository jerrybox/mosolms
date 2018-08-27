"""
Urls for sysadmin dashboard feature
"""

from django.conf.urls import patterns, url

from mosoadmin import views

urlpatterns = patterns(
    '',
    url(r'^$', views.Users.as_view(), name="sysadmin"),
    url(r'^courses/?$', views.Courses.as_view(), name="sysadmin_courses"),
    url(r'^staffing/?$', views.Staffing.as_view(), name="sysadmin_staffing"),
    url(r'^gitlogs/?$', views.GitLogs.as_view(), name="gitlogs"),
    url(r'^gitlogs/(?P<course_id>.+)$', views.GitLogs.as_view(),
        name="gitlogs_detail"),
)