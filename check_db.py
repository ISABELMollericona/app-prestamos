import os
from dotenv import load_dotenv
load_dotenv()
print(f'ENV URI: {os.getenv("SQLALCHEMY_DATABASE_URI")}')

from app import create_app, db
app = create_app('development')
print(f'App URI: {app.config["SQLALCHEMY_DATABASE_URI"]}')
print(f'Instance path: {app.instance_path}')

import pathlib
db_path = pathlib.Path(app.instance_path) / 'test_prestamos.db'
print(f'DB file path: {db_path}')
print(f'DB file exists: {db_path.exists()}')
