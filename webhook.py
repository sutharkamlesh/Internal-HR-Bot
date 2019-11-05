import json
import os
import traceback
import utils

from flask import Flask
import pandas as pd
from flask import request, make_response
from pymongo import MongoClient
from textblob import TextBlob

MONGODB_URI = "mongodb+srv://kamlesh:techmatters123@aflatoun-quiz-pflgi.mongodb.net/test?retryWrites=true&w=majority"
client = MongoClient(MONGODB_URI, connectTimeoutMS=30000)
db = client.hrchatbot
employee_details = db.employee_details

# Importing Holidays data sets
public_holidays = pd.read_csv("data/public_holidays.csv")

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
                    },
                    {
                        "quickReplies": {
                            "title": "What would you like to do next?",
                            "quickReplies": [
                                "Get Started",
                                "Check Leave Balance"
                            ]
                        },
                        "platform": "FACEBOOK"
                    }
                ]
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
                                   if val != ''}  # Removing empty parameters
            contact_info = employee_details.find_one(filtered_parameters)

            if contact_info and filtered_parameters:
                message = {
                              "card": {
                                  "title": contact_info.get("name"),
                                  "subtitle": contact_info.get('designation') + " | " + contact_info.get('department') +
                                              "\n" + "Phone: " + contact_info.get("contact_number"),
                                  "imageUri": "https://www.cristianmonroy.com/wp-content/uploads/2017/11/avatars"
                                              "-avataaars.png",
                                  "buttons": [
                                      {
                                          "text": "View Profile"
                                      }
                                  ]
                              },
                              "platform": "FACEBOOK"
                          }
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
                ]
            }

        elif action == "Feedback.Feedback-custom":
            feedback = req.get("queryResult").get("parameters").get('feedback')
            text = TextBlob(feedback)
            sentiment = text.sentiment.polarity
            subjective = text.sentiment.subjectivity

            if sentiment >= 0.15 or feedback == "🙂":
                message = u"\U0001F600 " + f"We are glad that you like our culture."
            elif sentiment <= -0.15 or feedback == "☹️":
                message = f"Sorry to hear that. We will make sure to improve our culture and make this " \
                          f"a better place to work."
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
            filtered_parameters = {key: val for key, val in parameters.items()
                                   if val != ''}  # Removing empty parameters
            contact_info = employee_details.find_one(filtered_parameters)
            if contact_info and filtered_parameters:
                message = {
                    "card": {
                        "title": contact_info.get("name"),
                        "subtitle": contact_info.get('designation') + " | " + contact_info.get('department') +
                                    "\n" + "Phone: " + contact_info.get("contact_number"),
                        "imageUri": "https://www.cristianmonroy.com/wp-content/uploads/2017/11/avatars-avataaars"
                                    ".png",
                        "buttons": [
                            {
                                "text": "View Profile"
                            }
                        ]
                    },
                    "platform": "FACEBOOK"
                }
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
                ]
            }

        elif action == "show.all.public.holidays":
            state = req.get("queryResult").get("parameters").get("geo-state")
            public_holidays_string = public_holidays[public_holidays["State"] == state].to_string(columns=["Date", "Holiday"], index=False)
            return {
                "source": "webhook",
                "fulfillmentMessages": [
                    {
                        "text": {
                            "text": [
                                "Here is the list of all public holidays in " + state + "\n" + public_holidays_string
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
