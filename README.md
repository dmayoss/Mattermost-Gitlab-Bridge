# Gitlab-Shaped OAuth 2.0 Provider

This is an OAuth 2.0 server using [Authlib](https://authlib.org/) written specifically to respond like Gitlab would.

The basic setup is shamelessly stolen from Authlib's example, which you can find below.

- Documentation: <https://docs.authlib.org/en/latest/flask/2/>
- Authlib Repo: <https://github.com/lepture/authlib>


## Basic Install

This is a ready to run server, you will just need to install all the dependencies first:

```bash
$ pip install -r requirements.txt
```

Set Flask and Authlib environment variables if necessary:

```bash
# disable check https (DO NOT SET THIS IN PRODUCTION)
$ export AUTHLIB_INSECURE_TRANSPORT=1
```

Create Database and run the development server:

- first, check your `userdb.ini` and `app.py` files for the settings you may need to adjust, then start it up.

```bash
$ flask run
```

Now, you can open your browser with `http://127.0.0.1:5000/`, login with any
name you want.

Before testing, you will need to create a client.


### Password flow example

Get your `client_id` and `client_secret` for testing. In this example, we
have enabled `password` grant types, let's try:

```bash
$ curl -u ${client_id}:${client_secret} -X POST http://127.0.0.1:5000/oauth/token -F grant_type=password -F username=${username} -F password=valid -F scope=profile
```

Because this is an example, every user's password is `valid`. Now you should be able to access `/api/me`:

```bash
$ curl -H "Authorization: Bearer ${access_token}" http://127.0.0.1:5000/api/me
```


### Authorization code flow example

To test the authorization code flow, you can just open this URL in your browser.
```bash
$ open http://127.0.0.1:5000/oauth/authorize?response_type=code&client_id=${client_id}&scope=profile
```

After granting the authorization, you should be redirected to `${redirect_uri}/?code=${code}`

Then your app can send the code to the authorization server to get an access token:

```bash
$ curl -u ${client_id}:${client_secret} -X POST http://127.0.0.1:5000/oauth/token -F grant_type=authorization_code -F scope=profile -F code=${code}
```

Now you can access `/api/me`:

```bash
$ curl -H "Authorization: Bearer ${access_token}" http://127.0.0.1:5000/api/me
```

**IMPORTANT**: To test implicit grant, you need to `token_endpoint_auth_method` to `none`.


## License

As this is a non-commercial, open-source project, this attempt at making a Flask-powered
Gitlab-Mattermost oauth login server is licensed under the BSD 2-Clause license.