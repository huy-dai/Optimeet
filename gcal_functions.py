from __future__ import print_function

import datetime
import os.path
import pytz
from dateutil.relativedelta import relativedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

calendarId_dict = {'User': '', 'Harry': '', 'Aaron': '', 'Blake': '', 'Myles': '', 'Bob': ''} # Preset Google Calendar IDs
emailId_dict = {'User': '', 'Harry': '', 'Aaron': '', 'Blake': '', 'Myles': '', 'Bob': ''} # Preset Email IDs

def get_credentials():
    """
    Gets credentials to authenticate interaction with Google Calendar API
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds

def create_dtobject(dtstring):
    """
    Creates a datetime Object from a custom string

    Parameters:
        dtstring (string): string containing date and time

    Returns:
        dtCombined (datetime Object): datetime object containing specified time and date
    """
    dtstring = dtstring.replace('-05:00', '')
    dtstring = dtstring.split('T')
    dtDate = datetime.datetime(int(dtstring[0][0:4]), int(dtstring[0][5:7]), int(dtstring[0][8:10]))
    dtTime = datetime.time(int(dtstring[1][0:2]), int(dtstring[1][3:5]), int(dtstring[1][6:8]))
    dtCombined = datetime.datetime.combine(dtDate, dtTime)

    return dtCombined

def get_user_meetings(start, end):
    """
    Retrieve all user meetings between start and end time

    Parameters:
        start (datetime Object): query start time
        end (datetime Object): query end time

    Returns:
        event_times (list): list of event start and end datetime objects
            Format: [(start_datetime1, end_datetime1), (start_datetime2, end_datetime2)]
    """ 
    service = build('calendar', 'v3', credentials=get_credentials())
    start = start.isoformat() + 'Z'
    end = end.isoformat() + 'Z'

    # Execute events() query
    body = {
        "calendarId": calendarId_dict['User'],
        "timeMin": start,
        "timeMax": end,
        "timeZone": 'US/Eastern',
        "maxResults": 100,
        "singleEvents": True,
        "orderBy=": 'startTime'
    }
    events_result = service.events().list(body=body).execute()
    events = events_result.get('items', [])

    if not events:
        return None

    event_times = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        event_times.append(create_dtobject(start), create_dtobject(end))

    return event_times

def get_contact_meetings(contact, start, end):
    """
    Retrieve all contact meetings between start and end time

    Parameters:
        contact (string): first name of contact
        start (datetime Object): query start time
        end (datetime Object): query end time

    Returns:
        event_times (list): list of event start and end datetime objects
            Format: [(start_datetime1, end_datetime1), (start_datetime2, end_datetime2)]
    """ 
    service = build('calendar', 'v3', credentials=get_credentials())
    start = start.isoformat() + 'Z'
    end = end.isoformat() + 'Z'

    # Execute freebusy() query
    body = {
        "timeMin": start.isoformat(),
        "timeMax": end.isoformat(),
        "timeZone": 'US/Eastern',
        "items": [
            {
                "id": calendarId_dict[contact]
            }
        ]
    }
    events_result = service.freebusy().query(body=body).execute()
    events_dict = events_result[u'calendars']
    events = events_dict[calendarId_dict[contact]]['busy']

    event_times = []
    for event in events:
        start = event['start']
        end = event['end']
        event_times.append(create_dtobject(start), create_dtobject(end))

    return event_times

def find_meeting_timeslot(contact, duration, order=1, earliest_hour=9, latest_hour=17, dayofweek=None, date=None):
    """
    Find free timeslot for meeting between user and contact

    Parameters:
        contact (string): first name of contact
        dayofweek (string): day of the week
        date (string): date (YYYY-MM-DD)
        length (integer): meeting duration
        user_unavailability (list): list of datetime objects where user is busy
            Format: [(start_datetime1, end_datetime1), (start_datetime2, end_datetime2)]
        contact_unavailability (list): list of datetime objects where contact is busy
            Format: [(start_datetime1, end_datetime1), (start_datetime2, end_datetime2)]
        order (integer): nth available meeting
        earliest_hour (integer): earliest hour when meetings can start

    Returns:
        availability (tuple): start datetime and end datetime of available timeslot
            Format: (start datetime Object, end datetime Object)
    """
    weekdays = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6}
	
    def date_for_weekday(day: int):
        today = date.today()
        weekday = today.weekday()
        return today + datetime.timedelta(days=day - weekday)
    
    if dayofweek != None:
        meeting_date = date_for_weekday(weekdays[dayofweek])
    elif date != None:
        meeting_date = date
    else:
         return None
    
    meeting_day_start = datetime.datetime.combine(meeting_date, datetime.time(0, 0, 0))
    meeting_day_end = datetime.datetime.combine(meeting_date, datetime.time(23, 59, 59))

    unavailable = get_user_meetings(meeting_day_start, meeting_day_end) + get_contact_meetings(contact, meeting_day_start, meeting_day_end)
    unavailable.sort(key=lambda meeting: meeting[0])

    earliest_time = datetime.datetime.combine(meeting_date, datetime.time(earliest_hour, 0, 0))
    latest_time = datetime.datetime.combine(meeting_date, datetime.time(latest_hour, 0, 0))
    unavailable.insert((meeting_day_start, earliest_time))
    unavailable.insert((latest_time, meeting_day_end))

    available = []
    for i in range(0, len(unavailable)-1):
        current_slot = unavailable[i]
        next_slot = unavailable[i+1]
        time_difference = (next_slot[0] - current_slot[1]).total_seconds() / 60
        if time_difference >= duration and current_slot[1] >= earliest_time and current_slot <= latest_time:
            for j in range(time_difference//duration):
                available.append((current_slot[1] + datetime.timedelta(minutes=j*duration), current_slot[1] + datetime.timedelta(minutes=(j+1)*duration)))
    
    if len(available) >= order:
        return available[order-1]            
    return None

def create_meeting(title, agenda, start, end, contact):
    """
    Create Google Calendar meeting with contact

    Parameters:
        title (str): meeting title
        agenda (string):  meeting agenda set by user
        start (datetime Object): start time of meeting
        end (datetime Object): end time of meeting
        contact (string): first name of contact

    Returns:
        None
    """
    service = build('calendar', 'v3', credentials=get_credentials())
    start = start.isoformat() + 'Z'
    end = end.isoformat() + 'Z'

    body = {
        'summary': title,
        'description': agenda,
        'start': {
        'dateTime': start,
        'timeZone': 'US/Eastern',
        },
        'end': {
        'dateTime': end,
        'timeZone': 'US/Eastern',
        },
        'attendees': [
        {'email': emailId_dict[contact]},
        ],
        'conferenceData':{
        'createRequest':{ 'requestId': 'Sample123', 
                          'conferenceSolutionKey':{type: 'hangoutsMeet'}
            }
        }
    }
    service.events().insert(calendarId=calendarId_dict['User'], body=body).execute()

    return None

def get_previous_meeting(contact):
    """
    Retrieves event ID of previous meeting with contact

    Parameters:
        contact (string): first name of contact
    
    Returns:
        eventId (string): Google calendar 
    """
    service = build('calendar', 'v3', credentials=get_credentials())
    now = datetime.datetime.utcnow()
    then = now - relativedelta(months=1)
    then = then.isoformat() + 'Z'

    body = {
        "calendarId": calendarId_dict['User'],
        "timeMin": then,
        "timeZone": 'US/Eastern',
        "q": emailId_dict[contact],
        "maxResults": 100,
        "singleEvents": True,
        "orderBy=": 'startTime'
    }
    events_result = service.events().list(body=body).execute()
    events = events_result.get('items', [])
    eventId = events.pop()['id']

    return eventId

def add_optinotes(eventId, optinotes):
    """
    Store optinotes for previous meeting with contact

    Parameters:
        eventId (string): Google Calendar event ID
        optinotes (string): user inputted meeting notes

    Returns:
        None
    """
    service = build('calendar', 'v3', credentials=get_credentials())

    event = service.events().get(calendarId=calendarId_dict['User'], eventId=eventId).execute()
    event['summary'] = optinotes

    service.events().update(calendarId='primary', eventId=event['id'], body=event).execute()


def get_optinotes(eventId):
    """
    Retrieve stored optinotes for previous meeting with contact

    Parameters:
        eventId (string): Google Calendar event ID

    Returns:
        optinotes (string): user inputted meeting notes
    """
    service = build('calendar', 'v3', credentials=get_credentials())

    event = service.events().get(calendarId=calendarId_dict['User'], eventId='eventId').execute()
    optinotes = event['description']

    return optinotes