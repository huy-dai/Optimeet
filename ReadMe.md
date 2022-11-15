# Server Design

You can run `server.py` to start up a Flask API server on localhost:5000. In theory we'll have different endpoints for:
    - Querying a time for a meeting (given date and meeting length)
    - Adding a meeting to the calendar (given date, start_time, end_time, contact)
    - Editing a meeting to add/change the agenda and summary

The storage of meetings will be managed by the Calendar and Meeting classes. In the future we'll have methods to load in meeting information from a text file and parse it into the corresponding Python objects (to act as example calendar with pre-existing meetings).