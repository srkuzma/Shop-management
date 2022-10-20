from datetime import timedelta;
import os;

databaseUrl = os.environ["DATABASE_URL"];
redisUrl = os.environ["REDIS_URL"];

class Configuration ( ):
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@{databaseUrl}/prodavnica";
    JWT_SECRET_KEY = "JWT_SECRET_KEY"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta ( minutes = 60 );
    JWT_REFRESH_TOKEN_EXPIRES = timedelta ( days = 30 );
    REDIS_HOST = redisUrl
    REDIS_IME_LIST = "imena";
    REDIS_KATEGORIJE_LIST = "kategorije"
    REDIS_KOLICINE_LIST = "kolicine"
    REDIS_NABAVNECENE_LIST = "nabavnecene"