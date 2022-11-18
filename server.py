from flask import Flask, json, request
import my_calendar as cal

app = Flask(__name__)
calendar = cal.read_initial_data()
#print([str(m) for m in calendar.meetings])

@app.route('/addmeeting', methods=['POST'])
def add_meeting():
  '''
  User provides meeting information in JSON body with the following params:
  
  `day` (str) - that denotes day of the week ('monday','tuesday', etc.)
  `start` (str) - Time of day (in form "HH:MM AM" or "HH:MM PM")
  `end` (str) -Time of day (in form "HH:MM AM" or "HH:MM PM"). Must be after `start`
  `contact` (str) - Name of person meeting with
  '''
  post_json = request.json
  day = cal.parseDate(post_json['day'])
  start = cal.parseTime(post_json['start'])
  end = cal.parseTime(post_json['end'])
  contact = post_json['contact']
  new_meeting = cal.Meeting(day,start,end,contact)
  res = calendar.add_meeting(new_meeting)
  if not res:
    return json.dumps({"success": False}), 400 #Bad request
  return json.dumps({"success": True}), 201

@app.route('/getmeeting', methods=['POST'])
def get_meeting():
  '''
  Get a meeting happening on `day` starting at `start` time.
  
  User provides meeting information in JSON body with the following params:
  
  `day` (str) - that denotes day of the week ('Monday','Tuesday', etc.)
  `start` (str) - Time of day (in form "HH:MM AM" or "HH:MM PM")
  `end` (str) -Time of day (in form "HH:MM AM" or "HH:MM PM"). Must be after `start`
  '''
  post_json = request.json
  day = cal.parseDate(post_json['day'])
  start = cal.parseTime(post_json['start'])
  
  meeting = calendar.get_meeting(day,start)
  if not meeting:
    return json.dumps({"success": False}), 400 #Bad request
  
  assert isinstance(meeting, cal.Meeting)
  res = {
    'day': cal.parseDate(meeting.day,reverse=True),
    'start': cal.parseTime(meeting.start,reverse=True),
    'end': cal.parseTime(meeting.end,reverse=True),
    'contact': meeting.contact,
    'notes': meeting.notes,
    'agenda':  meeting.agenda,
    'success': True    
  }
  return json.dumps(res), 201

@app.route('/findmeeting', methods=['POST'])
def find_meeting():
  '''
  Find an open meeting slot on a given day
  
  User provides meeting information in JSON body with the following params:
  `day` (str) - that denotes day of the week ('Monday','Tuesday', etc.)
  `length` (int) - Integer that denotes length of the meeting (in minutes)
 
  Whether a time slot was found will be denoted by `success` boolean (true for found)
  '''
  post_json = request.json
  day = cal.parseDate(post_json['day'])
  length = int(post_json['length'])
  found_meeting = calendar.find_time_slot(day,length)
  if not found_meeting:
    return json.dumps({"success": False}), 400 #Bad request
  
  res = {
    'day': post_json['day'],
    'start': cal.parseTime(found_meeting[0],reverse=True),
    'end': cal.parseTime(found_meeting[1],reverse=True),
    'success': True    
  }
  return json.dumps(res), 201

@app.route('/addnotes', methods=['POST'])
def add_notes():
  '''
  Add/overwrite notes for a meeting
  
  User provides meeting information in JSON body with the following params:
  
  `day` (str) - that denotes day of the week ('Monday','Tuesday', etc.)
  `start` (str) - Time of day (in form "HH:MM AM" or "HH:MM PM")
  `notes` (str) - Notes of meeting (to overwrite previous)
  '''
  post_json = request.json
  day = cal.parseDate(post_json['day'])
  start = cal.parseTime(post_json['start'])
  notes = post_json['notes']
  calendar.set_meeting_notes(day,start,notes)
  return json.dumps({"success": True}), 201
  
@app.route('/addagenda', methods=['POST'])
def add_agenda():
  '''
  Add/overwrite agenda for a meeting
  
  User provides meeting information in JSON body with the following params:
  
  `day` (str) - that denotes day of the week ('Monday','Tuesday', etc.)
  `start` (str) - Time of day (in form "HH:MM AM" or "HH:MM PM")
  `agenda` (str) - Agenda of meeting (to overwrite previous)
  '''
  post_json = request.json
  day = cal.parseDate(post_json['day'])
  start = cal.parseTime(post_json['start'])
  agenda = post_json['agenda']
  calendar.set_meeting_agenda(day,start,agenda)
  return json.dumps({"success": True}), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True) #Note: Not generally recommended to run Flask dev on all interfaces, but okay for our context
    