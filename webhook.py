import json
import os
import traceback
import utils

from flask import Flask
from flask import request, make_response
from pymongo import MongoClient
from textblob import TextBlob

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
            filtered_parameters = {key: val for key, val in parameters.items()
                                   if val != ''}    # Removing empty parameters
            contact_info = employee_details.find_one(filtered_parameters)

            if contact_info:
                message = {
                    "card": {
                        "title": contact_info.get("name"),
                        "subtitle": contact_info.get('designation') + " | " + contact_info.get('department') +
                                    "\n" + "Phone: " + contact_info.get("contact_number"),
                        "imageUri": "https://banner2.kisspng.com/20180403/tkw/kisspng-avatar-computer-icons-user"
                                    "-profile-business-user-avatar-5ac3a1f7d96614.9721182215227704238905.jpg",
                        "buttons": [
                            {
                                "text": "View Profile"
                            }
                        ]
                    },
                    "platform": "FACEBOOK"
                },
            else:
                message = {
                    "text": {
                        "text": [
                            "Sorry, I was not able to find the given person."
                        ]
                    },
                    "platform": "FACEBOOK"
                }

            return {
                "source": "webhook",
                "fulfillmentMessages": [
                    message,
                    {
                        "quickReplies": {
                            "title": "What would you like to do next?",
                            "quickReplies": [
                                "Get Started",
                                "Search other employees"
                            ]
                        },
                        "platform": "FACEBOOK"
                    }
                ],
            }

        elif action == "Feedback.Feedback-custom":
            feedback = req.get("queryResult").get("parameters").get('feedback')
            text = TextBlob(feedback)
            sentiment = text.sentiment.polarity
            subjective = text.sentiment.subjectivity

            if sentiment >= 0.15:
                message = f"We are glad that you like our culture.\nSentiment Score: {sentiment}"
            elif sentiment <= -0.15:
                message = f"Sorry to hear that. We will make sure to improve our culture and make this " \
                          f"a better place to work.\nSentiment Score: {sentiment}"
            else:
                message = "Alright, I have noted the feedback."

            return {
                "source": "webhook",
                "fulfillmentMessages": [
                    {
                        "text": {
                            "text": [
                                message
                            ]
                        },
                        "platform": "FACEBOOK"
                    }
                ],
            }

        elif action == "search_employee":
            parameters = req.get("queryResult").get("parameters")
            contact_info = employee_details.find_one(parameters)

            return {
                "source": "webhook",
                "fulfillmentMessages": [
                    {
                        "card": {
                            "title": contact_info.get("name"),
                            "subtitle": contact_info.get('designation') + " | " + contact_info.get('department') +
                                        "\n" + "Phone: " + contact_info.get("contact_number"),
                            "imageUri": "https://banner2.kisspng.com/20180403/tkw/kisspng-avatar-computer-icons-user"
                                        "-profile-business-user-avatar-5ac3a1f7d96614.9721182215227704238905.jpg",
                            "buttons": [
                                {
                                    "text": "View Profile"
                                }
                            ]
                        },
                        "platform": "FACEBOOK"
                    },
                    {
                        "quickReplies": {
                            "title": "What would you like to do next?",
                            "quickReplies": [
                                "Get Started",
                                "Search other employees"
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
