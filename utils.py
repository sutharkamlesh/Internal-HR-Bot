import smtplib

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
    s.login("kamlesh.suthar@techmatters.com", "fall0_40c")
    message = """\
    From: kamlesh.suthar@techmatters.com
    To: {0}
    Subject: {1} 
    
    {2}
    """.format(to_email, subject, body)
    # sending the mail
    s.sendmail("kamlesh.suthar@techmatters.com", to_email, message)
    # terminating the session
    s.quit()
