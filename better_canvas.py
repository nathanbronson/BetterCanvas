"""
NOTE ON THE CODE (2024):
Apologies for the code quality.
This was my first major app developed from scratch over 3 years ago, so the code is, in many places, inelegant, inefficient, and unintelligible. It also makes some questionable use of applescript.
Reverse engineer it at your own risk.
"""

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

try:
    import en_core_web_sm
except:
    os.system("python3 -m spacy download en_core_web_sm")

nlp = load('en_core_web_sm', disable=['ner','textcat'])
dateparser.search.search_dates("next monday")
days_abbr = [list(i) for i in _strptime.names["days_abbr"]]
months_abbr = [list(i) for i in _strptime.names["months_abbr"]]
abbr = months_abbr + days_abbr
abbr += [[n[0].upper(), n[1], n[2]] for n in abbr]
colon_chars = [str(i) for i in range(10)] + [" "]
add_event_osa = (
    """osascript -e '
    set theStartDate to (current date) + ({} * days)
    set hours of theStartDate to {}
    set minutes of theStartDate to {}
    set seconds of theStartDate to {}
    set theEndDate to theStartDate
    set hours of theEndDate to {}
    set minutes of theEndDate to {}
    set seconds of theEndDate to {}
    tell application "Calendar"
        tell calendar "Blender"
            make new event with properties {{description:"{}", summary:"{}", start date:theStartDate, end date:theEndDate}}
        end tell
    end tell'""")

class Day(object):
    def __init__(self, canvas_lms, canvas, dates, day):
        self.canvas_lms = canvas_lms
        self.canvas = canvas
        self.dates = dates
        if type(day) == type(datetime.datetime.now()):
            self.day = day
        elif type(day) == type(datetime.timedelta(1)):
            self.day = day + datetime.datetime.now()
        else:
            raise ValueError("invalid type for day, must be datetime or timedelta")
        self.day_events = self.get_day_events()
    
    def __str__(self):
        stri = ""
        for i in self.day_events:
            stri += i.__str__()
            stri += "\n"
        return stri
    
    def get_day_events(self):
        day_keys = []
        for i in list(self.dates.keys()):
            if (i.year, i.month, i.day) == (self.day.year, self.day.month, self.day.day):
                day_keys.append(i)
        day_items = []
        for i in day_keys:
            #print("i", i.year, i.month, i.day)
            for n in self.dates[i]:
                #print("n", n)
                day_items.append(n)
        return day_items if len(day_items) > 0 else []
    
    def ret_events(self):
        return self.day_events
    
    def get_week_day(self):
        return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][self.day.weekday()] + " " + str(self.day.day) + "\n"

class CustomView(object):
    def __init__(self, canvas_lms, canvas, dates, start, end):
        self.canvas_lms = canvas_lms
        self.canvas = canvas
        self.dates = dates
        if type(end) == type(datetime.datetime.now()):
            end = end - start
        elif type(end) == type(datetime.timedelta(1)):
            pass
        else:
            raise ValueError("invalid type for end, must be datetime or timedelta")
        self.week = [start + datetime.timedelta(i) for i in range(end.days)]
        self.each_day = self.get_week_days()
    
    def __str__(self):
        stri = ""
        week_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for i in list(self.week_events.keys()):
            stri += week_days[i.weekday()] + " the " + i.day + ":\n"
            for n in self.week_events[i]:
                stri += n.__str__()
                stri += "\n"
            stri += "\n"
        return stri
    
    def get_week_days(self):
        each_day = []
        for i in self.week:
            each_day.append(Day(self.canvas_lms, self.canvas, self.dates, i))
        return each_day
    
    def ret_days(self):
        return self.each_day
    
    def put_due_dates(self):
        events = []
        for i in self.ret_days():
            for n in i.get_day_events():
                events.append(n)
        add_to_calendar(events)

class WeekView(object):
    def __init__(self, canvas_lms, canvas, dates):
        self.canvas_lms = canvas_lms
        self.canvas = canvas
        self.dates = dates
        self.week = [datetime.datetime.now() + datetime.timedelta(i) for i in range(7)]
        self.each_day = self.get_week_days()
    
    def __str__(self):
        stri = ""
        week_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for i in list(self.week_events.keys()):
            stri += week_days[i.weekday()] + " the " + i.day + ":\n"
            for n in self.week_events[i]:
                stri += n.__str__()
                stri += "\n"
            stri += "\n"
        return stri
    
    def get_week_days(self):
        each_day = []
        for i in self.week:
            each_day.append(Day(self.canvas_lms, self.canvas, self.dates, i))
        return each_day
    
    def ret_days(self):
        return self.each_day
    
    def put_due_dates(self):
        events = []
        for i in self.ret_days():
            for n in i.get_day_events():
                events.append(n)
        add_to_calendar(events)

class TodayView(object):
    def __init__(self, canvas_lms, canvas, dates):
        self.canvas_lms = canvas_lms
        self.canvas = canvas
        self.dates = dates
        self.today_events = self.get_today_events()
    
    def __str__(self):
        stri = ""
        for i in self.today_events:
            stri += i.__str__()
            stri += "\n"
        return stri
    
    def get_today_events(self):
        now = datetime.datetime.now()
        today_keys = []
        for i in list(self.dates.keys()):
            #print("today", now.year, now.month, now.day)
            #print((i.year, i.month, i.day) == (now.year, now.month, now.day))
            if (i.year, i.month, i.day) == (now.year, now.month, now.day):
                today_keys.append(i)
        today_items = []
        for i in today_keys:
            #print("i", i.year, i.month, i.day)
            for n in self.dates[i]:
                #print("n", n.date)
                today_items.append(n)
        return today_items
    
    def ret_today_events(self):
        return self.today_events

class AssignmentItem(object):
    def __init__(self, name, body, date, url=False):
        self.name = str(name)
        self.body = str(body)
        self.date = date
        if type(self.date) == type(""):
            e = self.date
            day = datetime.datetime(year=int(e[0:4]), month=int(e[5:7]), day=int(e[8:10]), hour=int(e[11:13]), minute=int(e[14:16]), second=int(e[17:19]), tzinfo=timezone("Zulu"))
            self.date = day.astimezone(tzlocal())
        else:
            self.date = self.date.astimezone(tzlocal())
        self.url = url
        self.schedule_start = date
        self.schedule_end = date + datetime.timedelta(seconds=1)
    
    def __str__(self):
        return self.name
    
    def take_me_there(self):
        if self.url:
            webbrowser.open(self.url)
        else:
            print(self, "has no associated url")
    
    def give__choices(self):
        while True:
            choice = yield "0. Exit\n1. Take Me There\n2. Observe\n"
            choice = int(choice)
            if choice == 0:
                break
            elif choice == 1:
                self.take_me_there()
            elif choice == 2:
                self.observe()
    
    def give_choices(self):
        while True:
            choice = int(input("0. Exit\n1. Take Me There\n2. Observe\n"))
            if choice == 0:
                break
            elif choice == 1:
                self.take_me_there()
            elif choice == 2:
                self.observe()
    
    def observe(self):
        print("name", self.name)
        print("body", self.body)
        print("date", self.date)
        print("url", self.url)
    
    def as_type(self, _type):
        if _type == schedule_objects.ProvisionalEvent:
            if self.date.hour == 23 and self.date.minute == 59:
                return schedule_objects.ProvisionalEvent(self)
            else:
                naive = self.date
                return schedule_objects.ProvisionalEvent(self, pref_start=naive.replace(tzinfo=None))

class DatedItem(object):
    #date names could be posted_at_date, created_at_date
    def __init__(self, name, body, created_at_date, url=False):
        self.body = str(body)
        self.name = str(name)
        self.date = created_at_date
        if type(self.date) == type(""):
            e = self.date
            day = datetime.datetime(year=int(e[0:4]), month=int(e[5:7]), day=int(e[8:10]), hour=int(e[11:13]), minute=int(e[14:16]), second=int(e[17:19]), tzinfo=timezone("Zulu"))
            self.date = day.astimezone(tzlocal())
        else:
            self.date = self.date.astimezone(tzlocal())
        self.url = url
        self.schedule_start = self.date
        self.schedule_end = self.date + datetime.timedelta(seconds=1)
            
    def __str__(self):
        return self.name
    
    def take_me_there(self):
        if self.url:
            webbrowser.open(self.url)
        else:
            print(self, "has no associated url")
    
    def give__choices(self):
        while True:
            choice = yield "0. Exit\n1. Take Me There\n2. Observe\n"
            choice = int(choice)
            if choice == 0:
                break
            elif choice == 1:
                self.take_me_there()
            elif choice == 2:
                self.observe()
    
    def give_choices(self):
        while True:
            choice = int(input("0. Exit\n1. Take Me There\n2. Observe\n"))
            if choice == 0:
                break
            elif choice == 1:
                self.take_me_there()
            elif choice == 2:
                self.observe()
    
    def observe(self):
        print("name", self.name)
        print("body", self.body)
        print("date", self.date)
        print("url", self.url)
    
    def as_type(self, _type):
        if _type == schedule_objects.ProvisionalEvent:
            if self.date.hour == 23 and self.date.minute == 59:
                return schedule_objects.ProvisionalEvent(self)
            else:
                naive = self.date
                return schedule_objects.ProvisionalEvent(self, pref_start=naive.replace(tzinfo=None))
        
class UndatedItem(object):
    def __init__(self, body, name, url=False):
        self.body = str(body)
        self.name = str(name)
        self.url = url
            
    def __str__(self):
        return self.name
    
    def take_me_there(self):
        if self.url:
            webbrowser.open(self.url)
        else:
            print(self, "has no associated url")
    
    def give__choices(self):
        while True:
            choice = yield "0. Exit\n1. Take Me There\n2. Observe\n"
            choice = int(choice)
            if choice == 0:
                break
            elif choice == 1:
                self.take_me_there()
            elif choice == 2:
                self.observe()
    
    def give_choices(self):
        while True:
            choice = int(input("0. Exit\n1. Take Me There\n2. Observe\n"))
            if choice == 0:
                break
            elif choice == 1:
                self.take_me_there()
            elif choice == 2:
                self.observe()
    
    def observe(self):
        print("name", self.name)
        print("body", self.body)
        print("url", self.url)
    
    def as_type(self, _type):
        if _type == schedule_objects.ProvisionalEvent:
            if self.date.hour == 23 and self.date.minute == 59:
                return schedule_objects.ProvisionalEvent(self)
            else:
                naive = self.date
                return schedule_objects.ProvisionalEvent(self, pref_start=naive.replace(tzinfo=None))
        
class ImpliedItem(object):
    def __init__(self, name, date, source_item, date_str=False):
        self.name = str(name)
        self.date = date.replace(tzinfo=tzlocal())
        self.source_item = source_item
        if date_str:
            self.date_str = date_str
        self.schedule_start = date
        self.schedule_end = date + datetime.timedelta(seconds=1)
        self.url = self.source_item.url
    
    def __str__(self):
        return self.name
    
    def take_me_there(self):
        self.source_item.take_me_there()
    
    def give__choices(self):
        while True:
            choice = yield "0. Exit\n1. Take Me There\n2. Observe\n"
            choice = int(choice)
            if choice == 0:
                break
            elif choice == 1:
                self.take_me_there()
            elif choice == 2:
                self.observe()
    
    def give_choices(self):
        while True:
            choice = int(input("0. Exit\n1. Take Me There\n2. Observe\n3. Rename\n"))
            if choice == 0:
                break
            elif choice == 1:
                self.take_me_there()
            elif choice == 2:
                self.observe()
            elif choice == 3:
                self.rename()
    
    def observe(self):
        print("name", self.name)
        print("date", self.date)
        if self.date_str:
            print("date_str", self.date_str)
        print("source", self.source_item)
        self.source_item.observe()
    
    def rename(self):
        new_name = str(input("enter new name\n"))
        self.name = new_name
    
    def as_type(self, _type):
        if _type == schedule_objects.ProvisionalEvent:
            if self.date.hour == 23 and self.date.minute == 59:
                return schedule_objects.ProvisionalEvent(self)
            else:
                naive = self.date
                return schedule_objects.ProvisionalEvent(self, pref_start=naive.replace(tzinfo=None))

def before_root(doc, date, is_root=False):
    date = [str(i.text) for i in date]
    for i in doc:
        #print(i.text, str(i.dep_))
        if str(i.text) in date and str(i.dep_) == "ROOT":
            return is_root
        if str(i.dep_) == "ROOT":
            return False
        if str(i.text) in date:
            return True
    return False

def get_context(body, date):
    date = str(date)
    doc = str(body)
    doc = nlp(doc)
    #span = doc[doc[4].left_edge.i : doc[4].right_edge.i+1]
    try:
        span = doc[doc[0].left_edge.i : doc[0].right_edge.i+1]
    except IndexError:
        return
    threads = []
    date = nlp(str(date))
    l = before_root(doc, date)
    with doc.retokenize() as retokenizer:
        retokenizer.merge(span)
    #for i in doc:
    #    print(i, i.dep_, i.pos_, i.head.text)
    #print(l)
    #print(doc)
    #print(date)
    if l:
        for i in doc:
            #print(i.text, i.dep_, i.head.text)
            if str(i.dep_) == "ROOT":
                threads = [i, i.head]
                #print(threads)
                while True:
                    q = 0
                    for n in threads:
                        #print(n.head)
                        if not n.head in threads:
                            threads.append(n.head)
                            q += 1
                        for g in doc:
                            if not g in threads:
                                if g.head == n:
                                    threads.append(g)
                                    q += 1
                    if q == 0:
                        break
                break
    else:
        prefer_prop = False
        for i in doc:
            if str(i.pos_) == "ROOT":
                break
            prefer_prop = str(i.pos_) == "PROPN"
            if prefer_prop:
                break
        if not prefer_prop:
            for i in doc:
                #print(i.pos_)
                if str(i.pos_) == "NOUN" or str(i.pos_) == "PROPN":
                    threads = [i, i.head]
                    #print(threads)
                    while True:
                        q = 0
                        for n in threads:
                            if not n.head in threads:
                                threads.append(n.head)
                                q += 1
                        if q == 0:
                            break
                    break
        else:
            for i in doc:
                #print(i.pos_)
                if str(i.pos_) == "PROPN":
                    threads = [i, i.head]
                    #print(threads)
                    while True:
                        q = 0
                        for n in threads:
                            if not n.head in threads:
                                threads.append(n.head)
                                q += 1
                        if q == 0:
                            break
                    break
    #print("doc", doc)
    #print("threads", threads)
    for i in range(len(threads)):
        try:
            if str(threads[i]) in [str(n) for n in date]:
                threads.pop(i)
        except IndexError:
            pass
    #for n in threads:
    #    print(n, n.i)
    index = [n.i for n in threads]
    #print(index)
    if index == []:
        return
    if l:
        try:
            doc_ret = doc[min(index) : max(index)+1]
        except IndexError:
            doc_ret = doc[min(index) : max(index)]
    else:
        doc_ret = doc[min(index) : max(index)]
    stri = ""
    for n in [i.text for i in doc_ret]:
        stri += n + " "
    return stri

def get_html(url):
    with urllib.request.urlopen(url) as response:
        html = response.read()
    return html

def clean_body(body):
    body = list(str(body))
    c = 0
    while True:
        try:
            if body[c] == "<":
                while not body[c] == ">":
                    body.pop(c)
                body.pop(c)
                if body[c] == ".":
                    if body[c - 3:c] in abbr:
                        body.pop(c)
            elif body[c] == ".":
                if body[c - 3:c] in abbr:
                    body.pop(c)
                else:
                    c += 1
            elif body[c] == ":" and not body[c - 1] in colon_chars:
                body.insert(c, " ")
            #elif body[c] == "\r":
            #    body.pop(c)
            else:
                c += 1
        except IndexError:
            break
    stri = ""
    for i in body:
        stri += i
    return stri

def load_items(canvas_lms, canvas, classes):
    courses = []
    for i in classes:
        #print(i)
        courses.append(canvas.get_course(i))
    class ItemThreader(object):
        def __init__(self, courses):
            self.courses = courses
            self.items = []
            self.assignments = []
            self.pages = []
            self.announcements = []
            self.modules = []
            threads = [Thread(target=self.get_assignments, daemon=True), Thread(target=self.get_pages, daemon=True), Thread(target=self.get_announcements, daemon=True), Thread(target=self.get_modules, daemon=True)]
            for i in threads:
                i.start()
            for i in threads:
                i.join()
        
        def merge(self):
            self.items += self.assignments
            self.items += self.pages
            self.items += self.announcements
            self.items += self.modules
            return self.items
        
        def get_assignments(self):
            for i in self.courses:
                try:
                    for n in i.get_assignments():
                        try:
                            try:
                                self.assignments.append(AssignmentItem(n.name, clean_body(n.description), n.due_at_date, url=n.html_url))
                            except AttributeError:
                                self.assignments.append(AssignmentItem(n.name, clean_body(n.description), n.due_at_date))
                            #print("got assignment: ", items[0])
                        except Exception as err:
                            print(err)
                except Exception as err:
                    print(err)
        
        def get_pages(self):
            for i in self.courses:
                try:
                    for n in i.get_pages():
                        try:
                            try:
                                self.pages.append(DatedItem(n.title, clean_body(get_html(n.html_url)), n.created_at, url=n.html_url))
                            except AttributeError:
                                self.pages.append(DatedItem(n.title, clean_body(get_html(n.html_url)), n.created_at))
                            #print("got page: ", items[0])
                        except Exception as err:
                            print(err)
                except Exception as err:
                    print(err)
        
        def get_announcements(self):
            for i in self.courses:
                try:
                    for n in canvas.get_announcements(context_codes=['course_{}'.format(i.id)]):
                        #print(n, n.message, clean_body(n.message))
                        try:
                            try:
                                self.announcements.append(DatedItem(n.title, clean_body(n.message), n.posted_at_date, url=n.html_url))
                                #items[-1].give_choices()
                            except AttributeError:
                                #print("ANNOUNCEMENT ERROR")
                                self.announcements.append(DatedItem(n.title, clean_body(n.message), n.posted_at_date))
                            #print("got announcement: ", items[0])
                        except Exception as err:
                            print(err)
                except Exception as err:
                    print(err)
        
        def get_modules(self):
            for i in self.courses:
                try:
                    for n in i.get_modules():
                        try:
                            for g in n.get_module_items():
                                #print(i.get_page(g.page_url))
                                try:
                                    p = i.get_page(g.page_url)
                                    try:
                                        self.modules.append(DatedItem(p.title, clean_body(p.body), p.created_at, url=p.html_url))
                                    except AttributeError:
                                        self.modules.append(DatedItem(p.title, clean_body(p.body), p.created_at))
                                except Exception as err:
                                    print(err)
                        except Exception as err:
                            print(err)
                except Exception as err:
                    print(err)
    
    items = ItemThreader(courses)
    items = items.merge()
    set_dates = {}
    for i in items:
        if type(i) == AssignmentItem:
            if i.date in list(set_dates.keys()):
                set_dates[i.date] += [i]
            else:
                set_dates[i.date] = [i]
    return items, set_dates

def determine_date_eligibility(date_str, date):
    date_str = str(date_str)
    doc = nlp(date_str)
    if date == None:
        return False
    if datetime.datetime.now().year + 1 < date.year or datetime.datetime.now().year - 1 > date.year:
        return False
    if datetime.datetime.now().year - 1 == date.year and ((datetime.datetime.now().month + 12) - date.month) > 1:
        return False
    if datetime.datetime.now().year == date.year and (datetime.datetime.now().month - date.month) > 1:
        return False
    if len(date_str) <= 2:
        return False
    if "second" in date_str or "minute" in date_str:
        return False
    if len(doc) <= 1 and not date_str.lower() == "tomorrow" and not date_str.lower() in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
        return False
    if date_str.lower() == "now":
        return False
    return True

def find_dates(canvas_lms, canvas, items, due_dates, date_finder):
    date_finder.thread.join()
    return date_finder.dates

class DateFinder(object):
    def __init__(self, canvas_lms, canvas, items, due_dates):
        self.dates = None
        self.thread = Thread(target=self.find_dates, args=(canvas_lms, canvas, items, due_dates))
        self.thread.start()

    def find_dates(self, canvas_lms, canvas, items, due_dates):
        #get explicit dates
        self.dates = due_dates
        #dates = {}
        ###FOR SOME REASON THIS APPENDS THE NAME AND NOT THE BODY OF A DATED ITEM 
        bodies = [i.name + ". " + i.body for i in items]
        #print("BODIES", bodies)
        for i in bodies:
            #print(i)
            i_copy = nlp(i)
            sentences = [str(q) for q in i_copy.sents]
            for n in range(len(sentences)):
                try:
                    if sentences[n][-1] == "-":
                        sentences[n] = sentences[n] + " " + sentences[n + 1]
                        sentences.pop(n + 1)
                except IndexError:
                    pass
            for n in range(len(sentences)):
                try:
                    if sentences[n] == "":
                        sentences.pop(n)
                except IndexError:
                    pass
            _sentences = sentences
            sentences = []
            for n in _sentences:
                for g in n.split("\n"):
                    sentences.append(g)
                            
            #print("sentences", sentences)
            RELATIVE_BASE = False
            config = dateparser.conf.Settings()
            if type(items[bodies.index(i)]) == DatedItem or type(items[bodies.index(i)]) == AssignmentItem:
                #print("item date", items[bodies.index(i)].date, items[bodies.index(i)])
                if type(items[bodies.index(i)].date) == type(""):
                    e = items[bodies.index(i)].date
                    #print(items[bodies.index(i)].observe())
                    #print(items[bodies.index(i)].date)
                    #print(dateparser.search.search_dates(items[bodies.index(i)].date))
                    #print(dateparser.search.search_dates(items[bodies.index(i)].date)[0])
                    #print(dateparser.search.search_dates(items[bodies.index(i)].date)[0][1])
                    #config.RELATIVE_BASE = dateparser.search.search_dates(items[bodies.index(i)].date)[0][1]
                    day = datetime.datetime(year=int(e[0:4]), month=int(e[5:7]), day=int(e[8:10]), hour=int(e[11:13]), minute=int(e[14:16]), second=int(e[17:19]), tzinfo=timezone("Zulu"))
                    RELATIVE_BASE = day.astimezone(tzlocal())
                    config.RELATIVE_BASE = RELATIVE_BASE
                else:
                    try:
                        RELATIVE_BASE = items[bodies.index(i)].date
                        config.RELATIVE_BASE = RELATIVE_BASE
                    except AttributeError:
                        raise TypeError("type {} is invalid for RELATIVE_BASE".format(type(items[bodies.index(i)].date)))
            else:
                RELATIVE_BASE = datetime.datetime.now()
            #print(items[bodies.index(i)].date, config.RELATIVE_BASE)
            z = dateparser.search.search_dates(i, settings=config, languages=["en"])
            #print(i)
            #print(z)
            #print(l)
            r = 0
            for n in z if not z == None else []:
                #print("n", n)
                #print("*n", *n)
                frozen_date = None
                try:
                    with freeze_time(RELATIVE_BASE):
                        frozen_date = duparse(n[0])
                    is_dateparser = False
                    if type(frozen_date) == datetime.timedelta:
                        frozen_date = n[1]
                except Exception as err:
                    #print(err)
                    if n[0].lower() == "today":
                        frozen_date = RELATIVE_BASE
                    elif n[0].lower() == "tomorrow":
                        frozen_date = RELATIVE_BASE + datetime.timedelta(days=1)
                    else:
                        frozen_date = n[1]
                        is_dateparser = True
                #print(n, frozen_date)
                if determine_date_eligibility(n[0], frozen_date):
                    #process body to get sentence then pass sentence to context
                    date_tokens = nlp(n[0])
                    #print("date_tokens", date_tokens)
                    while True:
                        #experimental
                        try:
                            nlp_sent = nlp(sentences[0])
                            #print("nlp_sent", nlp_sent)
                        except:
                            break
                        #experimental
                        containing_sent = ""
                        for g in range(len(nlp_sent)):
                            #print("g", g)
                            try:
                                #print([nlp_sent[r + g] for r in range(len(date_tokens))], [e for e in date_tokens])
                                #print([nlp_sent[r + g] for r in range(len(date_tokens))] == [e for e in date_tokens])
                                if [q.text for q in [nlp_sent[r + g] for r in range(len(date_tokens))]] == [e.text for e in date_tokens]:
                                    containing_sent = nlp_sent
                                    break
                            except IndexError:
                                pass
                        r += 1
                        if containing_sent != "":
                            break
                        sentences.pop(0)
                    l = False
                    try:
                        if containing_sent[-1].text == ":":
                            #print("has colon")
                            ###NEEDS AN IF IS ROOT AS WELL
                            if before_root(containing_sent, date_tokens, is_root=True):
                                #print("before root")
                                if containing_sent[-2].text == date_tokens[-1].text:
                                    l = str(sentences[1])
                                    #print("-1==-2", l)
                                    #print(sentences)
                        elif [g.text for g in containing_sent] == [w.text for w in date_tokens]:
                            l = _sentences[r - 1]
                        else:
                            l = get_context(containing_sent, n[0])
                    except IndexError:
                        pass
                    #print(l)
                    if l:
                        strii = ""
                        for v in l:
                            if not v == "\r":
                                strii += v
                        l = strii
                    #print(frozen_date)
                    #try:
                        #print(l, frozen_date, n[0], containing_sent, sentences[0])
                    #except IndexError:
                        #print(l, frozen_date, n[0], containing_sent)
                    if l:
                        try:
                             self.dates[frozen_date] += [ImpliedItem(l, frozen_date, items[bodies.index(i)], date_str=n[0])]
                        except KeyError:
                            try:
                                self.dates[frozen_date] = [ImpliedItem(l, frozen_date, items[bodies.index(i)], date_str=n[0])]
                            except IndexError:
                                pass
        #get implied dates
        #return
        for i in list(self.dates.keys()):
            for n in self.dates[i]:
                if not n.name:
                    self.dates[i].pop(self.dates[i].index(n))
        for i in list(self.dates.keys()):
            if self.dates[i] == []:
                del self.dates[i]

def add_to_calendar(events):
    for i in events:
        #template = open("AppleCalendar/add_to_calendar.txt", "r")
        #script = open("AppleCalendar/CalendarScripts/new_event.scpt", "w+")
        delta = i.schedule_end - i.schedule_start
        start_sched = datetime.datetime(year=i.schedule_start.year, month=i.schedule_start.month, day=i.schedule_start.day, hour=i.schedule_start.hour, minute=i.schedule_start.minute, second=i.schedule_start.second)
        fills = [str((start_sched - datetime.datetime.now()).days), str(i.schedule_start.hour), str(i.schedule_start.minute), str(i.schedule_start.second), str(int((delta.seconds/60)/60)), str(int((delta.seconds%60)/60)), str((delta.seconds%60)%60), i.url, i.name]
        #for n in template.readlines():
        #    sel_fills = []
        #    for g in range(n.count("{}")):
        #        sel_fills.append(fills[0])
        #        fills.pop(0)
        #    script.write(n.format(*sel_fills))
        #script.close()
        #os.system("osascript AppleCalendar/CalendarScripts/new_event.scpt")
        #os.system("rm AppleCalendar/CalendarScripts/new_event.scpt")
        os.system(add_event_osa.format(*fills))

def schedule_items(items, days, meetings=None, pref_dates=None):
    events = []
    for i in items:
        if i in list(pref_dates.keys()):
            events.append(schedule_objects.ProvisionalEvent(i, pref_start=pref_dates[i]))
    for i in items:
        if not i in list(pref_dates.keys()):
            events.append(schedule_objets.ProvisionalEvent(i))
    schedule = schedule_objects.Schedule(days)
    if meetings:
        for i in meetings:
            schedule.add_event(i)
    schedule.schedule_events(events)
    return schedule

def make_secure_module(insecure_path, secure_path, salt_path):
    #print("opening insecure")
    with open(insecure_path, "r") as insecure_doc:
        insecure_text = insecure_doc.read()
    #print("done with insecure")
    kdf = nacl.pwhash.argon2i.kdf
    salt_size = nacl.pwhash.argon2i.SALTBYTES
    salt = nacl.utils.random(salt_size)
    #print("got salt")
    with open(salt_path, "wb") as salt_doc:
        salt_doc.write(salt)
    #print("saved salt")
    password = yield "enter password\n"
    password = str(password).encode("utf-8")
    key = kdf(nacl.secret.SecretBox.KEY_SIZE, password, salt, opslimit=3)
    insecure_text = insecure_text.encode("utf-8")
    box = nacl.secret.SecretBox(key)
    encrypted = box.encrypt(insecure_text)
    with open(secure_path, 'wb') as secure_doc:
        secure_doc.write(encrypted)
    os.system("rm {}".format(insecure_path))

def get_from_secure_module(secure_path, insecure_path, salt_path):
    password = yield "enter password\n"
    password = str(password).encode("utf-8")
    with open(salt_path, "rb") as salt_doc:
        salt = salt_doc.read()
    with open(secure_path, "rb") as secure_doc:
        secure_text = secure_doc.read()
    kdf = nacl.pwhash.argon2i.kdf
    key = kdf(nacl.secret.SecretBox.KEY_SIZE, password, salt, opslimit=3)
    box = nacl.secret.SecretBox(key)
    insecure_text = box.decrypt(secure_text)
    with open(insecure_path, "wb") as insecure_doc:
        insecure_doc.write(insecure_text)
    module = importlib.import_module(insecure_path[0 : -3])
    os.system("rm {}".format(insecure_path))
    yield module

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
        ###CREATE MEETINGS FROM SCHEDULE OBJECTS AND ADD TO LOGIN###
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
                #print("breaking")
                break
        #print("closing")
        l.close()
        #print("making mks")
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


###NEED TO SOLVE INPUT PROBLEMS IN OUTSIDE FUNCTIONS
class PythonRunSource(object):
    def __init__(self, run=True):
        pass
    
    def run(self):
        gen = self.start_up()
        _output = next(gen)
        while True:
            try:
                next(gen)
                _input = yield _output
                _output = gen.send(_input)
            except StopIteration:
                break
        gen = self.main_loop()
        _output = next(gen)
        while True:
            try:
                next(gen)
                _input = yield _output
                _output = gen.send(_input)
            except StopIteration:
                break
            
    
    def start_up(self):
        if not os.path.isfile("secure_login.bin"):
            #print("WELCOME")
            yield "Do you give permission for the program to use your Canvas account via your Canvas Access Token?\n1. Yes\n2. No\n"
            good = yield
            if good == 1:
                #print("Thanks!")
                pass
            else:
                #print("The program won't work without the token.")
                exit()
            yield "Enter your Canvas Access Token. To find it, go to Canvas in your browser, login, navigate to your settings page, find the button that says generate token, click it, and give me the token it gives you.\n"
            self.token = yield
            #print("This token will be stored in this folder, so don't share it.")
            yield "Are you in the Blue Valley School District?\n1. Yes\n2. No\n"
            self.bv = yield
            if self.bv == 1:
                self.site = "https://bvusd.instructure.com"
            else:
                yield "What is your Canvas url?\n"
                self.site = yield
            #print("LOGGING IN")
            self.canvas_lms = canvas_lms_api.Canvas(base=self.site, token=self.token)
            self.canvas = canvasapi.Canvas(self.site, self.token)
            #print("It worked. The token is going to be stored here, so don't share this folder or anything in it. Somebody could use it to access your Canvas account.")
            self.l = open("login.py", "w+")
            self.l.write("import schedule_objects\nimport datetime\n")
            self.l.write("token = '{}'\nsite = '{}'\n".format(self.token, self.site))
            self.courses = self.canvas_lms.GetCourses()
            #print("SET UP")
            while True:
                self.course_bindings = {}
                for i in self.courses:
                    self.course_bindings[i["name"]] = i["id"]
                self.course_string = ""
                for i in range(len(list(self.course_bindings.keys()))):
                    self.course_string = self.course_string + str(i) + ". " + [n for n in self.course_bindings.keys()][i] + "\n"
                yield "Enter the numbers of each course you want follow:\n" + self.course_string
                self.followed_course_numbers = yield
                self.followed_course_numbers = self.followed_course_numbers.replace(" ", "")
                self.followed_course_numbers = self.followed_course_numbers.split(",")
                self.followed_course_numbers = [int(i) for i in self.followed_course_numbers]
                self.followed_courses = []
                for i in self.followed_course_numbers:
                    self.followed_courses.append([n for n in self.course_bindings.keys()][i])
                for i in self.followed_courses:
                    #print(i)
                    pass
                yield "Are these the courses you want to follow?\n1. Yes\n2. No\n"
                right = yield
                if right == 1:
                    break
            self.my_courses = []
            for i in self.followed_courses:
                self.my_courses.append(self.course_bindings[i])
            self.l.write("followed_courses = {}\n".format(self.my_courses))
            ###CREATE MEETINGS FROM SCHEDULE OBJECTS AND ADD TO LOGIN###
            while True:
                yield "Would you like to save class times to help with scheduling?\n1. Yes\n2. No\n"
                choice = yield
                choice = int(choice)
                if choice == 1:
                    yield "What is the name of the class?\n"
                    name = yield
                    yield "When is the next time you will have this class? (include date and time with AM or PM)\n"
                    _ = yield
                    next = dateparser.search.search_dates(_)[0][1]
                    yield "What time does the class end? (include AM or PM)\n"
                    _ = yield
                    length = dateparser.search.search_dates(_)[0][1]
                    yield" Does this class occur on weekends?\n1. Yes\n2. No\n"
                    weekends = yield
                    if weekends == 1:
                        weekends = True
                    else:
                        weekends = False
                    patterns = ["Day of the Week", "Every Day", "Every Other Day", "Every Third Day", "Every Fourth Day", "Every Fifth Day", "Every Sixth Day", "Every Other Week", "Once A Month"]
                    stri = "Which meeting pattern does this class follow?\n"
                    for i in range(len(patterns)):
                        stri += "{}. {}\n".format(str(i), patterns[i])
                    yield stri
                    _ = yield
                    pattern = patterns[_]
                    self.l.write("MeetingEvent({}, datetime.datetime(year={}, month={}, day={}, hour={}, minute={}), datetime.datetime(year={}, month={}, day={}, hour={}, minute={}), {}, weekends=)".format(str(name), str(next.year), str(next.month), str(next.day), str(next.hour), str(next.minute), str(next.year), str(next.month), str(next.day), str(length.hour), str(length.minute), str(pattern), str(weekends)))
                else:
                    break
            self.l.close()
            mks = make_secure_module("login.py", "secure_login.bin", "login_salt.bin")
            try:
                yield "enter password\n"
                inp = yield
                mks.__next__()
                mks = mks.send(str(inp))
            except StopIteration:
                pass
            print("LOGGED IN")
            login = get_from_secure_module("secure_login.bin", "login.py", "login_salt.bin")
            try:
                yield "enter password\n"
                inp = yield
                login.__next__()
                login = login.send(str(inp))
            except StopIteration:
                pass
            #print("LOGGED IN")
            try:
                self.meetings = login.meetings
            except AttributeError:
                self.meetings = False
            self.l = os.system("rm old_login.py")
            self.followed_courses = self.my_courses
            #print("In order to use the Apple Calendar Integration, you'll have to create a new calendar.")
            yield "In order to use the Apple Calendar Integration, you'll have to create a new calendar. Would you like to do this?\n1. Yes\n2. No\n"
            choice = yield
            if choice == 1:
                os.system("osascript create_calendar.scpt")
            else:
                print("Okay. If you want to do this later, you can from the menu.")
        else:
            #print("Welcome back!")
            yield "Has any configuration information changed since you were here last?\n1. Yes\n2. No\n"
            good = yield
            if good == 1:
                #print("Restart the program to set up.")
                #print("Here is your current data:")
                #print("token: ", login.token, "\nfollowed courses: ", login.followed_courses, "\nsite: ", login.site)
                os.system("mv login.py old_login.py")
                os.system("rm login_salt.bin")
                os.system("rm secure_login.bin")
                exit()
            login = get_from_secure_module("secure_login.bin", "login.py", "login_salt.bin")
            try:
                yield "enter password\n"
                inp = yield
                login.__next__()
                login = login.send(str(inp))
            except StopIteration:
                pass
            self.canvas_lms = canvas_lms_api.Canvas(base=login.site, token=login.token)
            self.canvas = canvasapi.Canvas(login.site, login.token)
            self.followed_courses = login.followed_courses
            try:
                self.meetings = login.meetings
            except AttributeError:
                self.meetings = False
            #print("LOGGED IN")
    
    def main_loop(self):
        self.items, self.due_dates = load_items(self.canvas_lms, self.canvas, self.followed_courses)
        self.date_finder = DateFinder(self.canvas_lms, self.canvas, self.items, self.due_dates)
        self.dates = False
        self.today = False
        self.week = False
        while True:
            yield "Select an action:\n0. Find Dates\n1. Today View\n2. Week View\n3. Custom View\n4. Create Calendar\n5. Exit\n"
            action = yield
            action = int(action)
            if action == 0:
                if not self.dates:
                    self.dates = find_dates(self.canvas_lms, self.canvas, self.items, self.due_dates, self.date_finder)
                #print(self.dates)
            elif action == 1:
                if not self.dates:
                    self.dates = find_dates(self.canvas_lms, self.canvas, self.items, self.due_dates, self.date_finder)
                if not self.today:
                    self.today = TodayView(self.canvas_lms, self.canvas, self.dates)
                self.today_events = self.today.ret_today_events()
                stri = "0. Exit\n1. Create Schedule\n"
                for i in range(len(self.today_events)):
                    stri += str(i + 2) + ". " + self.today_events[i].__str__() + "\n"
                while True:
                    yield stri
                    choice = yield
                    coice = int(choice)
                    if choice == 0:
                        break
                    elif choice == 1:
                        self.schedule = schedule_objects.Schedule(datetime.datetime.now(), meetings=(self.meetings if self.meetings else []))
                        self.schedule.schedule_events(self.events)
                        gen = self.schedule.give__choices()
                        g = next(gen)
                        while True:
                            try:
                                yield g
                                newg = yield
                                g = gen.send(newg)
                            except StopIteration:
                                break
                    elif choice in range(len(self.today_events) + 2):
                        gen = self.today_events[choice - 2].give__choices()
                        g = next(gen)
                        while True:
                            try:
                                yield g
                                newg = yield
                                g = gen.send(newg)
                            except StopIteration:
                                break
            elif action == 2:
                if not self.dates:
                    self.dates = find_dates(self.canvas_lms, self.canvas, self.items, self.due_dates, self.date_finder)
                if not self.week:
                    self.week = WeekView(self.canvas_lms, self.canvas, self.dates)
                self.events = []
                stri = "0. Exit\n1. Create Schedule\n2. Add Due Dates\n"
                count = 3
                for i in self.week.ret_days():
                    stri += i.get_week_day()
                    for n in i.ret_events():
                        self.events.append(n)
                        stri += str(count) + ". " + n.__str__() + "\n"
                        count += 1
                while True:
                    yield stri
                    choice = yield
                    choice = int(choice)
                    if choice == 0:
                        break
                    elif choice == 1:
                        self.schedule = schedule_objects.Schedule(self.week.week, meetings=(self.meetings if self.meetings else []))
                        self.schedule.schedule_events(self.events)
                        gen = self.schedule.give__choices()
                        g = next(gen)
                        while True:
                            try:
                                yield g
                                newg = yield
                                g = gen.send(newg)
                            except StopIteration:
                                break
                    elif choice == 2:
                        self.week.put_due_dates()
                    elif choice in range(len(self.events) + 2):
                        gen = self.events[choice - 2].give__choices()
                        g = next(gen)
                        while True:
                            try:
                                yield g
                                newg = yield
                                g = gen.send(newg)
                            except StopIteration:
                                break
            elif action == 3:
                if not self.dates:
                    self.dates = find_dates(self.canvas_lms, self.canvas, self.items, self.due_dates, self.date_finder)
                while True:
                    try:
                        yield "input start\n"
                        r = yield
                        yield "input end\n"
                        g = yield
                        self.custom = CustomView(self.canvas_lms, self.canvas, self.dates, dateparser.search.search_dates(str(input(r)))[0][1], dateparser.search.search_dates(str(input(g)))[0][1])
                        break
                    except TypeError:
                        print("Date Was Not Recognized")
                        pass
                self.events = []
                stri = "0. Exit\n1. Create Schedule\n2. Add Due Dates\n"
                count = 3
                for i in self.custom.ret_days():
                    stri += i.get_week_day()
                    for n in i.ret_events():
                        self.events.append(n)
                        stri += str(count) + ". " + n.__str__() + "\n"
                        count += 1
                while True:
                    yield stri
                    choice = yield
                    choice = int(choice)
                    if choice == 0:
                        break
                    elif choice == 1:
                        self.schedule = schedule_objects.Schedule(self.custom.week, meetings=(self.meetings if self.meetings else []))
                        self.schedule.schedule_events(self.events)
                        gen = self.schedule.give__choices()
                        g = next(gen)
                        while True:
                            try:
                                yield g
                                newg = yield
                                g = gen.send(newg)
                            except StopIteration:
                                break
                    elif choice == 2:
                        self.custom.put_due_dates()
                    elif choice in range(len(self.events) + 2):
                        gen = self.events[choice - 2].give__choices()
                        g = next(gen)
                        while True:
                            try:
                                yield g
                                newg = yield
                                g = gen.send(newg)
                            except StopIteration:
                                break
            elif action == 4:
                os.system("osascript create_calendar.scpt")
            elif action == 5:
                break
