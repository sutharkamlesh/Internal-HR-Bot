import smtplib
import math, random

months = "January,February,March,April,May,June,July,August,September,October,November,December".split(",")


# Creating a function which context datetime string to readable text
def date2text(date_string):
    date = date_string.split("T")[0].split("-")
    return date[2] + " " + months[int(date[1]) - 1] + ", " + date[0]


# Creating a Function to send a mail
def send_mail(to_email, subject, body):
    # creates SMTP session
    s = smtplib.SMTP('smtp.gmail.com', 587)

    # start TLS for security
    s.starttls()

    # Authentication
    s.login("kamlesh.suthar@techmatters.com", "techmatters123")
    message = """\\nFrom: kamlesh.suthar@techmatters.com\nTo: {0}\nSubject: {1}\n\n{2}""".format(to_email, subject, body)
    # sending the mail
    s.sendmail("kamlesh.suthar@techmatters.com", to_email, message)
    # terminating the session
    s.quit()


def batch_update_entities(project_id, entity_type, entities):
    """Create an entity type with the given display name."""
    import dialogflow_v2 as dialogflow
    client = dialogflow.EntityTypesClient()
    parent = client.entity_type_path(project_id, entity_type)
    response = client.batch_create_entities(parent, entities)
    print("Entities Updated: \n{}".format(response))


def generateOTP():
    # Declare a string variable
    # which stores all string
    string = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    OTP = ""
    length = len(string)
    for i in range(6):
        OTP += string[math.floor(random.random() * length)]
    return OTP
