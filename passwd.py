#!/usr/bin/env python3
"Secure terminal-based password manager"

import os, hashlib, base64, random, json, sys, pyperclip, secrets
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.fernet import Fernet
from getpass import getpass

SECURITY_CHARS = 0 #the number of chars at the end of pw to print to console, rather than entire password put onto clipboard (recommended no more than 3)
GENERATE_LENGTH = 24
PWSTORE_DIR = "."
HELP_STR = """
Command list:
set <name> <password>: Set/update the password for a site name
get <name>: Copy a password to clipboard
print <name>: Print a password to stdout
comment <name> <new comment>: Set the comment for a site name
list [filter]: List all site names or optionally filter by name
delete <name>: Delete a password for a site name
generate <name>: Create a new password for site
setmainpw: Change the main password
"""

def readSalt() -> str:
    salt_dir = PWSTORE_DIR + '/salt'
    if (isFileEmpty(salt_dir)): #generate new salt
        salt = base64.b64encode(os.urandom(24)).decode('utf-8')
        with open(salt_dir, 'w') as f: f.write(salt + "\n### DO NOT CHANGE ###")
        return salt
    else: 
        with open(salt_dir, 'r') as f:
            salt = f.read().split('\n')[0]
            if (len(salt) < 16): print("Warning: Salt should be at least 16 chars (current length is %s)" % len(salt))
            return salt

def openPasswords(salt, pw, legacy=False) -> (dict, Fernet):
    fernet = getFernet(salt, pw, legacy=legacy)
    pwstore = PWSTORE_DIR + '/pwstore'
    if (isFileEmpty(pwstore)): return (None, fernet)
    try:
        with open(pwstore, 'r') as f:
            decrypted = fernet.decrypt(f.read())
            return (json.loads(decrypted), fernet)
    except Exception as ex: 
        return (None, fernet)

def writePasswords(vals: dict, fernet: Fernet):
    encrypted = fernet.encrypt(json.dumps(vals).encode('utf-8')).decode()
    with open(PWSTORE_DIR + '/pwstore', 'w') as f: f.write(encrypted)

def tryPassword(nacl: str) -> dict:
    pw = getpass("Enter your password: ")
    vals, fernet = openPasswords(nacl, pw)
    if (vals is None):
        vals, _ = openPasswords(nacl, pw, legacy=True)
        if (vals is None):
            print("Incorrect password.")
            return tryPassword(nacl)
        else:
            writePasswords(vals, fernet)
    return vals, fernet

def isFileEmpty(path: str) -> bool:
    if (not os.path.isfile(path)): return True
    with open(path, 'r') as f: return len(f.read()) == 0

def getFernet(salt, pw, legacy=False):
    pw = pw.strip()
    if (legacy):
        pwhash = hashlib.sha256(base64.b64encode((salt + pw).encode('utf-8'))).hexdigest()
        return Fernet(base64.urlsafe_b64encode(bytes.fromhex(pwhash)[0:32]))
    else: #no longer a toy project, scrypt far more secure key derivation
        kdf = Scrypt(salt=base64.b64decode(salt), length=32, n=2**20, r=8, p=1)
        key = kdf.derive(pw.encode('utf-8'))
        return Fernet(base64.b64encode(key))

def getPassword(key, vals):
    password, comments = None, None
    if (key in vals):
        if (isinstance(vals[key], dict)): 
            if ('password' in vals[key]): password = vals[key]['password']
            else: print("Malformatted key store for %s!" % key)
            if ('comment' in vals[key]): comments = vals[key]['comment']
        elif (isinstance(vals[key], str)): password = vals[key] #fallback
    return password, comments

def printPw(key, vals, copy=True):
    if (key in vals): 
        password, comments = getPassword(key, vals)
        if (comments is not None): print("Comment: %s" % comments)
        if (copy):
            if (SECURITY_CHARS <= 0):
                pyperclip.copy(password)
                print("Password copied to clipboard!")
            else:
                copy_chars = password[:-SECURITY_CHARS]
                end_chars = password[-SECURITY_CHARS:]
                pyperclip.copy(copy_chars)
                print("Paste first portion, THEN type: %s" % end_chars)
        else: print(password)
    else: print("Unknown site name")

def setComment(key, comment, vals):
    if not (key in vals): return
    password, old_comments = getPassword(key, vals)
    vals[key] = {
        'password': password,
        'comment': comment
    }
    return vals, old_comments

def newPw() -> str:
    while True:
        pw = getpass("Enter a new password: ")
        pw2 = getpass("Re-type new password: ")
        if (pw == pw2): return pw
        else: print("Passwords did not match.")

def confirm(prompt) -> bool:
    conf = input("%s [Y/n]: " % prompt).strip().lower()
    return (conf == 'y' or conf == 'yes')

if __name__ == "__main__":
    with_sysargs = len(sys.argv) > 1
    if (with_sysargs and sys.argv[1].lower() == '--help'): 
        print(HELP_STR)
        quit()

    salt = readSalt()
    vals = {}
    fernet = None
    if (isFileEmpty(PWSTORE_DIR + '/pwstore')):
        with open(PWSTORE_DIR + '/pwstore', 'w') as f: pass
        fernet = getFernet(salt, newPw())
    else: 
        vals, fernet = tryPassword(salt)
        if (not with_sysargs): print("Password accepted!")
    if (not with_sysargs): print("Type ? for a list of commands")
    first = True

    while first or not with_sysargs:
        args = sys.argv[1:] if with_sysargs else input("> ").split(" ")
        if (len(args) == 0 or len(args[0]) == 0): continue
        first = False
        if (len(args) == 0): continue
        args[0] = args[0].lower().replace('-', '')

        if (args[0] == '?' or args[0] == 'help'): print(HELP_STR)
        elif (args[0] == 'list' or args[0] == 'search'):
            keys = list(vals.keys())
            if (len(args) > 1):
                search_term = args[1].strip().lower()
                keys = list(filter(lambda i: search_term in i.lower(), keys))
                print("%s password key(s) for search term \"%s\":" % (len(keys), search_term))
            else: print("%s password key(s):" % len(keys))
            for key in keys: print("- %s" % key)
        elif (args[0] == 'get'): printPw(args[1].lower(), vals, copy=True)
        elif (args[0] == 'print' or args[0] == 'show'): printPw(args[1].lower(), vals, copy=False)

        elif (args[0] == 'set' or args[0] == 'put'):
            if (len(args) < 3): 
                print("Usage: set <name> <new password>")
                continue
            key = args[1].lower()
            if (key in vals and not confirm('Are you sure you want to overwrite this password?')):
                print("Cancelled")
                continue
            pw = args[2]
            if not with_sysargs: pw = ' '.join(args[2:]).strip() #concat all args if using built-in shell
            old_pw, comment = getPassword(key, vals)
            vals[key] = {
                'password': pw,
                'comment': comment
            }
            writePasswords(vals, fernet)
            print("Successfully set password for %s!" % key)

        elif (args[0] == 'comment'):
            if (len(args) < 3): 
                print("Usage: comment <name> <comment>")
                continue
            key = args[1].lower()
            if not (key in vals): 
                print("Unknown site name '%s'" % key)
                continue
            comment = args[2]
            if (not with_sysargs): comment = ' '.join(args[2:]).strip()
            vals, old_comment = setComment(key, comment, vals)
            writePasswords(vals, fernet)
            if (old_comment is not None): print("Old comment for %s: %s" % (key, old_comment))
            print("New comment for %s: %s" % (key, comment))

        elif (args[0] == 'delete' or args[0] == 'del'):
            if (len(args) < 2): 
                print("Usage: del <name>")
                continue
            key = args[1].lower()
            if (not key in vals):
                print("Unknown site '%s'" % key)
                continue
            if (not confirm("Are you sure you want to delete %s?" % key)): 
                print("Cancelled")
                continue
            del vals[key]
            writePasswords(vals, fernet)
            print("Deleted %s!" % key)

        elif (args[0] == 'generate' or args[0] == 'gen'):
            if (len(args) < 2):
                print("Generate a password for a new site. Usage: generate <name>")
                continue
            key = args[1].lower()
            if (key in vals and not confirm("Are you sure you want to overwrite %s?" % key)): 
                print("Cancelled")
                continue
            alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*()'
            pw = ''.join([alphabet[secrets.randbelow(len(alphabet))] for _ in range(GENERATE_LENGTH)])
            vals[key] = pw
            writePasswords(vals, fernet)
            print("Successfully generated new password!")
            printPw(key, vals, copy=True)

        elif (args[0] == 'setmainpw' or args[0] == 'passwd'):
            pw = newPw()
            os.remove(PWSTORE_DIR + "/salt")
            salt = readSalt()
            fernet = getFernet(salt, pw)
            writePasswords(vals, fernet)
            print("Password updated!")
        
        elif (args[0] == 'exit' or args[0] == 'quit'): break
        else: printPw(args[0].lower(), vals, copy=True)
        print('')