# -*- coding:utf-8 -*-
"""
This module creates a mosoadmin dashboard for managing and viewing
courses.
"""
import unicodecsv as csv
import json
import logging
import os
import StringIO
import subprocess

import mongoengine
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import IntegrityError
from django.http import Http404, HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import condition
from django.views.generic.base import TemplateView
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from path import Path as path

import dashboard.git_import as git_import
import track.views
from courseware.courses import get_course_by_id
from dashboard.git_import import GitImportError
from dashboard.models import CourseImportLog
from edxmako.shortcuts import render_to_response
from openedx.core.djangoapps.external_auth.models import ExternalAuthMap
from openedx.core.djangoapps.external_auth.views import generate_password
from student.roles import CourseInstructorRole, CourseStaffRole
from xmodule.modulestore.django import modulestore

log = logging.getLogger(__name__)

from django.shortcuts import redirect
from mosoadmin.models import MosoUser,MosoSchool
from xmodule.modulestore.django import modulestore

from opaque_keys.edx.locations import SlashSeparatedCourseKey
import re
from student.models import (
    ALLOWEDTOENROLL_TO_ENROLLED,
    ALLOWEDTOENROLL_TO_UNENROLLED,
    DEFAULT_TRANSITION_STATE,
    ENROLLED_TO_ENROLLED,
    ENROLLED_TO_UNENROLLED,
    UNENROLLED_TO_ALLOWEDTOENROLL,
    UNENROLLED_TO_ENROLLED,
    UNENROLLED_TO_UNENROLLED,
    CourseEnrollment,
    EntranceExamConfiguration,
    ManualEnrollmentAudit,
    Registration,
    UserProfile,
    anonymous_id_for_user,
    get_user_by_username_or_email,
    unique_id_for_user,
    UserAttribute
)
from lms.djangoapps.instructor.enrollment import (
    enroll_email,
    get_email_params,
    get_user_email_language,
    send_beta_role_email,
    send_mail_to_student,
    unenroll_email
)
from lms.djangoapps.instructor.views.tools import (
    dump_module_extensions,
    dump_student_extensions,
    find_unit,
    get_student_from_identifier,
    handle_dashboard_error,
    parse_datetime,
    require_student_from_identifier,
    set_due_date_extension,
    strip_if_string
)
from django.core.validators import validate_email
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.html import strip_tags
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError

from opaque_keys.edx.keys import CourseKey
from course_modes.models import CourseMode, CourseModesArchive
from django.core.urlresolvers import reverse


def _split_input_list(str_list):
    new_list = re.split(r'[\n\r\s,]', str_list)
    new_list = [s.strip() for s in new_list]
    new_list = [s for s in new_list if s != '']
    return new_list


def _get_boolean_param(request, param_name):
    return request.POST.get(param_name, False) in ['true', 'True', True]


class CourseEnroll(TemplateView):
    template_name = 'mosoadmin/mosoadmin_course_enrollment.html'
    msg = None

    def __init__(self, **kwargs):
        self.msg = u''
        super(CourseEnroll,self).__init__(**kwargs)

    def make_common_context(self):
        """Returns the datatable used for this view"""
        pass

    def make_datatable(self):
        """Creates course information datatable"""
        def_ms = modulestore()
        courselist = def_ms.get_courses()

        data = []
        for course in courselist:
            data.append([course.display_name, course.id.to_deprecated_string()])

        return dict(header=[_('Course Name'),
                            _('Directory/ID'),],
                    title=_('Information about all courses'),
                    data=data)

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return redirect("/login")
        if not UserAttribute.get_user_attribute(request.user, "access_mosoadmin"):
            return HttpResponse("No permission")

        context = {'msg':self.msg,
                   'datatable':self.make_datatable()
                   }
        return render_to_response(self.template_name, context)

    def post(self, request, *args, **kwargs):

        course_id = request.POST.get('course_id', False)
        if not course_id:
            self.msg = "No course_id"
            context = {'msg': self.msg,
                       'datatable': self.make_datatable()
                       }
            return render_to_response(self.template_name, context)

        course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        action = request.POST.get('action')
        identifiers_raw = request.POST.get('identifiers')
        identifiers = _split_input_list(identifiers_raw)
        auto_enroll = _get_boolean_param(request, 'auto_enroll')
        email_students = _get_boolean_param(request, 'email_students')
        is_white_label = CourseMode.is_white_label(course_id)
        reason = request.POST.get('reason')

        if is_white_label:
            if not reason:
                self.msg = "400"
                context = {'msg': self.msg,
                           'datatable': self.make_datatable()
                           }
                return render_to_response(self.template_name, context)

        enrollment_obj = None
        state_transition = DEFAULT_TRANSITION_STATE

        email_params = {}
        if email_students:
            course = get_course_by_id(course_id)
            email_params = get_email_params(course, auto_enroll, secure=request.is_secure())

        results = []
        for identifier in identifiers:
            # First try to get a user object from the identifer
            user = None
            email = None
            language = None
            try:
                user = get_student_from_identifier(identifier)
            except User.DoesNotExist:
                email = identifier
            else:
                email = user.email
                language = get_user_email_language(user)

            try:
                # Use django.core.validators.validate_email to check email address
                # validity (obviously, cannot check if email actually /exists/,
                # simply that it is plausibly valid)
                validate_email(email)  # Raises ValidationError if invalid
                if action == 'enroll':
                    before, after, enrollment_obj = enroll_email(
                        course_id, email, auto_enroll, email_students, email_params, language=language
                    )
                    before_enrollment = before.to_dict()['enrollment']
                    before_user_registered = before.to_dict()['user']
                    before_allowed = before.to_dict()['allowed']
                    after_enrollment = after.to_dict()['enrollment']
                    after_allowed = after.to_dict()['allowed']

                    if before_user_registered:
                        if after_enrollment:
                            if before_enrollment:
                                state_transition = ENROLLED_TO_ENROLLED
                            else:
                                if before_allowed:
                                    state_transition = ALLOWEDTOENROLL_TO_ENROLLED
                                else:
                                    state_transition = UNENROLLED_TO_ENROLLED
                    else:
                        if after_allowed:
                            state_transition = UNENROLLED_TO_ALLOWEDTOENROLL

                elif action == 'unenroll':
                    before, after = unenroll_email(
                        course_id, email, email_students, email_params, language=language
                    )
                    before_enrollment = before.to_dict()['enrollment']
                    before_allowed = before.to_dict()['allowed']
                    enrollment_obj = CourseEnrollment.get_enrollment(user, course_id)

                    if before_enrollment:
                        state_transition = ENROLLED_TO_UNENROLLED
                    else:
                        if before_allowed:
                            state_transition = ALLOWEDTOENROLL_TO_UNENROLLED
                        else:
                            state_transition = UNENROLLED_TO_UNENROLLED

                else:
                    return HttpResponseBadRequest(strip_tags(
                        "Unrecognized action '{}'".format(action)
                    ))

            except ValidationError:
                # Flag this email as an error if invalid, but continue checking
                # the remaining in the list
                results.append({
                    'identifier': identifier,
                    'invalidIdentifier': True,
                })
                # results.append(u"{} 验证失败,请检查用户是否存在。".format(identifier))

            except Exception as exc:  # pylint: disable=broad-except
                # catch and log any exceptions
                # so that one error doesn't cause a 500.
                log.exception(u"Error while #{}ing student")
                log.exception(exc)
                results.append({
                    'identifier': identifier,
                    'error': True,
                })
                # results.append(u"{} 验证失败,请检查输入内容。".format(identifier))

            else:
                ManualEnrollmentAudit.create_manual_enrollment_audit(
                    request.user, email, state_transition, reason, enrollment_obj
                )
                results.append({
                    'identifier': identifier,
                    'before': before.to_dict(),
                    'after': after.to_dict(),
                })
                # if identifier:
                #     results.append(u"{} 验证失败,请检查输入内容。".format(identifier))
        # response_payload = {
        #     'action': action,
        #     'results': results,
        #     'auto_enroll': auto_enroll,
        # }
        # return JsonResponse(response_payload)
        invalid_id = []
        valid_id = []

        for result in results:
            if ('error' in result) or ('invalidIdentifier' in result):
                invalid_id.append(result['identifier'])
            else:
                valid_id.append(result['identifier'])

        invalid_message = ["{} 无效 <br>".format(i) for i in invalid_id]
        valid_message = []

        action = "选课" if action == "enroll" else "弃选"

        for i in valid_id:
            if action == "弃选":
                valid_message.append("{0}  {1} 成功 <br>".format(i, action))
                continue
            if email_students:
                valid_message.append("{0}  {1} 成功，并向他发送电子邮件 <br>".format(i, action))
            else:
                valid_message.append("{0}  {1} 成功<br>".format(i, action))
        invalid_message.extend(valid_message)

        import json
        self.msg = "".join(invalid_message)

        context = {'msg': self.msg,
                   'datatable': self.make_datatable()
                   }
        return render_to_response(self.template_name, context)


class CreateSchool(TemplateView):
    pass


class ManageUsers(TemplateView):
    pass


class CreateUser(TemplateView):
    """
    The status view provides Web based user management, a listing of
    courses loaded, and user statistics
    """
    template_name = 'mosoadmin/mosoadmin_create_user.html'
    msg = None

    def __init__(self, **kwargs):
        self.msg = u''
        super(CreateUser,self).__init__(**kwargs)

    def make_common_context(self):
        """Returns the datatable used for this view"""
        pass

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return redirect("/login")
        if not UserAttribute.get_user_attribute(request.user, "access_mosoadmin"):
            return HttpResponse("No permission")

        context = {'msg':self.msg,}
        return render_to_response(self.template_name, context)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return redirect("/login")
        if not UserAttribute.get_user_attribute(request.user, "access_mosoadmin"):
            return HttpResponse("No permission")

        self.make_common_context()
        action = request.POST.get('action', '')

        if action == 'create_user':
            uname = request.POST.get('student_uname', '').strip()
            name = request.POST.get('student_fullname', '').strip()
            password = request.POST.get('student_password', '').strip()
            self.msg = u'<h4>{0}</h4><p>{1}</p><hr />'.format(
                _('Create User Results'),
                self.create_user(uname, name, password, request))

        context = {
            'msg': self.msg,
        }
        return render_to_response(self.template_name, context)

    def create_user(self, uname, name, password=None, request=None):
        """ Creates a user (both SSL and regular)"""

        if not uname:
            return _('Must provide username')
        if not name:
            return _('Must provide full name')

        msg = u''

        if '@' not in uname:
            msg += _('Email address must contain @')
            return msg
        elif not password:
            msg += _('Password must be supplied if not using certificates')
            return msg

        email = uname
        new_password = password

        try:
            from django.db import transaction
            with transaction.atomic():
                user = User(username=uname, email=email, is_active=True)
                user.set_password(new_password)
                user.save()
        except IntegrityError:
            msg += _('Oops, failed to create user {user}, {error}').format(
                user=uname,
                error="{} already exist.".format(email)
            )
            return msg

        reg = Registration()
        reg.register(user)

        profile = UserProfile(user=user)
        profile.name = name
        profile.save()

        mosouser = MosoUser(user=user,creted_by=request.user)
        mosouser.save()

        msg += _('User {user} created successfully!').format(user=user)
        return msg
