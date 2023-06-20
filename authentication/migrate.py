from flask import Flask;
from configuration import Configuration;
from flask_migrate import Migrate,init,migrate,upgrade;
from models import database, User, Role, UserRole;
from sqlalchemy_utils import database_exists, create_database, drop_database;

application = Flask(__name__);
application.config.from_object(Configuration);

migrateObject = Migrate(application, database);

if (not database_exists("mysql+pymysql://root:root@authenticationDatabase/authentication")):
    create_database("mysql+pymysql://root:root@authenticationDatabase/authentication");

database.init_app(application);

with application.app_context() as context:
    init();
    migrate(message="Migr authentication");
    upgrade();

    adminRole = Role(id=1, name="administrator");
    zvanicnikRole = Role(id=2, name="zvanicnik");

    database.session.add(adminRole);
    database.session.add(zvanicnikRole);

    database.session.commit();

    admin = User(email="admin@admin.com", jmbg="0000000000000", forename="admin", surname="admin", password="1");
    database.session.add(admin);
    database.session.commit();

    userRole = UserRole(userId=admin.id, roleId=adminRole.id);
    database.session.add(userRole);
    database.session.commit();