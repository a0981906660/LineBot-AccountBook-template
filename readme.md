# Description

This is an account book app based on LineBot.

# Structure

```bash
.
├── AccountBook.py
├── Procfile
├── app.py
├── clock.py
├── config.py
├── credentials
│   └── gs_credentials.json
├── readme.md
├── requirements.txt
├── runtime.txt
└── tools.py
```


## Example of configuration files

```python
# config.py

from google.oauth2.service_account import Credentials
# line-bot
channel_access_token = "YOUR_LINEBOT_CHANNEL_ACCESS_TOKEN"
channel_secret = "YOUR_LINEBOT_CHANNEL_SECRET"

# exchange rate api
# "https://v6.exchangerate-api.com/v6/"
exchange_rate_API_key = "API_KEY"
```


```json
// gs_credentials.json
{
  "type": "",
  "project_id": "",
  "private_key_id": "",
  "private_key": "",
  "client_email": "",
  "client_id": "",
  "auth_uri": "",
  "token_uri": "",
  "auth_provider_x509_cert_url": "",
  "client_x509_cert_url": ""
}
```