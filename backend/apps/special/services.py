"""A private page for one person only: the account whose email is
SPECIAL_EMAIL in backend/.env. Nothing else in Circle links to it; that
person is sent to it right after they sign in or sign up."""

from django.conf import settings

# Set in the session when the special person signs in; cleared once the
# page has been shown.
SESSION_KEY = 'special_page_pending'


def is_special(user):
    email = settings.SPECIAL_EMAIL.strip().lower()
    return bool(email) and user.is_authenticated and (user.email or '').strip().lower() == email


def remember_to_show(sender, request, user, **kwargs):
    """user_logged_in handler (password, Google and new sign ups)."""
    if request is not None and is_special(user):
        request.session[SESSION_KEY] = True
