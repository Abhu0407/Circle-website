import re

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')


class SignUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')
        extra_kwargs = {'email': {'required': True}}

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return value

    def validate(self, attrs):
        user = User(**{k: v for k, v in attrs.items() if k != 'password'})
        try:
            validate_password(attrs['password'], user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class SignInSerializer(serializers.Serializer):
    identifier = serializers.CharField(help_text='Username or email')
    password = serializers.CharField()

    def validate(self, attrs):
        identifier = attrs['identifier'].strip()
        username = identifier
        if '@' in identifier:
            match = User.objects.filter(email__iexact=identifier).first()
            if match:
                username = match.username

        user = authenticate(self.context.get('request'), username=username, password=attrs['password'])
        if user is None:
            raise serializers.ValidationError('Invalid username/email or password.')
        attrs['user'] = user
        return attrs


class GoogleSignInSerializer(serializers.Serializer):
    """Sign in or sign up with the ID token ("credential") that the Google
    Identity Services button hands the browser.

    The token is verified against GOOGLE_CLIENT_ID. An existing account with
    the same email is signed in; otherwise a new account is created.
    """

    credential = serializers.CharField()

    def validate(self, attrs):
        if not settings.GOOGLE_CLIENT_ID:
            raise serializers.ValidationError('Google sign in is not configured.')
        try:
            info = id_token.verify_oauth2_token(
                attrs['credential'], google_requests.Request(), settings.GOOGLE_CLIENT_ID,
            )
        except ValueError:
            raise serializers.ValidationError('Google sign in failed. Please try again.')
        except GoogleAuthError:
            raise serializers.ValidationError('Could not reach Google. Please try again.')

        if not info.get('email') or not info.get('email_verified'):
            raise serializers.ValidationError('Your Google account email is not verified.')
        attrs['google'] = info
        return attrs

    def create(self, validated_data):
        info = validated_data['google']
        email = info['email'].strip().lower()
        user = User.objects.filter(email__iexact=email).first()
        self.created = user is None
        if user is None:
            user = User(
                username=unique_username(email),
                email=email,
                first_name=info.get('given_name', '')[:150],
                last_name=info.get('family_name', '')[:150],
            )
            user.set_unusable_password()
            user.save()
        elif not user.is_active:
            raise serializers.ValidationError('This account is disabled.')
        return user


def unique_username(email):
    """Build a free username from the part of `email` before the @."""
    base = re.sub(r'[^\w.@+-]', '', email.split('@')[0])[:140] or 'user'
    username, n = base, 1
    while User.objects.filter(username__iexact=username).exists():
        n += 1
        username = f'{base}{n}'
    return username
