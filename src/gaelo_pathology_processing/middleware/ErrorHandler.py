import traceback
from django.conf import settings
from ..exceptions.gaelo_pathology_processing_exceptions import GaelOException

class ErrorHandlerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if settings.DEBUG:
            if exception:
                # Format your message here
                message = "**{url}**\n\n{error}\n\n````{tb}````".format(
                    url=request.build_absolute_uri(),
                    error=repr(exception),
                    tb=traceback.format_exc()
                )
                # Do now whatever with this message
                # e.g. requests.post(<slack channel/teams channel>, data=message)
        else:
            if isinstance(exception, GaelOException):
                return exception.get_response()
