import socket
import select
import yaml
import json
import asyncio

from requestCodes import RequestCodes
from registerUser import RegisterUser

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
            print(str(e))
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
                print(f"New connection from {client_address}")

            # Если событие исходит не от серверного сокета, но сработало прерывание на наполнение входного буффера
            else:
                dataJsonStr: str = ""
                try:
                    dataJsonStr = resource.recv(1024).decode("utf-8")

                # Если сокет был закрыт на другой стороне
                except ConnectionResetError:
                    pass

                if dataJsonStr:
                    print(f"Getting data: {str(dataJsonStr)} from {resource.getpeername()}")

                    try:
                        dataJson: dict = json.loads(dataJsonStr)
                        print(dataJson)
                    except json.JSONDecodeError:
                        print("Invalid json")
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

        print(f"Closing connection {peer}")

    def launch(self) -> None:
        self.__init_socket()
        self.__INPUTS.append(self.socket)

        print(f"Server started on {self.address}:{self.port}\nTo stop the server press Ctrl+C\n")

        try:
            while self.__INPUTS:
                readables, writables, exceptional = select.select(self.__INPUTS, self.__OUTPUTS, self.__INPUTS)
                self.__handle_readables(readables, self.socket)
                self.handle_writables(writables)
        except KeyboardInterrupt:
            print("\nServer stopped")

    @staticmethod
    def open_config(path: str) -> dict:
        """ Открывает файл конфига и возвращает словарь """
        with open(path, "r") as f:
            return yaml.safe_load(f)


if __name__ == "__main__":
    config = Server.open_config("config/server.yaml")
    server = Server(config["ADDRESS"], config["PORT"])
    server.launch()