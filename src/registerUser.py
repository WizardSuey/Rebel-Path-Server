import asyncio
import enum
import re
import json
import logging
import hashlib
import uuid

from .db import Db


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logging.basicConfig(level=logging.INFO, filename="log/log.log", filemode="a", format="%(asctime)s %(levelname)s %(message)s")


class RegisterUser:
    def __init__(self, userAddr: tuple, email, username, password):
        self.__useraddr = userAddr
        self.__email = email
        self.__username = username
        self.__password = password

        self.__email_pattern = "^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$"
        self.__max_email_len =      254

        self.__min_password_len =   8
        self.__max_password_len =   32

        self.__min_username_len =   3
        self.__max_username_len =   32
    
    class ResponseCode(enum.Enum):
            SUCCESS_REG =                       200

            INCORRECT_EMAIL_FORMAT =            300
            INCORRECT_EMAIL_EXISTS =            301
            INCORRECT_MAX_EMAIL_LEN =           302

            INCORRECT_USERNAME_EXISTS =         303
            INCORRECT_USERNAME_LESS_LEN =       304
            INCORRECT_USERNAME_GREATER_LEN =    305

            INCORRECT_PASSWORD_LESS_LEN =       306
            INCORRECT_PASSWORD_GREATER_LEN =    307

            NONE_TYPE_ERROR =                   400

    def __hash_password(self, password: str) -> str:
        salt = uuid.uuid4().hex # uuid используется для генерации случайного числа
        return hashlib.sha256(salt.encode() + password.encode()).hexdigest() + ':' + salt
    
    def __check_hash_password(self, hash_password: str, password: str) -> bool:
        password, salt = hash_password.split(':')
        return password == hashlib.sha256(salt.encode() + password.encode()).hexdigest()
    
    async def registerUser(self) -> ResponseCode:
        """ Регистрируем нового пользователя и возвращаем код ответа """
        logger.info(f"Start registration new user - {self.__useraddr} with email: {self.__email}, username: {self.__username}, password: {self.__password}")

        db_conf = Db.open_config("config/db.yaml")
        db = Db(host=db_conf["HOST"], port=db_conf["PORT"], user=db_conf["USER"], password=db_conf["PASSWORD"], database=db_conf["DATABASE"])

        # Проверки 
        #email
        if not re.match(self.__email_pattern, self.__email):
            return self.ResponseCode.INCORRECT_EMAIL_FORMAT
        if await db.check_user_email_exists(self.__email):
            return self.ResponseCode.INCORRECT_EMAIL_EXISTS
        if len(self.__email) > self.__max_email_len:
            return self.ResponseCode.INCORRECT_MAX_EMAIL_LEN
        
        #username
        if await db.check_user_username_exists(self.__username):
            return self.ResponseCode.INCORRECT_USERNAME_EXISTS
        if len(self.__username) < self.__min_username_len:
            return self.ResponseCode.INCORRECT_USERNAME_LESS_LEN
        if len(self.__username) > self.__max_username_len:
            return self.ResponseCode.INCORRECT_USERNAME_GREATER_LEN
        
        #password
        if len(self.__password) < self.__min_password_len:
            return self.ResponseCode.INCORRECT_PASSWORD_LESS_LEN
        if len(self.__password) > self.__max_password_len:
            return self.ResponseCode.INCORRECT_PASSWORD_GREATER_LEN
        #


        # Запись пользователя в БД
        try:
            hash_password = self.__hash_password(self.__password)
            connection = await db.connect()
            await connection.execute(
                "INSERT INTO users (email, username, password_digest) VALUES ($1, $2, $3)", 
                self.__email, 
                self.__username, 
                hash_password
            )
            await db.close(connection)
            logger.info(f"User registered - {self.__useraddr} with email: {self.__email}, username: {self.__username}, password: {self.__password}")
        except Exception as e:
            logger.error(e)
            return self.ResponseCode.NONE_TYPE_ERROR

        
        return self.ResponseCode.SUCCESS_REG