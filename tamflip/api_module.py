import requests
import json

# Getting an access token given API_KEY and API_SECRET
def get_token():
	url_post = 'https://test.api.amadeus.com/v1/security/oauth2/token'
	param_object_post = {
		'grant_type': 'client_credentials',
		'client_id':'jwCdvN4AVxtDLPqT7gDQI7Cdf1dlfdbb',
		'client_secret':'rHnOqnhEsGxQhV3f'
	}
	x_post = requests.post(url_post, data=param_object_post)
	y_post = x_post.json()
	access_token = y_post['access_token']
	return access_token

# Checking if an access token is valid or not
def check_valid_token():
	url_get_valid = 'https://test.api.amadeus.com/v1/security/oauth2/token/'
	url_get_valid += access_token
	x_get_valid = requests.get(url_get_valid)
	y_get_valid = x_get_valid.json()
	if y_get_valid['state'] == 'approved':
		return True
	return False

def class_of_travel(travel_class):
	return {
		'Economy': 'ECONOMY',
		'Premium Economy': 'PREMIUM_ECONOMY',
		'Business': 'BUSINESS',
		'First Class': 'FIRST'
	}[travel_class]

def process_time(ftime):
	det = ''
	val = int(ftime[0:2])
	if(val>12):
		val%=12
		det+=' PM'
	elif(val==12):
		det+=' PM'
	elif(val==0):
		det+=' AM'
		val+=12
	elif(val< 12):
		det+=' AM'
	return str(val)+ftime[2:]+det	

def process_date_time(date_time):
	year = date_time[0:4]
	month = date_time[5:7]
	day = date_time[8:10]
	time = 	date_time[11:16]
	return day+'-'+month+'-'+year+' '+process_time(time)

def process_duration(duration):
	return duration[2:].lower()

# makes a call and returns the flightDetails filled in the form
def get_flight_details(form_object):
	access_token = get_token()
	# prepare URL for sending
	url_get_flight = (
		'https://test.api.amadeus.com/v2/shopping/flight-offers?'
		+ '&originLocationCode=' + form_object['from_location']
		+ '&destinationLocationCode=' + form_object['to_location']
		+ '&departureDate=' + form_object['departure_date']
		+ ('' if (form_object['return_date'] is None
					or form_object['return_date'] == '')
		   else '&returnDate=' + form_object['return_date'])
		+ '&travelClass=' + class_of_travel(form_object['type_of_class'])
		+ '&adults=' + str(form_object['adults'])
		+ '&children=' + str(form_object['children'])
		+ '&infants=' + str(form_object['infants'])
		+ '&currencyCode=' + 'INR'
	)

	# Send HTTP request to Flight API to fetch flight details
	x_get_flight = requests.get(
		url_get_flight,
		headers={'Authorization': 'Bearer '+ str(access_token)}
	)
	y_get_flight = x_get_flight.json()

	# TODO: Handle the following cases by displaying error messages to UI.
	# In case request is invalid/no response from server
	if y_get_flight.get("errors") != None:
		return ([] , [])

	# In case of no flights detected
	if y_get_flight['meta']['count'] == 0:
		return ([], [])

	# We get a success response
	flight_details, price_details = preprocess_json(form_object, y_get_flight)
	print(flight_details)
	return (flight_details, price_details)

# preprocess the JSON object into a clean list
def preprocess_json(form_object, my_object):
	flight_details = []
	price_details = []
	# map carrier codes to carrier names
	carrier_map = {}
	for obj in my_object['dictionaries']['carriers']:
		carrier_map[obj] = my_object['dictionaries']['carriers'][obj]
	# store all the flight details into a dictionary
	for obj in my_object['data']:
		temp_list = []
		# stores one round trip if there
		for itineraries in obj['itineraries']:
			temp_dict = {}
			temp_dict['duration'] = process_duration(itineraries['duration'])
			temp_dict['departure_time'] = process_date_time(itineraries['segments'][0]['departure']['at'])
			temp_dict['arrival_time'] = process_date_time(itineraries['segments'][0]['arrival']['at'])
			temp_dict['carrier_code'] = itineraries['segments'][0]['carrierCode']
			temp_dict['carrier_name'] = carrier_map[temp_dict['carrier_code']]
			temp_dict['aircraft_code'] = itineraries['segments'][0]['aircraft']['code']
			temp_dict['number_of_stops'] = str(itineraries['segments'][0]['numberOfStops'])
			temp_list.append(temp_dict)
		price_details.append(obj['price']['total'])
		flight_details.append(temp_list)
	return flight_details, price_details

def query_tracked_flight(user_object):
	flight_details, price_details = get_flight_details(user_object)
	for i, flight in enumerate(flight_details):
		if (flight[0]['carrier_code'] == user_object['carrier_code']
			and flight[0]['aircraft_code'] == user_object['aircraft_code']):
			return flight, price_details[i]