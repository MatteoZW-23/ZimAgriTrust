import secrets

secret_key = secrets.token_hex(32)
refresh_secret = secrets.token_hex(32)
bootstrap_token = secrets.token_urlsafe(32)

env_content = f'''APP_NAME="Agri Trust Marketplace API"
DATABASE_URL="postgresql+psycopg2://agritrust:devpassword123@localhost:5432/zimagritrust"
REDIS_URL="redis://localhost:6379/0"
SECRET_KEY="{secret_key}"
REFRESH_SECRET_KEY="{refresh_secret}"
CORS_ORIGINS="*"
ALLOWED_HOSTS="*"
FORCE_HTTPS=False
ADMIN_BOOTSTRAP_TOKEN="{bootstrap_token}"
'''

with open('backend/.env', 'w') as f:
    f.write(env_content)
print('Updated backend/.env successfully')
