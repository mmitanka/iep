
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


def datetime_valid(date):
    try:
        datetime.fromisoformat(date)
    except ValueError:
        try:
            datetime.fromisoformat(date.replace('Z', '+00:00'))
        except ValueError:
            return False
        return True
    return True

def validate_iso( sval ):
    try:
        valid_datetime = parser.isoparse(sval);
        return True
    except ValueError:
        return False

def getParticipantId (electionId, pollNum) :
    election = Election.query.filter(Election.id == electionId).first();
    num = 1 ;
    for part in election.participants:
        if(num == pollNum):
            return part.id;
        num += 1;

def calcResultIndividual(electiondId, participantId):
   count = func.count(Vote.participantId);
   #ovo mi su mi glasovi za sve
   allVotes = Vote.query.filter(and_(Vote.electionId == electiondId, Vote.reason == None))\
       .with_entities(Vote.participantId, func.count(Vote.participantId)).group_by(Vote.participantId).all();

   if(len(allVotes) == 0):
       print("nesto nije u redu 3")
   validVotesCnt = 0;

   allValidVotesCnt = 0;
   for vote in allVotes:
       allValidVotesCnt += vote[1];
       if(vote[0]== participantId):
           print(f"broj glasova za kand {participantId} = {vote[1]}")
           validVotesCnt = vote[1];
   print(f"broj svih validnih glasova treba da bude 500= {allValidVotesCnt}, izbori id = {electiondId}");
   try:
       res = validVotesCnt/allValidVotesCnt;
       return round(res,2);
   except ZeroDivisionError:
       return 0;


def calcResultParty(electiondId, participantId):
    try:
        votesPerParties = [];
        count = func.count(Vote.participantId);
        allVotesCnt = Vote.query.filter(and_(Vote.electionId == electiondId, Vote.reason == None)).group_by(Vote.participantId).with_entities(Vote.participantId, count).all();

        participantsInElection = ElectionParticipant.query.filter(ElectionParticipant.electionId == electiondId); #svi ucesnici

        allValidVotesCnt = 0;
        validVotesPerPolParty = 0;
        for vote in allVotesCnt:
            allValidVotesCnt += vote[1];
            if (vote[0] == participantId):
                validVotesPerPolParty = vote[1];

        index = 0;
        my = -1;
        for politicalParty in participantsInElection:
            #nasli smo lasove za tu pol partiju
            #votes = Vote.query.filter(and_(Vote.electionId == electiondId, Vote.participantId == politicalParty.participantId, Vote.reason is None)).count();
            votes = 0;
            for vv in allVotesCnt:
                if(vv[0] == politicalParty.participantId):
                    votes = vv[1];

            if(isCensusPassed(votes,allValidVotesCnt)):
                votesPerParties.append(votes);

                if(participantId == politicalParty.participantId):
                    my = index;

                index += 1;

        mandatesPerParties = [];
        #punimo nulama listu
        for vote in votesPerParties:
            mandatesPerParties.append(0);

        if(my == -1):
            return 0;

        for i in range(1,251):
            max = -1;
            k = -1;
            #trazimo maximum u ovoj iteraciji
            for participantIndex in range(0,len(votesPerParties)):
                quot = votesPerParties[participantIndex]/(1 + mandatesPerParties[participantIndex]);
                if(max < quot):
                    k = participantIndex;
                    max = quot;

            #sada dodajem mandat maksimumu
            mandatesPerParties[k] += 1;

        return mandatesPerParties[my];

    except ValueError:
        return 0;


def isCensusPassed(votesPerParty, allVotes):
    if(allVotes == 0):
        return False;
    percentage = votesPerParty/allVotes*100;

    if(percentage >= 5):
        return True;
    else:
        return False;

@application.route("/createParticipant", methods=["POST"])
@jwt_required()
def createParticipant():
    # headerfield authorisation missing status 401
    authorisation = request.headers.get("Authorization", "")
    authorisationEmpty = len(authorisation) == 0;

    if (authorisationEmpty):
        res = "Missing Authorization Header";
        return flask.jsonify(msg=res), 401;

    name = request.json.get("name", "");
    individual = request.json.get("individual", "");

    nameEmpty = len(name) == 0;
    individualEmpty = individual == "";

    # field missing
    if (nameEmpty):
        res = "Field name is missing."
        return flask.jsonify(message=res), 400;
    elif (individualEmpty):
        res = "Field individual is missing."
        return flask.jsonify(message=res), 400;

    # add participant into databse participant
    participant = Participant(name=name, individual=individual);
    database.session.add(participant);
    database.session.commit();

    return flask.jsonify(id=participant.id), 200;


@application.route("/getParticipants", methods=["GET"])
@jwt_required()
def getParticipants():
    # headerfield authorisation missing status 401
    authorisation = request.headers.get("Authorization", "")
    authorisationEmpty = len(authorisation) == 0;

    if (authorisationEmpty):
        res = "Missing Authorization Header.";
        return flask.jsonify(msg=res), 401;

    js = [];
    participants = Participant.query.all();
    for p in participants:
        obj = {"name": p.name, "individual": p.individual, "id":p.id}
        print(obj)
        js.append(obj);
    obj2 = {
        "participants": js
    }
    return make_response(obj2,200);


@application.route("/createElection", methods=["POST"])
@jwt_required()

def createElection():
    # headerfield authorisation missing status 401
    authorisation = request.headers.get("Authorization", "")
    authorisationEmpty = len(authorisation) == 0;

    if (authorisationEmpty):
        res = "Missing Authorization Header.";
        return flask.jsonify(msg=res), 401;

    start = request.json.get("start", "");
    end = request.json.get("end", "");
    individual = request.json.get("individual", "");
    participants = request.json.get("participants", "");

    startEmpty = len(start) == 0;
    endEmpty = len(end) == 0;
    individualEmpty = individual == "";
    participantsEmpty = participants == "";

    # field missing
    if (startEmpty):
        return flask.jsonify(message="Field start is missing."),400;
    elif (endEmpty):
        return flask.jsonify(message="Field end is missing."),400;
    elif (individualEmpty):
        return flask.jsonify(message="Field individual is missing."),400;
    elif (participantsEmpty):
        return flask.jsonify(message="Field participants is missing."),400;


    # not checked date time ovde mozda pukne jer sam menjala datum iz string u datetime
    if (( not validate_iso(start))):
        return flask.jsonify(message="Invalid date and time."), 400;
    elif ((not validate_iso(end))):
        return flask.jsonify(message="Invalid date and time."), 400;
    elif (start > end):
        return flask.jsonify(message="Invalid date and time."), 400;

    # not checked date time
    elections = Election.query.all();
    for el in elections:
        if ((parser.isoparse(start).replace(tzinfo=None) >= el.start) and (parser.isoparse(start).replace(tzinfo=None) <= el.end)):
            return flask.jsonify(message="Invalid date and time."),400;
        if ((parser.isoparse(end).replace(tzinfo=None) >= el.start) and (parser.isoparse(end).replace(tzinfo=None) <= el.end)):
            return flask.jsonify(message="Invalid date and time."),400;
        if ((parser.isoparse(start).replace(tzinfo=None) < el.start) and (parser.isoparse(end).replace(tzinfo=None) > el.end)):
            return flask.jsonify(message="Invalid date and time."),400;

    lsi = [type(p) for p in participants]
    for ls in lsi:
        if(ls != int):
            return flask.jsonify(message="Invalid participants."), 400;

    #participant doesnt exists
    for p in participants:
        participant = Participant.query.filter(Participant.id == p).first();
        if(participant == None):
            return flask.jsonify(message="Invalid participants."),400;

    # only one participant
    if (len(participants)< 2):
        return flask.jsonify(message="Invalid participants."),400;

    #not right type of participant for this election
    for p in participants:
        participant = Participant.query.filter(Participant.id == p).first();
        if (participant.individual != individual):
            return flask.jsonify(message="Invalid participants."),400;

    pollNumbers = [];
    num = 1;
    for p in participants:
        pollNumbers.append(num);
        num += 1;

    #add new election into database
    election = Election(start=start, end=end, individual=individual);
    database.session.add(election);
    database.session.commit();

    num = 1;
    #adding to elections participant
    for p in participants:
        #OVDE DA SE DODA POLJE POLNUM
        elpar = ElectionParticipant(electionId=election.id, participantId=p, pollNum=num);
        database.session.add(elpar);
        database.session.commit();
        num += 1;

    return flask.jsonify(pollNumbers=pollNumbers), 200;


@application.route("/getElections", methods=["GET"])
@jwt_required()
#unchecked
def getElections():
    # headerfield authorisation missing status 401
    authorisation = request.headers.get("Authorization", "")
    authorisationEmpty = len(authorisation) == 0;

    if (authorisationEmpty):
        res = "Missing Authorization Header";
        return flask.jsonify(msg=res), 401;

    js = [];
    elections = Election.query.all();
    for e in elections:
        js2 = [];
        for p in e.participants:
            js2.append({"id": p.id, "name": p.name});
        js.append({"id": e.id, "start": e.start.isoformat(), "end": e.end.isoformat(), "individual": e.individual, "participants": js2});

    return flask.jsonify(elections=js), 200;

#not done
@application.route("/getResults", methods=["GET"])
@jwt_required()
def getResults():
    # headerfield authorisation missing status 401
    authorisation = request.headers.get("Authorization", "")
    authorisationEmpty = len(authorisation) == 0;

    if (authorisationEmpty):
        res = "Missing Authorization Header";
        return flask.jsonify(msg=res), 401;

    if("id" not in request.args):
        print("fali id polje");
        return flask.jsonify(message="Field id is missing."),400;

    electionId = request.args["id"];
    electionId = int(electionId);

    election = Election.query.filter(Election.id == electionId).first();
    if(not election):
        print("ne postoji izbor sa datim idjem");
        return flask.jsonify(message="Election does not exist."),400;


    seconds_added = timedelta(seconds=2)
    hours_added = timedelta(hours=2)
    minutes_added = timedelta(minutes=2)
    today = datetime.now()
    #today = today + seconds_added + hours_added;
    # election ongoing check
    if (election.start <= today and (election.end )>= today):
        print("izbor jos uvek traje");
        return flask.jsonify(message="Election is ongoing."), 400;

    refresh_claims = get_jwt();
    #if(refresh_claims["roles"]!="administrator"):
     #   print("user nije admin");
     #   return "User must be admin!",400;
    #sleep(60);

    #moramo da napravimo response, za sad ne vracam nista, NIJE ODRADJENO
    invalidVotes = Vote.query.filter(Vote.electionId == election.id).filter(or_(Vote.reason == "Duplicate ballot.", Vote.reason == "Invalid poll number.")).order_by(Vote.polNum.desc()).all();

    part1 = [];
    newParticipant1 = {};
    for p in election.participants:
        electionParticipant = ElectionParticipant.query.filter(and_(ElectionParticipant.participantId == p.id, ElectionParticipant.electionId == election.id)).first();


        # treba izracunati result da se doda, napravis novu fju calcResult
        if(p.individual):
            res = calcResultIndividual(electionId, p.id);
        else:
            res = calcResultParty(electionId, p.id);

        newParticipant1["pollNumber"] = electionParticipant.pollNum;
        newParticipant1["name"] = p.name;
        newParticipant1["result"] = res;
        #part1.append({"pollNumber": electionParticipant.pollNum, "name": p.name, "result": res});
        part1.append(newParticipant1);
        newParticipant1 = {};


    invVotes1 = [];
    invVote1 = {};

    for invVote in invalidVotes:
        if(invVote.polNum is None):
            pollNumber = ElectionParticipant.query.filter(and_(ElectionParticipant.participantId == invVote.participantId, ElectionParticipant.electionId == election.id)).first();
            pollNumber = pollNumber.pollNum;
        else:
            pollNumber = invVote.polNum;

        invVote1["electionOfficialJmbg"] = invVote.election_official_jmbg;
        invVote1["ballotGuid"]= invVote.guid;
        invVote1["pollNumber"]= pollNumber;
        invVote1["reason"] = invVote.reason;
        #invVotes1.append({"electionOfficialJmbg": invVote.election_official_jmbg, "ballotGuid": invVote.guid,
                          #"pollNumber": pollNumber, "reason": invVote.reason});
        invVotes1.append(invVote1);
        invVote1 = {};

    if(len(invVotes1) == 0):
        print("nema inv glasova");
    if(len(part1) == 0):
        print("nema part i zbog toga puca");

    dicti1 = {};
    dicti1["participants"] = part1;
    dicti1["invalidVotes"] = invVotes1;
    return flask.make_response(flask.jsonify(dicti1), 200);

if (__name__ == "__main__"):
    database.init_app(application);
    application.run(debug=True,host = "0.0.0.0", port=5000);
