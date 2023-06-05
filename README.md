# LAPS-Tool


This tool has been built as a Python learning project, it has no guarantees of functionality or otherwise. It was also meant to be used as a teaching tool, it could probably be much more efficient but I was going for readability, not perfection, as will be obvious. Feel free to reach out with suggestions and feedback.

If you wish to utilize this tool, by all means. But since I am some no-name rando on the internet, downloading a suspicious zip file might not be advised. I have inlcuded the `setup.py` file in here that can be used with the py2app module to build a .app for this tool.

This is my list of known issues and QoL improvements that I am considering implementing/fixing.

Known issues:
* ~~Does not display anything when valid comp ID inputted but no PW to be found.~~ *Resolved.*
* No logic for expired token (hopefully shows in logs?). Should renew if receiving 401 and then throw error if unsuccessful
* pasting errors, specifically white space will break the URL without an error or correction
* The main page isn't centered in the window.
* Not great error handling in general. Broken or incorrect URLS only sort of output an error.
- One option would be, if there is an error other than bad credentials, to just dump the error into logs and post a message about checking those.

Qol Improvements:
* If serial slider is enabled tkinter configure the Computer ID field to have placeholder text be "Serial Number"
* Output when the password will update next
* Looks like my logging errors aren't 100% accurate, malformed URLs and bad credentials complain about a token issue.
* Split into separate files for more readily reused code.
* Include new endpoints for setting the password and changing The Jamf Pro Settings.