import json, base64
from typing_extensions import Literal
from rest_framework import authentication
from rest_framework import exceptions
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest


class ServerUser(AnonymousUser):
    @property
    def is_authenticated(self) -> Literal[False]:
        return True


class GaelOPathologyProcessingAuthentication(authentication.BasicAuthentication):

    def authenticate(self, request :HttpRequest):
        #Exception for root url
        if(request.path == '/'):
            return (ServerUser(), None)
        
        authorization_header: str = request.headers.get('Authorization')
        if (authorization_header == None):
            raise exceptions.AuthenticationFailed('No such user or wrong password')
        
        authorization_header = authorization_header.replace("Basic ", "")
        message = base64.b64decode(authorization_header).decode("utf-8")
        login_password = message.split(':')
        username = login_password[0]
        password = login_password[1]
        user_dictionary: dict = json.loads(settings.REGISTERED_USERS)
        if not username in list(user_dictionary.keys()):
            return None
        
        if (password != user_dictionary.get(username)):
            raise exceptions.AuthenticationFailed('No such user')
        
        return (ServerUser(), None)
