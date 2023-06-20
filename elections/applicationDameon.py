from datetime import datetime, timedelta;

import flask;
from flask import Flask, request, Response;
from configuration import Configuration;
from models import database, Election, Vote, Participant;
from flask_jwt_extended import JWTManager, jwt_required
from redis import Redis;
import os;

application = Flask(__name__);
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False;
application.config.from_object(Configuration);
#jwt = JWTManager(application);

def getParticipantId (electionId, pollNum) :
    election = Election.query.filter(Election.id == electionId).first();
    num = 1 ;
    for part in election.participants:
        if(num == pollNum):
            return part.id;
        num += 1;

# def verifyAllVotes():
    # with Redis(Configuration.REDIS_HOST, charset="utf-8", decode_responses=True) as redis:
        #uzimam glas po glas iz liste i proveravam ga
        #oznacavam da li je validan ili ne
        #uzimam i jmbg zvanicnika, to cu poslednje da stavim na redis
        #tako da uzimam to prvo

        # electionOfficialJmbg = redis.lpop("electionOfficialJmbg");
        # redis.delete("electionOfficialJmbg");
        #vratio mi sve keys odnosno sve guide koji su mi trenutno na redisu
        # keys = redis.keys('*');

        #nije gotovo treba proveriti da li se trenutno odrzavaju izbori
        # electionId = 0 ;
        # election = Election.query.filter(id=electionId).first();

        # for key in keys:
        #     guid = key;
        #     keyList = redis.lrange(key, 0, -1);
            # for k in key: #nzm da li mogu ovo ovako
            #     pollNum = redis.lpop(key);

                # ballot = Vote.query.filter (id= guid).first();
                #vec postoji duplicat je
                # if (ballot) :
                #     vote = Vote(id=guid, election_official_jmbg=electionOfficialJmbg,electionId=electionId, participantId=getParticipantId(electionId,pollNum), reason="Duplicate ballot.");
                #     database.session.add(vote);
                #     database.session.commit();
                #nije dobar poll num
                # elif(pollNum >= len(election.participants) or pollNum <= 0):
                #     vote = Vote(id=guid, election_official_jmbg=electionOfficialJmbg, electionId=electionId, participantId=pollNum, reason="Invalid pollnumber.");
                #     database.session.add(vote);
                #     database.session.commit();
                # else:
                #     vote = Vote(id=guid, election_official_jmbg=electionOfficialJmbg, electionId=electionId, participantId=getParticipantId(electionId,pollNum));
                #     database.session.add(vote);
                #     database.session.commit();

   #novo sa subscribe na redis

#VRATI ZA DEPLOYMENT
redishost = os.environ["redisHost"];

#novo sa subscribe na redis

def main(vote):
    print("usao sam u dameona!");
    #one_line_vote = subscription.get_message(timeout=1000)["data"].split(",");
    #one_line_vote = subscription.get_message(timeout=1000)["data"].split(",");
    one_line_vote = vote.split(",");
    hours_added = timedelta(hours=2);
    current_date_and_time = datetime.now().replace ( microsecond = 0 ) + hours_added;

    seconds_added = timedelta(seconds=2)
    future_date_and_time = current_date_and_time #+ hours_added + seconds_added; ovo mozda treba za deployment
    elections = Election.query.all();

    found_election = -1;
    eureka = False;
    sekunde_proba = timedelta(minutes=2);
    for election in elections:
        print(f"trenutno vreme je {current_date_and_time} a start je {election.start} a end je {election.end} ")
        if(current_date_and_time >= election.start  and current_date_and_time <= (election.end )):
            found_election = election;
            eureka = True;
            break;

    if(eureka == False):
        print("trenutno nema izbora koji se odrzavaju zato odbaci glas!")
        return; #idi na pocetak while-a

    guid = one_line_vote[0];
    votee = Vote.query.filter(Vote.guid == guid).first(); # da vrati koliko glasova ima, mozda ne mora tako
    pollNum = int(one_line_vote[1]);

    partNum = 0 ;

    for part in found_election.participants:
        partNum += 1;

    #ako ima vise od jedan onda je duplikat
    if(votee):
        participantId = getParticipantId(found_election.id, pollNum);
        new_vote = Vote(guid=guid, election_official_jmbg=one_line_vote[2], electionId=found_election.id, participantId=participantId, reason="Duplicate ballot.");
        database.session.add(new_vote);
        database.session.commit();

        print(f"dodat novi glas3 ");
        #redis.publish("stiglo", "dodat novi glas3")

    elif (pollNum > partNum or pollNum <= 0):
        participantId = Participant.query.first();
        participantId = participantId.id;
        new_vote = Vote(guid=guid, election_official_jmbg=one_line_vote[2], electionId=found_election.id, participantId=participantId, reason="Invalid poll number.", polNum=pollNum);
        database.session.add(new_vote);
        database.session.commit();

        print(f"dodat novi glas2 ");
        #redis.publish("stiglo", "dodat novi glas2")
    else:
        participantId = getParticipantId(found_election.id, pollNum);

        new_vote = Vote(guid=guid, election_official_jmbg=one_line_vote[2], electionId=found_election.id, participantId=participantId);
        database.session.add(new_vote);
        database.session.commit();

        print(f"dodat novi glas1 ");
        #redis.publish("stiglo", "dodat novi glas1")

if (__name__ == "__main__"):
    database.init_app(application);
    #application.run(debug=True, port=5003);

    with application.app_context():
        while True:
            print("AJDE BRE!")
            with Redis(host=redishost) as redis:
                print("pre blokiranja na votess")
                #inace kad radis u deployment vrati na redisost
                _, one_line_vote = redis.blpop("votess");
                one_line_vote = one_line_vote.decode("utf-8");
                main(one_line_vote);