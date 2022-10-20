from flask import Flask, request, Response, jsonify, json;
from configuration import Configuration;
from models import database, User, UserRole;
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, get_jwt_identity;
from sqlalchemy import and_;
import re
from authentication.decorator import roleCheck

application = Flask ( __name__ );
application.config.from_object ( Configuration );
jwt = JWTManager(application)

@application.route ( "/register", methods = ["POST"] )
def register ( ):
    email = request.json.get ( "email", "" );
    password = request.json.get ( "password", "" );
    forename = request.json.get ( "forename", "" );
    surname = request.json.get ( "surname", "" );
    is_customer = request.json.get ( "isCustomer", "" );

    missingField = ""

    forenameEmpty = len ( forename ) == 0;
    missingField = "forename" if forenameEmpty and missingField == "" else missingField

    surnameEmpty = len ( surname ) == 0;
    missingField = "surname" if surnameEmpty and missingField == "" else missingField

    emailEmpty = len(email) == 0;
    missingField = "email" if emailEmpty and missingField == "" else missingField

    passwordEmpty = len(password) == 0;
    missingField = "password" if passwordEmpty and missingField == "" else missingField

    is_customer_Empty = is_customer != False and is_customer != True
    missingField = "isCustomer" if is_customer_Empty and missingField == "" else missingField

    response = {"message": "Field " + missingField + " is missing."}
    if missingField != "":
        return Response(json.dumps(response), status = 400)

    if (not re.match("[^@]+@[^@]+\.[^@]{2,}", email)):
        response = {"message": "Invalid email."}
        return Response ( json.dumps(response), status = 400 );

    def bad_format(password):
        ok_length = len(password) >= 8
        has_digit = re.search(".*[0-9].*", password) != None
        has_capital = re.search(".*[a-z].*", password) != None
        has_small = re.search(".*[A-Z].*", password) != None
        return not(ok_length and has_digit and has_small and has_capital)

    if bad_format(password):
        response = {"message": "Invalid password."}
        return Response ( json.dumps(response), status = 400 );

    email_exists = User.query.filter(User.email == email).all()

    if email_exists:
        response = {"message": "Email already exists."}
        return Response(json.dumps(response), status=400);

    user = User ( email = email, password = password, forename = forename, surname = surname, is_customer=is_customer );
    database.session.add ( user );
    database.session.commit ( );

    userRole = UserRole ( userId = user.id, roleId = 2 if is_customer else 3);
    database.session.add ( userRole );
    database.session.commit ( );

    return Response ( status = 200 );

jwt = JWTManager ( application );

@application.route ( "/login", methods = ["POST"] )
def login ( ):
    email = request.json.get ( "email", "" );
    password = request.json.get ( "password", "" );

    missingField = ""

    emailEmpty = len(email) == 0;
    missingField = "email" if emailEmpty and missingField == "" else missingField

    passwordEmpty = len(password) == 0;
    missingField = "password" if passwordEmpty and missingField == "" else missingField

    response = {"message": "Field " + missingField + " is missing."}
    if missingField != "":
        return Response(json.dumps(response), status=400)

    if (not re.match("[^@]+@[^@]+\.[^@]{2,}", email)):
        response = {"message": "Invalid email."}
        return Response(json.dumps(response), status=400);

    user = User.query.filter ( and_ ( User.email == email, User.password == password ) ).first ( );

    if ( not user ):
        response = {"message": "Invalid credentials."}
        return Response(json.dumps(response), status=400);

    additionalClaims = {
            "forename": user.forename,
            "surname": user.surname,
            "isCustomer": user.is_customer,
            "roles": [str(role) for role in user.roles]
    }

    accessToken = create_access_token ( identity = user.email, additional_claims = additionalClaims );
    refreshToken = create_refresh_token ( identity = user.email, additional_claims = additionalClaims );

    # return Response ( accessToken, status = 200 );
    return jsonify ( accessToken = accessToken, refreshToken = refreshToken );

@application.route ( "/refresh", methods = ["POST"] )
@jwt_required ( refresh = True )
def refresh ( ):
    identity = get_jwt_identity ( );
    refreshClaims = get_jwt ( );

    additionalClaims = {
            "forename": refreshClaims["forename"],
            "surname": refreshClaims["surname"],
            "isCustomer": refreshClaims["isCustomer"],
            "roles": refreshClaims["roles"]
    };

    return jsonify(accessToken = create_access_token(identity = identity, additional_claims = additionalClaims ))

@application.route ( "/delete", methods = ["POST"] )
@roleCheck ( role = "admin" )
def delete ( ):
    email = request.json.get("email", "");
    emailEmpty = len(email) == 0;

    missingField = "email" if emailEmpty else ""

    response = {"message": "Field " + missingField + " is missing."}
    if missingField != "":
        return Response(json.dumps(response), status=400)

    if (not re.match("[^@]+@[^@]+\.[^@]{2,}", email)):
        response = {"message": "Invalid email."}
        return Response ( json.dumps(response), status = 400 );

    user = User.query.filter(User.email == email).first();

    if not user:
        response = {"message": "Unknown user."}
        return Response(json.dumps(response), status=400);

    database.session.delete(user);
    database.session.commit();

    return Response(status=200);

@application.route ( "/", methods = ["GET"] )
def index ( ):
    return "Hello world!";

if ( __name__ == "__main__" ):
    database.init_app ( application );
    application.run ( debug = True, host="0.0.0.0", port = 5000 );