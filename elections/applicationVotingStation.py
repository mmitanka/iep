import flask;
from flask import Flask, request, Response;
from configuration import Configuration;
from models import database, Vote, Election;
from flask_jwt_extended import JWTManager, jwt_required, get_jwt;
from redis import Redis;
import io;
import csv;
import os;

application = Flask(__name__);
application.config.from_object(Configuration);
jwt = JWTManager(application);

#VRATI POSLE ZBOG DEPLOYMENT
redishost = os.environ["redisHost"];

def getParticipantId (electionId, pollNum) :
    election = Election.query.filter(Election.id==electionId).first();
    num = 1 ;
    for part in election.participants:
        if(num == pollNum):
            return part.id;
        num += 1;


@application.route("/vote", methods=["POST"])
@jwt_required()
def vote () :
        # header field authorisation missing status 401
        authorisation = request.headers.get("Authorization", "")
        authorisationEmpty = len(authorisation) == 0;

        if (authorisationEmpty):
            res = "Missing Authorization Header";
            return flask.jsonify(msg=res), 401;

        try:
            if (not (request.files["file"])):
                return flask.jsonify(message="Field file missing."), 400
        except:
            return flask.jsonify(message="Field file is missing."), 400

        claims = get_jwt();
        ellectionOfficialJmbg = claims["jmbg"];


        with Redis(host=redishost) as redis:
            #here i will use redis.rpush data from
            #csv file, vazno da pamtis i id ovog koji se ulogovao
            #to ces preko jwt identity
            try:
                if (not(request.files["file"])):
                    return flask.jsonify(message="Field file is missing."), 400;
            except:
                return flask.jsonify(message="Field file is missing."), 400;

            content = request.files["file"].stream.read().decode("utf-8");
            stream = io.StringIO(content);
            reader = csv.reader(stream);

            votes = [];
            line_cnt = 0;

            for row in reader:
                #provere
                try:
                    if (len(row) != 2):
                        return flask.jsonify(message=f"Incorrect number of values on line {line_cnt}."), 400;
                    elif (int(row[1]) <= 0 or row[1] == ""):
                        return flask.jsonify(message=f"Incorrect poll number on line {line_cnt}."), 400;
                except:
                    return flask.jsonify(message=f"Incorrect poll number on line {line_cnt}."), 400;

                votes.append((row[0], row[1]));
                line_cnt += 1;
                #redis.rpush(row[0], row[1]); #key mi je guid a value pollnumb
                #votes.append(row[0]); #nzm da li mi je potrebno
                #ipak sam publish string i tako cu dad ga dohvatim

            for row in votes:
                redis_message = str(row[0]) + "," + str(row[1]) + "," + str(ellectionOfficialJmbg);
                #redis.publish("votes", redis_message);
                redis.rpush("votess", redis_message);

            #redis.rpush("electionOfficialJmbg", ellectionOfficialJmbg);

        return Response(200);

@application.route("/getvote", methods=["POST"])
def getVote():
    with Redis(host=redishost) as redis:
        _, message = redis.blpop("votess");
        message = message.decode("utf-8");
        message = message.split(",");
        guid = message[0];
        election = Election.query.first();
        participantId = getParticipantId(election.id, int(message[1]))
        new_vote = Vote(guid=guid, election_official_jmbg=message[2], electionId=election.id, participantId=participantId);
        database.session.add(new_vote);
        database.session.commit();

        return Response(200);

if (__name__ == "__main__"):
    database.init_app(application);
    application.run(debug=True,host = "0.0.0.0", port=5001);