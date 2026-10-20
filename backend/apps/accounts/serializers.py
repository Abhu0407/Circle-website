import re

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from rest_framework import serializers

from apps.communities.models import Category, Community
from apps.communities.serializers import CommunitySerializer

from .models import AVATARS, avatar_url

User = get_user_model()



def avatar_choices():
    """[{value, label, url}] for the avatar picker."""
    return [{'value': key, 'label': label, 'url': avatar_url(key)} for key, label in AVATARS]


class UserSerializer(serializers.ModelSerializer):
    join_community = CommunitySerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'name', 'email', 'first_name', 'last_name',
            'interested_category', 'join_community', 'location', 'latitude', 'longitude',
            'avatar', 'profile_picture',
        )


class ProfileSerializer(serializers.ModelSerializer):
    """What a signed-in user may change about themselves.

    The email is read-only. A new username must not be taken by anyone else
    (compared case-insensitively, like sign in does). `avatar` is a key from
    AVATARS, or "" to go back to the initial.
    """

    avatar = serializers.ChoiceField(
        choices=AVATARS, allow_blank=True, required=False,
        error_messages={'invalid_choice': 'Pick one of the avatars.'},
    )
    # Interests are community categories (keys such as "sports").
    interested_category = serializers.ListField(
        child=serializers.ChoiceField(
            choices=Category.choices,
            error_messages={'invalid_choice': 'Pick interests from the list of categories.'},
        ),
        required=False,
    )
    # Ids of the communities to stay in; leaving one = sending the list without it.
    join_community = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Community.objects.all(), required=False,
    )

    class Meta:
        model = User
        fields = (
            'id', 'username', 'name', 'email', 'location', 'latitude', 'longitude',
            'interested_category', 'join_community', 'avatar',
        )
        read_only_fields = ('id', 'email')
        # Replace the default case-sensitive unique check with validate_username.
        extra_kwargs = {'username': {'validators': [UnicodeUsernameValidator()]}}

    def validate_username(self, value):
        value = value.strip()
        if username_taken(value, exclude=self.instance):
            raise serializers.ValidationError('This username is already taken.')
        return value

    def validate_interested_category(self, value):
        """Drop duplicates, keeping the order they were picked in."""
        return list(dict.fromkeys(value))

    def validate(self, attrs):
        # A map point needs both halves.
        lat, lng = attrs.get('latitude', ...), attrs.get('longitude', ...)
        if (lat is ...) != (lng is ...) or (lat is None) != (lng is None):
            raise serializers.ValidationError({'location': 'Send latitude and longitude together.'})
        return attrs


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
                name=info.get('name', '')[:150],
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


def username_taken(username, exclude=None):
    """True if another account already uses `username` (ignoring case)."""
    qs = User.objects.filter(username__iexact=username)
    if exclude is not None:
        qs = qs.exclude(pk=exclude.pk)
    return qs.exists()
