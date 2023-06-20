import flask;
from flask import Flask, request, Response, make_response;
from configuration import Configuration;
from models import database, Participant, Election, ElectionParticipant, Vote;
from sqlalchemy import and_, or_, func;
from flask_jwt_extended import JWTManager, jwt_required, get_jwt
from datetime import datetime, timedelta
from dateutil import parser
from time import sleep

application = Flask(__name__);
application.config.from_object(Configuration);
jwt = JWTManager(application);


@application.route("/get", methods=["POST"])
def getSomething():
    guid = request.json.get("guid", "");
    searchString = f"%{guid}%";

    votes = Vote.query.join(ElectionParticipant, Vote.participantId == ElectionParticipant.participantId).filter(Vote.guid.like(searchString))
    return flask.jsonify(votes = votes), 200;

if (__name__ == "__main__"):
    database.init_app(application);
    application.run(debug=True,host = "0.0.0.0", port=5004);
