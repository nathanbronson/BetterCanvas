import os
import strptime as _strptime
import importlib
import canvas_lms_api
import canvasapi
import dateparser.conf
import dateparser.search
from dateparser.utils import strptime
from spacy import load
import datetime
import urllib.request
import webbrowser
from pytz import timezone
from dateutil.tz import tzlocal
from freezegun import freeze_time
from dateutil.parser import parse as duparse
from threading import Thread
import nacl.secret
import nacl.utils
import nacl.pwhash
import schedule_objects
import en_core_web_sm

nlp = load('en_core_web_sm', disable=['ner','textcat'])
dateparser.search.search_dates("next monday")
days_abbr = [list(i) for i in _strptime.names["days_abbr"]]
months_abbr = [list(i) for i in _strptime.names["months_abbr"]]
abbr = months_abbr + days_abbr
abbr += [[n[0].upper(), n[1], n[2]] for n in abbr]
colon_chars = [str(i) for i in range(10)] + [" "]

if __name__ == "__main__":
    if not os.path.isfile("secure_login.bin"):
        print("WELCOME")
        good = int(input("Do you give permission for the program to use your Canvas account via your Canvas Access Token?\n1. Yes\n2. No\n"))
        if good == 1:
            print("Thanks!")
        else:
            print("The program won't work without the token.")
            exit()
        token = input("Enter your Canvas Access Token. To find it, go to Canvas in your browser, login, navigate to your settings page, find the button that says generate token, click it, and give me the token it gives you.\n")
        print("This token will be stored in this folder, so don't share it.")
        bv = int(input("Are you in the Blue Valley School District?\n1. Yes\n2. No\n"))
        if bv == 1:
            site = "https://bvusd.instructure.com"
        else:
            site = str(input("What is your Canvas url?\n"))
        print("LOGGING IN")
        canvas_lms = canvas_lms_api.Canvas(base=site, token=token)
        canvas = canvasapi.Canvas(site, token)
        print("It worked. The token is going to be stored here, so don't share this folder or anything in it. Somebody could use it to access your Canvas account.")
        l = open("login.py", "w+")
        l.write("from schedule_objects import MeetingEvent\nfrom datetime import datetime\n")
        l.write("token = '{}'\nsite = '{}'\n".format(token, site))
        courses = canvas_lms.GetCourses()
        print("SET UP")
        while True:
            course_bindings = {}
            for i in courses:
                course_bindings[i["name"]] = i["id"]
            course_string = ""
            for i in range(len(list(course_bindings.keys()))):
                course_string = course_string + str(i) + ". " + [n for n in course_bindings.keys()][i] + "\n"
            followed_course_numbers = str(input("Enter the numbers of each course you want follow:\n" + course_string))
            exec("followed_course_numbers = [" + followed_course_numbers + "]")
            followed_courses = []
            for i in followed_course_numbers:
                followed_courses.append([n for n in course_bindings.keys()][i])
            for i in followed_courses:
                print(i)
            right = int(input("Are these the courses you want to follow?\n1. Yes\n2. No\n"))
            if right == 1:
                break
        my_courses = []
        for i in followed_courses:
            my_courses.append(course_bindings[i])
        l.write("followed_courses = {}\n".format(my_courses))
        l.write("meetings = []\n")
        while True:
            choice = int(input("Would you like to save class times to help with scheduling?\n1. Yes\n2. No\n"))
            if choice == 1:
                name = str(input("What is the name of the class?\n"))
                _next = dateparser.search.search_dates(str(input("When is the next time you will have this class? (include date and time with AM or PM)\n")))[0][1]
                length = dateparser.search.search_dates(str(input("What time does the class end? (include AM or PM)\n")))[0][1]
                weekends = int(input("Does this class occur on weekends?\n1. Yes\n2. No\n"))
                if weekends == 1:
                    weekends = True
                else:
                    weekends = False
                patterns = ["Day of the Week", "Every Day", "Every Other Day", "Every Third Day", "Every Fourth Day", "Every Fifth Day", "Every Sixth Day", "Every Other Week", "Once A Month"]
                stri = "Which meeting pattern does this class follow?\n"
                for i in range(len(patterns)):
                    stri += "{}. {}\n".format(str(i), patterns[i])
                pattern = patterns[int(input(stri))]
                l.write("meetings.append(MeetingEvent('{}', datetime(year={}, month={}, day={}, hour={}, minute={}), datetime(year={}, month={}, day={}, hour={}, minute={}), {}, weekends={}))\n".format(str(name), str(_next.year), str(_next.month), str(_next.day), str(_next.hour), str(_next.minute), str(_next.year), str(_next.month), str(_next.day), str(length.hour), str(length.minute), patterns.index(str(pattern)), str(weekends)))
            else:
                break
        l.close()
        mks = make_secure_module("login.py", "secure_login.bin", "login_salt.bin")
        try:
            mks = mks.send(str(input(next(mks))))
        except StopIteration:
            pass
        print("LOGGED IN")
        login = get_from_secure_module("secure_login.bin", "login.py", "login_salt.bin")
        try:
            login = login.send(str(input(next(login))))
        except StopIteration:
            pass
        try:
            meetings = login.meetings
        except AttributeError:
            meetings = False
        l = os.system("rm old_login.py")
        followed_courses = my_courses
        print("In order to use the Apple Calendar Integration, you'll have to create a new calendar.")
        choice = int(input("Would you like to do this?\n1. Yes\n2. No\n"))
        if choice == 1:
            os.system("osascript create_calendar.scpt")
        else:
            print("Okay. If you want to do this later, you can from the menu.")
    
    else:
        print("Welcome back!")
        login = get_from_secure_module("secure_login.bin", "login.py", "login_salt.bin")
        try:
            login = login.send(str(input(next(login))))
        except StopIteration:
            pass
        good = int(input("Has any configuration information changed since you were here last?\n1. Yes\n2. No\n"))
        if good == 1:
            print("Restart the program to set up.")
            print("Here is your current data:")
            print("token: ", login.token, "\nfollowed courses: ", login.followed_courses, "\nsite: ", login.site)
            os.system("mv login.py old_login.py")
            os.system("rm login_salt.bin")
            os.system("rm secure_login.bin")
            exit()
        canvas_lms = canvas_lms_api.Canvas(base=login.site, token=login.token)
        canvas = canvasapi.Canvas(login.site, login.token)
        followed_courses = login.followed_courses
        try:
            print("getting meetings")
            print(login.meetings)
            meetings = login.meetings
            print("meetings:", meetings, meetings if meetings else [])
        except AttributeError:
            meetings = False
        print("LOGGED IN")
    items, due_dates = load_items(canvas_lms, canvas, followed_courses)
    date_finder = DateFinder(canvas_lms, canvas, items, due_dates)
    dates = False
    today = False
    week = False
    while True:
        action = int(input("Select an action:\n0. Find Dates\n1. Today View\n2. Week View\n3. Custom View\n4. Create Calendar\n5. Exit\n"))
        if action == 0:
            if not dates:
                dates = find_dates(canvas_lms, canvas, items, due_dates, date_finder)
            for i in list(dates.keys()):
                for n in dates[i]:
                    print(n, i)
        elif action == 1:
            if not dates:
                dates = find_dates(canvas_lms, canvas, items, due_dates, date_finder)
            if not today:
                today = TodayView(canvas_lms, canvas, dates)
            today_events = today.ret_today_events()
            stri = "0. Exit\n1. Create Schedule\n"
            for i in range(len(today_events)):
                stri += str(i + 2) + ". " + today_events[i].__str__() + "\n"
            while True:
                choice = int(input(stri))
                if choice == 0:
                    break
                elif choice == 1:
                    schedule = schedule_objects.Schedule(datetime.datetime.now(), meetings=(meetings if meetings else []))
                    schedule.schedule_events(events)
                    schedule.give_choices()
                elif choice in range(len(today_events) + 2):
                    today_events[choice - 2].give_choices()
        elif action == 2:
            if not dates:
                dates = find_dates(canvas_lms, canvas, items, due_dates, date_finder)
            if not week:
                week = WeekView(canvas_lms, canvas, dates)
            events = []
            stri = "0. Exit\n1. Create Schedule\n2. Add Due Dates\n"
            count = 3
            for i in week.ret_days():
                stri += i.get_week_day()
                for n in i.ret_events():
                    events.append(n)
                    stri += str(count) + ". " + n.__str__() + "\n"
                    count += 1
            while True:
                choice = int(input(stri))
                if choice == 0:
                    break
                elif choice == 1:
                    schedule = schedule_objects.Schedule(week.week, meetings=(meetings if meetings else []))
                    schedule.schedule_events(events)
                    schedule.give_choices()
                elif choice == 2:
                    week.put_due_dates()
                elif choice in range(len(events) + 2):
                    events[choice - 2].give_choices()
        elif action == 3:
            if not dates:
                dates = find_dates(canvas_lms, canvas, items, due_dates, date_finder)
            while True:
                try:
                    custom = CustomView(canvas_lms, canvas, dates, dateparser.search.search_dates(str(input("input start\n")))[0][1], dateparser.search.search_dates(str(input("input end\n")))[0][1])
                    break
                except TypeError:
                    print("Date Was Not Recognized")
                    pass
            events = []
            stri = "0. Exit\n1. Create Schedule\n2. Add Due Dates\n"
            count = 3
            for i in custom.ret_days():
                stri += i.get_week_day()
                for n in i.ret_events():
                    events.append(n)
                    stri += str(count) + ". " + n.__str__() + "\n"
                    count += 1
            while True:
                choice = int(input(stri))
                if choice == 0:
                    break
                elif choice == 1:
                    schedule = schedule_objects.Schedule(custom.week, meetings=(meetings if meetings else []))
                    schedule.schedule_events(events)
                    schedule.give_choices()
                elif choice == 2:
                    custom.put_due_dates()
                elif choice in range(len(events) + 2):
                    events[choice - 2].give_choices()
        elif action == 4:
            os.system("osascript create_calendar.scpt")
        elif action == 5:
            break