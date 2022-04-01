# dowd-chute-gauge
Virtual streamflow gauge for Dowd Chute on the Eagle River

This project creates a small web app that estimates the streamflow on the Eagle River in Dowd Chute for whitewater boaters.  It is a Python Flask application that calls realtime streamflow from other locations in the watershed using the USGS Instantaneous Values Webservice API then estimates flow in Dowd Chute using a linear regression from other nearby gauge values.
