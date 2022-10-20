import shutil

from flask import Flask;
from configuration import Configuration;
from flask_migrate import Migrate, init, migrate, upgrade;
from models import database, Role, UserRole, User;
from sqlalchemy_utils import database_exists, create_database, drop_database;

application = Flask ( __name__ );
application.config.from_object ( Configuration );

migrateObject = Migrate ( application, database );

done = False
while not done:
    try:

        if (not database_exists(application.config["SQLALCHEMY_DATABASE_URI"])):
            create_database(application.config["SQLALCHEMY_DATABASE_URI"]);

        database.init_app(application);

        with application.app_context() as context:
            init();
            migrate(message="Production migration");
            upgrade();

            adminRole = Role(name="admin");
            kupacRole = Role(name="kupac");
            magacionerRole = Role(name="magacioner");

            database.session.add(adminRole);
            database.session.add(kupacRole);
            database.session.add(magacionerRole)
            database.session.commit();

            admin = User(
                email="admin@admin.com",
                password="1",
                forename="admin",
                surname="admin",
                is_customer=False
            );

            database.session.add(admin);
            database.session.commit();

            userRole = UserRole(
                userId=admin.id,
                roleId=adminRole.id
            );
            database.session.add(userRole);
            database.session.commit();
            done = True
    except Exception as error:
        print(error)
