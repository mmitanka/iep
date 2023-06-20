import flask;
from flask import Flask, request, Response;
from configuration import Configuration;
from models import database, User, UserRole;
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, \
    get_jwt_identity;
from sqlalchemy import and_;
from re import compile;

application = Flask(__name__);
application.config.from_object(Configuration);
jwt = JWTManager(application);

def calkK(jmbg):
    k = 0;
    n= 7;
    try:
      for i in range(0, 6):
        k += n * (int(jmbg[i]) + int(jmbg[i+6]));
        n -= 1;
    except ValueError:
        return -1;
    return 11 - k % 11;

@application.route("/register", methods=["POST"])
def register():
    jmbg = request.json.get("jmbg", "");
    forename = request.json.get("forename", "");
    surname = request.json.get("surname", "");
    email = request.json.get("email", "");
    password = request.json.get("password", "");

    # provere za required
    jmbgEmpty = len(jmbg) == 0;
    forenameEmpty = len(forename) == 0;
    surnameEmpty = len(surname) == 0;
    emailEmpty = len(email) == 0;
    passwordEmpty = len(password) == 0;

    # return bad response
    if (jmbgEmpty):
        res = "Field jmbg is missing.";
        return flask.jsonify(message=res), 400;
    elif (forenameEmpty):
        res = "Field forename is missing.";
        return flask.jsonify(message=res), 400;

    elif (surnameEmpty):
        res = "Field surname is missing.";
        return flask.jsonify(message=res), 400;

    elif (emailEmpty):
        res = "Field email is missing.";
        return flask.jsonify(message=res), 400;

    elif (passwordEmpty):
        res = "Field password is missing."
        return flask.jsonify(message=res), 400;

    # inavlid jmbg provera
    JMBG_REGEX = compile('((0[1-9]|[1-2][0-9]|30|31)(0[1-9]|1[0-2])([0-9]{3})([7-9][0-9])([0-9]{3})([0-9]))');
    match_jmbg= JMBG_REGEX.match(jmbg);
    if (match_jmbg is None):
        return flask.jsonify(message="Invalid jmbg."), 400;
    k = int(jmbg[12]);
    m = calkK(jmbg);
    if ( m == 10 or m == 11):
        if(k!=0):
            return flask.jsonify(message="Invalid jmbg."), 400;
    else:
        if(k!=m):
            return flask.jsonify(message="Invalid jmbg."), 400;
    # invalid email
    email_regex = compile(r"[^@]+@[^@]+\.[^@]{2,}")
    match_email = email_regex.match(email);
    if (match_email is None):
        return flask.jsonify(message="Invalid email."), 400;

    PASSWORD_REGEX = compile(r'\A(?=\S*?\d)(?=\S*?[A-Z])(?=\S*?[a-z])\S{8,}\Z');
    match_password = PASSWORD_REGEX.match(password);
    # invalid password format
    if (not match_password):
        return flask.jsonify(message="Invalid password."), 400;

    # check if user already exists
    user = User.query.filter_by(email=email).first();
    if (user):
        return flask.jsonify(message="Email already exists."), 400;

    user = User(email=email, password=password, forename=forename, surname=surname, jmbg=jmbg);
    database.session.add(user);
    database.session.commit();

    user_role1 = UserRole(userId=user.id, roleId=2);
    database.session.add(user_role1);
    database.session.commit();

    return Response(status=200);


@application.route("/login", methods=["POST"])
def login():
    email = request.json.get("email", "");
    password = request.json.get("password", "");
    emailEmpty = len(email) == 0;
    passwordEmpty = len(password) == 0;

    # field missing
    if (emailEmpty):
        res = "Field email is missing."
        return flask.jsonify(message=res), 400;

    elif (passwordEmpty):
        res = "Field password is missing."
        return flask.jsonify(message=res), 400;

    # invalid email

    email_regex = compile(r"[^@]+@[^@]+\.[^@]{2,}")
    match_email = email_regex.match(email);
    if (match_email is None):
        return flask.jsonify(message="Invalid email."), 400;

    # invalid credentials
    user = User.query.filter(and_(User.email == email, User.password == password)).first();

    if (not user):
        return flask.jsonify(message="Invalid credentials."), 400;


    additionalClaims = {
        "jmbg": user.jmbg,
        "forename": user.forename,
        "surname": user.surname,
        "email": user.email,
        "password": user.password,
        "roles": [str(role) for role in user.roles]
    }
    accessToken = create_access_token(identity=user.email, additional_claims=additionalClaims);
    refreshToken = create_refresh_token(identity=user.email, additional_claims=additionalClaims);

    return flask.jsonify(accessToken=accessToken, refreshToken=refreshToken), 200;


@application.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    # headerfield authorisation missing
    authorisation = request.headers.get("Authorization", "")
    authorisationEmpty = len(authorisation) == 0;

    if (authorisationEmpty):
        res = "Missing Authorization Header";
        return flask.jsonify(msg=res), 401;

    identity = get_jwt_identity();
    refreshClaims = get_jwt();

    additionalClaims = {
        "jmbg": refreshClaims["jmbg"],
        "forename": refreshClaims["forename"],
        "surname": refreshClaims["surname"],
        "email": refreshClaims["email"],
        "password": refreshClaims["password"],
        "roles": refreshClaims["roles"]
    }
    accessToken = create_access_token(identity=identity, additional_claims=additionalClaims);
    return flask.jsonify(accessToken=accessToken), 200;

@application.route("/delete", methods=["POST"])
@jwt_required()
def delete():
    # headerfield authorisation missing status 401
    authorisation = request.headers.get("Authorization", "")
    authorisationEmpty = len(authorisation) == 0;

    if (authorisationEmpty):
        res = "Missing Authorization Header.";
        return flask.jsonify(msg=res), 401;

    email = request.json.get("email", "");
    emailEmpty = len(email) == 0;

    # field missing
    if (emailEmpty):
        res = "Field email is missing."
        return flask.jsonify(message=res), 400;

    # invalid email
    email_regex = compile(r"[^@]+@[^@]+\.[^@]{2,}")
    match_email = email_regex.match(email);
    if (match_email is None):
        return flask.jsonify(message="Invalid email."), 400;

    # invalid credentials
    user = User.query.filter((User.email == email)).first();

    if (not user):
        return flask.jsonify(message="Unknown user."), 400;

    #delete first from userrole
    UserRole.query.filter(UserRole.userId == user.id).delete();

    user = User.query.filter((User.email == email)).delete();
    database.session.commit();

    return Response(status=200);

if (__name__ == "__main__"):
    database.init_app(application);
    application.run(debug=True,host = "0.0.0.0", port=5002);
