months = "January,February,March,April,May,June,July,August,September,October,November,December".split(",")


# Creating a function which
def date2text(date_string):
    date = date_string.split("T")[0].split("-")
    return date[2] + " " + months[int(date[1]) - 1] + ", " + date[0]
