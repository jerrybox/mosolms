# -*- coding:utf-8 -*-
from django.contrib.auth.models import User
from django.db import models
from student.models import UserProfile
from django.utils import timezone
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField


class Province(models.Model):
    name = models.CharField(unique=True, null=False, blank=False, max_length=255,verbose_name=u"行政区域")

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def __unicode__(self):
        """
        解决：UnicodeEncodeError: 'ascii' codec can't encode characters in position 0-9: ordinal not in range(128)
        """
        return self.name


class MosoSchool(models.Model):
    name = models.CharField(unique=True, null=False, blank=False, max_length=255, verbose_name=u"学校名称")
    school_code = models.CharField(unique=True, null=True, blank=True, max_length=255, verbose_name=u"学校标识码")
    department = models.CharField(max_length=255, null=True, blank=True, verbose_name=u"主管部门")
    city = models.CharField(null=True, blank=True, max_length=255, verbose_name=u"所在地")
    province = models.ForeignKey(Province, null=True, blank=True, on_delete=None)
    grade = models.CharField(null=True, blank=True, max_length=255, verbose_name=u"办学层次")
    ps = models.CharField(null=True, blank=True, max_length=255, verbose_name=u"备注")

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


class MosoRole(models.Model):
    """mosostaff"""
    name = models.CharField(unique=True, max_length=255)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


class MosoUser(models.Model):
    user = models.OneToOneField(User, unique=True, db_index=True, related_name='mosouser',on_delete=models.CASCADE)
    activate_start = models.DateField(null=True,verbose_name=u"激活时间", blank=True, default=timezone.now)
    activate_end = models.DateField(null=True,verbose_name=u"到期时间", blank=True, default=timezone.now)
    school = models.ForeignKey(MosoSchool,on_delete=None, blank=True, null=True, verbose_name=u"学校")
    creted_by = models.ForeignKey(User, on_delete=None, blank=True, null=True, verbose_name=u"负责人",related_name="creted_by")

    def __str__(self):
        return self.user.username

    def __unicode__(self):
        return self.user.username


class MosoContract(models.Model):
    code = models.CharField(unique=True, max_length=255, verbose_name=u"合同编码")
    organization = models.ForeignKey(MosoSchool, null=True, blank=True, verbose_name=u"学校")
    signed_date = models.DateField(blank=True, null=True, verbose_name=u"签署日期")

    # def __str__(self):
    #     """
    #     TypeError: coercing to Unicode: need string or buffer, MosoContract found
    #     """
    #     return "Contract Code {}".format(self.code.encode('utf-8'))

    def __unicode__(self):
        return u"合同编码：%s" % self.code


class ContractItem(models.Model):
    """
    D:\PycharmProject\NativestackEdxDoc\app\edxapp\edx-platform\common\djangoapps\student\models.py +990
    """
    course_id = CourseKeyField(max_length=255, db_index=True)
    start_date = models.DateField(blank=True, null=True, verbose_name=u"开始日期")
    end_date = models.DateField(blank=True, null=True, verbose_name=u"结束日期")
    contract = models.ForeignKey(MosoContract, blank=True, null=True, related_name='in_contract', verbose_name=u"隶属合同")
    students = models.ManyToManyField(User, blank=True, null=True, verbose_name=u"包含学员", related_name="student_contractitem")

    def __unicode__(self):
        """
          File "/edx/app/edxapp/edx-platform/lms/djangoapps/mosoadmin/models.py", line 92, in __unicode__
                return "  {}   " % self.contract.code
            TypeError: not all arguments converted during string formatting
        字符串格式化处理中文时，优选 % 且加 u''
        """
        return u"隶属于 %s 合同" % self.contract.code
