import enum


class RequestCode(enum.Enum):
    """  Коды запросов от пользователя"""
    REGISTER_USER =         1
    AUTH_USER =             2