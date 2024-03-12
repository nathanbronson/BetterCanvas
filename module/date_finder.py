def find_dates(canvas_lms, canvas, items, due_dates, date_finder):
    date_finder.thread.join()
    return date_finder.dates

class DateFinder(object):
    def __init__(self, canvas_lms, canvas, items, due_dates):
        self.dates = None
        self.thread = Thread(target=self.find_dates, args=(canvas_lms, canvas, items, due_dates))
        self.thread.start()

    def find_dates(self, canvas_lms, canvas, items, due_dates):
        self.dates = due_dates
        bodies = [i.name + ". " + i.body for i in items]
        for i in bodies:
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
            RELATIVE_BASE = False
            config = dateparser.conf.Settings()
            if type(items[bodies.index(i)]) == DatedItem or type(items[bodies.index(i)]) == AssignmentItem:
                if type(items[bodies.index(i)].date) == type(""):
                    e = items[bodies.index(i)].date
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
            z = dateparser.search.search_dates(i, settings=config, languages=["en"])
            r = 0
            for n in z if not z == None else []:
                frozen_date = None
                try:
                    with freeze_time(RELATIVE_BASE):
                        frozen_date = duparse(n[0])
                    is_dateparser = False
                    if type(frozen_date) == datetime.timedelta:
                        frozen_date = n[1]
                except Exception as err:
                    if n[0].lower() == "today":
                        frozen_date = RELATIVE_BASE
                    elif n[0].lower() == "tomorrow":
                        frozen_date = RELATIVE_BASE + datetime.timedelta(days=1)
                    else:
                        frozen_date = n[1]
                        is_dateparser = True
                if determine_date_eligibility(n[0], frozen_date):
                    date_tokens = nlp(n[0])
                    while True:
                        try:
                            nlp_sent = nlp(sentences[0])
                        except:
                            break
                        containing_sent = ""
                        for g in range(len(nlp_sent)):
                            try:
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
                            if before_root(containing_sent, date_tokens, is_root=True):
                                if containing_sent[-2].text == date_tokens[-1].text:
                                    l = str(sentences[1])
                        elif [g.text for g in containing_sent] == [w.text for w in date_tokens]:
                            l = _sentences[r - 1]
                        else:
                            l = get_context(containing_sent, n[0])
                    except IndexError:
                        pass
                    if l:
                        strii = ""
                        for v in l:
                            if not v == "\r":
                                strii += v
                        l = strii
                    if l:
                        try:
                             self.dates[frozen_date] += [ImpliedItem(l, frozen_date, items[bodies.index(i)], date_str=n[0])]
                        except KeyError:
                            try:
                                self.dates[frozen_date] = [ImpliedItem(l, frozen_date, items[bodies.index(i)], date_str=n[0])]
                            except IndexError:
                                pass
        for i in list(self.dates.keys()):
            for n in self.dates[i]:
                if not n.name:
                    self.dates[i].pop(self.dates[i].index(n))
        for i in list(self.dates.keys()):
            if self.dates[i] == []:
                del self.dates[i]