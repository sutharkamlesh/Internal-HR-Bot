import json
import os
import traceback

from flask import Flask
from flask import request, make_response
from pymongo import MongoClient
from bson.objectid import ObjectId


MONGODB_URI = "MONGO_DATABASE_URL"
client = MongoClient(MONGODB_URI, connectTimeoutMS=30000)
db = client.aflatoun
questions = db.questions


# Flask app should start in global layout
app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    res = process_request(req)
    res = json.dumps(res, indent=4)
    # print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def process_request(req):
    try:
        action = req.get("queryResult").get("action")

        if action == "input.welcome":
            print("Webhook Successfully connected.")

    except Exception as e:
        print("Error:", e)
        traceback.print_exc()
        return {
            "fulfillmentText": "Oops...I am not able to help you at the moment, please try again..",
            "source": "webhook"
        }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print("Starting app on port {}".format(port))
    app.run(debug=False, port=port, host='0.0.0.0')
