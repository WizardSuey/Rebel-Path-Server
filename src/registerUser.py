import asyncio
import enum
import hashlib


class RegisterUser:
    def __init__(self, email, username, password):
        self.email = email
        self.username = username
        self.password = password
    
    class ResponseCodes(enum.Enum):
            SUCCESS_REG =                       200

            INCORRECT_EMAIL_FORMAT =            300
            INCORRECT_EMAIL_EXISTS =            301

            INCORRECT_USERNAME_EXISTS =         302
            INCORRECT_USERNAME_LESS_LEN =       303
            INCORRECT_USERNAME_GREATER_LEN =    304

            INCORRECT_PASSWORD_LESS_LEN =       305
            INCORRECT_PASSWORD_GREATER_LEN =    306

            NONE_TYPE_ERROR =                   400

    async def registerUser(self, email: str, username: str, password: str):
        pass