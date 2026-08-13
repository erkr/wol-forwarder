# Post WebHooks to Home Assistant
import os
import requests
import logging

# Configure logging (the main module configures root logging; keep this basic)
logger = logging.getLogger(__name__)

def send_ha_webhook(webhook_id, payload_data):
    if not webhook_id:
        logging.debug("Webhook posting not configured")
        return
  
    # Fetch the supervisor token automatically provided to the add-on container
    supervisor_token = os.environ.get("SUPERVISOR_TOKEN", None)
    # Alternative is a specified URL
    homeassistant_api_url = os.environ.get("HA_API_URL", '')
    if homeassistant_api_url:
        # Default is overruled by some (External) URL, only supported without authorization
        url = f"{homeassistant_api_url}/webhook/{webhook_id}"
        headers = {
             "Content-Type": "application/json"
        }
    elif supervisor_token:
        # Internal API URL for Home Assistant endpoints
        url = f"http://supervisor/core/api/webhook/{webhook_id}"
        headers = {
            "Authorization": f"Bearer {supervisor_token}",
            "Content-Type": "application/json"
        }
    else:
        logging.error("Failed to retrieve HA API address for posting WebHooks")
        return
       
    try:
        response = requests.post(url, json=payload_data, headers=headers)
        if response.status_code in [200, 201]:
            logging.debug("Webhook posted successfully!")
        else:
            logging.error("Failed to send webhook to [%s]. Status code: %s", url, response.status_code)
            logging.error("Error details: %s", response.text)
    except requests.exceptions.RequestException as e:
        logging.error("An error occurred: %s", e)


