from __future__ import print_function

import datetime
from math import fabs
import os.path
import json
from dateutil.relativedelta import relativedelta

from difflib import get_close_matches
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

DATES = {
    'monday':0,
    'tuesday':1,
    'wednesday':2,
    'thursday':3,
    'friday':4,
    'saturday':5,
    'sunday':6
}

artificial_meetings = {
    
} # Stores mapping from 'name' to meeting notes

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']

calendarId_dict = {'User': 'i1mn18fuoqv9r0b8itrik8nkqc@group.calendar.google.com', 'Harry': 'huydai.gsmst@gmail.com', 'Blake': 'sk0evg955m95m7gqc3d12l6b0k@group.calendar.google.com', 'Myles': 'l08mvs6u6u5dln0vlc8nskjens@group.calendar.google.com', 'Marcos': 'mfespitialvarez@gmail.com'} # Preset Google Calendar IDs
emailId_dict = {'User': 'akarshaurora@gmail.com', 'Harry': 'fb4g6fcf0qnid4u6al21frlvec@group.calendar.google.com', 'Blake': 'firmestboy@gmail.com', 'Myles': 'mylesstapelberg@gmail.com', 'Marcos': 'mfespitiaalvarez@gmail.com'} # Preset Email IDs

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
    events_result = service.events().list(calendarId=calendarId_dict['User'], timeMin=start, timeMax=end, timeZone='US/Eastern',
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
    weekdays = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6}
	
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

    user_mtgs = get_user_meetings(meeting_day_start, meeting_day_end)
    if not user_mtgs:
        user_mtgs = []
    unavailable =  user_mtgs + get_all_contact_meetings()
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

#time = find_meeting_timeslot('Marcos', 60, order=1, earliest_hour=9, latest_hour=17, dayofweek='Tuesday', date=None)
#print(time)

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

#time = quick_schedule('Marcos')
#print(time)


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

def get_meeting(meetingID):
    """
    Get the meeting object corresponding with meetingID

    Parameters
        meetingID (str): ID of the meeting
    
    Returns:
        meeting (dict): Object representing the meeting
    """
    service = build('calendar', 'v3', credentials=get_credentials())
    event = service.events().get(calendarId=calendarId_dict['User'], eventId=meetingID).execute()
    return event


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

    if 'description' in event and optinotes_title in event['description']:
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
    if 'description' in event and "Optinotes:" in event['description']:
        optinotes = event['description'].split("Optinotes:", 1)[1]
    else:
        optinotes = ""
    return optinotes
    
## Helper misc functions

def get_closest_contact(contact):
    '''
    Given a contact name `contact`, try to find a known calendar user name 
    closest to that name (within reasonable margins).
    
    Otherwise, return the main user as the contact
    '''
    contact_set = set(calendarId_dict.keys())
    
    #In the case Voiceflow or the user misspoke the name, get
    #the name of contacts which we had a meeting with that sounded
    #closest to the provided name

    close_matches = get_close_matches(contact, contact_set) #By default, similarity cutoff is 0.6
    if not close_matches: 
        return 'User' #No previously known contact with that name. Returns ourself
    best_contact = close_matches[0]
    return best_contact
        
def get_artificial_notes(contact):
    '''
    Given a contact name `contact`, try to find the latest meeting notes with that 
    user from the artificial meetings list
    
    If no such user, return None
    ''' 
    if contact not in artificial_meetings:
        return None      
    return artificial_meetings[contact]

def store_artificial_notes(contact,notes,overwrite=True):
    if overwrite or contact not in artificial_meetings:
        artificial_meetings[contact] = notes
    else: 
        artificial_meetings[contact] = artificial_meetings[contact] + ". " + notes
        
## Helper date and time functions  
def get_date(dayofweek):
    '''
    Get the closest date that is on `dayofweek`. 
    
    Parameters:
        dayofweek (str): Day of week [0,7]
    
    Returns:
        nextDayOfWeek (DateTime Date): Day closest to today that is on `dayofweek`
            If today is also `dayofweek`, return today's date.
    '''
    today = datetime.datetime.today()
    daysUntilClosest = (dayofweek - today.weekday()) %  7
    nextDayOfWeek = today + datetime.timedelta(days=daysUntilClosest)
    return nextDayOfWeek.date()

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

def parseDate(day, reverse=False):
    '''
    Given day in text form, return corresponding integer
    in range [0,6]
    
    If reverse=True, then we convert from int back into text form
    ''' 
    if not reverse:
        lower_day = day.lower()
        return DATES[lower_day]

    inv_dates = {v: k for k, v in DATES.items()}
    print(inv_dates)
    return inv_dates[day]

def parseTime(time, reverse=False):
    '''
    Given time in text form, e.g. "HH:MM AM" or "HH:MM PM",
    return the corresponding DateTime.Time object
    for that time
    
    If reverse=True, then we convert from DateTime.Time back to string format
    ''' 
    if not reverse:
        time = datetime.datetime.strptime(time, "%I:%M %p")
        return time.time()
    return time.strftime("%I:%M %p")
 
def get_dt(date,time):
    '''
    Given a DateTime.Date object `date` and DateTime.Time object `time`,
    return the corresponding DateTime object
    '''
    return datetime.datetime.combine(date,time)

#TODO
# Server setup
# Separating agenda from optinotes
# Storing optinotes for nonexisting meetings
# Building 4 calendars

if __name__ == "__main__":
    pass
    start = datetime.datetime.now()
    end = start+datetime.timedelta(hours=1)
    #create_meeting("Meeting with Huy", "", start, end, "Aaron")
    meetingID = get_previous_meeting("Aaron")
    meeting = get_meeting(meetingID)
    print(meeting)
    print(meeting['start'])
    
    #print(get_closest_contact("Henry"))
    #print(get_dt(datetime.date(2011, 1, 1), datetime.time(10, 23)))
    #print(get_date(6))
    #print(datetime_to_string((datetime.datetime.now(),datetime.datetime.now())))
    
    #time = find_meeting_timeslot('Marcos', 60, order=1, earliest_hour=9, latest_hour=17, dayofweek='Tuesday', date=None)
    #print(time)
    #create_meeting('Test', 'Test Optimeet', time[0], time[1], 'Marcos')
    #add_optinotes(get_previous_meeting('Marcos'), 'hey my name is akarsh')
    #print(get_optinotes(get_previous_meeting('Marcos')))
    #print(datetime_to_string(time))