import os
os.environ["AUTHLIB_INSECURE_TRANSPORT"] = "1"

from website.app import create_app


app = create_app({
    'SECRET_KEY': 'secret',
    'OAUTH2_REFRESH_TOKEN_GENERATOR': True,
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'SQLALCHEMY_DATABASE_URI': 'mysql+mysqlconnector://oauth:password@testcloud.lan/oauth2?collation=utf8mb4_general_ci&charset=utf8mb4',
})
