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
            if (i.year, i.month, i.day) == (now.year, now.month, now.day):
                today_keys.append(i)
        today_items = []
        for i in today_keys:
            for n in self.dates[i]:
                today_items.append(n)
        return today_items
    
    def ret_today_events(self):
        return self.today_events