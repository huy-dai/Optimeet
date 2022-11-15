class Meeting:
    def __init__(self, day, start, end, contact, summary=None, agenda=None):
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
        self.summary = summary
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
    def __hash__(self):
        return hash((self.day,self.start, self.end))
    def __eq__(self, other):
        return (self.start, self.end) == (other.start, other.end)
    def __ne__(self, other):
        return not(self == other)
    
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
        Raises ValueError if new_meeting conflicts in time with current meetings
        '''
        for m in self.meetings:
            if m.overlap(new_meeting):
                raise ValueError("New meeting can't overlap current meetings")
        self.meetings.append(new_meeting)
            
            
first_meet = Meeting(2,0,30,"Huy Dai","We met with two guys")
cal = Calendar()
cal.add_meeting(first_meet)
print(cal.find_time_slot(2,60))
