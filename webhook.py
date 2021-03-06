# coding=utf-8
import calendar
import datetime
import json
import os
import random
import time
import traceback
from datetime import datetime

import pandas as pd
from flask import Flask
from flask import request, make_response
from pymongo import MongoClient
from textblob import TextBlob

import source
import utils

MONGODB_URI = "mongodb://uptime:Basketball10@134.122.18.134:27017/admin"
client = MongoClient(MONGODB_URI, connectTimeoutMS=30000)
db = client.hrbot_database

employee_details = db.employee_details
jobs = db.Hiring_PublicJobPosition
tickets = db.Tickets
history = db.hrbot_history
new_joinee = db.new_joinee
feedbackdata = db.feedback_data
survey = db.survey
# chck = {'employ_id': 'EMP100013'}
#
# contact_info = employee_details.find_one(chck)
# print("++++++++++++++++++++++")
# print(contact_info)
# print("++++++++++++++++++++++")
# cursor = feedbackdata.find()
# for record in cursor:
#     print(record)

# Importing Holidays data sets
public_holidays = pd.read_csv("data/public_holidays.csv")

# Flask app should start in global layout
app = Flask(__name__)

# Adding a counter variable
unknown_flag = 0
employ_id = {}
email = {}
feedback = []
feed = {}
survey_details = {}


@app.route('/webhook', methods=['POST'])
def webhook():

    req = request.get_json(silent=True, force=True)
    print("Request Header: ", request.headers)
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        print("Request IP : ", request.environ['REMOTE_ADDR'])
    else:
        print("Request IP: ", request.environ['HTTP_X_FORWARDED_FOR'])
    res = process_request(req)
    res = json.dumps(res, indent=4)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


import argparse
import uuid
project_id="internal-hr-bot-womtev "
texts="hi"

def detect_intent_texts(project_id, session_id, texts, language_code):
    """Returns the result of detect intent with texts as inputs.
    Using the same `session_id` between requests allows continuation
    of the conversation."""
    import dialogflow_v2 as dialogflow
    session_client = dialogflow.SessionsClient()

    session = session_client.session_path(project_id, session_id)
    print('Session path: {}\n'.format(session))

    for text in texts:
        text_input = dialogflow.types.TextInput(
            text=text, language_code=language_code)

        query_input = dialogflow.types.QueryInput(text=text_input)

        response = session_client.detect_intent(
            session=session, query_input=query_input)

        print('=' * 20)
        print('Query text: {}'.format(response.query_result.query_text))
        print('Detected intent: {} (confidence: {})\n'.format(
            response.query_result.intent.display_name,
            response.query_result.intent_detection_confidence))
        print('Fulfillment text: {}\n'.format(
            response.query_result.fulfillment_text))


def process_request(req):

    # --------------------------
    # For session
    # s = requests.Session()

    # ---------------------------



    global unknown_flag
    global employ_id
    global email
    global feedback, survey_details
    global feed
    req.update({"date": datetime.date(datetime.now()).isoformat(), "time": datetime.time(datetime.now()).isoformat()})

    # req.update({"employ_id":employ_id["employ_id"]})
    # today = date.today()
    # req.update({"today date":today.strftime("%B %d, %Y")})
    now = datetime.now()
    timestamp = datetime.timestamp(now)
    timestamp1 = int(timestamp * (10 ** 3))
    req.update({"timestamp": timestamp1})

    try:
        # planUS.insert(req, check_keys=False)
        history.insert(req, check_keys=False)
    except:
        pass
    try:
        action = req.get("queryResult").get("action")
        knowledge = req.get('queryResult').get('intent').get('displayName')
        if action == "input.welcome":
            print("Webhook Successfully connected.")

        elif action == "emp_id":
            parameters = req.get("queryResult").get("parameters")
            parameters["employ_id"] = parameters["employ_id"].upper()
            print(parameters)

            #For session----------------------------
            # print("------------")
            # setcookiesurl = "http://httpbin.org/cookies/set"
            # getcookiesurl = "http://httpbin.org/cookies"
            # s.get(setcookiesurl, params=parameters)
            # r = s.get(getcookiesurl)
            # print(r.text)
            # print("------------")
            # --------------------------------------------

            filtered_parameters = {key: val for key, val in parameters.items()
                                   if val != ''}  # Removing empty parameters
            print(filtered_parameters)
            contact_info = employee_details.find_one(filtered_parameters)
            if parameters and contact_info:
                # req.update({"employ_id": employ_id["employ_id"]})

                employ_id = filtered_parameters
                print("employ id " + str(employ_id))
                print(type(employ_id))
                email = contact_info.get("email_ID")
                print(email)
                to_email = email
                otp = random.randrange(1000, 9999)
                employee_details.find_one_and_update(filtered_parameters, {"$set": {"temp_otp": otp}}, upsert=True)
                print(otp)
                subject = "Qrata - verification code"
                body = "Your verification code is :- " + str(
                    otp) + " please enter the code in the chatbot for completing your verification process"
                utils.send_mail(to_email, subject, body)
                message = {
                    "source": "webhook",
                    "fulfillmentMessages": [
                        {
                            "text": {
                                "text": [
                                    "Enter the OTP send to your registered Email-ID"
                                ]
                            },
                            "platform": "FACEBOOK"
                        },
                    ],
                }

            else:
                message = {
                    "source": "webhook",
                    "fulfillmentMessages": [
                        {
                            "text": {
                                "text": [
                                    "Employee ID not valid"
                                ]
                            },
                            "platform": "FACEBOOK"
                        },
                        {
                            "quickReplies": {
                                "title": "Try again",
                                "quickReplies": [
                                    "Get Started",
                                    "Existing Employee",
                                ]
                            },
                            "platform": "FACEBOOK"
                        }
                    ],
                }

            return message


        elif action == "otp":
            otp = req.get("queryResult").get("queryText")
            print(otp)
            print(type(otp))
            contact_info = employee_details.find_one(employ_id)
            orginal_otp = contact_info.get("temp_otp")

            print(employ_id)
            print(orginal_otp)
            print(type(orginal_otp))
            if int(otp) == orginal_otp:

                return {
                    "source": "webhook",
                    "fulfillmentMessages": [
                        {
                            "quickReplies": {
                                "title": "Thank you for verification. I am Qi, your virtual HR assistant and I can help you in these following things.",
                                "quickReplies": [
                                    "My Leave & Absence",
                                    "My General Support",
                                    "My Pay & Benefits",
                                    "Happify Me",
                                    "My Learning"
                                ]
                            },
                            "platform": "FACEBOOK"
                        },
                        {
                            "text": {
                                "text": [
                                    ""
                                ]
                            }
                        }
                    ]
                }
            else:
                return {
                    "source": "webhook",
                    "fulfillmentMessages": [
                        {
                            "quickReplies": {
                                "title": "You employee id or otp is incorrect. Please try again ",
                                "quickReplies": [
                                    "Existing Employee"
                                ]
                            },
                            "platform": "FACEBOOK"
                        },
                        {
                            "text": {
                                "text": [
                                    ""
                                ]
                            }
                        }
                    ]
                }

        elif "Knowledge.KnowledgeBase" in knowledge:
            answer = (req.get('queryResult').get('fulfillmentMessages'))

            return {
                "source": "webhook",
                "fulfillmentMessages": answer,
                "outputContexts": [
                    {
                        "name": "projects/hr-bot-2-0-qfiwte/agent/sessions/8361885c-2b57-509c-c8b4-a86057fac036/contexts/existingemployee",
                        "lifespanCount": 1,
                        "parameters": {
                            "number": 1234,
                            "number.original": "1234"
                        }
                    }
                ]
            }

        for i in range(0, 5):
            question, op1, op2, op3, op4, op5, ans, option, hint1, hint2, hint3, hint4, hint5, quest = source.data(i)

            if action == "question" + str(i + 1):
                answer = req.get("queryResult").get("parameters").get("ans")
                data = {"question" + str(i): answer}
                survey_details.update(data)
                # survey_details.pop("question0")

                print(survey_details)

                # calling first question
                return {
                    "fulfillmentText": "This is a text response",
                    "fulfillmentMessages": [
                        # {
                        #     "card": {
                        #         "title": quest,
                        #     }
                        # },
                        {
                            "text": {
                                "text": [
                                    quest
                                ]
                            }
                        },
                        {
                            "quickReplies": {
                                "quickReplies": [
                                    "1",
                                    "2",
                                    "3",
                                    "4",
                                    "5"
                                ]
                            }
                        },

                    ]
                }

        if action == "completed":
            answer = req.get("queryResult").get("parameters").get("ans")
            data = {"question5": answer}
            survey_details.update(data)
            print(survey_details)
            survey_details.pop("question0")
            survey.insert(survey_details)
            print(survey_details)
            survey_details = {}

        elif action == "askhr":
            query = req.get("queryResult").get("parameters").get("query")
            print(query)
            token = random.randint(1000, 9999)
            issue = "ISU" + str(token)
            tickets.insert_one({
                "issue_no": issue,
                "token_id": tickets.count() + 1,
                "description": query,
                "priority": "high",
                "status": "open",
                "created_date": "date",
                # "created_date": datetime.datetime.now().isoformat(),
                "due_date": "",
                "comment": "",
            })
            print(tickets)
            return {
                "source": "webhook",
                "fulfillmentMessages": [
                    {
                        "text": {
                            "text": [
                                "Issue No : " + issue
                            ]
                        },
                        "platform": "FACEBOOK"
                    },
                    {
                        "quickReplies": {
                            "title": "Great. I will notify our HR about your query, and they resolve it as soon as "
                                     "possible.",
                            "quickReplies": [
                                "Verify Documents",
                                "See Induction",
                                "Offer Letter",
                                "ASK HR ",
                                "Code of Compliance",
                                "On boarding Feedback"
                            ]
                        },
                        "platform": "FACEBOOK"
                    }
                ]
            }



        elif action == "new_joinee":
            parameters = req.get("queryResult").get("parameters")
            print(parameters)
            parameters["email_id"] = parameters["email_id"].lower()
            print("lwer")
            print(parameters)
            filtered_parameters = {key: val for key, val in parameters.items()
                                   if val != ''}  # Removing empty parameters
            print(filtered_parameters)
            contact_info = new_joinee.find_one(filtered_parameters)
            print(contact_info)
            if parameters and contact_info:
                email = parameters
                email_id = contact_info.get("email_id")
                to_email = email_id
                otp = random.randrange(1000, 9999)
                new_joinee.find_one_and_update(filtered_parameters, {"$set": {"otp": otp}}, upsert=True)
                print(otp)
                subject = "Qrata - Verification OTP"
                body = "Your verification code is :- " + str(
                    otp) + " please enter the code in the chatbot for completing your verification process"
                utils.send_mail(to_email, subject, body)
                message = {
                    "source": "webhook",
                    "fulfillmentMessages": [
                        {
                            "text": {
                                "text": [
                                    "Enter the OTP send to your registered Email-ID"
                                ]
                            },
                            "platform": "FACEBOOK"
                        },
                    ],
                }

            else:
                message = {
                    "source": "webhook",
                    "fulfillmentMessages": [
                        {
                            "text": {
                                "text": [
                                    "Sorry !! your Email ID is not registered "
                                ]
                            },
                            "platform": "FACEBOOK"
                        },
                        {
                            "quickReplies": {
                                "title": "What would you like to do next?",
                                "quickReplies": [
                                    "Existing Employee",
                                    "New Joinee"
                                ]
                            },
                            "platform": "FACEBOOK"
                        }
                    ],
                }

            return message

        elif action == "feedback.score.1":
            score1 = req.get("queryResult").get("parameters").get("number")
            feedback.append(score1)
            feed["score1"] = score1

            print(feedback)

        elif action == "feedback.score.2":
            score2 = req.get("queryResult").get("parameters").get("number")
            feedback.append(score2)
            feed["score2"] = score2

            print(feedback)
        #
        # elif action == "Feedback":
        #     userfeedback = req.get("queryResult").get("parameters").get("feedback")
        #     # print(userfeedback)
        #
        #     # print(feedback)
        #     # print("****************************************************************************************************************************************")
        #     # print(feedback)

        elif action == "newjoinee.otp":
            otp = req.get("queryResult").get("queryText")
            print(otp)
            print(type(otp))
            contact_info = new_joinee.find_one(email)
            print(email)
            orginal_otp = contact_info.get("otp")

            print(email)
            print(orginal_otp)
            print(type(orginal_otp))
            name = contact_info.get("name")

            if int(otp) == orginal_otp:

                return {
                    "source": "webhook",
                    "fulfillmentMessages": [
                        {
                            "text": {
                                "text": [
                                    "Congratulations " + name + " on being part of the team! The whole company welcomes you and we look forward to a successful journey with you! Welcome aboard!"
                                    # "Hi "+name+ ", welcome to Qrata !! "
                                ]
                            }
                        },
                        {
                            "payload": {
                                "facebook": {
                                    "attachment": {
                                        "payload": {
                                            "elements": [
                                                {
                                                    "url": "https://www.facebook.com/109485067074411/videos/504973897123117/",
                                                    "media_type": "video"
                                                }
                                            ],
                                            "template_type": "media"
                                        },
                                        "type": "template"
                                    }
                                }
                            },
                            "platform": "FACEBOOK"
                        },
                        {
                            "quickReplies": {
                                "title": "Onboarding Menu",
                                "quickReplies": [
                                    "Verify Documents",
                                    "See Induction",
                                    "Offer Letter",
                                    "ASK HR ",
                                    "Code of Compliance",
                                    "Onboarding Feedback"
                                ]
                            },
                            "platform": "FACEBOOK"
                        },
                    ]
                }
            else:
                return {
                    "source": "webhook",
                    "fulfillmentMessages": [
                        {
                            "quickReplies": {
                                "title": " OTP Not valid",
                                "quickReplies": [
                                    "Existing Employee",
                                    "New Joinee"
                                ]
                            },
                            "platform": "FACEBOOK"
                        },
                        {
                            "text": {
                                "text": [
                                    ""
                                ]
                            }
                        }
                    ]
                }






        elif action == "remaining_leaves":
            if employ_id:
                contact_info = employee_details.find_one(employ_id)
                remaining_leave = contact_info.get("leaves")
                print(employ_id)
                print(remaining_leave)
                return {
                    "source": "webhook",
                    "fulfillmentMessages": [
                        {
                            "text": {
                                "text": [
                                    "You have " + str(
                                        remaining_leave) + " leaves out of 18 and these are going to expire by 31 December, 2019."
                                ]
                            },
                            "platform": "FACEBOOK"
                        },
                        {
                            "quickReplies": {
                                "title": "What would you like to do next?",
                                "quickReplies": [
                                    "Apply for Leave",
                                    "Cancel a Leave",
                                    "Get Started"
                                ]
                            },
                            "platform": "FACEBOOK"
                        }
                    ]
                }
            else:
                return {
                    "source": "webhook",
                    "fulfillmentMessages": [
                        {
                            "text": {
                                "text": [
                                    "please validate yourself as a existing employee"
                                ]
                            },
                            "platform": "FACEBOOK"
                        },
                        {
                            "quickReplies": {
                                "title": "What would you like to do next?",
                                "quickReplies": [
                                    "existing employee"
                                ]
                            },
                            "platform": "FACEBOOK"
                        }
                    ]
                }


        elif action == "request.leave":
            date_string = req.get("queryResult").get("parameters").get("date")
            return {
                "source": "webhook",
                "fulfillmentMessages": [
                    {
                        "text": {
                            "text": [
                                "Okay, you applied a leave for " + utils.date2text(
                                    date_string) + ",  a mail has been send to your manager for approval "
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
                    },
                    {
                        "quickReplies": {
                            "title": "What would you like to do next?",
                            "quickReplies": [
                                "Get Started",
                                "Check Leave Balance",

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
                    },
                    {
                        "quickReplies": {
                            "title": "What would you like to do next?",
                            "quickReplies": [
                                "Get Started",
                                "Reimbursement",
                                "My Health Insurance"
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



        # elif action == "remaining_leaves":

        elif action == "Feedback":
            userfeedback = req.get("queryResult").get("parameters").get('feedback')

            feedback.append(userfeedback)
            timec = datetime.date(datetime.now()).isoformat()
            feed["feedback"] = userfeedback
            ts = calendar.timegm(time.gmtime())
            feed["time"] = str(timec)
            feed["timestamp"] = ts
            print(feed)
            text = TextBlob(userfeedback)
            sentiment = text.sentiment.polarity
            subjective = text.sentiment.subjectivity
            feedback.clear()
            print(subjective)
            if sentiment >= 0.15 or userfeedback == "🙂":
                feed["sentiment"] = "positive"
                feedbackdata.insert_one(feed)
                print(feed)
                message = u"\U0001F600 " + f"We are glad that you like our culture."
                feed.clear()
            elif sentiment <= -0.15 or userfeedback == "☹️":
                feed["sentiment"] = "negative"
                feedbackdata.insert_one(feed)
                print(feed)

                message = "Sorry to hear that. We will make sure to improve our culture and make this " \
                          "a better place to work."
                feed.clear()
            else:
                feed["sentiment"] = "positive"
                feedbackdata.insert_one(feed)
                message = "Alright, I have noted the feedback."
                feed.clear()

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
                    },
                    {
                        "quickReplies": {
                            "title": "What would you like to do next?",
                            "quickReplies": [
                                "Get Started",
                                "Submit An idea"
                            ]
                        },
                        "platform": "FACEBOOK"
                    }
                ]
            }

        elif action == "search_employee":
            inputname = req.get("queryResult").get("parameters").get("name").get("name")
            print(inputname)
            inputname = inputname.lower()
            contact_info = employee_details.find({"name": {"$regex": inputname}}).limit(3)
            print(contact_info)
            if contact_info.count() != 0:
                return {
                    "source": "webhook",
                    "fulfillmentMessages": [
                                               {
                                                   "card": {
                                                       "title": emp["name"],
                                                       "subtitle": emp["designation"] + " | " + "Phone: " + " | " + str(
                                                           emp["contact_number"]),
                                                       "imageUri": "https://www.cristianmonroy.com/wp-content/uploads/2017/11/avatars-avataaars"
                                                                   ".png",
                                                       "buttons": [
                                                           {
                                                               "text": "Profile",
                                                               "postback": emp["profile"]
                                                           }
                                                       ]
                                                   },
                                                   "platform": "FACEBOOK"
                                               } for emp in contact_info] + [
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
            else:
                return {
                    "source": "webhook",
                    "fulfillmentMessages": [
                        {
                            "text": {
                                "text": [
                                    "Sorry, I was not able to find the given person."
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



        elif action == "search_employee_emp":
            parameters = req.get("queryResult").get("parameters")
            print(parameters)
            parameters["employ_id"] = parameters["employ_id"].upper()
            filtered_parameters = {key: val for key, val in parameters.items()
                                   if val != ''}  # Removing empty parameters
            print(filtered_parameters)
            contact_info = employee_details.find_one(filtered_parameters)
            if contact_info and filtered_parameters:
                message = {
                    "card": {
                        "title": contact_info.get("name"),
                        "subtitle": contact_info.get('designation') + " | " + "Phone: " + str(
                            contact_info.get("contact_number")),
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
            public_holidays_string = public_holidays[public_holidays["State"] == state].to_string(
                columns=["Date", "Holiday"], header=False, index=False)
            return {
                "source": "webhook",
                "fulfillmentMessages": [
                    {
                        "text": {
                            "text": [
                                "Here is the list of all public holidays in " + state + "\n\n" + public_holidays_string
                            ]
                        },
                        "platform": "FACEBOOK"
                    },
                    {
                        "quickReplies": {
                            "title": "What would you like to do next?",
                            "quickReplies": [
                                "Get Started",
                                "Check Leave Balance",
                                "Apply for leave"
                            ]
                        },
                        "platform": "FACEBOOK"
                    }
                ]
            }



        elif action == "show.all.jobs":
            jobs_search = jobs.find({"statusVisible": "enum.Hiring_JobPositionStatusVisible.Public"}).limit(10)

            if jobs_search.count() != 0:
                return {
                    "source": "webhook",
                    "fulfillmentMessages": [
                                               {
                                                   "text": {
                                                       "text": [
                                                           "Here are some job openings available in our organisation."
                                                       ]
                                                   },
                                                   "platform": "FACEBOOK"
                                               }] + [
                                               {
                                                   "card": {
                                                       "title": job["jobTitle"],
                                                       "subtitle": job["companyName"] + " | " + job[
                                                           "locality"] + " | " + job["region"],
                                                       "imageUri": "https://akm-img-a-in.tosshub.com/sites/btmt/images/stories/jobs660_090518050232_103118054303_022119084317.jpg",
                                                       "buttons": [
                                                           {
                                                               "text": "Refer this Job",
                                                               "postback": job["jobDetailsUrl"]
                                                           }
                                                       ]
                                                   },
                                                   "platform": "FACEBOOK"
                                               } for job in jobs_search] + [
                                               {
                                                   "quickReplies": {
                                                       "title": "What would you like to do next?",
                                                       "quickReplies": [
                                                           "Get Started"
                                                       ]
                                                   },
                                                   "platform": "FACEBOOK"
                                               }
                                           ]
                }
            else:
                return {
                    "source": "webhook",
                    "fulfillmentMessages": [
                        {
                            "text": {
                                "text": [
                                    "Sorry to inform you that currently we don't have any job openings"
                                ]
                            },
                            "platform": "FACEBOOK"
                        },
                        {
                            "quickReplies": {
                                "title": "What would you like to do next?",
                                "quickReplies": [
                                    "Get Started"
                                ]
                            },
                            "platform": "FACEBOOK"
                        }
                    ]
                }

        elif action == "raise.ticket":
            query = req.get("queryResult").get("parameters").get("query")
            print(query)
            token = random.randint(1000, 9999)
            issue = "ISU" + str(token)
            tickets.insert_one({
                "issue_no": issue,
                "token_id": tickets.count() + 1,
                "employee_id": "EMP" + str(random.randint(1000, 9999)),
                "description": query,
                "priority": "high",
                "status": "open",
                "created_date": "date",
                # "created_date": datetime.datetime.now().isoformat(),
                "due_date": "",
                "comment": "",
            })
            print(tickets)
            return {
                "source": "webhook",
                "fulfillmentMessages": [
                    {
                        "text": {
                            "text": [
                                "Issue No : " + issue
                            ]
                        },
                        "platform": "FACEBOOK"
                    },
                    {
                        "quickReplies": {
                            "title": "Great. I will notify our HR about your query, and they resolve it as soon as "
                                     "possible.",
                            "quickReplies": [
                                "Get Started"
                            ]
                        },
                        "platform": "FACEBOOK"
                    }
                ]
            }

        elif action == "input.unknown":
            unknown_flag += 1

            if unknown_flag >= 2:
                unknown_flag = 0
                query = req.get("queryResult").get("queryText")
                return {
                    "source": "webhook",
                    "fulfillmentMessages": [
                        {
                            "quickReplies": {
                                "title": "If I am not able to fulfill your request, you can raise the ticket so that "
                                         "our HR team can respond you directly.",
                                "quickReplies": [
                                    "Raise the Ticket",
                                    "Get Started"
                                ]
                            },
                            "platform": "FACEBOOK"
                        }
                    ],
                    "outputContexts": [
                        {
                            "name": "projects/internal-hr-bot-womtev/agent/sessions/f6ec5940-9c6d-d669-af33-45426780ba5d/contexts/raise_ticket",
                            "lifespanCount": 1,
                            "parameters": {
                                "query": query,
                            }
                        }
                    ]
                }

    except Exception as e:
        print("Error:", e)
        traceback.print_exc()
        return {
            "source": "webhook",
            "fulfillmentMessages": [
                {
                    "quickReplies": {
                        "title": "Sorry, I am not able to help you at the moment. This are some topics I can help you with",
                        "quickReplies": [
                            "My Leave & Absence",
                            "My General Support",
                            "My Pay & Benefits",
                            "Happify Me",
                            "My Learning"
                        ]
                    },
                    "platform": "FACEBOOK"
                },
                {
                    "text": {
                        "text": [
                            ""
                        ]
                    }
                }
            ]
        }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print("Starting app on port {}".format(port))
    app.run(debug=True, port=port, host='0.0.0.0')
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        '--project-id',
        help='Project/agent id.  Required.',
        required=True)
    parser.add_argument(
        '--session-id',
        help='Identifier of the DetectIntent session. '
             'Defaults to a random UUID.',
        default=str(uuid.uuid4()))
    parser.add_argument(
        '--language-code',
        help='Language code of the query. Defaults to "en-US".',
        default='en-US')
    parser.add_argument(
        'texts',
        nargs='+',
        type=str,
        help='Text inputs.')

    args = parser.parse_args()

    detect_intent_texts(args.project_id, args.session_id, args.texts, args.language_code)
