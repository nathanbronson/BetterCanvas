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