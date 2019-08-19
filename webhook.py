import json
import os
import traceback
import utils

from flask import Flask
from flask import request, make_response
from pymongo import MongoClient


MONGODB_URI = "mongodb+srv://kamlesh:techmatters123@aflatoun-quiz-pflgi.mongodb.net/test?retryWrites=true&w=majority"
client = MongoClient(MONGODB_URI, connectTimeoutMS=30000)
db = client.hrchatbot
employee_details = db.employee_details


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

        elif action == "request.leave":
            date_string = req.get("queryResult").get("parameters").get("date")
            return {
                "source": "webhook",
                "fulfillmentMessages": [
                    {
                        "text": {
                            "text": [
                                "Okay, I will inform your manager that you are not going to come on " +
                                utils.date2text(date_string)
                            ]
                        },
                        "platform": "FACEBOOK"
                    }
                ],
            }

        elif action == "request.vacation":
            start_date = req.get("queryResult").get("parameters").get("date-period").get("startDate")
            end_date = req.get("queryResult").get("parameters").get("date-period").get("endDate")
            return {
                "source": "webhook",
                "fulfillmentMessages": [
                    {
                        "text": {
                            "text": [
                                "Okay, I will request your manager to grant you a leave from " +
                                utils.date2text(start_date) + " to " + utils.date2text(end_date)
                            ]
                        },
                        "platform": "FACEBOOK"
                    }
                ],
            }

        elif action == "ProvideSalarySlips.TakeEmailAddress":
            to_email = req.get("queryResult").get("parameters").get("email")
            start_date = req.get("queryResult").get("parameters").get("date-period").get("startDate")
            end_date = req.get("queryResult").get("parameters").get("date-period").get("endDate")
            subject = "Salary Slips"
            body = "This is mail to provide a salary slips from " + utils.date2text(start_date) + " to " + \
                   utils.date2text(end_date)
            utils.send_mail(to_email, subject, body)

            return {
                "source": "webhook",
                "fulfillmentMessages": [
                    {
                        "text": {
                            "text": [
                                "Your Salary Slips are on your way. Please check your mail."
                            ]
                        },
                        "platform": "FACEBOOK"
                    }
                ],
            }

        elif action == "find.colleague":
            parameters = req.get("queryResult").get("parameters")
            if "designation" in parameters.keys() and "department" in parameters.keys():
                contact_info = employee_details.find_one({
                    'designation': parameters.get('designation'),
                    'department': parameters.get('department')
                })
            elif "designation" in parameters.keys():
                contact_info = employee_details.find_one({
                    'designation': parameters.get('designation')
                })
            elif "name" in parameters.keys():
                contact_info = employee_details.find_one({
                    'department': parameters.get('department')
                })
            else:
                contact_info = None

            if contact_info is not None:
                return {
                    "source": "webhook",
                    "fulfillmentMessages": [
                        {
                            "text": {
                                "text": [
                                    "You can talk to {0} who is working as {1} in {2} department of this "
                                    "firm.\nContact: {3}".format(contact_info.get('name'),
                                                                 contact_info.get('designation'),
                                                                 contact_info.get('department'),
                                                                 contact_info.get('contact_number'))
                                ]
                            },
                            "platform": "FACEBOOK"
                        }
                    ],
                }
            else:
                return {
                    "source": "webhook",
                    "fulfillmentMessages": [
                        {
                            "text": {
                                "text": [
                                    "Sorry we don't have any information regarding this."
                                ]
                            },
                            "platform": "FACEBOOK"
                        }
                    ]
                }

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
