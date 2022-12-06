from difflib import get_close_matches, SequenceMatcher

DATES = {
    'monday':1,
    'tuesday':2,
    'wednesday':3,
    'thursday':4,
    'friday':5,
    'saturday':6,
    'sunday':7
}

class Calendar:
    def __init__(self):
        '''
        Initializes a calendar consisting of meetings
        '''
        self.meetings = []
    
    def find_time_slot(self, dayofweek, length, order=1, earliest_hour=8):
        '''
        Find free time slot in Calendar for day `dayofweek`
        for `length` number of minutes given that the earliest hour 
        we want to meet is `earliest_hour` and that we want to get
        the `order`_th open time slot of the day
        
        Returns (start,end) if time slot found, None otherwise
        '''
        # Get meetings on that day that are after earliest_hour 
        available = [m.get_time_tuple() for m in self.meetings if m.day == dayofweek and m.start >= 60*earliest_hour]
        available.sort(key=lambda m: m[0])
        available.insert(0,(60*earliest_hour,60*earliest_hour)) #Start marker
        available.append((1440-1,1440-1)) #End marker
        
        open_time_slots = []    
        for i in range(0,len(available)-1):
            curr = available[i]
            next = available[i+1]
            diff = next[0] - curr[1]
            if diff >= length and curr[1]//60 >= earliest_hour:
                for j in range(diff//length):
                    open_time_slots.append((curr[1]+length*j,curr[1]+length*(j+1)))
        if len(open_time_slots) >= order:
            return open_time_slots[order-1]            
        return None
    
    def add_meeting(self,new_meeting):
        '''
        Add a new meeting to the Calendar.
        '''
        #Note: overlap check removed to support "artificial" meetings
        #for m in self.meetings:
        #    if m.overlap(new_meeting):
        #        return False
        self.meetings.append(new_meeting)
        return True
    
    def get_meeting(self, dayofweek, start):
        '''
        Get information about a meeting with a given
        start time
        
        Requires:
        - `start` is an int in range [0,1440-1]
        - A meeting in calendar exists with that start time
        '''
        for m in self.meetings:
            if m.day == dayofweek and m.get_time_tuple()[0] == start:
                return m
        return None

    def get_contact_meeting(self, contact):
        '''
        Get the last meeting we had with a given contact. 
        
        Requires:
        - `contact` is a string denoting first name of that person
        
        '''
        contact_set = set([m.contact for m in self.meetings])
        
        #In the case Voiceflow or the user misspoke the name, get
        #the name of contacts which we had a meeting with that sounded
        #closest to the provided name
        
        close_matches = get_close_matches(contact, contact_set) #By default, similarity cutoff is 0.6
        if not close_matches: 
            return None #No previously known contact with that name
        best_contact = close_matches[0]
        meetings_with_contact = [m for m in self.meetings if m.contact == best_contact]
        meetings_with_contact.sort(reverse=True,key=lambda m: (m.day,m.start)) 
        return meetings_with_contact[0] #Return the latest meeting

    def set_meeting_notes(self, dayofweek, start, new_notes):
        '''
        Overwrite notes for the meeting on `dayofweek` starting at `start` time
        '''
        for m in self.meetings:
            if m.day == dayofweek and m.get_time_tuple()[0] == start:
                m.set_notes(new_notes)
                return
    def add_artificial_meeting_notes(self, contact, new_notes):
        '''
        Create an artificial meeting for a given `contact` with notes of `new_notes`
        
        This meeting is set by convention to be Sunday from 11:58-11:59 PM
        '''
        new_meeting = Meeting(7,1438,1439,contact,new_notes)
        self.add_meeting(new_meeting)
        
    def set_meeting_agenda(self, dayofweek, start, new_agenda):
        '''
        Overwrite agenda for the meeting on `dayofweek` starting at `start` time
        '''
        for m in self.meetings:
            if m.day == dayofweek and m.get_time_tuple()[0] == start:
                m.set_agenda(new_agenda)
                return
            
class Meeting:
    def __init__(self, day, start, end, contact, notes='', agenda=''):
        '''
        Creates a meeting event with:
        day (int) = Day of week [1,7]
        start, end (int) = Start and end time for meeting [0,1440-1]
        contact (str) = Name of contact 
        summary (str) = Summary of meeting
        agenda (str) = Agenda of meeting
        '''
        self.day = day
        self.start = start
        self.end = end
        self.contact = contact
        self.notes = notes
        self.agenda = agenda
    def overlap(self,other):
        '''
        Check if another meeting overlaps with this one
        '''
        if (self.day==other.day):
            return (self.start < other.start < self.end) or (self.start < other.end < self.end)
        return False
    def get_time_tuple(self):
        '''
        Returns tuple representing (start_time, end_time) of meeting
        '''
        return (self.start, self.end)
    def set_notes(self,new_notes):
        self.notes = new_notes
    def set_agenda(self,new_agenda):
        self.agenda = new_agenda
    def __hash__(self):
        return hash((self.day,self.start, self.end))
    def __eq__(self, other):
        return (self.start, self.end) == (other.start, other.end)
    def __ne__(self, other):
        return not(self == other)
    def __str__(self):
        return f"{self.day}|{self.start}|{self.end}|{self.contact}|{self.notes}|{self.agenda}"

def parseDate(day, reverse=False):
    '''
    Given day in text form, return corresponding integer
    in range [1,7]
    
    If reverse=True, then we convert from int back into text form
    ''' 
    if not reverse:
        lower_day = day.lower()
        return DATES[lower_day]

    inv_dates = {v: k for k, v in DATES.items()}
    return inv_dates[day]

def parseTime(time, reverse=False):
    '''
    Given time in text form, e.g. "HH:MM AM" or "HH:MM PM"
    and return that time in number of minutes 
    in range [0,1440-1]
    ''' 
    if not reverse:
        timestamp, am_or_pm = time.split(" ")
        hour, minute = timestamp.split(":")
        hour = int(hour)
        minute = int(minute)
        if am_or_pm == "PM" and hour != 12:
            hour += 12
        if hour==12 and am_or_pm=="AM":
            hour = 0
        return hour*60+minute

    hour = time // 60
    minute = time % 60
    am_or_pm = ""
    if hour <= 11:
        am_or_pm = "AM"
    else:
        hour -= 12
        am_or_pm = "PM"
    if hour == 0:
        hour = 12
    return f"{hour:02}:{minute:02} {am_or_pm}"
    
def read_initial_data(filename="initial_data.txt"):
    '''
    Given a filename with lines in the format:
    `dateofweek|start|end|contact|notes|agenda`
    
    Return a calendar with those meetings added in
    '''
    cal = Calendar()
    with open(filename,"r") as f:
        lines = f.read().splitlines()
        for line in lines:
            meet_info = line.split("|")
            meet_info[0] = parseDate(meet_info[0]) #day
            meet_info[1] = parseTime(meet_info[1]) #start
            meet_info[2] = parseTime(meet_info[2]) #end
            new_meeting = Meeting(*meet_info)
            cal.add_meeting(new_meeting)
    return cal

# first_meet = Meeting(2,0,30,"Huy Dai","We met with two guys")
# cal = Calendar()
# cal.add_meeting(first_meet)

# print(cal.get_meeting(2,0))

#cal = read_initial_data()
#print(cal.find_time_slot(2,60,7))
#print(cal.get_contact_meeting("Myle"))
#print(parseTime("1:30 AM"))
#print(parseTime(1439,True))
#print(parseTime(39,True))