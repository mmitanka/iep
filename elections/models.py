from flask_sqlalchemy import SQLAlchemy;

database = SQLAlchemy();

class ElectionParticipant(database.Model):
    __tablename__ = "electionparticipant";
    id = database.Column(database.Integer, primary_key=True);
    electionId = database.Column(database.Integer, database.ForeignKey("elections.id"), nullable=False);
    participantId = database.Column(database.Integer, database.ForeignKey("participants.id"), nullable=False);
    pollNum = database.Column(database.Integer, nullable=False);
    #voteId = database.Column(database.Integer, database.ForeignKey("votes.id"), nullable=False);

class Election(database.Model):
    __tablename__ = "elections";
    id = database.Column(database.Integer, primary_key=True);
    start = database.Column(database.DATETIME,nullable=False);
    end = database.Column(database.DATETIME,nullable=False);
    individual = database.Column(database.Boolean,nullable=False);

    participants = database.relationship("Participant", secondary=ElectionParticipant.__table__, back_populates="elections");
    #one to many rel, one election may have multiple votes
    votes = database.relationship("Vote", back_populates ="election");

class Participant(database.Model):
    __tablename__ = "participants";
    id = database.Column(database.Integer, primary_key=True);
    name = database.Column(database.String(256),nullable=False);
    individual = database.Column(database.Boolean,nullable=False);

    elections = database.relationship("Election", secondary= ElectionParticipant.__table__, back_populates = "participants");

#not updated database with this
class Vote(database.Model):
    __tablename__ = "votes";
    id = database.Column(database.Integer, primary_key= True);
    guid = database.Column(database.String(256),  nullable=False);
    election_official_jmbg = database.Column(database.String(13), nullable=False);
    electionId = database.Column(database.Integer, database.ForeignKey("elections.id"), nullable=False);
    participantId = database.Column(database.Integer, database.ForeignKey("participants.id"), nullable=False);
    polNum = database.Column(database.Integer, nullable=True);
    reason = database.Column(database.String(256),nullable=True);
    election = database.relationship("Election",  back_populates = "votes");