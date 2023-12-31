from datetime import timedelta
import os;

baseString = os.environ["DATABASE_URL"]; #ovo je za deployment

class Configuration () :
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@{baseString}/authentication"; #ovo je za deployment
    #SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@localhost/authentication";
    JWT_SECRET_KEY = "JWT_SECRET_KEY"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta ( minutes = 60 );
    JWT_REFRESH_TOKEN_EXPIRES = timedelta ( days = 30 );
