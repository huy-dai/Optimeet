from flask import Flask, json, request
import my_calendar as cal
import gcal_functions as gcal
import datetime
import dateutil.parser
import pytz

app = Flask(__name__)
calendar = cal.read_initial_data()

@app.route('/addmeeting', methods=['POST'])
def add_meeting():
  '''
  User provides meeting information in JSON body with the following params:
  
  `day` (str) - that denotes day of the week ('monday','tuesday', etc.)
  `length` (int) - Integer that denotes length of the meeting (in minutes)
  `order` (int) - A number >= 1 telling the server to get the n_th open time slot in the day
  `agenda` (str) -  Agenda for the meeting
  `contact` (str) - First name of person meeting with
  '''
  post_json = request.get_json(force=True) 
  app.logger.info(post_json)
  day = post_json['day'].lower()
  length = int(post_json['length'])
  order = int(post_json['order'])
  agenda = post_json['agenda']
  contact = post_json['contact']
  if contact != "User":
    title = f"Meeting with {contact}"
  else:
    title = "Scheduled meeting"
  res = gcal.find_meeting_timeslot(contact,length,order,earliest_hour=9,latest_hour=17,dayofweek=day)
  if not res:
      app.logger.info({"success": False})
      return json.dumps({"success": False}), 201
  start, end = res[0], res[1]
  gcal.create_meeting(title,agenda,start,end,contact)
  app.logger.info({"success": True})
  return json.dumps({"success": True}), 201

@app.route('/getcontactmeeting', methods=['POST'])
def get_contact_meeting():
  '''
  Get last meeting that we had with a given person. This includes "artificial" meetings
  (set by convention to be Sunday from 11:58-11:59 PM) that contains notes stored for that person.
  
  User provides meeting information in JSON body with the following params:
  `contact` (str) - first name of person we had the meeting with

  Whether a meeting was found will be denoted by `success` boolean (true for found)
  '''
  post_json = request.get_json(force=True) 
  app.logger.info(post_json)
  contact = gcal.get_closest_contact(post_json['contact'])
  if contact == "User": #No matching GCal contact
    artificial_notes = gcal.get_artificial_notes(post_json['contact'])
    if not artificial_notes:
      app.logger.info({"success": False})
      return json.dumps({"success": False}), 201 #No such meeting found
    res = {
      'day':"sunday",
      'start':"11:58 PM",
      'end':"11:59 PM",
      'contact': post_json['contact'],
      'notes': artificial_notes,
      'agenda': "",
      'success': True
    }
    app.logger.info(res)
    return json.dumps(res), 201
  else: 
    prev_meetingID = gcal.get_previous_meeting(contact)
    meeting = gcal.get_meeting(prev_meetingID)
    est = pytz.timezone('US/Eastern')
    start_dt = dateutil.parser.isoparse(meeting['start']['dateTime']).astimezone(est)
    end_dt = dateutil.parser.isoparse(meeting['end']['dateTime']).astimezone(est)
    day = gcal.parseDate(start_dt.weekday(),reverse=True)
    notes = gcal.get_optinotes(prev_meetingID)
    res = {
      'day': day,
      'start': datetime.datetime.strftime(start_dt,"%I:%M %p"),
      'end': datetime.datetime.strftime(end_dt,"%I:%M %p"),
      'contact': meeting['attendees'][0]['email'],
      'notes': notes,
      'agenda':  "", 
      'success': True    
    }
    app.logger.info(res)
    return json.dumps(res), 201

@app.route('/findmeeting', methods=['POST'])
def find_meeting():
  '''
  Find an open meeting slot on a given day
  
  User provides meeting information in JSON body with the following params:
  `day` (str) - that denotes day of the week ('Monday','Tuesday', etc.)
  `contact` (str) - Name of contacts we're meeting with
  `length` (int) - Integer that denotes length of the meeting (in minutes)
  `order` (int) - A number >= 1 telling the server to get the n_th open time slot in the day
  `asap` (bool) - A boolean indicating whether to get the latest meeting.
      If this is True, we will ignore the `day` and `order` parameters
  Whether a time slot was found will be denoted by `success` boolean (true for found)
  '''
  post_json = request.get_json(force=True) 
  app.logger.info(post_json)
  contact = post_json['contact']
  length = int(post_json['length'])
  found_meeting = None
  if bool(post_json['asap']):
    found_meeting = gcal.quick_schedule(contact,length)
    if not found_meeting:
      app.logger.info({"success": False})
      return json.dumps({"success": False}), 201 #Bad request
    day = gcal.parseDate(found_meeting[0].weekday(),reverse=True)
    start = gcal.parseTime(found_meeting[0].time(),reverse=True)
    end = gcal.parseTime(found_meeting[1].time(),reverse=True)
  else:
    day = post_json['day'].lower()
    order = int(post_json['order'])
    found_meeting = gcal.find_meeting_timeslot(contact,length,order,earliest_hour=9,latest_hour=17,dayofweek=day)
    if not found_meeting:
      app.logger.info({"success": False})
      return json.dumps({"success": False}), 201 #No meeting available
    start = gcal.parseTime(found_meeting[0],reverse=True)
    end = gcal.parseTime(found_meeting[1],reverse=True)

  res = {
    'day': day,
    'start': start,
    'end': end,
    'success': True    
  }
  app.logger.info(res)
  return json.dumps(res), 201

@app.route('/addnotes', methods=['POST'])
def add_notes():
  '''
  Add/overwrite notes for a meeting
  
  User provides meeting information in JSON body with the following params:
  `contact` (str) - first name of person we had the meeting with
  `notes` (str) - Notes of meeting (to overwrite previous)
  `overwrite` (bool) - Whether to overwrite or not (if not, then we append)
  '''
  post_json = request.get_json(force=True) 
  app.logger.info(post_json)
  contact = gcal.get_closest_contact(post_json['contact'])
  notes = post_json['notes']
  if bool(post_json['overwrite']):
    gcal.overwrite_optinotes(gcal.get_previous_meeting(contact), notes)
  else:
    gcal.add_optinotes(gcal.get_previous_meeting(contact), notes)
  app.logger.info({"success": True})
  return json.dumps({"success": True}), 201

@app.route('/addartificialnotes', methods=['POST'])
def add_artificial_notes():
  '''
  Add notes for an "artificial" meeting for a given contact
  
  User provides meeting information in JSON body with the following params:
  `contact` (str) - first name of person we had the meeting with
  `notes` (str) - notes of meeting (to overwrite previous, if one exists)
  `overwrite` (bool) - Whether to overwrite or not (if not, then we append)
  '''
  post_json = request.get_json(force=True) 
  app.logger.info(post_json)
  contact = gcal.get_closest_contact(post_json['contact'])
  notes = post_json['notes']
  overwrite = bool(post_json['overwrite'])
  gcal.store_artificial_notes(contact,notes,overwrite)
  app.logger.info({"success": True})
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
  # post_json = request.get_json(force=True) 
  # day = cal.parseDate(post_json['day'])
  # start = cal.parseTime(post_json['start'])
  # agenda = post_json['agenda']
  # calendar.set_meeting_agenda(day,start,agenda)
  app.logger.info({"success": True})
  return json.dumps({"success": True}), 201

@app.route('/checkcontactexists', methods=['POST'])
def check_contact_exists():
    post_json = request.get_json(force=True) 
    app.logger.info(post_json)
    if gcal.check_contact_exists(post_json['contact']):
        app.logger.info({"success": True})
        return json.dumps({"success": True}), 201
    app.logger.info({"success": False})
    return json.dumps({"success": False}), 201

# NOTE: Route is no longer used
# @app.route('/getmeeting', methods=['POST'])
# def get_meeting():
#   '''
#   Get a meeting happening on `day` starting at `start` time.
#
#   User provides meeting information in JSON body with the following params:
#   `day` (str) - that denotes day of the week ('Monday','Tuesday', etc.)
#   `start` (str) - Time of day (in form "HH:MM AM" or "HH:MM PM")
#   `end` (str) -Time of day (in form "HH:MM AM" or "HH:MM PM"). Must be after `start`
#   '''
#   post_json = request.get_json(force=True) 
#   day = cal.parseDate(post_json['day'])
#   start = cal.parseTime(post_json['start'])
#   meeting = calendar.get_meeting(day,start)
#   if not meeting:
#     return json.dumps({"success": False}), 201 #Bad request
#   assert isinstance(meeting, cal.Meeting)
#   res = {
#     'day': cal.parseDate(meeting.day,reverse=True),
#     'start': cal.parseTime(meeting.start,reverse=True),
#     'end': cal.parseTime(meeting.end,reverse=True),
#     'contact': meeting.contact,
#     'notes': meeting.notes,
#     'agenda':  meeting.agenda,
#     'success': True    
#   }
#   return json.dumps(res), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True) #Note: Not generally recommended to run Flask dev on all interfaces, but okay for our context
    