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
            else:
                c += 1
        except IndexError:
            break
    stri = ""
    for i in body:
        stri += i
    return stri