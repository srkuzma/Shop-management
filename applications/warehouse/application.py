import csv
import io
import json

from flask_jwt_extended import JWTManager
from redis import Redis
from flask import Flask, request, Response;
from applications.configuration import Configuration;
from applications.decorator import roleCheck

application = Flask ( __name__ );
application.config.from_object ( Configuration )
jwt = JWTManager ( application );


@application.route("/update", methods=["POST"])
@roleCheck("magacioner")
def update():
    try:
        content = request.files["file"].stream.read().decode("utf-8");
    except Exception:
        response = {"message": "Field file is missing."}
        return Response(json.dumps(response), status=400);
    stream = io.StringIO(content);
    reader = csv.reader(stream);
    reader1 = []

    with Redis ( host = Configuration.REDIS_HOST ) as redis:
        id = -1
        for row in reader:
            reader1.append(row)
            id += 1
            if len(row) != 4:
                response = {"message": "Incorrect number of values on line " + str(id) + "."}
                return Response(json.dumps(response), status=400);
            if not row[2].isdigit() or int(row[2]) <= 0:
                response = {"message": "Incorrect quantity on line " + str(id) + "."}
                return Response(json.dumps(response), status=400);

            try:
                x = float(row[3])
                if x <= 0:
                    response = {"message": "Incorrect price on line " + str(id) + "."}
                    return Response(json.dumps(response), status=400);
            except ValueError:
                response = {"message": "Incorrect price on line " + str(id) + "."}
                return Response(json.dumps(response), status=400);

        for row in reader1:
            redis.rpush(Configuration.REDIS_KATEGORIJE_LIST, row[0] );
            redis.rpush(Configuration.REDIS_IME_LIST, row[1]);
            redis.rpush(Configuration.REDIS_KOLICINE_LIST, row[2]);
            redis.rpush(Configuration.REDIS_NABAVNECENE_LIST, row[3]);

    return Response(status=200)

if ( __name__ == "__main__" ):
    application.run ( debug = True, host="0.0.0.0",  port=5002);