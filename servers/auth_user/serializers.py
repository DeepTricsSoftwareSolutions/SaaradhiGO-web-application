from rest_framework.serializers import ModelSerializer
from django.contrib.auth import get_user_model

class UserModelSerializer(ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = [
            'id', 'username', 'full_name', 'phone_number', 'email', 
            'gender', 'dob', 'house_no', 'street', 'city', 'zip_code',
            'emergency_contact', 'role', 'avatar', 'fcm_token', 'updated_at', 'created_at','is_updated'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }