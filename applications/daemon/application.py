from flask import Flask;
from applications.configuration import Configuration;
from flask_migrate import Migrate, init, migrate, upgrade;
from applications.models import database, Proizvod, ProizvodKategorija, Kategorija, Narudzbina
from sqlalchemy_utils import database_exists, create_database;
from redis import Redis

application = Flask(__name__);
application.config.from_object(Configuration);

#migrateObject = Migrate ( application, database );

def check_completed(narudzbina):
    for zahtev in narudzbina.zahtevi:
        if (zahtev.dobijeno != zahtev.naruceno):
            return
    narudzbina.status = "COMPLETE"

if (not database_exists(application.config["SQLALCHEMY_DATABASE_URI"])):
    create_database(application.config["SQLALCHEMY_DATABASE_URI"]);

database.init_app(application);

while (True):
    with Redis(host=Configuration.REDIS_HOST) as redis:
        with application.app_context() as context:
            # init();
            # migrate(message="Production migration");
            # upgrade();

            bytes = redis.blpop(Configuration.REDIS_KATEGORIJE_LIST)[1];
            kategorije = bytes.decode("utf-8");
            kategorije = kategorije.split("|")

            bytes = redis.blpop(Configuration.REDIS_IME_LIST)[1];
            ime = bytes.decode("utf-8");

            bytes = redis.blpop(Configuration.REDIS_KOLICINE_LIST)[1];
            kolicina = bytes.decode("utf-8");
            kolicina = int(kolicina)

            bytes = redis.blpop(Configuration.REDIS_NABAVNECENE_LIST)[1];
            cena = bytes.decode("utf-8");
            cena = float(cena)

            proizvod = Proizvod.query.filter(Proizvod.ime == ime).first()
            if not proizvod:  # proizvod ne postoji u bazi
                proizvod = Proizvod(ime=ime, cena=cena, kolicina=kolicina)

                database.session.add(proizvod)
                for k in kategorije:
                    kategorija = Kategorija.query.filter(Kategorija.ime == k).first()
                    if not kategorija:
                        kategorija = Kategorija(ime=k)
                        database.session.add(kategorija)
                database.session.commit()

                idP = proizvod.id

                for k in kategorije:
                    kategorija = Kategorija.query.filter(Kategorija.ime == k).first()
                    idK = kategorija.id
                    proizvodkategorija = ProizvodKategorija(proizvodId=idP, kategorijaId=idK)
                    database.session.add(proizvodkategorija)
                database.session.commit()
            else:  # proizvod postoji u bazi
                kategorijeProizvod = [k.ime for k in proizvod.kategorije]
                kategorijeProizvod.sort()
                kategorije.sort()


                def same(list1, list2):
                    if len(list1) != len(list2):
                        return False
                    for i in range(len(list1)):
                        if list1[i] != list2[i]:
                            return False
                    return True


                if not same(kategorije, kategorijeProizvod):
                    continue

                kolicinaProizvod = proizvod.kolicina
                cenaProizvod = proizvod.cena

                novaCena = (float)((float)((float)(cenaProizvod * kolicinaProizvod) + (float)(cena * kolicina)) / (float)(kolicinaProizvod + kolicina))
                # print(novaCena, flush=True)
                novaKolicina = kolicina + kolicinaProizvod

                proizvod.cena = novaCena
                proizvod.kolicina = novaKolicina

                narudzbine = Narudzbina.query.order_by(Narudzbina.timestamp).all()

                for narudzbina in narudzbine:
                    for zahtev in narudzbina.zahtevi:
                        if zahtev.proizvodId == proizvod.id:
                            ispunjenje = min(proizvod.kolicina, zahtev.naruceno - zahtev.dobijeno)
                            proizvod.kolicina -= ispunjenje
                            zahtev.dobijeno += ispunjenje
                    check_completed(narudzbina)

                database.session.commit()
