#-------------------------------------------------------------------------------------------------------#
# Copyright (c) 2023 by <Company/Name>                                                                  #
#                                                                                                       #
# Licensed under the MIT License                                                                        #
#                                                                                                       #
#-------------------------------------------------------------------------------------------------------#
"""

config.py
Description:
Contains configuration settings for the application. This module centralizes settings such as database credentials, API keys, and other configuration parameters.

Content Overview:
Configuration Variables: Settings for the Flask app, database, and other services.
Environment Management: Different configurations for development, testing, and production environments.

"""

from dotenv import load_dotenv
import os
from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient
from twilio.rest import Client
from azure.storage.blob import BlobServiceClient

# Azure Key vault connections
load_dotenv()
client_ID=os.getenv('Azure_client_ID')
tenant_ID=os.getenv('Azure_tenant_ID')
client_secret=os.getenv('Azure_client_secret')
vault_url=os.getenv('Azure_vault')

credential = ClientSecretCredential(client_id=client_ID,
                                    client_secret=client_secret,
                                    tenant_id=tenant_ID)
secret_client = SecretClient(vault_url=vault_url, credential=credential)

# Twilio credentials
# secret_name = "twilioaccountsid1"
account_sid = secret_client.get_secret("twilioaccountsid1").value


# secret_name='twilioauthtoken'
auth_token = secret_client.get_secret('twilioauthtoken').value


app_secretkey=secret_client.get_secret("appsecretkey").value

init_AppConfig=secret_client.get_secret("initAppConfig").value

# Azure Blob Storage credentials
connect_str = secret_client.get_secret('connectstrblob').value
container_name = "opengovchatbot"

client = Client(account_sid, auth_token)
blob_service_client = BlobServiceClient.from_connection_string(connect_str)


# MySQL database credentials
config = {
    'host': secret_client.get_secret('dburl').value,
    'user': secret_client.get_secret('dbuser').value,
    'password': secret_client.get_secret('dbpassword').value,
    'database': 'ogapp'
    }

# Twilio credentials
twilio_number = '+13202722061'

# Dev URL
# ngrok_url = 'https://a2f5-2401-4900-1cb9-157a-c92e-88b7-cf52-b03.ngrok-free.app'

# PROD URL
ProdURL = secret_client.get_secret('ProdURL').value
ngrok_url = ProdURL

# Voice change string
voice_change = "Polly.Aditi"

# Dev tables to handle the buckets
registration_table="callbot_event_registration"

# PROD tables to handle the buckets
# registration_table="callbot_event_registration_PROD"

# Dev tables to handle the buckets
table1="callbot_response_callback"
table2="callbot_response_accepted"
table3="callbot_response_accepted_pickupdrop"
table4="callbot_response_declined_pickupdrop"
table5="callbot_response_invalidoptioninput"
table6="callbot_response_noanswer"
table7="callbot_reminder_status"

# PROD tables to handle the buckets
# table1="callbot_response_callback_PROD"
# table2="callbot_response_accepted_PROD"
# table3="callbot_response_accepted_pickupdrop_PROD"
# table4="callbot_response_declined_pickupdrop_PROD"
# table5="callbot_response_invalidoptioninput_PROD"
# table6="callbot_response_noanswer_PROD"
# table7="callbot_reminder_status_PROD"
