import os
import datetime
import dateparser.search
from dateutil.parser import parse
import freezegun

dateparser.search.search_dates("monday")

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
            make new event with properties {{description:\"{}\", summary:\"{}\", start date:theStartDate, end date:theEndDate}}
        end tell
    end tell'""")

get_calendar_osa = ("""osascript -e '
    set now to current date
    set dia to (now) - (time of now)
    set dia to dia + ({} * 24 * 60 * 60)
    set next_day to dia + (24 * 60 * 60)
    set thePath to \"{}\"
    tell application \"Terminal\"
        set l to do script \"echo -n -e \\"\\\\033]0;get_event_comp_proc_window\\\\007\\"; python3 \" & thePath & \"/add_calendar_event.py \\"__none__\\" \\"__none__\\" \\"__none__\\" \\"\" & thePath & \"\\"\"
        repeat until number of (windows whose name contains \"get_event_comp_proc_window\") is greater than 0
            delay 0.01
        end repeat
        tell application \"System Events\"
            try
                set visible of first item of (every window whose name contains \"get_event_comp_proc_window\") to false
            end try
        end tell
        repeat until busy of first item of (every window whose name contains \"get_event_comp_proc_window\") is false
            delay 0.01
        end repeat
        close (every window whose name contains \"get_event_comp_proc_window\")
    end tell
    tell application \"Calendar\"
        repeat with i in (every calendar)
            repeat with n in ((every event in i) whose (start date) is greater than or equal to dia and (start date) is less than next_day)
                set theStart to start date of n
                set theEnd to end date of n
                set theSummary to summary of n
                tell application \"Terminal\"
                    set l to do script \"echo -n -e \\"\\\\033]0;get_event_comp_proc_window\\\\007\\"; python3 \" & thePath & \"/add_calendar_event.py \\"\" & (theSummary) & \"\\" \\"\" & (theStart) & \"\\" \\"\" & (theEnd) & \"\\" \\"\" & thePath & \"\\"\"
                    repeat until number of (windows whose name contains \"get_event_comp_proc_window\") is greater than 0
                        delay 0.01
                    end repeat
                    tell application \"System Events\"
                        try
                            set visible of first item of (every window whose name contains \"get_event_comp_proc_window\") to false
                        end try
                    end tell
                    repeat until busy of first item of (every window whose name contains \"get_event_comp_proc_window\") is false
                        delay 0.01
                    end repeat
                    close (every window whose name contains \"get_event_comp_proc_window\")
                end tell
            end repeat
        end repeat
    end tell'""")

class ScopeError(Exception):
    def __init__(self, message=False):
        if not message:
            super().__init__("Event is not in schedule scope")
        else:
            super().__init__(message)

class SchedulingError(Exception):
    def __init__(self, offender, start, end):
        self.offender = offender
        self.start = start
        self.end = end
        self.message = "Event {} was attempting to overlap with another event at times {} : {}".format(self.offender, self.start, self.end)
        super().__init__(self.message)

class Schedule(object):
    def __init__(self, days, around_preexisting=False, meetings=[]):
        self.days = days
        for i in self.days:
            i = datetime.datetime(year=i.year, month=i.month, day=i.day)
        self.around_preexisting = around_preexisting
        self._schedule = {}
        self._schedule_times = {}
        for i in days:
            self._schedule[datetime.datetime(year=i.year, month=i.month, day=i.day)] = []
            self._schedule_times[datetime.datetime(year=i.year, month=i.month, day=i.day)] = []
            for n in meetings:
                ###ADD MEETIGNS###
                try:
                    self.add_event(n)
                except ScopeError:
                    pass
                for g in n.occurrences:
                    try:
                        try:
                            self.add_event(g)
                        except SchedulingError:
                            pass
                    except ScopeError:
                        pass
            if self.around_preexisting:
                for n in get_calendar_events((i - datetime.datetime.now()).days + 1):
                    new_n = n
                    new_n.set_env(self)
                    self._schedule[datetime.datetime(year=i.year, month=i.month, day=i.day)].append(new_n)
                    self._schedule_times[datetime.datetime(year=i.year, month=i.month, day=i.day)].append((n.start_time, n.end_time, True))

    def add_event(self, event):
        lookup_time = datetime.datetime(year=event.start_time.year, month=event.start_time.month, day=event.start_time.day)
        if lookup_time in list(self._schedule.keys()):
            day = self._schedule_times[lookup_time]
            for i in day:
                if event.start_time >= i[0] and event.start_time <= i[1]:
                    if i[2] and self.around_preexisting:
                        raise SchedulingError(event, i[0], i[1])
                    elif not i[2]:
                        raise SchedulingError(event, i[0], i[1])
                elif event.end_time >= i[0] and event.end_time <= i[1]:
                    if i[2] and self.around_preexisting:
                        raise SchedulingError(event, i[0], i[1])
                    elif not i[2]:
                        raise SchedulingError(event, i[0], i[1])
            self._schedule_times[lookup_time].append((event.start_time, event.end_time, False))
            #print("after1", self._schedule_times[lookup_time])
            if not type(event) == MeetingEvent:
                new_event = event
                new_event.set_env(self)
            else:
                new_event = event
            self._schedule[lookup_time].append(new_event)
            #print("after2", self._schedule_times[lookup_time])
        else:
            raise ScopeError()
    
    def time_is_in(self, time, period):
        if time >= period[0] and time <= period[1]:
            return True
        return False
    
    def schedule_event(self, event):
        """
        event is Provisional Event
        """
        earl = []
        if datetime.datetime(year=event.hard_stop.year, month=event.hard_stop.month, day=event.hard_stop.day) in list(self._schedule.keys()):
            for i in self._schedule_times[datetime.datetime(year=event.hard_stop.year, month=event.hard_stop.month, day=event.hard_stop.day)]:
                earl.append(i[1])
            if len(earl) > 0:
                earliest = min(earl)
            else:
                earliest = datetime.datetime(year=event.hard_stop.year, month=event.hard_stop.month, day=event.hard_stop.day, hour=7, minute=30)
            if type(earliest) == freezegun.api.FakeDatetime:
                earliest = datetime.datetime(year=earliest.year, month=earliest.month, day=earliest.day, hour=earliest.hour, minute=earliest.minute)
            possible = []
            for i in list(self._schedule.keys()):
                possible += [i + datetime.timedelta(seconds=(n * 60)) for n in range(24 * 60)]
            pops = []
            for i in range(len(possible)):
                try:
                    for g in list(self._schedule.keys()):
                        for n in self._schedule_times[g]:
                            if self.time_is_in(possible[i], n):
                                pops.append(possible[i])
                except IndexError:
                    pass
            for i in pops:
                possible.pop(possible.index(i))
            worked = 1
            ##print(possible)
            earliest = datetime.datetime(year=earliest.year, month=earliest.month, day=earliest.day, hour=earliest.hour, minute=earliest.minute)
            if event.pref_start:
                if event.pref_start in possible:
                    if all([event.pref_start + datetime.timedelta(seconds=(i * 60)) in possible for i in range(int(event.length.seconds/60) + 1)]):
                        start = event.pref_start
                        try:
                            length = event.length
                            start_delt = datetime.timedelta(0)
                        except:
                            length = event.end_time - event.start_time
                            start_delt = datetime.timedelta(0)
                    else:
                        start = event.pref_start
                        ###REPLACE WITH STARTDELTS###
                        start_delt = datetime.timedelta(0)
                        #while not start + event.length in possible or not start in possible and all(datetime(year=start.year, month=start.month, day=start.day, hour=int(i/60), minute=i%60) in possible for i in range(event.length.seconds/60)):
                        while not all([start + start_delt + datetime.timedelta(seconds=(i * 60)) in possible for i in range(int(event.length.seconds/60) + 1)]):
                            #print("loop1", [start + start_delt + datetime.timedelta(seconds=(i * 60)) in possible for i in range(int(event.length.seconds/60) + 1)])
                            #print("loop1_", start)
                            #print(181)
                            if start + start_delt - datetime.timedelta(seconds=(5 * 60)) >= earliest:
                                start_delt -= datetime.timedelta(seconds=(5 * 60))
                            else:
                                worked = 0
                                break
                            #print("loop1", [start + start_delt + datetime.timedelta(seconds=(i * 60)) in possible for i in range(int(event.length.seconds/60) + 1)])
                            #print("loop1_", start)
                        if worked == 0:
                            worked = 1
                            while not all([start + start_delt + datetime.timedelta(seconds=(i * 60)) in possible for i in range(int(event.length.seconds/60) + 1)]):
                                #print("loop2", [start + datetime.timedelta(seconds=(i * 60)) in possible for i in range(int(event.length.seconds/60) + 1)])
                                #print("loop2_", start)
                                if start + start_delt + event.length + datetime.timedelta(seconds=(5 * 60)) <= event.hard_stop:
                                    start_delt += datetime.timedelta(seconds=(5 * 60))
                                else:
                                    worked = 0
                                    break
                            if worked == 0:
                                worked = 1
                                while not all([start + start_delt + datetime.timedelta(seconds=(i * 60)) in possible for i in range(int(event.length.seconds/60) + 1)]):
                                    #print("loop3", [start + datetime.timedelta(seconds=(i * 60)) in possible for i in range(int(event.length.seconds/60) + 1)])
                                    #print("loop3_", start)
                                    start_delt -= datetime.timedelta(seconds=(5 * 60))
                                    if start + start_delt < min(list(self._schedule.keys())):
                                        worked = 0
                                        break
                                    #####PICKUPHERE#####
                else:
                    start = event.pref_start
                    start_delt = datetime.timedelta(0)
                    #while not start + event.length in possible or not start in possible and all(datetime(year=start.year, month=start.month, day=start.day, hour=int(i/60), minute=i%60) in possible for i in range(event.length.seconds/60)):
                    while not all([start + start_delt + datetime.timedelta(seconds=(i * 60)) in possible for i in range(int(event.length.seconds/60) + 1)]):
                        #print("loop1", [start + start_delt + datetime.timedelta(seconds=(i * 60)) in possible for i in range(int(event.length.seconds/60) + 1)])
                        #print("loop1_", start)
                        #print(206)
                        if start + start_delt - datetime.timedelta(seconds=(5 * 60)) >= earliest:
                            start_delt -= datetime.timedelta(seconds=(5 * 60))
                        else:
                            worked = 0
                            break
                        #print("loop1", [start + start_delt + datetime.timedelta(seconds=(i * 60)) in possible for i in range(int(event.length.seconds/60) + 1)])
                        #print("loop1_", start)
                    if worked == 0:
                        worked = 1
                        while not all([start + start_delt + datetime.timedelta(seconds=(i * 60)) in possible for i in range(int(event.length.seconds/60) + 1)]):
                            #print("loop2", [start + datetime.timedelta(seconds=(i * 60)) in possible for i in range(int(event.length.seconds/60) + 1)])
                            #print("loop2_", start)
                            if start + start_delt + event.length + datetime.timedelta(seconds=(5 * 60)) <= event.hard_stop:
                                start_delt += datetime.timedelta(seconds=(5 * 60))
                            else:
                                worked = 0
                                break
                        if worked == 0:
                            worked = 1
                            while not all([start + start_delt + datetime.timedelta(seconds=(i * 60)) in possible for i in range(int(event.length.seconds/60) + 1)]):
                                #print("loop3", [start + datetime.timedelta(seconds=(i * 60)) in possible for i in range(int(event.length.seconds/60) + 1)])
                                #print("loop3_", start)
                                start_delt -= datetime.timedelta(seconds=(5 * 60))
                                if start + start_delt < min(list(self._schedule.keys())):
                                    worked = 0
                                    break
            else:
                start = earliest + datetime.timedelta(seconds=(60 ** 2))
                start_delt = datetime.timedelta(0)
                #print([datetime.datetime(year=start.year, month=start.month, day=start.day, hour=int(i/60), minute=i%60) for i in range(int(event.length.seconds/60) + 1)])
                #print([start + start_delt + datetime.timedelta(seconds=(i * 60)) in possible for i in range(int(event.length.seconds/60) + 1)])
                while not all([start + start_delt + datetime.timedelta(seconds=(i * 60)) in possible for i in range(int(event.length.seconds/60) + 1)]):
                    #print("loop1", [start + start_delt + datetime.timedelta(seconds=(i * 60)) in possible for i in range(int(event.length.seconds/60) + 1)])
                    #print("loop1_", start)
                    #print(231)
                    if start + start_delt - datetime.timedelta(seconds=(5 * 60)) >= earliest:
                        start_delt -= datetime.timedelta(seconds=(5 * 60))
                    else:
                        worked = 0
                        break
                    #print("loop1", [start + start_delt + datetime.timedelta(seconds=(i * 60)) in possible for i in range(int(event.length.seconds/60) + 1)])
                    #print("loop1_", start)
                if worked == 0:
                    worked = 1
                    while not all([start + start_delt + datetime.timedelta(seconds=(i * 60)) in possible for i in range(int(event.length.seconds/60) + 1)]):
                        #print("loop2", [start + datetime.timedelta(seconds=(i * 60)) in possible for i in range(int(event.length.seconds/60) + 1)])
                        #print("loop2_", start)
                        if start + start_delt + event.length + datetime.timedelta(seconds=(5 * 60)) <= event.hard_stop:
                            start_delt += datetime.timedelta(seconds=(5 * 60))
                        else:
                            worked = 0
                            break
                    if worked == 0:
                        worked = 1
                        while not all([start + start_delt + datetime.timedelta(seconds=(i * 60)) in possible for i in range(int(event.length.seconds/60) + 1)]):
                            #print("loop3", [start + datetime.timedelta(seconds=(i * 60)) in possible for i in range(int(event.length.seconds/60) + 1)])
                            #print("loop3_", start + start_delt)
                            start_delt -= datetime.timedelta(seconds=(5 * 60))
                            if start + start_delt < min(list(self._schedule.keys())):
                                worked = 0
                                break
            if worked == 0:
                start_delt = datetime.timedelta(0)
                start = event.hard_stop
                while not all([start + start_delt + datetime.timedelta(seconds=(i * 60)) in possible for i in range(int(event.length.seconds/60) + 1)]):
                    start_delt -= datetime.timedelta(seconds=(5 * 60))
                    if start + start_delt < min(list(self._schedule.keys())):
                        raise ScopeError("Suitable time could not be found within scope")
            ##print(event, start, event.length)
            self.add_event(MoveableEvent(event, start + start_delt, start + start_delt + event.length))
        else:
            raise ScopeError()
    
    def schedule_events(self, events, reorder=True):
        _events = events
        events = []
        for i in _events:
            if not type(i) == ProvisionalEvent:
                try:
                    events.append(i.as_type(ProvisionalEvent))
                except AttributeError:
                    raise TypeError("attempting to schedule invalid type {}".format(type(i)))
            else:
                events.append(i)
        _events = {}
        for i in events:
            if not i.hard_stop in list(_events.keys()):
                _events[i.hard_stop] = [i]
            else:
                _events[i.hard_stop].append(i)
        events = []
        for i in range(len(list(_events.keys()))):
            n = min(list(_events.keys()))
            events += _events[n]
            del _events[n]
        for i in events:
            #print(i.bound_object, i.hard_stop)
            pass
        for i in events:
            ##print("i", i)
            self.schedule_event(i)
    
    def ret_events(self):
        events = []
        for i in list(self._schedule.keys()):
            for n in self._schedule[i]:
                events.append(n)
        return events
    
    def give__choices(self):
        while True:
            stri = "0. Exit\n1. Add Schedule to Calendar\n"
            count = 2
            events = self.ret_events()
            for i in events:
                try:
                    stri += "{}. {} at {} until {}\n".format(str(count), str(i.bound_object.name), i.start_time, i.end_time)
                    count += 1
                except AttributeError:
                    stri += str(count) + ". " + str(i.name) + "\n"
                    count += 1
            choice = yield stri
            choice = int(choice)
            if choice == 0:
                break
            elif choice == 1:
                add_to_calendar(events)
            elif choice in list(range(int(len(events)) + 2)):
                gen = events[choice - 2].give__choices()
                g = next(gen)
                while True:
                    try:
                        newg = yield g
                        g = gen.send(newg)
                    except StopIteration:
                        break
    
    def give_choices(self):
        while True:
            stri = "0. Exit\n1. Add Schedule to Calendar\n"
            count = 2
            events = self.ret_events()
            for i in events:
                try:
                    stri += "{}. {} at {} until {}\n".format(str(count), str(i.bound_object.name), i.start_time, i.end_time)
                    count += 1
                except AttributeError:
                    stri += str(count) + ". " + str(i.name) + "\n"
                    count += 1
            choice = int(input(stri))
            if choice == 0:
                break
            elif choice == 1:
                add_to_calendar(events)
            elif choice in list(range(int(len(events)) + 2)):
                events[choice - 2].give_choices()
    
class ImmovableEvent(object):
    def __init__(self, name, start_time, end_time):
        self.name = name
        self.start_time = start_time if not type(start_time) == type("") else parse(start_time)
        self.end_time = end_time if not type(end_time) == type("") else parse(end_time)
        if type(self.start_time) == freezegun.api.FakeDatetime:
            self.start_time = datetime.datetime(year=self.start_time.year, month=self.start_time.month, day=self.start_time.day, hour=self.start_time.hour, minute=self.start_time.minute)
        if type(self.end_time) == freezegun.api.FakeDatetime:
            self.end_time = datetime.datetime(year=self.end_time.year, month=self.end_time.month, day=self.end_time.day, hour=self.start_time.hour, minute=self.end_time.minute)
        self.env = None
        self.length = self.end_time - self.start_time
        self.lookup_time = datetime.datetime(year=self.start_time.year, month=self.start_time.month, day=self.start_time.day)
    
    def rename(self, name):
        self.name = name

    def set_env(self, env):
        self.env = env
    
    def delete(self):
        self.env._schedule[self.lookup_time].pop(self.env._schedule[self.lookup_time].index(self))
        self.env._schedule_times[self.lookup_time].pop(self.env._schedule_times[self.lookup_time].index((self.start_time, self.end_time, True)))
    
    def move_start(self, new_start):
        self.env._schedule_times[self.lookup_time][self.env._schedule_times[self.lookup_time].index((self.start_time, self.end_time, False))] = (self.start_time, self.end_time, True)
        self.start_time = new_start
    
    def move_end(self, new_end):
        self.env._schedule_times[self.lookup_time][self.env._schedule_times[self.lookup_time].index((self.start_time, self.end_time, False))] = (self.start_time, new_end, True)
        self.end_time = new_end
    
    def give__choices(self):
        choices = ["Rename", "Delete", "Move Start", "Move End"]
        choices_func = [self.rename, self.delete, self.move_start, self.move_end]
        while True:
            stri = "0. Exit\n"
            for i in range(len(choices)):
                stri += str(i + 1) + ". " + choices[i] + "\n"
            choice = yield stri
            choice = int(choice)
            if choice == 0:
                break
            elif choice in list(range(len(choices) + 1)):
                if choice == 3:
                    new_start = yield "Input new start\n"
                    choices_func[choice - 1](dateparser.search.search_dates(str(new_start))[0][1])
                elif choice == 4:
                    new_end = yield "Input new end\n"
                    choices_func[choice - 1](dateparser.search.search_dates(str(new_end))[0][1])
                else:
                    choices_func[choice - 1]()
    
    def give_choices(self):
        choices = ["Rename", "Delete", "Move Start", "Move End"]
        choices_func = [self.rename, self.delete, self.move_start, self.move_end]
        while True:
            stri = "0. Exit\n"
            for i in range(len(choices)):
                stri += str(i + 1) + ". " + choices[i] + "\n"
            choice = int(input(stri))
            if choice == 0:
                break
            elif choice in list(range(len(choices) + 1)):
                if choice == 3:
                    choices_func[choice - 1](dateparser.search.search_dates(str(input("Input new start\n")))[0][1])
                elif choice == 4:
                    choices_func[choice - 1](dateparser.search.search_dates(str(input("Input new end\n")))[0][1])
                else:
                    choices_func[choice - 1]()

class MeetingEvent(object):
    def __init__(self, name, start_time, end_time, pattern, weekends=False, oc=True):
        self.name = name
        self.start_time = start_time
        self.end_time = end_time
        if type(self.start_time) == freezegun.api.FakeDatetime:
            self.start_time = datetime.datetime(year=self.start_time.year, month=self.start_time.month, day=self.start_time.day, hour=self.start_time.hour, minute=self.start_time.minute)
        if type(self.end_time) == freezegun.api.FakeDatetime:
            self.end_time = datetime.datetime(year=self.end_time.year, month=self.end_time.month, day=self.end_time.day, hour=self.end_time.hour, minute=self.end_time.minute)
        self.occurrences = []
        self.pattern = pattern
        patterns = ["self.{}_time + datetime.timedelta(7 * {})", "self.{}_time + datetime.timedelta(1 * {})", "self.{}_time + datetime.timedelta(2 * {})", "self.{}_time + datetime.timedelta(3 * {})", "self.{}_time + datetime.timedelta(4 * {})", "self.{}_time + datetime.timedelta(5 * {})", "self.{}_time + datetime.timedelta(6 * {})", "self.{}_time + datetime.timedelta(14 * {})", "datetime.datetime(year=self.{0}_time.year, month=self.{0}_time.month + {1}, day=self.{0}_time.day, hour=self.{0}_time.hour, minute=self.{0}_time.minute)"]
        for i in range(100):
            exec("self.occurrences.append(({}, {}))".format(patterns[pattern].format("start", str(i)), patterns[pattern].format("end", str(i))))
        self.env = None
        if oc:
            _occ = []
            for i in self.occurrences:
                _occ.append((self.name, i[0], i[1], self.pattern))
            self.occurrences = []
            for i in _occ:
                self.occurrences.append(MeetingEvent(*i, oc=False))
        self.length = self.end_time - self.start_time
        #patterns = ["Day of the Week", "Every Day", "Every Other Day", "Every Third Day", "Every Fourth Day", "Every Fifth Day", "Every Sixth Day", "Every Other Week", "Once A Month"]
        self.lookup_time = datetime.datetime(year=self.start_time.year, month=self.start_time.month, day=self.start_time.day)

    def rename(self, name):
        self.name = name
    
    def set_env(self, env, populate=True):
        self.env = env
        #if populate:
        #    for i in self.occurrences:
        #        try:
        #            event = MeetingEvent(self.name, i[0], i[1], self.pattern)
        #            event.set_env(self.env, populate=False)
        #            self.env.add_event(event)
        #        except ScopeError:
        #            break
        #del self.occurrences
    
    def delete(self):
        self.env._schedule[self.lookup_time].pop(self.env._schedule[self.lookup_time].index(self))
        self.env._schedule_times[self.lookup_time].pop(self.env._schedule_times[self.lookup_time].index((self.start_time, self.end_time, False)))
    
    def move_start(self, new_start):
        self.env._schedule_times[self.lookup_time][self.env._schedule_times[self.lookup_time].index((self.start_time, self.end_time, False))] = (self.start_time, self.end_time, False)
        self.start_time = new_start
    
    def move_end(self, new_end):
        self.env._schedule_times[self.lookup_time][self.env._schedule_times[self.lookup_time].index((self.start_time, self.end_time, False))] = (self.start_time, new_end, False)
        self.end_time = new_end
    
    def give__choices(self):
        choices = ["Rename", "Delete", "Move Start", "Move End"]
        choices_func = [self.rename, self.delete, self.move_start, self.move_end]
        while True:
            stri = "0. Exit\n"
            for i in range(len(choices)):
                stri += str(i + 1) + ". " + choices[i] + "\n"
            choice = yield stri
            choice = int(choice)
            if choice == 0:
                break
            elif choice in list(range(len(choices) + 1)):
                if choice == 3:
                    new_start = yield "Input new start\n"
                    choices_func[choice - 1](dateparser.search.search_dates(str(new_start))[0][1])
                elif choice == 4:
                    new_end = yield "Input new end\n"
                    choices_func[choice - 1](dateparser.search.search_dates(str(new_end))[0][1])
                else:
                    choices_func[choice - 1]()
    
    def give_choices(self):
        choices = ["Rename", "Delete", "Move Start", "Move End"]
        choices_func = [self.rename, self.delete, self.move_start, self.move_end]
        while True:
            stri = "0. Exit\n"
            for i in range(len(choices)):
                stri += str(i + 1) + ". " + choices[i] + "\n"
            choice = int(input(stri))
            if choice == 0:
                break
            elif choice in list(range(len(choices) + 1)):
                if choice == 3:
                    choices_func[choice - 1](dateparser.search.search_dates(str(input("Input new start\n")))[0][1])
                elif choice == 4:
                    choices_func[choice - 1](dateparser.search.search_dates(str(input("Input new end\n")))[0][1])
                else:
                    choices_func[choice - 1]()

class MoveableEvent(object):
    def __init__(self, bound_object, start_time, end_time):
        self.bound_object = bound_object
        self.start_time = start_time
        self.end_time = end_time
        if type(self.start_time) == freezegun.api.FakeDatetime:
            self.start_time = datetime.datetime(year=self.start_time.year, month=self.start_time.month, day=self.start_time.day, hour=self.start_time.hour, minute=self.start_time.minute)
        if type(self.end_time) == freezegun.api.FakeDatetime:
            self.end_time = datetime.datetime(year=self.end_time.year, month=self.end_time.month, day=self.end_time.day, hour=self.start_time.hour, minute=self.end_time.minute)
        self.env = None
        self.lookup_time = datetime.datetime(year=self.start_time.year, month=self.start_time.month, day=self.start_time.day)
        self.length = self.end_time - self.start_time
        self.url = self.bound_object.url
        self.name = self.bound_object.name

    def rename(self, name):
        self.name = name
    
    def set_env(self, env):
        self.env = env
    
    def delete(self):
        self.env._schedule[self.lookup_time].pop(self.env._schedule[self.lookup_time].index(self))
        self.env._schedule_times[self.lookup_time].pop(self.env._schedule_times[self.lookup_time].index((self.start_time, self.end_time, False)))
    
    def move_start(self, new_start):
        self.env._schedule_times[self.lookup_time][self.env._schedule_times[self.lookup_time].index((self.start_time, self.end_time, False))] = (self.start_time, self.end_time, False)
        self.start_time = new_start
    
    def move_end(self, new_end):
        self.env._schedule_times[self.lookup_time][self.env._schedule_times[self.lookup_time].index((self.start_time, self.end_time, False))] = (self.start_time, new_end, False)
        self.end_time = new_end
    
    def give__choices(self):
        choices = ["Rename", "Delete", "Move Start", "Move End"]
        choices_func = [self.rename, self.delete, self.move_start, self.move_end]
        while True:
            stri = "0. Exit\n"
            for i in range(len(choices)):
                stri += str(i + 1) + ". " + choices[i] + "\n"
            choice = yield stri
            choice = int(choice)
            if choice == 0:
                break
            elif choice in list(range(len(choices) + 1)):
                if choice == 3:
                    new_start = yield "Input new start\n"
                    choices_func[choice - 1](dateparser.search.search_dates(str(new_start))[0][1])
                elif choice == 4:
                    new_end = yield "Input new end\n"
                    choices_func[choice - 1](dateparser.search.search_dates(str(new_end))[0][1])
                else:
                    choices_func[choice - 1]()
    
    def give_choices(self):
        choices = ["Rename", "Delete", "Move Start", "Move End"]
        choices_func = [self.rename, self.delete, self.move_start, self.move_end]
        while True:
            stri = "0. Exit\n"
            for i in range(len(choices)):
                stri += str(i + 1) + ". " + choices[i] + "\n"
            choice = int(input(stri))
            if choice == 0:
                break
            elif choice in list(range(len(choices) + 1)):
                if choice == 3:
                    choices_func[choice - 1](dateparser.search.search_dates(str(input("Input new start\n")))[0][1])
                elif choice == 4:
                    choices_func[choice - 1](dateparser.search.search_dates(str(input("Input new end\n")))[0][1])
                else:
                    choices_func[choice - 1]()

class ProvisionalEvent(object):
    def __init__(self, bound_object, pref_start=None, length=None):
        """
        pref_start is datetime.datetime
        length is datetime.timedelta
        """
        self.bound_object = bound_object
        self.hard_stop = self.bound_object.date
        self.hard_stop = datetime.datetime(year=self.hard_stop.year, month=self.hard_stop.month, day=self.hard_stop.day, hour=self.hard_stop.hour, minute=self.hard_stop.minute)
        self.pref_start = pref_start
        if not self.pref_start:
            self.pref_start = self.hard_stop
        else:
            self.pref_start = datetime.datetime(year=self.pref_start.year, month=self.pref_start.month, day=self.pref_start.day, hour=self.pref_start.hour, minute=self.pref_start.minute)
        if type(self.hard_stop) == freezegun.api.FakeDatetime:
            self.hard_stop = datetime.datetime(year=self.hard_stop.year, month=self.hard_stop.month, day=self.hard_stop.day, hour=self.hard_stop.hour, minute=self.hard_stop.minute)
        if type(self.pref_start) == freezegun.api.FakeDatetime:
            self.pref_start = datetime.datetime(year=self.pref_start.year, month=self.pref_start.month, day=self.pref_start.day, hour=self.pref_start.hour, minute=self.pref_start.minute)
        self.length = length
        if not self.length:
            self.length = datetime.timedelta(seconds=(15 * 60))
        if self.pref_start and self.length:
            self.pref_end = self.pref_start + self.length
        self.start_time = None
        self.end_time = None
        self.name = bound_object.name
        self.env = None
        self.url = self.bound_object.url
        self.lookup_time = datetime.datetime(year=self.hard_stop.year, month=self.hard_stop.month, day=self.hard_stop.day)

    def rename(self, name):
        self.name = name
    
    def set_env(self, env):
        self.env = env
    
    def delete(self):
        self.env._schedule[self.lookup_time].pop(self.env._schedule[self.lookup_time].index(self))
        self.env._schedule_times[self.lookup_time].pop(self.env._schedule_times[self.lookup_time].index((self.start_time, self.end_time, False)))

def get_calendar_events(days_from_today):
    #print("getting events")
    os.system(get_calendar_osa.format(days_from_today, os.environ["PWD"]))
    from AppleCalendar.preexisting_calendar_events import events as eventos
    preexisting_events = eventos
    del eventos
    os.system("rm preexisting_calendar_events.py")
    return preexisting_events

def add_to_calendar(events):
    for i in events:
        delta = i.length
        fills = [str((datetime.datetime.now() - i.start_time).days), str(i.start_time.hour), str(i.start_time.minute), str(i.start_time.second), str(int(int(delta.seconds/60)/60)), str(int(delta.seconds/60)), str(delta.seconds%60), str(i.url), str(i.name)]
        os.system(add_event_osa.format(*fills))