from __future__ import print_function

import datetime
from math import fabs
import os.path
from dateutil.relativedelta import relativedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']

calendarId_dict = {'User': 'i1mn18fuoqv9r0b8itrik8nkqc@group.calendar.google.com', 'Harry': '', 'Aaron': '', 'Blake': '', 'Myles': '', 'Bob': '', 'Marcos': 'mfespitialvarez@gmail.com'} # Preset Google Calendar IDs
emailId_dict = {'User': 'akarshaurora@gmail.com', 'Harry': '', 'Aaron': '', 'Blake': '', 'Myles': '', 'Bob': '', 'Marcos': 'mfespitiaalvarez@gmail.com'} # Preset Email IDs

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
    events_result = service.events().list(calendarId='i1mn18fuoqv9r0b8itrik8nkqc@group.calendar.google.com', timeMin=start, timeMax=end, timeZone='US/Eastern',
                                              maxResults=100, singleEvents=True,
                                              orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        return None

    event_times = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        event_times.append((create_dtobject(start), create_dtobject(end)))

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
        "timeMin": start,
        "timeMax": end,
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

def find_meeting_timeslot(meeting_contacts, duration, order=1, earliest_hour=9, latest_hour=17, dayofweek=None, date=None):
    """
    Find free timeslot for meeting between user and contact

    Parameters:
        contact (string): user response to meeting contact query
        duration (integer): meeting duration
        order (integer): nth available meeting
        earliest_hour (integer): earliest hour when meetings can start
        latest_hour (integer): latest hour when meetings can no longer start
        dayofweek (string): day of the week
        date (string): date (YYYY-MM-DD)

    Returns:
        availability (tuple): start datetime and end datetime of available timeslot
            Format: (start datetime Object, end datetime Object)
    """
    weekdays = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6}
	
    def date_for_weekday(day: int):
        today = datetime.date.today()
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

    def get_all_contact_meetings():
        unavailable = []
        contacts = calendarId_dict.keys()
        for contact in contacts:
            if contact in meeting_contacts:
                unavailable = unavailable + get_contact_meetings(contact, meeting_day_start, meeting_day_end)
        return unavailable 

    unavailable = get_user_meetings(meeting_day_start, meeting_day_end) + get_all_contact_meetings()
    unavailable.sort(key=lambda meeting: meeting[0])

    earliest_time = datetime.datetime.combine(meeting_date, datetime.time(earliest_hour, 0, 0))
    latest_time = datetime.datetime.combine(meeting_date, datetime.time(latest_hour, 0, 0))
    unavailable.insert(0, (meeting_day_start, earliest_time))
    unavailable.append((latest_time, meeting_day_end))

    available = []
    for i in range(0, len(unavailable)-1):
        current_slot = unavailable[i]
        next_slot = unavailable[i+1]
        time_difference = (next_slot[0] - current_slot[1]).total_seconds() / 60
        if time_difference >= duration and current_slot[1] >= earliest_time and current_slot[1] <= latest_time:
            for j in range(int(time_difference)//duration):
                available.append((current_slot[1] + datetime.timedelta(minutes=j*duration), current_slot[1] + datetime.timedelta(minutes=(j+1)*duration)))
    
    if len(available) >= order:
        return available[order-1]            
    return None

time = find_meeting_timeslot('Marcos', 60, order=1, earliest_hour=9, latest_hour=17, dayofweek='Tuesday', date=None)
print(time)

def quick_schedule(meeting_contacts, duration=60, order=1, earliest_hour=9, latest_hour=17):
    """
    Find free timeslot for meeting between user and contact
    Parameters:
        meeting_contacts (string): user response to meeting contact query
        duration (integer): meeting duration
        order (integer): nth available meeting
        earliest_hour (integer): earliest hour when meetings can start
        latest_hour (integer): latest hour when meetings cannot start
    Returns:
        availability (tuple): start datetime and end datetime of available timeslot
            Format: (start datetime Object, end datetime Object)
    """
    start = datetime.datetime.combine(datetime.date.today() + datetime.timedelta(days=1), datetime.time(0, 0, 0))
    end = start + datetime.timedelta(days=8)
    
    def get_all_contact_meetings():
        unavailable = []
        contacts = calendarId_dict.keys()
        for contact in contacts:
            if contact in meeting_contacts:
                unavailable = unavailable + get_contact_meetings(contact, start, end)
        return unavailable

    unavailable = get_user_meetings(start, end) + get_all_contact_meetings()
    unavailable.sort(key=lambda meeting: meeting[0])

    available = []
    for i in range(0, len(unavailable)-1):
        current_slot = unavailable[i]
        next_slot = unavailable[i+1]
        time_difference = (next_slot[0] - current_slot[1]).total_seconds() / 60
        if time_difference >= duration and current_slot[1].hour >= earliest_hour and current_slot[1].hour <= latest_hour:
            for j in range(int(time_difference)//duration):
                available.append((current_slot[1] + datetime.timedelta(minutes=j*duration), current_slot[1] + datetime.timedelta(minutes=(j+1)*duration)))
    
    if len(available) >= order:
        return available[order-1]            
    return None

time = quick_schedule('Marcos')
print(time)


def create_meeting(title, agenda, start, end, meeting_contacts):
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
    start = (start + datetime.timedelta(hours=5)).isoformat() + 'Z'
    end = (end + datetime.timedelta(hours=5)).isoformat() + 'Z'


    def build_email_list():
        email_list = []
        contacts = emailId_dict.keys()
        for contact in contacts:
            if contact in meeting_contacts:
                email_list.append({'email': emailId_dict[contact]})
        return email_list

    agenda_title = 'Agenda:'
    new_line = '\n'

    body = {
        'summary': title,
        'description': f"{agenda_title}{new_line}{agenda}",
        'start': {
        'dateTime': start,
        'timeZone': 'US/Eastern',
        },
        'end': {
        'dateTime': end,
        'timeZone': 'US/Eastern',
        },
        'attendees': build_email_list(),
        "conferenceData": {
        "createRequest": {
          "conferenceSolutionKey": {
            "type": "hangoutsMeet"
          },
          "requestId": "RandomString"
          }
        },
    }
    service.events().insert(calendarId=calendarId_dict['User'], body=body).execute()

    return None

# create_meeting('Test', 'Test Optimeet', time[0], time[1], 'Marcos')

def get_previous_meeting(contact):
    """
    Retrieves event ID of previous meeting with contact

    Parameters:
        contact (string): first name of contact
    
    Returns:
        eventId (string): Google calendar 
    """
    service = build('calendar', 'v3', credentials=get_credentials())
    now = datetime.datetime.now()
    then = now - relativedelta(months=1)
    then = then.isoformat() + 'Z'

    events_result = service.events().list(calendarId=calendarId_dict['User'], timeMin=then, timeZone='US/Eastern', q=emailId_dict[contact],
                                              maxResults=10, singleEvents=True,
                                              orderBy='startTime').execute()
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

    spacer = '###################################'
    optinotes_title = 'Optinotes:'
    new_line = '\n'

    event = service.events().get(calendarId=calendarId_dict['User'], eventId=eventId).execute()

    if optinotes_title in event['description']:
        event['description'] = f"{event['description']}{new_line}{optinotes}"
    else:
        event['description'] = f"{event['description']}{new_line}{new_line}{spacer}{new_line}{new_line}{optinotes_title}{new_line}{optinotes}"

    service.events().update(calendarId=calendarId_dict['User'], eventId=eventId, body=event).execute()

    return None

# add_optinotes(get_previous_meeting('Marcos'), 'this is adding optinotes')

def overwrite_optinotes(eventId, optinotes):
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

    spacer = '###################################\n'
    optinotes_title = 'Optinotes:'
    new_line = '\n'
    agenda = event['description'].split(spacer, 1)[0]
    event['description'] = f"{agenda}{spacer}{new_line}{optinotes_title}{new_line}{optinotes}"

    service.events().update(calendarId=calendarId_dict['User'], eventId=eventId, body=event).execute()

    return None

overwrite_optinotes(get_previous_meeting('Marcos'), 'this is overwriting optinotes')

def get_optinotes(eventId):
    """
    Retrieve stored optinotes for previous meeting with contact

    Parameters:
        eventId (string): Google Calendar event ID

    Returns:
        optinotes (string): user inputted meeting notes
    """
    service = build('calendar', 'v3', credentials=get_credentials())

    event = service.events().get(calendarId=calendarId_dict['User'], eventId=eventId).execute()
    optinotes = event['description'].split("Optinotes:", 1)[1]

    return optinotes

print(get_optinotes(get_previous_meeting('Marcos')))

def datetime_to_string(datetime_tuple):
    """
    Convert datetime object to tuple of strings

    Parameters:
        datetime_tuple (tuple): date and time
            Format: (start_datetime, end_datetime)

    Returns:
        datetime_str_tuple (tuple): date, start time, and end time strings
            Format: ("date", "start time", "end time")
    """
    start_datetime = datetime_tuple[0]
    end_datetime = datetime_tuple[1]

    datetime_str = start_datetime.strftime("%A, %B %d from %I:%M %p to ")
    datetime_str = datetime_str + end_datetime.strftime("%I:%M %p")

    return datetime_str

print(datetime_to_string(time))

# Server setup
# Separating agenda from optinotes
# Storing optinotes for nonexisting meetings
# Building 4 calendars