from django.contrib.auth.models import User

from rest_framework import serializers

from mosoadmin.models import (
    Province,
    MosoSchool,
    MosoRole,
    MosoUser,
    MosoContract,
    ContractItem
)

class ContractItemSerializer(serializers.Serializer):
    course_id = serializers.CharField(read_only=True)
    start_date = serializers.DateField(format='iso-8601', read_only=True)
    end_date = serializers.DateField(format='iso-8601', read_only=True)
    contract = serializers.PrimaryKeyRelatedField(many=False, queryset=MosoContract.objects.all(), required=True,
                                              source='contract.code')
    students = serializers.PrimaryKeyRelatedField(many=False, queryset=User.objects.all(), required=True,
                                              source='students.code')



class MosoUserListSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(many=False, queryset=User.objects.all(), required=True, source='user.profile.name')
    email = serializers.PrimaryKeyRelatedField(many=False, queryset=User.objects.all(), required=True,
                                              source='user.email')

    activate_start = serializers.DateField(format='iso-8601', read_only=True)
    activate_end = serializers.DateField(format='iso-8601', read_only=True)

    school = serializers.PrimaryKeyRelatedField(many=False, queryset=MosoSchool.objects.all(), required=True,
                                              source='school.name')

    contractitem_course = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all(), required=True,
                                              source='user.student_contractitem')

    contract_code = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all(), required=True,
                                              source='user.student_contractitem')



    creted_by = serializers.PrimaryKeyRelatedField(many=False, queryset=User.objects.all(), required=True, source='creted_by.profile.name')


class MosoUserModelSerializer(serializers.ModelSerializer):
    pass

