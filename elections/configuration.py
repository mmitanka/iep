from datetime import timedelta
import os;

baseString = os.environ["DATABASE_URL"];

class Configuration () :
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@{baseString}/elections";
    #SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@localhost:3307/elections";
    JWT_SECRET_KEY = "JWT_SECRET_KEY"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta ( minutes = 60 );
    JWT_REFRESH_TOKEN_EXPIRES = timedelta ( days = 30 );
    REDIS_HOST = "localhost";