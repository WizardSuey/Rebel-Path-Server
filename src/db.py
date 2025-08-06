import asyncpg
import yaml
import asyncio
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logging.basicConfig(level=logging.INFO, filename="log/log.log", filemode="a", format="%(asctime)s %(levelname)s %(message)s")


class Db:
    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database

    async def connect(self) -> asyncpg.Connection:
        try:
            conn = await asyncpg.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            print("Connection to Database successful")
            return conn
        except asyncpg.exceptions.ClientCannotConnectError as e:
            print(e)
            pass
    
    async def close(self, connection: asyncpg.Connection):
        try:
            await connection.close()
        except Exception as e:
            print(e)
            pass
        print("Connection to Database closed")

    async def init_db(self) -> None:
        connection = await self.connect()
        config = self.open_config("config/db.yaml")
        with open(config["SCHEMA_PATH"], "r") as f:
            schema = f.read()
        try:
            await connection.execute(schema)
            print("Database initialized successfully")
        except Exception as e:
            print("Database initialization failed")
            print(e)
        await self.close(connection)

    async def seed_db(self) -> None:
        connection = await self.connect()
        config = self.open_config("config/db.yaml")
        with open(config["SEED_PATH"], "r") as f:
            seed = f.read()
        try:
            await connection.execute(seed)
            print("Database seeded successfully")
        except Exception as e:
            print("Database seeding failed")
            print(e)
        await self.close(connection)

    async def check_user_email_exists(self, email: str) -> bool:
        """ Проверяет существует ли почта """
        connection = await self.connect()
        try:
            result = await connection.fetch("SELECT * FROM users WHERE email = $1", email)
            return len(result) > 0
        except Exception as e:
            logger.error(e)
        await self.close(connection)
        return False
    
    async def check_user_username_exists(self, username: str) -> bool:
        """ Проверяет существует ли username """
        connection = await self.connect()
        try:
            result = await connection.fetch("SELECT * FROM users WHERE username = $1", username)
            return len(result) > 0
        except Exception as e:
            logger.error(e)
        await self.close(connection)
        return False

    @staticmethod
    def open_config(path: str) -> dict:
        """ Открывает файл конфига и возвращает словарь """
        with open(path, "r") as f:
            return yaml.safe_load(f)
