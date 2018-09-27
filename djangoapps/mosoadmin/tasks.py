# -*- coding:utf-8 -*-
from lms import CELERY_APP
from django.contrib.auth.models import User


@CELERY_APP.task
def deactivate_tempuser(uid):
    """
    deactivate user task
    id: user.id
    print log into edx.log
    """
    user = User.objects.get(id=uid)
    try:
        from django.db import transaction
        with transaction.atomic():
            user.is_active = False
            user.save()
    except:
        print("*** Deactivate User Task Failed ***: ")
        return False
    print("*** Deactivate User Task Succeed ***: user id: %s ;user email: %s " % (uid, user.email))
    return True
