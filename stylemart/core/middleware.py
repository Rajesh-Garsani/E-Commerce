# core/middleware.py
from django.conf import settings

class SeparateAdminSessionMiddleware:
    """
    Give admin and user separate session cookies.
    Prevents user login/logout from affecting the Django admin site.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Default cookie for users
        cookie_name = settings.SESSION_COOKIE_NAME

        # If it's the admin site → use special cookie
        if request.path.startswith("/admin"):
            cookie_name = settings.ADMIN_SESSION_COOKIE_NAME

        # Swap cookies before processing
        if cookie_name in request.COOKIES:
            request.COOKIES[settings.SESSION_COOKIE_NAME] = request.COOKIES[cookie_name]

        response = self.get_response(request)

        # After response, rename admin cookie properly
        if request.path.startswith("/admin"):
            if settings.SESSION_COOKIE_NAME in response.cookies:
                response.cookies[settings.ADMIN_SESSION_COOKIE_NAME] = response.cookies.pop(settings.SESSION_COOKIE_NAME)

        return response
