import csv
import datetime
import io
import json

from flask_jwt_extended import JWTManager, get_jwt
from flask import Flask, request, Response;
from applications.configuration import Configuration;
from applications.decorator import roleCheck
from applications.models import database, Proizvod, ProizvodKategorija, Kategorija, Narudzbina, Zahtev
from sqlalchemy import and_, func, desc;

application = Flask ( __name__ );
application.config.from_object ( Configuration )
jwt = JWTManager ( application );

@application.route("/productStatistics", methods=["GET"])
@roleCheck("admin")
def productStatistics():
    response = {
        "statistics": [
            {
                "name": p.ime,
                "sold": sum(z.naruceno for z in Zahtev.query.filter(Zahtev.proizvodId == p.id).all()),
                "waiting": sum(z.naruceno - z.dobijeno for z in Zahtev.query.filter(Zahtev.proizvodId == p.id).all())
            }
            for p in Proizvod.query.join(Zahtev).all()
        ]
    }
    return Response(json.dumps(response), status=200)

@application.route("/categoryStatistics", methods=["GET"])
@roleCheck("admin")
def categoryStatistics():

    response = {
        "statistics": [
            c[0]
            for c in Kategorija.query.outerjoin(ProizvodKategorija).outerjoin(Proizvod).outerjoin(Zahtev).\
                group_by(Kategorija.id).with_entities(Kategorija.ime, func.sum(Zahtev.naruceno).label("naruceno")).order_by(desc("naruceno"), Kategorija.ime).all()
        ]
    }
    return Response(json.dumps(response), status=200)

if ( __name__ == "__main__" ):
    database.init_app(application)
    application.run ( debug = True, host="0.0.0.0",  port=5003);