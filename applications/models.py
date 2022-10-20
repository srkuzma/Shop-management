import datetime

from flask_sqlalchemy import SQLAlchemy;

database = SQLAlchemy ( );

class ProizvodKategorija(database.Model):
    __tablename__ = "proizvodkategorija";
    id = database.Column(database.Integer, primary_key=True);
    proizvodId = database.Column(database.Integer, database.ForeignKey("proizvodi.id"), nullable=False);
    kategorijaId = database.Column(database.Integer, database.ForeignKey("kategorije.id"), nullable=False);

class Proizvod(database.Model):
    __tablename__ = "proizvodi";
    id = database.Column(database.Integer, primary_key=True);
    ime = database.Column(database.String(256), nullable=False);
    cena = database.Column(database.Float, nullable=False);
    kolicina = database.Column(database.Integer, nullable=False, default=0)
    kategorije = database.relationship("Kategorija", secondary=ProizvodKategorija.__table__, back_populates="proizvodi");
    zahtevi = database.relationship("Zahtev", back_populates="proizvod");

    def __repr__(self):
        return "({}, {}, {}, {}, {})".format(self.id, self.ime, self.cena, self.kolicina, str(self.kategorije));

class Kategorija(database.Model):
    __tablename__ = "kategorije";
    id = database.Column(database.Integer, primary_key=True);
    ime = database.Column(database.String(256), nullable=False);
    proizvodi = database.relationship("Proizvod", secondary=ProizvodKategorija.__table__, back_populates="kategorije");

    def __repr__(self):
        return "({}, {}, {})".format(self.id, self.ime, str(self.proizvodi));

class Zahtev(database.Model):
    __tablename__ = "zahtevi";
    id = database.Column(database.Integer, primary_key=True);
    naruceno = database.Column(database.Integer, nullable=False);
    dobijeno = database.Column(database.Integer, nullable=False, default=0);

    proizvodId = database.Column(database.Integer, database.ForeignKey("proizvodi.id"), nullable=False);
    proizvod = database.relationship("Proizvod", back_populates="zahtevi");

    narudzbinaId = database.Column(database.Integer, database.ForeignKey("narudzbine.id"), nullable=False);
    narudzbina = database.relationship ( "Narudzbina", back_populates = "zahtevi" );

    cena = database.Column(database.Float, nullable=False)

class Narudzbina(database.Model):
    __tablename__ = "narudzbine";
    id = database.Column(database.Integer, primary_key=True);
    cena = database.Column(database.Float, nullable=False);
    status = database.Column(database.String(256), nullable=False, default="PENDING")
    zahtevi = database.relationship ( "Zahtev", back_populates = "narudzbina" );
    timestamp = database.Column(database.DateTime, nullable=False, default=datetime.datetime.now())
    korisnikMejl = database.Column(database.String(256), nullable=False)
