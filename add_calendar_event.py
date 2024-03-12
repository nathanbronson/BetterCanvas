import sys
import os

name = sys.argv[1]
start = sys.argv[2]
end = sys.argv[3]
pwd = sys.argv[4]

if name == "__none__" and start == "__none__" and end == "__none__":
    os.system("rm " + pwd + "/preexisting_calendar_events.py")
    doc = open(pwd + "/preexisting_calendar_events.py", "w+")
    doc.write("from schedule_objects import ImmovableEvent as j\nevents = []\n")
    exit()

if not os.path.isfile(pwd + "/preexisting_calendar_events.py"):
    doc = open(pwd + "/preexisting_calendar_events.py", "w+")
    doc.write("from schedule_objects import ImmovableEvent as j\nevents = []\n")
else:
    doc = open(pwd + "/preexisting_calendar_events.py", "a")

doc.write("events.append(j('{}', '{}', '{}'))\n".format(name, start, end))
doc.close()