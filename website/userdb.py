import hashlib
import base64

from configparser import ConfigParser
from mysql.connector import MySQLConnection, Error
from flask import abort

from .otp import totp


def read_db_config(filename='userdb.ini', section='mysql'):
    ''' 
    Read database configuration file and return a dictionary object
    reads file from root of project

    :param filename: name of the configuration file
    :param section: section of database configuration
    :return: a dictionary of database parameters
    '''

    # create parser and read ini configuration file
    parser = ConfigParser()
    parser.read(filename)

    # get section, default to mysql
    db = {}
    if parser.has_section(section):
        items = parser.items(section)
        for item in items:
            db[item[0]] = item[1]
    else:
        raise Exception('{0} not found in the {1} file'.format(section, filename))

    return db


def userdb_delete_row(sql, *args):
    '''
    Connect to MySQL database and delete row(s)
    '''

    try:
        db_config = read_db_config()
        conn = MySQLConnection(**db_config)

        if not conn.is_connected():
            raise Exception('Problem connecting to user database')

        cursor = conn.cursor(prepared=True)
        cursor.execute(sql, args)
        conn.commit()
        result = cursor.rowcount

    except Error as error:
        raise Exception('Problem establishing DB handle: {}'.format(error))

    finally:
        cursor.close()
        conn.close()

    result = {
        'row': result,
        'fields': None,
        'text': "{} records deleted".format(result),
    }

    return result



def userdb_fetch_row(sql, *args):
    '''
    Connect to MySQL database and fetch one row
    '''

    try:
        db_config = read_db_config()
        conn = MySQLConnection(**db_config)

        if not conn.is_connected():
            raise Exception('Problem connecting to user database')

        cursor = conn.cursor(prepared=True)
        cursor.execute(sql, args)
        row = cursor.fetchone()  # None if empty

        fields = [i[0] for i in cursor.description]
        # field_names.index('id') == 0
    except Error as error:
        raise Exception('Problem establishing DB handle: {}'.format(error))

    finally:
        cursor.close()
        conn.close()

    result = {
        'row': row,
        'fields': fields,
    }

    return result


def userdb_fetch_all(sql, *args):
    '''
    Connect to MySQL database and fetch all rows.
    We're not actually using this one right now...
    '''

    try:
        db_config = read_db_config()
        conn = MySQLConnection(**db_config)

        if not conn.is_connected():
            raise Exception('Problem connecting to user database')

        cursor = conn.cursor(prepared=True)
        cursor.execute(sql, args)
        rows = cursor.fetchall()  # None if empty

        fields = [i[0] for i in cursor.description]
        # fields.index('id') == 0

    except Error as error:
        raise Exception('Problem establishing DB handle: {}'.format(error))

    finally:
        cursor.close()
        conn.close()

    result = {
        'row': rows[0],  # incase somebody is silly
        'rows': rows,
        'fields': fields,
    }

    return result


def get_userdb_details(email):
    '''
    fetches userdb (django) first and last name.
    if it's active.
    '''
    sql = "SELECT first_name, last_name FROM users_customuser WHERE email=? AND is_active=1"
    result = userdb_fetch_row(sql, email)
    return result


def get_userdb_app_entry(email):
    '''
    get hash and deets for checking against, if active.
    requires GITLAB type app entry for the user (username is email)
    '''
    sql = "SELECT password, salt, iter FROM users_apppasswords WHERE username=? AND application='GITLAB' AND active=1"
    result = userdb_fetch_row(sql, email)
    return result


def get_userdb_entry(email):
    '''
    fetches userdb (django) password entry matching 'email'.
    if it's active.
    '''
    sql = "SELECT id, password FROM users_customuser WHERE email=? AND is_active=1"
    result = userdb_fetch_row(sql, email)
    return result


def get_userdb_otp_static_device(user_id):
    '''
    fetches (all) userdb (django) OTP backup devices matching 'user_id' if 'confirmed'
    '''
    sql = "SELECT id FROM otp_static_staticdevice WHERE user_id=? AND confirmed=1"
    result = userdb_fetch_row(sql, user_id)
    return result


def get_userdb_otp_static_token(device_id, token):
    '''
    fetches (matching) userdb (django) OTP backup (static) code id matching 'device_id' and 'token'.
    '''
    sql = "SELECT id FROM otp_static_statictoken WHERE device_id=? and token=?"
    result = userdb_fetch_row(sql, device_id, token)
    return result


def delete_userdb_otp_static_token(token_id):
    '''
    deletes (used) static token matching 'id'
    '''
    sql = "DELETE FROM otp_static_statictoken WHERE id=?"
    result = userdb_delete_row(sql, token_id)
    return result


def try_userdb_otp_backup(user_id, token):
    static_device_entry = get_userdb_otp_static_device(user_id)

    # word to the wicked, this index should just be '0'
    row = static_device_entry['row']
    fields = static_device_entry['fields']

    if not row:
        return None

    static_device_id = row[fields.index('id')]

    static_token_entry = get_userdb_otp_static_token(static_device_id, token)

    row = static_token_entry['row']
    fields = static_token_entry['fields']

    if not row:
        return None

    return row[fields.index('id')]


def get_userdb_otp_totp(user_id):
    '''
    fetches userdb (django) OTP device entry matching 'user_id'.
    if it's active.
    '''
    sql = "SELECT `key`, `step`, `t0`, `digits`, `tolerance`, `drift`, `last_t` FROM otp_totp_totpdevice WHERE user_id=? AND confirmed=1"
    result = userdb_fetch_row(sql, user_id)
    return result


def gitlab_get_app_user(user):
    '''
    Fetches an APP PASSWORD user from the (django) userdb
    '''
    email = user.username  # from the user object
    user_id = user.id

    res = get_userdb_details(email)
    
    row = res['row']
    fields = res['fields']

    if not row:
        abort(404)

    full_name = "{} {}".format(row[fields.index('first_name')],row[fields.index('last_name')])
    state = 'active'  # is_active=1 is a pre-req to getting the user

    result = {
        'id': user_id,  # from oauth db
        'state': state,
        'email': email,
        'login': email,
        'name': full_name,
        'username': email,
    }

    return result


def gitlab_get_user(user):
    email = user.username  # from the user object
    user_id = user.id

    res = get_userdb_details(email)
    
    row = res['row']
    fields = res['fields']

    if not row:
        abort(404)

    full_name = "{} {}".format(row[fields.index('first_name')],row[fields.index('last_name')])
    state = 'active'  # is_active=1 is a pre-req to getting the user

    result = {
        'id': user_id,  # from oauth db
        'state': state,
        'email': email,
        'login': email,
        'name': full_name,
        'username': email,
    }

    return result


def gitlab_check_otp(username, otp):
    '''
    checks the OTP against the userdb (django) OTP entry for said username
    '''
    user_app_entry = get_userdb_entry(username)  # 'user' is email

    row = user_app_entry['row']
    fields = user_app_entry['fields']

    if not row:
        abort(404)

    user_id = row[fields.index('id')]

    # first, check TOTP (time sensitive)
    totp_entry = get_userdb_otp_totp(user_id)   

    row = totp_entry['row']
    fields = totp_entry['fields']

    try:
        key = row[fields.index('key')]
        step = row[fields.index('step')]
        t0 = row[fields.index('t0')]
        digits = row[fields.index('digits')]
        drift = row[fields.index('drift')]
    except:
        abort(404)

    realkey = bytes.fromhex(key)
    totp_result = totp(realkey, step, t0, digits, drift)

    try:
        # totp good?
        if int(totp_result) == int(otp):
            return True
    except:
        # we might be using a backup key
        pass

    # totp failed? try to find a matching backup
    # if it exists, 'use' it and delete
    static_token_id = try_userdb_otp_backup(user_id, otp)

    if not static_token_id:
        return False
    else:
        delete_userdb_otp_static_token(static_token_id)

    return True


def gitlab_check_app_pass(username, password):
    '''
    checks the (oauth) password against the userdb (django) password entry for said email (user)
    '''
    user_app_entry = get_userdb_app_entry(username)  # 'user' is email

    row = user_app_entry['row']
    fields = user_app_entry['fields']

    if not row:
        abort(404)

    try:
        salt = row[fields.index('salt')]
        iter = row[fields.index('iter')]
        hash = row[fields.index('password')]
    except:
        abort(404)

    return checkAppHash(password, salt, hash, iter)


def gitlab_check_pass(username, password):
    '''
    checks the (oauth) password against the userdb (django) password entry for said email (user)
    
    should return a field like this:
        pbkdf2_sha256$ITER$SALT$HASH
    so split on '$'
    '''
    user_app_entry = get_userdb_entry(username)  # 'user' is email

    row = user_app_entry['row']
    fields = user_app_entry['fields']

    if not row:
        abort(404)

    try:
        algo, iter, salt, hash = row[fields.index('password')].split('$', 3)
    except:
        abort(404)

    return checkAppHash(password, salt, hash, iter)


def checkAppHash(password, salt, hash, iter=260000, algo='sha256', dklen=64):
    '''
    Checks the password against django's password hash
    dklen removed, not used/needed
    iter forced to integer, for some reason it was sticking as a str
    '''
    key = hashlib.pbkdf2_hmac(
        algo,
        password.encode(),
        salt.encode(),
        int(iter),
    )

    binhash = base64.urlsafe_b64decode(hash)

    if (binhash == key):
        return True
    else:
        return False
