
import secrets

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail


def send_magic_link_email(email):
    pin = f"{secrets.randbelow(1000000):06d}"

    # XXX: in a later phase inactive users should be deleted periodically
    user, _ = User.objects.get_or_create(username=email, defaults={"email": email, "is_active": False})
    user.set_password(pin)
    user.save()

    link = f"{settings.PUBLIC_URL}/login?email={email}&pin={pin}"

    send_mail(
        "Your Magic Login Link",
        (
            f"Click here to login on moviedb.nl: {link}\n\n"
            "This link is valid forever and can be used to login at any time."
            "Bookmark this link for easy access."
        ),
        "noreply@moviedb.nl",
        [email],
        fail_silently=False,
    )

def ensure_activate_user(user: User):
    """Logging in for first time activates the user.

    This allows to track which Users are active and which are not.
    """
    if user.is_active:
        return
    user.is_active = True
    user.save()



def _get_django_request_with_session(session_key=None):
    from django.conf import settings
    from django.contrib.auth.middleware import AuthenticationMiddleware
    from django.contrib.sessions.middleware import SessionMiddleware
    from django.http import HttpRequest

    request = HttpRequest()
    if session_key:
        request.COOKIES[settings.SESSION_COOKIE_NAME] = session_key
        
    # Run SessionMiddleware to populate request.session
    # We pass 'lambda r: None' as get_response because we only care about process_request
    middleware = SessionMiddleware(lambda r: None)
    middleware.process_request(request)
    
    # Run AuthenticationMiddleware to populate request.user
    middleware = AuthenticationMiddleware(lambda r: None)
    middleware.process_request(request)
    
    return request


def start_django_session(user):
    from django.contrib.auth import login
    
    request = _get_django_request_with_session()
    
    # Ensure user has a backend set
    if not hasattr(user, 'backend'):
        from django.conf import settings
        user.backend = settings.AUTHENTICATION_BACKENDS[0]

    login(request, user)
    request.session.save()
    
    return request.session.session_key


def get_user_from_session_key(session_key):
    if not session_key:
        return None
        
    request = _get_django_request_with_session(session_key)
    
    if request.user.is_authenticated:
        return request.user
    return None
