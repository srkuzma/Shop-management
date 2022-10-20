import csv
import datetime
import io
import json

from flask_jwt_extended import JWTManager, get_jwt
from flask import Flask, request, Response;
from applications.configuration import Configuration;
from applications.decorator import roleCheck
from applications.models import database, Proizvod, ProizvodKategorija, Kategorija, Narudzbina, Zahtev
from sqlalchemy import and_;

application = Flask ( __name__ );
application.config.from_object ( Configuration )
jwt = JWTManager ( application );

@application.route("/search", methods=["GET"])
@roleCheck("kupac")
def search():
    proizvod = request.args.get('name')
    if not proizvod:
        proizvod = ""

    kategorija = request.args.get('category')
    if not kategorija:
        kategorija = ""

    def getProizvod(idp):
        return Proizvod.query.filter(Proizvod.id == idp).first()

    def getKategorija(idk):
        return Kategorija.query.filter(Kategorija.id == idk).first()

    proizvodKategorije = database.session.query(ProizvodKategorija).join(Kategorija).join(Proizvod).filter(
             and_(Kategorija.ime.like(f"%{kategorija}"), Proizvod.ime.like(f"%{proizvod}"))
    ).all()

    proizvodi = set()
    kategorije = set()

    for proizvodKategorija in proizvodKategorije:
        proizvod = getProizvod(proizvodKategorija.proizvodId)
        kategorija = getKategorija(proizvodKategorija.kategorijaId)

        proizvodi.add(proizvod)
        kategorije.add(kategorija)

    def getjson(p):
        return {
            "categories": [
                k.ime for k in p.kategorije
            ],
            "id": p.id,
            "name": p.ime,
            "price": p.cena,
            "quantity": p.kolicina
        }

    kategorijeJson = [k.ime for k in kategorije]
    proizvodiJson = [getjson(p) for p in proizvodi]

    response = json.dumps({"categories": kategorijeJson, "products": proizvodiJson})

    return Response(response, status=200)

def check_completed(narudzbina):
    for zahtev in narudzbina.zahtevi:
        if (zahtev.dobijeno != zahtev.naruceno):
            return
    narudzbina.status = "COMPLETE"

@application.route("/order", methods=["POST"])
@roleCheck("kupac")
def order():
    zahtevi = request.json.get("requests")
    if not zahtevi:
        response = {"message" : "Field requests is missing."}
        return Response(json.dumps(response), status=400)
    claims = get_jwt();
    mejl = claims["sub"]

    for index, zahtev in enumerate(zahtevi):
        if not "id" in zahtev:
            response = {"message": "Product id is missing for request number " + str(index) + "."}
            return Response(json.dumps(response), status=400)
        if not "quantity" in  zahtev:
            response = {"message": "Product quantity is missing for request number " + str(index) + "."}
            return Response(json.dumps(response), status=400)
        quantity = zahtev["quantity"]
        id = zahtev["id"]
        if not isinstance(id, int) or id <= 0:
            response = {"message": "Invalid product id for request number " + str(index) + "."}
            return Response(json.dumps(response), status=400)
        if not isinstance(quantity, int) or quantity <= 0:
            response = {"message": "Invalid product quantity for request number " + str(index) + "."}
            return Response(json.dumps(response), status=400)

        proizvodId = int(zahtev["id"])
        proizvod = Proizvod.query.filter(Proizvod.id == proizvodId).first()
        if not proizvod:
            response = {"message": "Invalid product for request number " + str(index) + "."}
            return Response(json.dumps(response), status=400)

    narudzbina = Narudzbina(korisnikMejl=mejl, cena=0, timestamp=datetime.datetime.now())
    database.session.add(narudzbina)

    cena = 0

    for zahtev in zahtevi:
        proizvodId = zahtev["id"]
        kolicina = int(zahtev["quantity"])
        proizvod = Proizvod.query.filter(Proizvod.id == proizvodId).first()

        noviZahtev = Zahtev(proizvodId=proizvod.id, narudzbinaId=narudzbina.id, naruceno=kolicina, cena=proizvod.cena)
        database.session.add(noviZahtev)
        database.session.commit()

        ispunjenje = min(proizvod.kolicina, kolicina)
        proizvod.kolicina -= ispunjenje
        noviZahtev.dobijeno += ispunjenje

        dodatnaCena = kolicina * proizvod.cena
        cena += dodatnaCena

    narudzbina.cena += cena

    check_completed(narudzbina)

    database.session.commit()
    return Response(json.dumps({"id" : narudzbina.id}) ,status=200)

@application.route("/status", methods=["GET"])
@roleCheck("kupac")
def status():
    claims = get_jwt();
    mejl = claims["sub"]
    narudzbine = Narudzbina.query.filter(Narudzbina.korisnikMejl == mejl).all()

    def getJson(n):
        return {
            "products": [
                {
                    "categories": [k.ime for k in z.proizvod.kategorije],
                    "name": z.proizvod.ime,
                    "price": z.cena,
                    "received": z.dobijeno,
                    "requested": z.naruceno
                } for z in n.zahtevi
            ],
            "price": n.cena,
            "status": n.status,
            "timestamp": str(n.timestamp)
        }
    response = json.dumps({"orders": [getJson(n) for n in narudzbine]})
    return Response(response, status=200)

if ( __name__ == "__main__" ):
    database.init_app(application)
    application.run ( debug = True, host="0.0.0.0", port=5001);