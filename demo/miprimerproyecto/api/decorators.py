import base64
from builtins import Exception
from functools import wraps

from api.logger import ApiAuthenticationLogger
from django.http import HttpResponse


def http_basic_auth(func):
    @wraps(func)
    def _decorator(request, *args, **kwargs):
        # base64 for kibo user - a2libzphQnNhZDU0c3NTZVQ5NHh4cXVsMDkyNDg2QUJMTmlx
        if 'HTTP_AUTHORIZATION' in request.META:
            allowed_users = {
                'helloworld': 'VrDlKsoRlluYuQkoFIdcYoFS9w1XCT47',
            }
            read_only_users = [
                'helloworld',
            ]
            authmeth, auth = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
            if authmeth.lower() == 'basic':
                try:
                    auth = base64.b64decode(auth).decode()
                except Exception as e:
                    ApiAuthenticationLogger.log("http_basic_auth() - error decoding base64 auth string: {0}".format(e))
                    return HttpResponse(status=400, reason="Authorization string does not decode")
                username, password = auth.split(':', 1)
                ApiAuthenticationLogger.log('http_basic_auth() - username: {0}'.format(username))
                if username in allowed_users and password == allowed_users[username]:
                    ApiAuthenticationLogger.log("http_basic_auth() - user {0} authenticated".format(username))
                    ApiAuthenticationLogger.log(
                        "http_basic_auth() - calling function '{0}' with request method {1}".format(func.__name__,
                                                                                                    request.method))
                    # Handle read-only users
                    if username in read_only_users:
                        # Allow access to any API using the GET method
                        if request.method == 'GET':
                            pass
                        # Allow access to the members_get_or_update API using the POST method (it's read-only)
                        elif request.method == 'POST':
                            pass
                        # Otherwise deny access
                        else:
                            ApiAuthenticationLogger.log(
                                "http_basic_auth() - read-only user '{}' not authorized to access '{}' with method '{}'".format(
                                    username, func.__name__, request.method))
                            return HttpResponse(status=401, reason="Read only user not authorized")

                    return func(request, *args, **kwargs)
                else:
                    ApiAuthenticationLogger.log("http_basic_auth() - user {0} failed authentication".format(username))
        response = HttpResponse(status=401)
        return response

    return _decorator