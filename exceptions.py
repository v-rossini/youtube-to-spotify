class ResponseException(Exception):
    def __init__(self, status_code, message=""):
        self.message = message
        self.status_code = status_code

    def __str__(self):
        return self.message + f"codigo da resposta: {self.status_code}"
