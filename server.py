from calendar import Calendar, Meeting
from flask import Flask, json

app = Flask(__name__)

@app.route('/add', methods=['POST'])
def add_calendar():
  #Read in given POST body
  return json.dumps({"success": True}), 201

if __name__ == '__main__':
    calendar = Calendar()
    app.run() 
    