def before_root(doc, date, is_root=False):
    date = [str(i.text) for i in date]
    for i in doc:
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
    try:
        span = doc[doc[0].left_edge.i : doc[0].right_edge.i+1]
    except IndexError:
        return
    threads = []
    date = nlp(str(date))
    l = before_root(doc, date)
    with doc.retokenize() as retokenizer:
        retokenizer.merge(span)
    if l:
        for i in doc:
            if str(i.dep_) == "ROOT":
                threads = [i, i.head]
                while True:
                    q = 0
                    for n in threads:
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
                if str(i.pos_) == "NOUN" or str(i.pos_) == "PROPN":
                    threads = [i, i.head]
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
                if str(i.pos_) == "PROPN":
                    threads = [i, i.head]
                    while True:
                        q = 0
                        for n in threads:
                            if not n.head in threads:
                                threads.append(n.head)
                                q += 1
                        if q == 0:
                            break
                    break
    for i in range(len(threads)):
        try:
            if str(threads[i]) in [str(n) for n in date]:
                threads.pop(i)
        except IndexError:
            pass
    index = [n.i for n in threads]
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