import time
import json

from flask import Blueprint, request, session, url_for, abort, render_template, redirect

from werkzeug.security import gen_salt

from .models import db, User, OAuth2Client, OAuth2Token
from .oauth2 import authorization
from .userdb import gitlab_get_user, get_userdb_entry

route = Blueprint('home', __name__)


def current_user():
    if 'id' in session:
        uid = session['id']
        return User.query.get(uid)
    return None


def split_by_crlf(s):
    return [v for v in s.splitlines() if v]


@route.route('/', methods=('GET', 'POST'))
def home():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        otp = request.form.get('otp')

        '''
        first, check that the given (userdb) otp + password is correct
        if so, create an (oauth) user
        otherwise, not authorized
        '''

        # given it's time sensitive, check OTP first
        if not User.check_otp(username, otp):
            abort(401)

        if User.check_password(username, password):
            u = get_userdb_entry(username)
            uid = u.row[u.fields.index('id')]

            user = User.query.filter_by(id=uid).first()
            if not user:
                user = User(id=uid)
                db.session.add(user)
                db.session.commit()
            session['id'] = user.id
        else:
            abort(401)
        
        # if user is trying to authorize themselves and needs to head back to the auth page, then redirect
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect('/')
    
    # otherwise we're in GET
    user = current_user()
    if user:
        clients = OAuth2Client.query.filter_by(user_id=user.id).all()
    else:
        clients = []
    
    return render_template('home.html', user=user, clients=clients)


@route.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@route.route('/create_client', methods=('GET', 'POST'))
def create_client():
    user = current_user()
    if not user:
        return redirect('/')

    # if we're not a superuser, access denied
    if not user.superuser:
        abort(401)

    # not currently used, but also send user to template
    if request.method == 'GET':
        return render_template('create_client.html', user=user)

    # else we're in POST
    client_id = gen_salt(24)
    client_id_issued_at = int(time.time())
    client = OAuth2Client(
        client_id=client_id,
        client_id_issued_at=client_id_issued_at,
        user_id=user.id,
    )

    form = request.form
    client_metadata = {
        "client_name": form["client_name"],
        "client_uri": form["client_uri"],
        "grant_types": split_by_crlf(form["grant_type"]),
        "redirect_uris": split_by_crlf(form["redirect_uri"]),
        "response_types": split_by_crlf(form["response_type"]),
        "scope": form["scope"],
        "token_endpoint_auth_method": form["token_endpoint_auth_method"]
    }
    client.set_client_metadata(client_metadata)

    if form['token_endpoint_auth_method'] == 'none':
        client.client_secret = ''
    else:
        client.client_secret = gen_salt(48)

    db.session.add(client)
    db.session.commit()

    return redirect('/')


@route.route('/oauth/authorize', methods=['GET', 'POST'])
def authorize():
    user = current_user()

    # if user is not logged in, do so first
    if not user:
        return redirect(url_for('home.home', next=request.url))

    # logged in? good. continue GET
    if request.method == 'GET':
        return render_template('authorize.html', user=user)

    # else we're in POST
    confirm = request.form.get('confirm', default = 'denied')

    if 'confirm' in confirm:
        grant_user = user
    else:
        grant_user = None
    
    return authorization.create_authorization_response(grant_user=grant_user)


@route.route('/oauth/token', methods=['POST'])
def issue_token():
    return authorization.create_token_response()


@route.route('/oauth/revoke', methods=['POST'])
def revoke_token():
    return authorization.create_endpoint_response('revocation')


@route.route('api/v4/user', methods=['GET'])
def gitlab_v4_user():
    auth_header = request.headers.get('Authorization')

    # got the header?
    if not auth_header:
        abort(401)

    # got the code?
    try:
        token_split = auth_header.split(' ')
        token_type = token_split[0]  # should be 'Bearer'
        token = token_split[1]
    except:
        abort(401)

    # found a matching token?
    try:
        token_user = OAuth2Token.query.filter_by(access_token=token).first()
    except Exception as e:
        abort(401)

    # found a (gitlab) user?
    user_id = token_user.user_id
    user = User.query.get(user_id)
    if not user:
        abort(401)

    # get the deets
    gitlab_user = gitlab_get_user(user)

    # override if we're an old token
    is_active = token_user.is_refresh_token_active()

    if is_active:
        return json.dumps(gitlab_user)
    else:
        gitlab_user['state'] = 'inactive'
        return json.dumps(gitlab_user)
