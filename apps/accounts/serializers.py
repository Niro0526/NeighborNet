from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, UserRoleAssignment, RoleChoices

class UserRoleAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRoleAssignment
        fields = ['role', 'is_approved', 'approved_at']

class UserSerializer(serializers.ModelSerializer):
    assignedRoles = serializers.SerializerMethodField()
    name = serializers.CharField(read_only=True)
    fullName = serializers.CharField(source='full_name', required=False)
    avatarUrl = serializers.URLField(source='avatar_url', required=False, allow_null=True)
    defaultWorkspace = serializers.CharField(source='default_workspace', required=False)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'name', 'fullName', 'phone', 'assignedRoles',
            'defaultWorkspace', 'avatarUrl', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'email', 'status', 'created_at']

    def get_assignedRoles(self, obj):
        return obj.get_approved_roles()

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid email or password credentials.')
            if user.status == 'suspended':
                raise serializers.ValidationError('Your account has been suspended. Please contact coordinator administration.')
        else:
            raise serializers.ValidationError('Both email and password are required.')
        attrs['user'] = user
        return attrs

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    roles = serializers.ListField(
        child=serializers.ChoiceField(choices=RoleChoices.choices),
        required=False,
        default=['FOOD_PROVIDER']
    )
    full_name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'full_name', 'phone', 'roles']

    def validate_roles(self, value):
        # Explicit security requirement: client cannot self-assign COORDINATOR role!
        if RoleChoices.COORDINATOR in value:
            raise serializers.ValidationError(
                'Security restriction: Coordinator permissions cannot be self-assigned during registration. Coordinator access requires statutory board delegation.'
            )
        if not value:
            return [RoleChoices.FOOD_PROVIDER]
        return value

    def create(self, validated_data):
        roles = validated_data.pop('roles', [RoleChoices.FOOD_PROVIDER])
        user = User.objects.create_user(**validated_data)
        for role in roles:
            UserRoleAssignment.objects.create(
                user=user,
                role=role,
                is_approved=True
            )
        return user
