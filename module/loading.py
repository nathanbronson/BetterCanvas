def load_items(canvas_lms, canvas, classes):
    courses = []
    for i in classes:
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
                        except Exception as err:
                            print(err)
                except Exception as err:
                    print(err)
        
        def get_announcements(self):
            for i in self.courses:
                try:
                    for n in canvas.get_announcements(context_codes=['course_{}'.format(i.id)]):
                        try:
                            try:
                                self.announcements.append(DatedItem(n.title, clean_body(n.message), n.posted_at_date, url=n.html_url))
                            except AttributeError:
                                self.announcements.append(DatedItem(n.title, clean_body(n.message), n.posted_at_date))
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