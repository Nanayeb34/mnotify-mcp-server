import os
import requests
from dotenv import load_dotenv
import time
from typing import Optional


TIMEOUT = 30 
MAX_RETRIES = 3

load_dotenv()

base_url = 'https://api.mnotify.com/api'
message_endPoint = 'https://api.mnotify.com/api/template' # template list endpoint
group_endPoint = 'https://api.mnotify.com/api/group' # group list endpoint
contact_endPoint = 'https://api.mnotify.com/api/contact' # contact list endpoint
sms_endPoint = 'https://api.mnotify.com/api/sms' # sms list endpoint
schedule_sms_endPoint = 'https://api.mnotify.com/api/scheduled' # scheduled sms list endpoint
sender_id_endpoint = 'https://api.mnotify.com/api/senderid' # register sender id endpoint
sms_balance_endPoint = 'https://api.mnotify.com/api/balance/sms' # sms balance endpoint

def get_template_list():
    """
    Retrieve a list of all message templates from MNotify API.
    
    Returns:
        dict: JSON response with the following structure:
            - On success: {
                'status': 'success',
                'template_list': [
                    {
                        '_id': int,           # Template unique identifier
                        'title': str,         # Template title/name
                        'content': str,       # Template message content
                        'type': str           # Template type (e.g., 'Local SMS Template', 'Unknown Template Type')
                    },
                    ...
                ]
            }
            - On error: {
                'error': str                  # Error message describing what went wrong
            }
        
    Example:
        {
            'status': 'success',
            'template_list': [
                {
                    '_id': 34500,
                    'title': 'EASTER CONFERENCE 2025',
                    'content': 'EASTER @ EWC 2025\\n\\nThe most important time...',
                    'type': 'Local SMS Template'
                },
                {
                    '_id': 34650,
                    'title': 'Good friday message',
                    'content': 'EASTER @ EWC 2025\\n\\nOn behalf of our GLP...',
                    'type': 'Local SMS Template'
                }
            ]
        }
    """
    apiKey = os.getenv("MNOTIFY_API_KEY")
    url = message_endPoint + '?key=' + apiKey
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()
            return data
        except requests.exceptions.Timeout:
            if attempt == MAX_RETRIES - 1:
                return {"error": "Request timed out after multiple attempts"}
            time.sleep(1)
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

def get_message_template(template_id: str):
    """
    Retrieve details of a specific message template.
    
    Args:
        template_id (str): The unique identifier of the template
        
    Returns:
        dict: JSON response with the following structure:
            - On success: {
                'status': 'success',
                'template': 
                    {
                        '_id': int,           # Template unique identifier
                        'title': str,         # Template title/name
                        'content': str,       # Template message content
                        'type': str           # Template type (e.g., 'Local SMS Template', 'Unknown Template Type')
                    }
            }
            - On error: {
                'error': str                  # Error message describing what went wrong
            }
        Example:
            {
                'status': 'success',
                'template': 
                    {
                        '_id': 34500,
                        'title': 'EASTER CONFERENCE 2025',
                        'content': 'EASTER @ EWC 2025\\n\\nThe most important time...',
                        'type': 'Local SMS Template'
                    }
            }
    """
    apiKey = os.getenv("MNOTIFY_API_KEY")
    url = message_endPoint + '/' + template_id + '?key=' + apiKey
    response = requests.get(url)
    data = response.json()
    return data

def add_message_template(title: str, content: str):
    """
    Create a new message template.
    
    Args:
        title (str): The title of the template
        content (str): The content/body of the template
        
    Returns:
        dict: JSON response with the following structure:
            - On success: {
                'status': 'success',
                '_id': int,   # Created template unique identifier
            }
            - On error: {
                'error': str                  # Error message describing what went wrong
            }
        Example:
            {
                'status': 'success',
                '_id': 34500,
            }
    """
    apiKey = os.getenv("MNOTIFY_API_KEY")
    url = message_endPoint + '?key=' + apiKey
    response = requests.post(url, json={"title": title, "body": content})
    data = response.json()
    return data

def update_message_template(template_id: str, title: Optional[str] = None, content: Optional[str] = None):
    """
    Update an existing message template.
    
    Args:
        template_id (str): The unique identifier of the template to update
        title (str): The new title of the template
        content (str): The new content/body of the template
        
    Returns:
        dict: JSON response with the following structure:
            - On success: {
                'status': 'success',
                'message': 'Template updated',
            }
            - On error: {
                'error': str                  # Error message describing what went wrong
    """
    apiKey = os.getenv("MNOTIFY_API_KEY")
    url = message_endPoint + '/' + template_id + '?key=' + apiKey
    response = requests.put(url, json={"title": title, "body": content, "id": template_id})
    data = response.json()
    return data

def delete_message_template(template_id: str):  
    """
    Delete a message template.
    
    Args:
        template_id (str): The unique identifier of the template to delete
        
    Returns:
        dict: JSON response with the following structure:
            - On success: {
                'status': 'success',
                'message': 'template deleted successfully',
            }
            - On error: {
                'error': str                  # Error message describing what went wrong
    """
    apiKey = os.getenv("MNOTIFY_API_KEY")
    url = message_endPoint + '/' + template_id + '?key=' + apiKey
    response = requests.delete(url)
    data = response.json()
    return data

def get_group_list():
    """
    Retrieve a list of all contact groups from MNotify API.
    
    Returns:
        dict: JSON response containing the list of groups
        - On success: {
            'status': 'success',
            'group_list': [
                {
                    '_id': int,   # Group unique identifier
                    'group_name': str,   # Group name
                    'total_contacts': int,   # Total number of contacts in the group
                },
                ...
            ]
        }
        - On error: {
            'error': str                  # Error message describing what went wrong
        }
        Example:
            {
                'status': 'success',
                'group_list': [
                    {
                        '_id': 34500,
                        'group_name': 'EWC 2025',
                        'total_contacts': 100,
                    },
                    ...
                ]
            }
    """
    apiKey = os.getenv("MNOTIFY_API_KEY")
    url = group_endPoint + '?key=' + apiKey
    response = requests.get(url)
    data = response.json()
    return data

def get_group_details(group_id: str):
    """
    Retrieve details of a specific contact group.
    
    Args:
        group_id (str): The unique identifier of the group
        
    Returns:
        dict: JSON response containing the group details
        - On success: {
            'status': 'success',
            'group': {
                '_id': int,   # Group unique identifier
                'group_name': str,   # Group name
                'total_contacts': int,   # Total number of contacts in the group
            }
        }
        - On error: {
            'error': str                  # Error message describing what went wrong
        }
        Example:
            {
                'status': 'success',
                'group': {
                    '_id': 34500,
                    'group_name': 'EWC 2025',
                    'total_contacts': 100,
                }
    """
    apiKey = os.getenv("MNOTIFY_API_KEY")
    url = group_endPoint + '/' + group_id + '?key=' + apiKey
    response = requests.get(url)
    data = response.json()
    return data

def add_group(group_name: str):
    """
    Create a new contact group.
    
    Args:
        group_name (str): The name of the group to create
        
    Returns:
        dict: JSON response with the following structure:
            - On success: {
                'status': 'success',
                '_id': int,   # Created group unique identifier
            }
            - On error: {
                'error': str                  # Error message describing what went wrong
            }
        Example:
            {
                'status': 'success',
                '_id': 34500,
            }
    """ 
    apiKey = os.getenv("MNOTIFY_API_KEY")
    url = group_endPoint + '?key=' + apiKey
    response = requests.post(url, json={"name": group_name})
    data = response.json()
    return data

def update_group(group_id: str, group_name: str):
    """
    Update an existing contact group name.
    
    Args:
        group_id (str): The unique identifier of the group to update
        group_name (str): The name for the group
        
    Returns:
        dict: JSON response with the following structure:
            - On success: {
                'status': 'success',
                'message': 'group updated',
            }
            - On error: {
                'error': str                  # Error message describing what went wrong
            }
    """
    apiKey = os.getenv("MNOTIFY_API_KEY")
    url = group_endPoint + '/' + group_id + '?key=' + apiKey
    response = requests.put(url, json={"name": group_name})
    data = response.json()
    return data

def delete_group(group_id: str):
    """
    Delete a contact group.
    
    Args:
        group_id (str): The unique identifier of the group to delete
        
    Returns:
        dict: JSON response containing the deletion status
        - On success: {
            'status': 'success',
            'message': 'group deleted successfully',
        }
        - On error: {
            'error': str                  # Error message describing what went wrong
        }
    """
    apiKey = os.getenv("MNOTIFY_API_KEY")
    url = group_endPoint + '/' + group_id + '?key=' + apiKey
    response = requests.delete(url)
    data = response.json()
    return data

def get_contact_list():
    """
    Retrieve a list of all contacts from MNotify API.
    
    Returns:
        dict: JSON response with the following structure:
            - On success: {
                'status': 'success',
                'contacts_list': [
                    {
                        'id': int,              # Contact unique identifier
                        'firstname': str|None,  # Contact's first name (can be None)
                        'lastname': str|None,   # Contact's last name (can be None)
                        'phone': str,           # Contact's phone number
                        'email': str|None,      # Contact's email address (can be None)
                        'date_of_birth': str|None  # Contact's date of birth (can be None)
                    },
                    ...
                ],
                'pagination': {
                    'total': int,           # Total number of contacts
                    'per_page': int,        # Number of contacts per page
                    'current_page': int,    # Current page number
                    'last_page': int,       # Total number of pages
                    'from': int,            # Starting contact number on this page
                    'to': int               # Ending contact number on this page
                }
            }
            - On error: {
                'error': str                  # Error message describing what went wrong
            }
        
    Example:
        {
            'status': 'success',
            'contacts_list': [
                {
                    'id': 72556928,
                    'firstname': None,
                    'lastname': None,
                    'phone': '+233 24 314 9991',
                    'email': None,
                    'date_of_birth': None
                },
                {
                    'id': 72556929,
                    'firstname': None,
                    'lastname': None,
                    'phone': '+233 24 334 9779',
                    'email': None,
                    'date_of_birth': None
                }
            ],
            'pagination': {
                'total': 2478,
                'per_page': 10,
                'current_page': 1,
                'last_page': 248,
                'from': 1,
                'to': 10
            }
        }
    """
    apiKey = os.getenv("MNOTIFY_API_KEY")
    url = contact_endPoint + '?key=' + apiKey
    response = requests.get(url)
    data = response.json()
    return data

def get_contact_details(contact_id: str):
    """
    Retrieve details of a specific contact.
    
    Args:
        contact_id (str): The unique identifier of the contact
        
    Returns:
        dict: JSON response containing the contact details
        - On success: {
            'status': 'success',
            'contact': {
                '_id': int,             # Contact unique identifier
                'firstname': str|None,  # Contact's first name (can be None)
                'lastname': str|None,   # Contact's last name (can be None)
                'phone': str,           # Contact's phone number
                'email': str|None,      # Contact's email address (can be None)
                'dob': str|None  # Contact's date of birth (can be None)
            }
        }
        - On error: {
            'error': str                  # Error message describing what went wrong
    """
    apiKey = os.getenv("MNOTIFY_API_KEY")
    url = contact_endPoint + '/' + contact_id + '?key=' + apiKey
    response = requests.get(url)
    data = response.json()
    return data

def get_group_contacts(group_id: str):
    """
    Retrieve all contacts belonging to a specific group.
    
    Args:
        group_id (str): The unique identifier of the group
        
    Returns:
        dict: JSON response containing the list of contacts in the group
        - On success: {
            'status': 'success',
            'contacts_list': [
                {
                    'id': int,              # Contact unique identifier
                    'firstname': str|None,  # Contact's first name (can be None)
                    'lastname': str|None,   # Contact's last name (can be None)
                    'phone': str,           # Contact's phone number
                    'email': str|None,      # Contact's email address (can be None)
                    'date_of_birth': str|None  # Contact's date of birth (can be None)
                },
                ...
            ],
            'pagination': {
                'total': int,           # Total number of contacts
                'per_page': int,        # Number of contacts per page
                'current_page': int,    # Current page number
                'last_page': int,       # Total number of pages
                'from': int,            # Starting contact number on this page
                'to': int               # Ending contact number on this page
            }
        }
        - On error: {
            'error': str                  # Error message describing what went wrong
        }
    """
    apiKey = os.getenv("MNOTIFY_API_KEY")
    url = contact_endPoint + '/group/' + group_id + '?key=' + apiKey
    response = requests.get(url)
    data = response.json()
    return data

def add_contact(group_id: str,  phone: str, first_name: Optional[str] = None, last_name: Optional[str] = None, dob: Optional[str] = None, email: Optional[str] = None):
    """
    Add a new contact to a specific group.
    
    Args:
        first_name (str): The first name of the contact
        last_name (str): The last name of the contact
        phone (str): The phone number of the contact
        dob (str): The date of birth in YYYY-MM-DD format
        email (str): The email address of the contact
        group_id (str): The unique identifier of the group to add the contact to
        
    Returns:
        dict: JSON response containing the created contact details
        - On success: {
            'status': 'success',
            '_id': int,   #  unique identifier of the created contact
        }
        - On error: {
            'error': str                  # Error message describing what went wrong
        }
        - Example:
            {
                'status': 'success',
                '_id': 34500,
    """
    apiKey = os.getenv("MNOTIFY_API_KEY")
    url = contact_endPoint + '/' + group_id + '?key=' + apiKey
    response = requests.post(url, json={"firstname": first_name, "lastname": last_name, "phone": phone, "dob": dob, "email": email, "group_id": group_id})
    
    # Check if response is successful before trying to parse JSON
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Error: {response.status_code}")
        print(f"Response text: {response.text}")

def update_contact(contact_id: str, phone: str, first_name: Optional[str] = None, last_name: Optional[str] = None, dob: Optional[str] = None, email: Optional[str] = None, group_id: Optional[str] = None):
    """
    Update an existing contact's information.
    
    Args:
        contact_id (str): The unique identifier of the contact to update
        first_name (str): The updated first name of the contact
        last_name (str): The updated last name of the contact
        phone (str): The updated phone number of the contact
        dob (str): The updated date of birth in YYYY-MM-DD format
        email (str): The updated email address of the contact
        group_id (str): The unique identifier of the group the contact belongs to
        
    Returns:
        dict: JSON response containing the updated contact details
        - On success: {
            'status': 'success',
            '_id': int,   #  unique identifier of the updated contact
        }
        - On error: {
            'error': str                  # Error message describing what went wrong
        }
        - Example:
            {
                'status': 'success',
                '_id': 34500,
            }
    """
    apiKey = os.getenv("MNOTIFY_API_KEY")
    url = contact_endPoint + '/' + contact_id + '?key=' + apiKey
    response = requests.put(url, json={"firstname": first_name, "lastname": last_name, "phone": phone, "dob": dob, "email": email, "group_id": group_id})
    data = response.json()
    return data

def delete_contact(contact_id: str):
    """
    Delete a contact from the system.
    
    Args:
        contact_id (str): The unique identifier of the contact to delete
        
    Returns:
        dict: JSON response containing the deletion status (if successful)
        - On success: {
            'status': 'success',
            'message': 'contact deleted successfully',
        }
        - On error: {
            'error': str                  # Error message describing what went wrong
    """
    apiKey = os.getenv("MNOTIFY_API_KEY")
    url = contact_endPoint + '/' + contact_id + '?key=' + apiKey

    response = requests.delete(url)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Error: {response.status_code}")
        print(f"Response text: {response.text}")

def send_quick_bulk_sms(recipient: list, sender_id: str, message: str, schedule: Optional[bool] = False, schedule_time: Optional[str] = None):
    """
    Send bulk SMS to a list of phone numbers.
    
    Args:
        recipient (list): List of phone numbers to send SMS to
        sender_id (str): The registered sender ID
        message (str): The SMS message content. Must be 460 characters or less for single SMS
        schedule (bool): Whether to schedule the SMS for later
        schedule_time (str): The scheduled time in YYYY-MM-DD HH:MM format (if schedule is True)
        
    Returns:
        dict: JSON response containing the campaign details
        - On success if sent instantly: {
            'status': 'success',
            'code': 'str', # status code
            'message': 'messages sent successfully',
            'summary': {
            '_id': int,   #  campaign identifier of the sent SMS used to check the delivery report
            "message_id': str,   #  unique identifier of the sent SMS
            'type': str,   #  type of the sent SMS
            'total_sent': int,   #  total number of messages sent
            'contacts': int,   #  total number of contacts sent to
            'total_rejected': int,   #  total number of failed sent messages
            'numbers_sent': list,   #  list of phone numbers sent to
            'credit_used': int,   #  total credit used for the sent SMS
            'credit_left': int,   #  total credit left for the sent SMS
            }
        }
        - Example:
            {
                'status': 'success',
                'code': '2000',
                'message': 'messages sent successfully',
                'summary': {
                    '_id': 'CC7475AA-200A-499B-9874-5C45E8E32105',
                    'message_id': '20250815233545142039V2',
                    'type': 'API QUICK SMS',
                    'total_sent': 1,
                    'contacts': 1,
                    'total_rejected': 0,
                    'numbers_sent': ['0545142039'],
                    'credit_used': 1,
                    'credit_left': 7701
                }
            }
        - On success if scheduled: {
            'status': 'success',
            'code': 'str', # status code
            'message': 'messages scheduled successfully',
            'summary': {
                '_id': int,   #  campaign identifier of the sent SMS used to check the delivery report
                "message_id': str,   #  unique identifier of the sent SMS
                'type': str,   #  type of the sent SMS
                'total_sent': int,   #  total number of messages sent
                'contacts': int,   #  total number of contacts sent to
                'total_rejected': int,   #  total number of failed sent messages
            }
        }
        - Example:
            {
                'status': 'success',
                'code': '2000',
                'message': 'messages scheduled successfully',
                'summary': {
                    '_id': 'CC7475AA-200A-499B-9874-5C45E8E32105',
                    'message_id': '20250815233545142039V2',
                    'type': 'API QUICK SMS',
                    'total_sent': 1,
                    'contacts': 1,
                    'total_rejected': 0,
                }
        - On error: {
            'error': str                  # Error message describing what went wrong
        }
    """
    apiKey = os.getenv("MNOTIFY_API_KEY")
    url = sms_endPoint + '/quick/' + '?key=' + apiKey
    response = requests.post(url, json={"recipient": recipient, "sender": sender_id, "message": message, "is_schedule": schedule, "schedule_date": schedule_time})
    data = response.json()
    return data

def send_bulk_group_sms(group_id: list, sender_id: str, message: str, schedule: Optional[bool] = False, schedule_time: Optional[str] = None):
    """
    Send bulk SMS to contacts in specified groups.
    
    Args:
        group_id (list): List of group IDs to send SMS to
        sender_id (str): The registered sender ID
        message (str): The SMS message content. Must be 460 characters or less for single SMS
        schedule (bool): Whether to schedule the SMS for later
        schedule_time (str): The scheduled time in YYYY-MM-DD HH:MM format (if schedule is True)
        
    Returns:
        dict: JSON response containing the campaign details
        - On success if sent instantly: {
            'status': 'success',
            'code': 'str', # status code
            'message': 'messages sent successfully',
            'summary': {
                '_id': int,   #  unique campaign identifier of the sent SMS used to check the delivery report
                "message_id': str,   #  unique message id of the sent SMS
                'type': str,   #  type of the sent SMS
                'total_sent': int,   #  total number of messages sent
                'contacts': int,   #  total number of contacts sent to
                'total_rejected': int,   #  total number of failed sent messages
            }
        }
        - Example:
            {
                'status': 'success',
                'code': '2000',
                'message': 'messages sent successfully',
                'summary': {
                    '_id': 'CC7475AA-200A-499B-9874-5C45E8E32105',
                    'message_id': '20250815233545142039V2',
                    'type': 'API GROUP SMS',
                    'total_sent': 1,
                    'contacts': 1,
                    'total_rejected': 0,
                }
            }
        - On success if scheduled: {
            'status': 'success',
            'code': 'str', # status code
            'message': 'messages scheduled successfully',
            'summary': {
                '_id': int,   # unique campaign identifier of the sent SMS used to check the delivery report
                "message_id': str,   # message id of the sent SMS
                'type': str,   #  type of the sent SMS
                'total_sent': int,   #  total number of messages sent
                'contacts': int,   #  total number of contacts sent to
                'total_rejected': int,   #  total number of failed sent messages
                    }
                }
        - Example:
            {
                'status': 'success',
                'code': '2000',
                'message': 'messages scheduled successfully',
                'summary': {
                    '_id': 'CC7475AA-200A-499B-9874-5C45E8E32105',
                    'message_id': '20250815233545142039V2',
                    'type': 'API GROUP SMS',
                    'total_sent': 1,
                    'contacts': 1,
                    'total_rejected': 0,
                    'numbers_sent': ['0545142039'],
                    'credit_used': 1,
                    'credit_left': 7701
                }
                
    """
    apiKey = os.getenv("MNOTIFY_API_KEY")
    url = sms_endPoint + '/group/' + '?key=' + apiKey
    response = requests.post(url, json={"group_id": group_id, "sender": sender_id, "message": message, "is_schedule": schedule, "schedule_date": schedule_time}) #YYYY-MM-DD hh:mm
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Error: {response.status_code}")
        print(f"Response text: {response.text}")
    
def check_scheduled_sms():
    """
    Retrieve the history of all scheduled SMS campaigns.
    
    Returns:
        dict: JSON response containing the list of scheduled SMS campaigns
        - On success: {
            'status': 'success',
            'code': 'str', # status code
            'message': 'Data results found',
            'summary': [
                {
                    '_id': str,   #  unique identifier of the campaign that can be used to update the campaign
                    'campaign_name': str,   #  name of the campaign
                    'message': str,   #  message of the campaign
                    'sender_id': str,   #  sender ID of the campaign
                    'date_time': str,   #  date and time of the campaign
                    'campaign_charge': str,   #  cost of campaign 
                    'total_recipients': int,   #  total number of recipients
                    'campaign_id': str,   # identifier of the campaign
                    'status': str,   #  status of the campaign
                }
            ]
        }
        - On error: {
            'error': str                  # Error message describing what went wrong
        }
        - Example:  
            {
                'status': 'success',
                'code': '2000',
                'message': 'Data results found',
                'summary': [
                    {
                        '_id': '120950',
                        'campaign_name': 'Scheduled-API_V2-2025-08-15',
                        'message': 'This is a test message',
                        'sender_id': 'MNOTIFY',
                        'date_time': '2025-08-15 21:00',
                        'campaign_charge': '1',
                        'total_recipients': 1,
                        'campaign_id': '20250815233545142039V2',
                        'status': 'scheduled'
                    },
                    {
                        '_id': '120949',
                        'campaign_name': 'Scheduled-API_V2-2025-07-26',
                        'message': 'This was a test message',
                        'sender_id': 'MNOTIFY',
                        'date_time': '2025-08-14 21:00',
                        'campaign_charge': '1',
                        'total_recipients': 1,
                        'campaign_id': '20250815233545142039V2',
                        'status': 'completed'
                    }
                ]
            }
    """
    apiKey = os.getenv("MNOTIFY_API_KEY")
    url = schedule_sms_endPoint + '?key=' + apiKey
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Error: {response.status_code}")
        print(f"Response text: {response.text}")

def update_scheduled_sms(_id: str, sender_id: str, schedule_time: str, message: Optional[str] = None):
    """
    Update a scheduled SMS campaign.
    
    Args:
        _id (str): The unique identifier of the campaign to update
        sender_id (str): The updated sender ID
        schedule_time (str): The updated scheduled time in YYYY-MM-DD HH:MM format
        message (str): The updated SMS message content (optional)
        
    Returns:
        dict: JSON response containing the updated campaign details
        - On success: {
            'status': 'success',
            'code': 'str', # status code
            'message': 'scheduled message updated',
            'summary': {
                '_id': str,   #  unique identifier of the campaign that can be used to update the campaign
                'campaign_name': str,   #  name of the campaign
                'message': str,   #  message of the campaign
                'sender_id': str,   #  sender ID of the campaign
                'date_time': str,   #  date and time of the campaign
                'campaign_charge': str,   #  cost of campaign 
                'total_recipients': int,   #  total number of recipients
                'campaign_id': str,   # identifier of the campaign
                'status': str,   #  status of the campaign
            }
        }
        - On error: {
            'error': str                  # Error message describing what went wrong
        }
        - Example:  
            {
                'status': 'success',
                'code': '2000',
                'message': 'scheduled message updated',
                'summary': {
                    '_id': '120950',
                    'campaign_name': 'Scheduled-API_V2-2025-08-15',
                    'message': 'updated message',
                    'sender_id': 'EWCFaithCom',
                    'date_time': '2025-08-15 21:10',
                    'campaign_charge': '1',
                    'total_recipients': 1,
                    'campaign_id': '20250815233545142039V2',
                    'status': 'pending'
                }
            }
    """
    apiKey = os.getenv("MNOTIFY_API_KEY")
    url = schedule_sms_endPoint + '/' + _id + '?key=' + apiKey
    response = requests.put(url, json={"sender": sender_id, "schedule_date": schedule_time, "message": message})
    data = response.json()
    return data

def register_sender_id(sender_id: str, purpose: str):
    """
    Register a new sender ID for SMS sending.
    
    Args:
        sender_id (str): The sender ID to register (maximum 11 characters)
        purpose (str): The purpose for which the sender ID will be used
        
    Returns:
        dict: JSON response containing the registration status
        - On success: {
            'status': 'success',
            'code': 'str', # status code
            'message': 'sender ID Successfully Registered.',
            'summary': {
                'sender_name': str,   #  registered sender ID
                'purpose': str,   #  purpose for which the sender ID will be used
                'status': str,   #  status of the sender ID
            }
        }
        - On error: {
            'error': str                  # Error message describing what went wrong
        }
        - Example:
            {
                'status': 'success',
                'code': '2000',
                'message': 'sender ID Successfully Registered.',
                'summary': {
                    'sender_name': 'Mnotify',
    """
    apiKey = os.getenv("MNOTIFY_API_KEY")
    url = sender_id_endpoint + '/register/' + '?key=' + apiKey
    response = requests.post(url, json={"sender_name": sender_id, "purpose": purpose})
    data = response.json()
    return data

def check_sender_id(sender_id: str):
    """
    Check the status of a registered sender ID.
    
    Args:
        sender_id (str): The sender ID to check the status for
        
    Returns:
        dict: JSON response containing the sender ID status
        - On success: {
            'status': 'success',
            'code': 'str', # status code
            'summary': {
                '_id': str,   #  unique identifier of the sender ID
                'sender_name': str,   #  registered sender ID
                'purpose': str,   #  purpose for which the sender ID will be used
                'status': str,   #  status of the sender ID
            }
        }
        - On error: {
            'error': str                  # Error message describing what went wrong
        }
        - Example:
            {
                'status': 'success',
                'code': '2000',
                'summary': {
                    '_id': '86351',
                    'sender_name': 'Mnotify',
                    'purpose': 'to send newsletters',
                    'status': 'active'
                }
            }
    """
    apiKey = os.getenv("MNOTIFY_API_KEY")
    url = sender_id_endpoint + '/status/' +  '?key=' + apiKey
    response = requests.post(url,json={"sender_name": sender_id})
    data = response.json()
    return data

def check_sms_balance():
    """
    Check the current SMS balance in your MNotify account.
    
    Returns:
        dict: JSON response containing the SMS balance information
        - On success: {
            'status': 'success',
            'wallet': str, # money in wallet account
            'balance': int, # current SMS balance
            'bonus': int, # bonus SMS balance
            }
        - On error: {
            'error': str                  # Error message describing what went wrong
        }
        - Example:
            {
                'status': 'success',
                'wallet': '0',
                'balance': 1000,
                'bonus': 1000
            }
    """
    apiKey = os.getenv("MNOTIFY_API_KEY")
    url = sms_balance_endPoint + '?key=' + apiKey
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()
            return data
        except requests.exceptions.Timeout:
            if attempt == MAX_RETRIES - 1:
                return {"error": "SMS balance check timed out. Please check your internet connection."}
            time.sleep(1)
        except requests.exceptions.RequestException as e:
            return {"error": f"SMS balance check failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error checking SMS balance: {str(e)}"}

def sms_delivery_report(_id: str):
    """
    Get delivery report for a specific SMS campaign.
    
    Args:
        _id (str): The unique identifier of the sms that was sent
        
    Returns:
        dict: JSON response containing the delivery report for the campaign
        - On success: {
            'status': 'success',
            'report': {[
                '_id': int,   #  
                'recipient': str,   #  unique identifier of the sent SMS
                'message': str,   #  message of the sent SMS
                'status': str,   #  status of the sent SMS
                'date_sent': str,   #  date and time of the sent SMS
                'campaign_id': str,   #  sender ID of the sent SMS
                'message_id': str,   #  campaign identifier of the sent SMS
                'retries': int,   #  number of retries
                ]}
        }
        - On error: {
            'error': str                  # Error message describing what went wrong
        }
        - Example:
            {
                'status': 'success',
                'report': [
                    {
                        '_id': 787239792,
                        'recipient': '0545142039',
                        'message': 'This is a test message',
                        'status': 'DELIVERED',
                        'date_sent': '2025-08-15 21:50:53',
                        'campaign_id': 'CC7475AA-200A-499B-9874-5C45E8E32105',
                        'message_id': '20250815233545142039V2',
                        'retries': 0
                    }
                ]
    """
    apiKey = os.getenv("MNOTIFY_API_KEY")
    url = base_url + '/campaign/' + _id + '?key=' + apiKey
    response = requests.get(url)
    data = response.json()
    return data

def specific_sms_delivery_report(campaign_id: str):
    """
    Get delivery status for a specific SMS message.
    
    Args:
        campaign_id (str): The campaign identifier of the specific message from the delivery report
        
    Returns:
        dict: JSON response containing the delivery status of the message
        - On success: {
            'status': 'success',
            'report': {
                '_id': str,   #  unique identifier of the sent SMS
                'recipient': str,   #  recipient of the sent SMS
                'message': str,   #  message of the sent SMS
                'sender': str,   #  sender ID of the sent SMS
                'status': str,   #  status of the sent SMS
                'date_sent': str,   #  date and time of the sent SMS
                'campaign_id': str,   #  campaign identifier of the sent SMS
                'message_id': str,   #  unique identifier of the sent SMS
                'retries': int,   #  number of retries
            }
        }
        - On error: {
            'error': str                  # Error message describing what went wrong
        }
        - Example:
            {
                'status': 'success',
                'report': {
                    '_id': '787239792',
                    'recipient': '0545142039',
                    'message': 'This is a test message',
                    'sender': 'MNOTIFY',
                    'status': 'DELIVERED',
                    'date_sent': '2025-08-15 21:50:53',
                    'campaign_id': 'CC7475AA-200A-499B-9874-5C45E8E32105',
                    'message_id': '20250815233545142039V2',
                    'retries': 0
                }
            }
    """
    apiKey = os.getenv("MNOTIFY_API_KEY")
    url = base_url + '/status/' + campaign_id + '?key=' + apiKey
    response = requests.get(url)
    data = response.json()
    return data

def periodic_sms_delivery_report(from_date: str, to_date: str):
    """
    Get delivery reports for SMS campaigns within a specific date range.
    
    Args:
        from_date (str): Start date in YYYY-MM-DD format
        to_date (str): End date in YYYY-MM-DD format
        
    Returns:
        dict: JSON response containing the delivery reports for the specified period
        - On success: {
            'status': 'success',
            'report': [{
                '_id': int,   #  unique identifier of the sent SMS
                'recipient': str,   #  recipient of the sent SMS
                'message': str,   #  message of the sent SMS
                'sender': str,   #  sender ID of the sent SMS
                'status': str,   #  status of the sent SMS
                'date_sent': str,   #  date and time of the sent SMS
                'campaign_id': str,   #  campaign identifier of the sent SMS
                'message_id': str,   #  unique identifier of the sent SMS
                'retries': int,   #  number of retries
            }],
            'pagination': {
                'total': int,   #  total number of SMS sent
                'per_page': int,   #  number of SMS per page
                'current_page': int,   #  current page number
                'last_page': int,   #  total number of pages
            }
        }
        - On error: {
            'error': str                  # Error message describing what went wrong
        }
    """
    apiKey = os.getenv("MNOTIFY_API_KEY")
    url = base_url + '/report/' + '?key=' + apiKey  
    response = requests.get(url, json={"from": from_date, "to": to_date}) #dates are YYYY-MM-DD
    data = response.json()
    return data

# Validation functions for robust error handling
def validate_sms_request(message: str, recipients=None, groups=None):
    """
    Validate SMS request parameters before sending.
    
    Args:
        message (str): The SMS message content
        recipients (list, optional): List of phone numbers
        groups (list, optional): List of group IDs
        
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not message or not message.strip():
        return False, "Message content is required and cannot be empty"
    
    if len(message) > 460:
        return False, f"Message is too long ({len(message)} characters). SMS messages should be 160 characters or less for single SMS"
    
    if not recipients and not groups:
        return False, "Please specify either phone numbers or groups to send the message to"
    
    if recipients and not isinstance(recipients, list):
        return False, "Recipients must be provided as a list of phone numbers"
    
    if groups and not isinstance(groups, list):
        return False, "Groups must be provided as a list of group IDs"
    
    return True, None

def validate_contact_data(first_name: str, last_name: str, phone: str, email: str = ""):
    """
    Validate contact information before adding/updating.
    
    Args:
        first_name (str): Contact's first name
        last_name (str): Contact's last name  
        phone (str): Contact's phone number
        email (str, optional): Contact's email address
        
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not first_name or not first_name.strip():
        return False, "First name is required"
    
    if not last_name or not last_name.strip():
        return False, "Last name is required"
    
    if not phone or not phone.strip():
        return False, "Phone number is required"
    
    # Basic phone number validation (digits and common formatting)
    import re
    phone_clean = re.sub(r'[^\d+]', '', phone)
    if len(phone_clean) < 10:
        return False, "Phone number appears to be too short"
    
    # Basic email validation if provided
    if email and email.strip():
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email.strip()):
            return False, "Invalid email address format"
    
    return True, None

def safe_api_call(func, *args, **kwargs):
    """
    Wrapper for API calls with enhanced error handling.
    
    Args:
        func: The API function to call
        *args: Arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        dict: Result with success/error status
    """
    try:
        result = func(*args, **kwargs)
        
        # Check if result indicates an error
        if isinstance(result, dict):
            if result.get('status') == 'error' or 'error' in result:
                return {
                    'success': False,
                    'error': result.get('error', 'API returned error status'),
                    'data': result
                }
            else:
                return {
                    'success': True,
                    'data': result
                }
        else:
            return {
                'success': True,
                'data': result
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f"API call failed: {str(e)}",
            'data': None
        }


# To DO:
# 1. Add a function to get number of sent sms, submitted and pending sms

