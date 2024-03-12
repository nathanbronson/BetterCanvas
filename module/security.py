def make_secure_module(insecure_path, secure_path, salt_path):
    with open(insecure_path, "r") as insecure_doc:
        insecure_text = insecure_doc.read()
    kdf = nacl.pwhash.argon2i.kdf
    salt_size = nacl.pwhash.argon2i.SALTBYTES
    salt = nacl.utils.random(salt_size)
    with open(salt_path, "wb") as salt_doc:
        salt_doc.write(salt)
    password = yield "enter password\n"
    password = str(password).encode("utf-8")
    key = kdf(nacl.secret.SecretBox.KEY_SIZE, password, salt, opslimit=3)
    insecure_text = insecure_text.encode("utf-8")
    box = nacl.secret.SecretBox(key)
    encrypted = box.encrypt(insecure_text)
    with open(secure_path, 'wb') as secure_doc:
        secure_doc.write(encrypted)
    os.system("rm {}".format(insecure_path))

def get_from_secure_module(secure_path, insecure_path, salt_path):
    password = yield "enter password\n"
    password = str(password).encode("utf-8")
    with open(salt_path, "rb") as salt_doc:
        salt = salt_doc.read()
    with open(secure_path, "rb") as secure_doc:
        secure_text = secure_doc.read()
    kdf = nacl.pwhash.argon2i.kdf
    key = kdf(nacl.secret.SecretBox.KEY_SIZE, password, salt, opslimit=3)
    box = nacl.secret.SecretBox(key)
    insecure_text = box.decrypt(secure_text)
    with open(insecure_path, "wb") as insecure_doc:
        insecure_doc.write(insecure_text)
    module = importlib.import_module(insecure_path[0 : -3])
    os.system("rm {}".format(insecure_path))
    yield module