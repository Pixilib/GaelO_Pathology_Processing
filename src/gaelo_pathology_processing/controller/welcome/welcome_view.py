from rest_framework.views import APIView
from rest_framework.request import Request
from django.http import HttpResponse


class WelcomeView(APIView):

    def get(self, request: Request) -> HttpResponse:
        return HttpResponse('Welcome to GaelO Pathology Processing Backend !')