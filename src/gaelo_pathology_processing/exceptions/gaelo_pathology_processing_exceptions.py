from django.http import HttpResponse

class GaelOException(Exception):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code

    def get_response(self):
        return HttpResponse({'errorMessage:': self.args}, content_type='application/json; charset=utf-8', status=self.status_code)

class GaelOBadRequestException(GaelOException):
    def __init__(self, message):
        super().__init__(message, 400)

class GaelONotFoundException(GaelOException):
    def __init__(self, message):
        super().__init__(message, 404)

class GaelOConflictException(GaelOException):
    def __init__(self, message):
        super().__init__(message, 409)

class GaeloInternalServerErrorException(GaelOException):
    def __init__(self, message):
        super().__init__(message, 500)


