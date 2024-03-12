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

def add_to_calendar(events):
    for i in events:
        delta = i.schedule_end - i.schedule_start
        start_sched = datetime.datetime(year=i.schedule_start.year, month=i.schedule_start.month, day=i.schedule_start.day, hour=i.schedule_start.hour, minute=i.schedule_start.minute, second=i.schedule_start.second)
        fills = [str((start_sched - datetime.datetime.now()).days), str(i.schedule_start.hour), str(i.schedule_start.minute), str(i.schedule_start.second), str(int((delta.seconds/60)/60)), str(int((delta.seconds%60)/60)), str((delta.seconds%60)%60), i.url, i.name]
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