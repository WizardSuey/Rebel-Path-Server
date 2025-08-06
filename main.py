import socket
import select
import yaml
import json
import asyncio
import sys
import logging

from requestCode import RequestCode
from src.registerUser import RegisterUser
from src.db import Db

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logging.basicConfig(level=logging.INFO, filename="log/log.log", filemode="a", format="%(asctime)s %(levelname)s %(message)s")

class Server:
    def __init__(self, address: str, port: str):
        self.address: str = address
        self.port: str = port
        self.socket: socket.socket = None
        self.__MAX_CONNECTIONS = 10
        self.__INPUTS = []
        self.__OUTPUTS = []

    def __init_socket(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(False)
        try:
            self.socket.bind((self.address, self.port))
        except socket.error as e:
            logger.error(str(e))
            exit(1)

        self.socket.listen(self.__MAX_CONNECTIONS)
    
    def __handle_readables(self, readables: list[socket.socket], server: socket.socket) -> None:
        """ Обработка появления событий на входах """
        for resource in readables:

            # Если событие исходит от серверного сокета, то мы получаем новое подключение
            if resource is server:
                connection, client_address = resource.accept()
                connection.setblocking(False)
                self.__INPUTS.append(connection)
                logger.info(f"New connection from {client_address}")

            # Если событие исходит не от серверного сокета, но сработало прерывание на наполнение входного буффера
            else:
                dataJsonStr: str = ""
                try:
                    dataJsonStr = resource.recv(1024).decode("utf-8")

                # Если сокет был закрыт на другой стороне
                except ConnectionResetError:
                    logger.info(f"Connection closed by {resource.getpeername()}")
                    self.__clear_resource(resource)

                if dataJsonStr:
                    logger.info(f"Getting data: {str(dataJsonStr)} from {resource.getpeername()}")

                    try:
                        """ Парсим строку json и дойстаём от туда код запроса и данные """
                        dataJson: dict = json.loads(dataJsonStr)

                        #################################
                        # Переключатель запросов
                        if dataJson["code"] is RequestCode.REGISTER_USER:
                            userAddr = resource.getpeername()
                            registerUser = RegisterUser(userAddr, dataJson["Email"], dataJson["Username"], dataJson["Password"])
                            statusCode = asyncio.run(registerUser.registerUser())

                            sendData = {
                                "code": statusCode
                            }

                            sendDataJson = json.dumps(sendData)
                            try:
                                resource.send(bytes(sendDataJson, encoding="utf-8"))
                            except OSError:
                                self.__clear_resource(resource)
                        # Переключатель запросов
                        #################################

                    except json.JSONDecodeError:
                        logger.error(f"Invalid json from client {resource.getpeername()}")
                        continue

                    # Говорим о том, что мы будем еще и писать в данный сокет
                    if resource not in self.__OUTPUTS:
                        self.__OUTPUTS.append(resource)
                
                # Если данных нет, ничего не делаем
                else:
                    pass


    def handle_writables(self, writables: list[socket.socket]) -> None:
        """  Данное событие возникает когда в буффере на запись освобождается место """
        for resource in writables:
            try:
                resource.send(bytes("Hello from server!", encoding="utf-8"))
            except OSError:
                self.__clear_resource(resource)

    def __clear_resource(self, resource: socket.socket) -> None:
        """ Метод очистки ресурсов использования сокета """
        try:
            peer = resource.getpeername()
        except OSError:
            peer = "<unknown>"
        if resource in self.__OUTPUTS:
            self.__OUTPUTS.remove(resource)
        if resource in self.__INPUTS:
            self.__INPUTS.remove(resource)
        try:
            resource.close()
        except Exception:
            pass

        logger.info(f"Closing connection {peer}")

    def launch(self) -> None:
        self.__init_socket()
        self.__INPUTS.append(self.socket)

        logger.info(f"Server started on {self.address}:{self.port}\nTo stop the server press Ctrl+C\n")

        try:
            while self.__INPUTS:
                readables, writables, exceptional = select.select(self.__INPUTS, self.__OUTPUTS, self.__INPUTS)
                self.__handle_readables(readables, self.socket)
                self.handle_writables(writables)
        except KeyboardInterrupt:
            logger.info("\nServer stopped")

    def init_db(self):
        config = Db.open_config("config/db.yaml")
        db = Db(host=config["HOST"], port=config["PORT"], user=config["USER"], password=config["PASSWORD"], database=config["DATABASE"])
        asyncio.run(db.init_db())

    def seed_db(self):
        config = Db.open_config("config/db.yaml")
        db = Db(host=config["HOST"], port=config["PORT"], user=config["USER"], password=config["PASSWORD"], database=config["DATABASE"])
        asyncio.run(db.seed_db())

    @staticmethod
    def open_config(path: str) -> dict:
        """ Открывает файл конфига и возвращает словарь """
        with open(path, "r") as f:
            return yaml.safe_load(f)


if __name__ == "__main__":
    config = Server.open_config("config/server.yaml")
    server = Server(config["ADDRESS"], config["PORT"])
    for i, arg in enumerate(sys.argv):
        if arg == "--version":
            print(config["VERSION"])
            exit(0)
        if arg == "--init_db":
            server.init_db()
            exit(0)
        if arg == "--seed_db":
            server.seed_db()
            exit(0)
    server.launch()