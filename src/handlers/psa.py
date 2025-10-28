from flask_jwt_extended import jwt_required
import config
import httpx
import flask 

psa = flask.Blueprint('psa', __name__)

@psa.route("/v1/psa")
@jwt_required()
def psa_api_lookup () :
    """
    Look up a PSA cert number and return info about the slab
    """
    cert = flask.request.args.get("id")

    if cert is None:
        return flask.Response('{"error": "Cert number not provided"}', status=401)

    headers={
        "User-Agent": "curl/7.79.1",
        "Accept": "*/*",
        "Connection": "keep-alive",
        "Host": "api.psacard.com",
        "Authorization": f"Bearer {config.PSA_TOKEN}"
    }

    response = httpx.request("GET", f"https://api.psacard.com/publicapi/cert/GetByCertNumber/{cert}", headers=headers)

    if response.status_code != 200:
        return flask.Response('{"error": "Could not find cert info in PSA database"}', status=401)
    
    

    json = response.json()["PSACert"]
    json["Brand"] = json["Brand"].replace("POKEMON GAME ", "")
    json["Brand"] = json["Brand"].replace("POKEMON ", "")

    return {"cert": json["CertNumber"],
            "grade": f"{json['CardGrade'].split(' ')[-1]}",
            "grader": "PSA",
            "name": f"{json['Brand']} {json['Subject']} {json['CardNumber']}"}


    