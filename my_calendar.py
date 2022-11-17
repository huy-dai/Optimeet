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
    
    def find_time_slot(self, dayofweek, length):
        '''
        Find free time slot in Calendar for day `dayofweek`
        for `length` number of minutes
        
        Returns (start,end) if time slot found, None otherwise
        '''
        available = [m.get_time_tuple() for m in self.meetings if m.day == dayofweek] #Meetings on that day
        available.insert(0,(0,0)) #Start marker
        available.append((1440-1,1440-1)) #End marker
        for i in range(0,len(available)-1):
            curr = available[i]
            next = available[i+1]
            assert next[0] >= curr[1]
            diff = next[0] - curr[1]
            if diff >= length:
                return (curr[1], curr[1]+length)
        return None
    def add_meeting(self,new_meeting):
        '''
        Add a new meeting to the Calendar.
        Returns False if new_meeting conflicts in time with current meetings, True otherwise
        '''
        for m in self.meetings:
            if m.overlap(new_meeting):
                return False
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
    def set_meeting_notes(self, dayofweek, start, new_notes):
        '''
        Overwrite notes for the meeting on `dayofweek` starting at `start` time
        '''
        for m in self.meetings:
            if m.day == dayofweek and m.get_time_tuple()[0] == start:
                m.set_notes(new_notes)
                return
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
        if am_or_pm == "PM":
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
        am_or_pm = "PM"
    if hour == 0:
        hour = 12
    return f"{hour:02}:{minute:02} {am_or_pm}"
    
    
# first_meet = Meeting(2,0,30,"Huy Dai","We met with two guys")
# cal = Calendar()
# cal.add_meeting(first_meet)

# print(cal.get_meeting(2,0))
# print(cal.find_time_slot(2,60))

#print(parseTime("1:30 AM"))
#print(parseTime(1439,True))