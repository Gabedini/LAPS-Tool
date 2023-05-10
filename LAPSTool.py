#!/usr/bin/env python
import requests, json, keyring
import customtkinter
from datetime import datetime

username = ''
password = ''

session = requests.Session()
logs = open("/tmp/LAPSTool.log", "a")
global clientManagementId
global compId
clientManagementId = ""
compId = ""

"""This method gets us a bearer token from Jamf Pro."""
def getToken(url, jpUser, jpPass):
	try:
		response = session.post(url + "auth/token", auth = (jpUser, jpPass))
		print(response)
		if response.status_code == 401:
			logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Tried to get a token: {response} - incorrect username or password.")
			return "bad creds"
		logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Getting token from: {url}auth/token")
		responseData = response.json()
		token = responseData["token"]
		return token
	except requests.exceptions.MissingSchema as error:
		errorMsg = str(error)
		logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Seems like the URL was malformed: {errorMsg}")
		return errorMsg

"""Grabs the current settings in Jamf Pro"""
def getComputerID(url, dataForHeader, serialNumber):
	logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Collecting the computer ID from {serialNumber}")
	"""because classic API is dumb we need to specify json, so we're doing that below:"""
	dataForHeader["Accept"] = "application/json"
	response = session.get(url + f"computers/serialnumber/{serialNumber}", headers=dataForHeader)
	if response.status_code == 401:
		logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Failed to collect computer ID: {response} - the token may have expired. Please close and reopen app....")
		return "Token may have expired. Please close and reopen app."
	elif response.status_code == 200:
		content = response.json()
		computerID = content['computer']['general']['id']
		logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Successfully collected the computer ID from {serialNumber}: {computerID}")
		return computerID
	else:
		logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ")
		return "Something went wrong, please check that this serial exists in your Jamf Pro instance."

"""Grabs the current settings in Jamf Pro"""
def getCurrentSettings(url, dataForHeader):
	response = session.get(url + "local-admin-password/settings", headers=dataForHeader)
	if response.status_code == 401:
		logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Attempt to collect Current LAPS Settings: {response} - the token may have expired. Please close and reopen app....")
		return "Token may have expired. Please close and reopen app."
	elif response.status_code == 200:
		logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Collecting current settings: {response.text}")
		currentSettings = response.json()
		logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} returning current settings: {currentSettings}")
		return currentSettings
	else:
		logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Something went wrong collecting the current settings. It may be that simply your Jamf Pro does not support this endpoint")
		return "Something went wrong, please ensure your Jamf Pro version is greater than 10.45."

"""Gets the Client Management ID from the computer record"""
def getManagementID(url, dataForHeader, computerID):
	global clientManagementId
	"""This endpint only appears as computers-inventory in the API GUI"""
	response = session.get(url + f"computers-inventory-detail/{computerID}", headers=dataForHeader)
	print(response)
	if response.status_code == 401:
		logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Attempt to collect Client Management ID: {response} - the token may have expired. Please close and reopen app....")
		return "Token may have expired. Please close and reopen app."
	elif response.status_code == 200:
		logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Collecting Managment ID for: {url}computers-inventory-detail/{computerID}")
		content = response.json()
		clientManagementId = content["general"]["managementId"]
		logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Collected managemend ID: {clientManagementId}")
		return clientManagementId
	elif response.status_code == 404:
		clientManagementId = "Unable"
		return "Unable"
	else:
		clientManagementId = "Unable"
		logs.write(f"Unable\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Unable to gather Client ID when executing the command. Most likely this computer ID either doesn't exist in Jamf Pro or was not configured for this workflow on enrollment")
		return "Unable to gather Client ID when executing the command. Most likely this computer ID either doesn't exist in Jamf Pro or was not configured for this workflow on enrollment"

"""Enables LAPS if disabled"""
def enableIfDisabled(url, dataForHeader):
	print("is this thing on?")
	if currentAutoDeployEnabled == False:
		logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Currently disabled, activating")
		"""putting the 'current' variables in here, likely would make more sense to update these independently, but this can work as default data for now
		It won't accept leaving out data points, we need to supply them all, it seems. I'll look to see if we can skip them somehow, later"""
		jsonToEnable = {"autoDeployEnabled":"true", "passwordRotationTime":currentPasswordRotationTime, "autoExpirationTime":currentAutoExpirationTime}
		response = session.put(url + "local-admin-password/settings", headers=dataForHeader, json = jsonToEnable)
		if response.status_code == 401:
			logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Attempt to enable LAPS: {response} - the token may have expired. Please close and reopen app....")
			return "Token may have expired. Please close and reopen app."
		elif response.status_code == 200:
			logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Attempt to enable LAPS: {response}")
			content = response.text
			logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {content}")
			print('consider printing something about this not working on machines enrolled before selecting this option')
			return content
		else:
			logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} If this option errors out it likely means it was a connection error. Closing and re-opening should clear that up.")
			return "Something went wrong, please ensure your Jamf Pro version is greater than 10.45."
	else:
		logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} LAPS already enabled, skipping...")
		return "LAPS already enabled, skipping"
"""Note: not sure in what context this would useful other than initial setup, as this would need to be enabled prior to machine enrollment.
I'll probably just make this a button and then mention that in the GUI somewhere"""

"""Get LAPS password viewed history. (returns the whole json for formatting later if we feel like it)"""
def getViewedHistory(url, dataForHeader, computerID, username):
	global clientManagementId
	if computerID == "" or username == "":
		logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Missing Computer ID or Username")
		return "Missing Computer ID or Username"
	else:
		if clientManagementId == "":
			logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Missing Client Management ID, collecting...")
			getManagementID(jpURL, head, computerID)
		if clientManagementId.startswith("Unable") == True:
			return "Unable to get history, Client ManagementID appears to be incorrect. Most likely this computer ID doesn't exist."
		response = session.get(url + f"local-admin-password/{clientManagementId}/account/{username}/audit", headers=dataForHeader)
		if response.status_code == 401:
			logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} History collection: {response} - the token may have expired. Please close and reopen app....")
			return "Token may have expired. Please close and reopen app."
		elif response.status_code == 200:
			logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} History collection: {response}")
			history = response.json()
			logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} History: {history}")
			prettyHistory = json.dumps(history, indent=4)
			return prettyHistory
		else:
			logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Something went wrong. It may be that the computerID or local admin account supplied were unrecognized by the server, or that simply your Jamf Pro does not support this endpoint")
			return "Something went wrong, please ensure your Jamf Pro version is greater than 10.45 and that this computer is configured for this workflow."

"""Get current LAPS password for specified username on a client. (returns just the password)"""
def getLAPSPassword(url, dataForHeader, computerID, username):
	global clientManagementId
	if computerID == "" or username == "":
		logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Missing Computer ID or Username")
		return "Missing Computer ID or Username"
	else:
		if clientManagementId == "":
			logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Missing Client Management ID, collecting...")
			getManagementID(jpURL, head, computerID)
		if clientManagementId.startswith("Unable") == True:
			return "Unable to get history, Client ManagementID appears to be incorrect. Most likely this computer ID doesn't exist."
		response = session.get(url + f"local-admin-password/{clientManagementId}/account/{username}/password", headers=dataForHeader)
		if response.status_code == 401:
			logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Password collection: {response} - the token may have expired. Please close and reopen app....")
			return "Token may have expired. Please close and reopen app."
		elif response.status_code == 200:
			logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Password collection: {response}. Printing to GUI")
			content = response.json()
			lapsPass = content["password"]
			return lapsPass
		else:
			logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Something went wrong. It may be that the computerID or local admin account supplied were unrecognized by the server, or that simply your Jamf Pro does not support this endpoint")
			return "Something went wrong, please ensure your Jamf Pro version is greater than 10.45."

"""Get the LAPS capable admin accounts for a device. (returns just the account name)"""
def getLAPSAccount(url, dataForHeader, computerID):
	global clientManagementId
	global compId
	print("this runs, right?")
	print(f"global compid is {compId}")
	logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Getting LAPS Enabled Account for computer ID:  {computerID}")
	if computerID == "":
		logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Missing Computer ID")
		return "Missing Computer ID"
	else:
		if clientManagementId == "":
			logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Missing Client Management ID, collecting...")
			getManagementID(jpURL, head, computerID)
		if compId != computerID: 
			compId = computerID
			logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Computer ID has been updated, getting new Client Management ID...")
			getManagementID(jpURL, head, computerID)
		if clientManagementId.startswith("Unable") == True:
			return "Unable to get history, Client ManagementID appears to be incorrect. Most likely this computer ID doesn't exist."
		response = session.get(url + f"local-admin-password/{clientManagementId}/accounts", headers=dataForHeader)
		print(f"{url}local-admin-password/{clientManagementId}/accounts")
		if response.status_code == 401:
			logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Account collection: {response} - the token may have expired. Please close and reopen app....")
			return "Token may have expired. Please close and reopen app."
		elif response.status_code == 200:
			logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Account collection: {response}")
			content = response.json()
			logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {content}")
			lapsAccount = content['results'][0]['username']
			logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Account Found: {lapsAccount}")
			return lapsAccount
		else:
			logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Something went wrong. It may be that the computerID or local admin account supplied were unrecognized by the server, or that simply your Jamf Pro does not support this endpoint")
			return "Something went wrong, please ensure your Jamf Pro version is greater than 10.45."


"""———————————————————————————————————————"""
"""Below this line are all the GUI items"""
"""———————————————————————————————————————"""
customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("dark-blue")
class App(customtkinter.CTk):
	def __init__(self):
		super().__init__()
		self.title("LAPS Tool")
		self.minsize(400, 300)

		self.grid_rowconfigure((0, 1), weight=1)
		self.grid_columnconfigure((0, 4), weight=1)

		"""Here we save the information if the toggle is selected. It defaults on if the LAPS URl is saved to the Keychain"""
		if keyring.get_password("LAPS URL", "url") != None:
			keyringURL = keyring.get_password("LAPS URL", "url")
			self.inputURLVar = customtkinter.StringVar(value=keyringURL)
			self.inputURL = customtkinter.CTkEntry(master=self, textvariable=self.inputURLVar)
			self.inputURL.pack(pady=12, padx=10)

			keyringUSER = keyring.get_password("LAPS Username", "username")
			self.inputUsernmVar = customtkinter.StringVar(value=keyringUSER)
			self.inputUsernm = customtkinter.CTkEntry(master=self, textvariable=self.inputUsernmVar)
			self.inputUsernm.pack(pady=12, padx=10)
		
			keyringPASS = keyring.get_password("LAPS Password", "password")
			self.inputPasswordVar = customtkinter.StringVar(value=keyringPASS)
			self.inputPasswd = customtkinter.CTkEntry(master=self, textvariable=self.inputPasswordVar, show="*")
			self.inputPasswd.pack(pady=12, padx=10)
		
			self.loginButton = customtkinter.CTkButton(master=self, text="Login", command=self.userLogin)
			self.loginButton.pack(padx=20, pady=20)

			self.saveCredsSwitch = customtkinter.CTkSwitch(master=self, state="enabled", text="Save Credentials")
			self.saveCredsSwitch.pack(pady=10, padx=10)
			self.saveCredsSwitch.select()

		else:
			"""Same stuff but not pre-filled"""
			self.inputURL = customtkinter.CTkEntry(master=self, placeholder_text="https://example.com")
			self.inputURL.pack(pady=12, padx=10)

			self.inputUsernm = customtkinter.CTkEntry(master=self, placeholder_text="Username")
			self.inputUsernm.pack(pady=12, padx=10)
		
			self.inputPasswd = customtkinter.CTkEntry(master=self, placeholder_text="Password", show="*")
			self.inputPasswd.pack(pady=12, padx=10)
		
			self.loginButton = customtkinter.CTkButton(master=self, text="Login", command=self.userLogin)
			self.loginButton.pack(padx=20, pady=20)

			self.saveCredsSwitch = customtkinter.CTkSwitch(master=self, text="Save Credentials")
			self.saveCredsSwitch.pack(pady=10, padx=10)

		"""This is used later to ensure that we don't add our box to the GUI twice"""
		self.outputBox = None

	def enabling(self):
		output = enableIfDisabled(jpURL, head)
		if self.outputBox.get("1.0", "end") != "":
			self.outputBox.delete('1.0', 'end')
		self.outputBox.insert("insert", f"{output}\n")

	def lapsAccount(self):
		computerID = self.inputComputerID.get()
		print(f"button was clicked, computer ID is: {computerID}")

		"""Clears our outputBox if there is already data in it"""
		if self.outputBox.get("1.0", "end") != "":
			self.outputBox.delete('1.0', 'end')

		"""Gets the computer ID if a serial number is inputted instead of ID"""
		if self.idTypeSwitch.get()==1:
			global classicURL
			print("running the computer ID collection")
			logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Serial Number toggle enabled...running ID collection.")
			computerID = getComputerID(classicURL, head, self.inputComputerID.get())
			print(f"computer ID collected: {computerID}")

		unOutput = getLAPSAccount(jpURL, head, computerID)
		self.outputBox.insert("insert", f"{unOutput}\n")

		pwOutput = getLAPSPassword(jpURL, head, computerID, unOutput)
		self.outputBox.insert("insert", f"{pwOutput}\n")

		hisOutput = getViewedHistory(jpURL, head, computerID, unOutput)
		self.outputBox.insert("insert", f"{hisOutput}\n")

	def optionPage(self):
		self.inputComputerID = customtkinter.CTkEntry(master=self, placeholder_text="Computer ID")
		self.inputComputerID.grid(row=0, column=0, pady=12, padx=10)

		self.idTypeSwitch = customtkinter.CTkSwitch(master=self, text="Enable for Serial Number")
		self.idTypeSwitch.grid(row=1, column=0, pady=10, padx=10)

		self.enableLAPS = customtkinter.CTkButton(master=self, text="Enable LAPS", command=self.enabling)
		self.enableLAPS.grid(row=2, column=0, padx=20, pady=20)

		"""self.collectViewedHistory = customtkinter.CTkButton(master=self, text="Collect PW Viewed History", command=self.gettingHistory)
		self.collectViewedHistory.grid(row=1, column=1, padx=20, pady=20)

		self.collectCurrentPassword = customtkinter.CTkButton(master=self, text="Collect Current PW", command=self.lapsPass)
		self.collectCurrentPassword.grid(row=2, column=0, padx=20, pady=20)"""

		self.collectLAPSAccount = customtkinter.CTkButton(master=self, text="Collect LAPS Data", command=self.lapsAccount)
		self.collectLAPSAccount.grid(row=3, column=0, padx=20, pady=20)

		self.outputBox = customtkinter.CTkTextbox(master=self)
		self.outputBox.configure(wrap="none")
		self.outputBox.grid(row=4, column=0, columnspan=2, padx=20, pady=20)

	def userLogin(self):
		"""anything that might be referenced outside of the GUI button functions is global"""
		global jpURL
		global classicURL
		global head
		global currentAutoDeployEnabled
		global currentPasswordRotationTime
		global currentAutoExpirationTime
		
		"""Making some variables."""
		classicURL = f"{self.inputURL.get()}/JSSResource/"
		jpURL = f"{self.inputURL.get()}/api/v1/"
		username = self.inputUsernm.get()
		password = self.inputPasswd.get()
		url = self.inputURL.get()

		print("login button pressed")
		
		print(f"{self.inputUsernm.get()}")
		print(f"{self.inputPasswd.get()}")
		if self.saveCredsSwitch.get()==1:
			logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Saving login info on, saving to Keychain.")
			"""This is where we save things for use in future runs if the toggle is selected"""
			"""Here's where we save the username, since keyring can only call passwords we just pass 'username' as filler"""
			keyring.set_password("LAPS Username", "username", username)
			"""Here's saving the password to the Keychain"""
			keyring.set_password("LAPS Password", "password", password)
			"""And here we abuse keyring to save the URL as well as if it's a password so that it doesn't have to be kept in a file"""
			keyring.set_password("LAPS URL", "url", url)
			logs.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Logging into {url} with username {username}")


		"""gets and sets token (note: token is app global but not program global)"""
		token = getToken(jpURL, username, password)
		print(token)

		"""puts token in header for us to pass later"""
		if token.startswith("Invalid URL") == True:
			if self.outputBox is None:
				self.outputBox = customtkinter.CTkTextbox(master=self)
				self.outputBox.pack(padx=20, pady=20)
			"""Clears the outputbox every time there is an error to only print the most recent one"""
			if self.outputBox.get("1.0", "end") != "":
				self.outputBox.delete('1.0', 'end')
			self.outputBox.insert("insert", f"{token}")
		if token == "bad creds":
			if self.outputBox is None:
				self.outputBox = customtkinter.CTkTextbox(master=self)
				self.outputBox.pack(padx=20, pady=20)
			"""Clears the outputbox every time there is an error to only print the most recent one"""
			if self.outputBox.get("1.0", "end") != "":
				self.outputBox.delete('1.0', 'end')
			self.outputBox.insert("insert", f"Incorrect username or password entered.{chr(10)}")

		head = {'Authorization': f'Bearer {token}' }

		"""gets and returns whatever the current settings are"""
		currentSettings = getCurrentSettings(jpURL, head)
		print(currentSettings)
		"""———————————————————————————————————————"""
		"""For reference if needed later"""
		"""Setting means: Whether LAPS is enabled"""
		currentAutoDeployEnabled = currentSettings["autoDeployEnabled"]
		print(currentAutoDeployEnabled)
		"""Setting means: The length of time between viewing a local admin password and rotating the password — the default is one hour"""
		currentPasswordRotationTime = currentSettings["passwordRotationTime"]
		print(currentPasswordRotationTime)
		"""Setting means: The length of time Jamf Pro routinely rotates the local admin password — the default is 90 days"""
		currentAutoExpirationTime = currentSettings["autoExpirationTime"]
		print(currentAutoExpirationTime)
		"""———————————————————————————————————————"""

		self.loginButton.pack_forget()
		self.inputUsernm.pack_forget()
		self.inputPasswd.pack_forget()
		self.inputURL.pack_forget()
		self.saveCredsSwitch.pack_forget()
		if self.outputBox is None:
			print("good to go")
		else:
			self.outputBox.pack_forget()
		self.optionPage()

if __name__ == "__main__":
	app = App()
	app.mainloop()




#SDG
