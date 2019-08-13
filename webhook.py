import json
import os
import traceback
import utils

from flask import Flask
from flask import request, make_response

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
