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
