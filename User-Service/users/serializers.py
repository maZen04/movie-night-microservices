from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator

class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True, validators=[UniqueValidator(queryset=User.objects.all(), message="This email is already registered.")])
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    display_name = serializers.CharField(required=True, min_length=3, max_length=50, trim_whitespace=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'display_name', 'password', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate_display_name(self, value):
        value = value.strip()

        if not value or len(value) < 3:
            raise serializers.ValidationError(
                "Display name must be at least 3 characters long."
            )

        return value
        
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

    
class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'display_name', 'password', 'created_at', 'updated_at']
        read_only_fields = ['id', 'email', 'created_at', 'updated_at']
        