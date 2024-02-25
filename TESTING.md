# log in

```
curl -ki -u ${client_id}:${client_secret} -X POST https://{oauth_server}/oauth/token -F grant_type=password -F username=${username} -F password=valid -F scope=profile
```

## result
```
HTTP/2 200 
server: nginx/1.22.0
date: Tue, 27 Sep 2022 13:05:39 GMT
content-type: application/json
content-length: 177
cache-control: no-store
pragma: no-cache
strict-transport-security: max-age=15552000; includeSubDomains

{"access_token": "3OpQTaFTcfzGI8XUEpKBu6hkQJYtwuUH9dmO67TIZI", "expires_in": 864000, "refresh_token": "5fks6JFVAoVvc9qVymBaMbppYmyxY56xPGj08Ct2MgCYCOng", "token_type": "Bearer"}
```

## Alternative for authorization code

```
    curl -u ${client_id}:${client_secret} -X POST https://${oauth_server}/oauth/token -F grant_type=authorization_code -F scope=profile -F code=${code}
```

# use it to get /api/v4/user

```
    curl -ki -H "Authorization: Bearer 3OpQTaFTcfzGI8XUEpKBu6hkQJYtwuUH9dmO67TIZI" https://${oauth_server}/api/v4/user
```