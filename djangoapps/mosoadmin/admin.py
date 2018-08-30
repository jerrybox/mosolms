# -*- coding:utf-8 -*-
from django.contrib import admin
from mosoadmin.models import MosoSchool,MosoRole,MosoUser,Province


class ProvinceAdmin(admin.ModelAdmin):
    fields = ('name',)
    list_display = ('name',)


class MosoSchoolAdmin(admin.ModelAdmin):
    fields = ('name','school_code','department','city','province','grade','ps')
    list_display = ('name','department','city','grade','ps')
    list_filter = ('province','grade')


class MosoRoleAdmin(admin.ModelAdmin):
    fields = ('name',)
    list_display = ('name',)


class MosoUserAdmin(admin.ModelAdmin):
    fields = ('user','activate_start','activate_end','school','creted_by')
    list_display = ('user','activate_start','activate_end','school','creted_by')
    list_filter = ('user','activate_start','activate_end','school','creted_by')


# Register your models here.
admin.site.register(Province, ProvinceAdmin)
admin.site.register(MosoSchool, MosoSchoolAdmin)
admin.site.register(MosoRole, MosoRoleAdmin)
admin.site.register(MosoUser, MosoUserAdmin)
