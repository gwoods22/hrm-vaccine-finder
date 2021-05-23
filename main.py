import requests
from datetime import datetime
import time
import json

def getLocal(utc_datetime):
    date = datetime.fromisoformat(utc_datetime.replace("Z", "+00:00"))
    now_timestamp = time.time()
    offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
    localDate = date + offset
    return localDate.strftime("%b %d %H:%M %p")

def main():
    locationsUrl = 'https://sync-cf2-1.canimmunize.ca/fhir/v1/public/booking-page/17430812-2095-4a35-a523-bb5ce45d60f1/appointment-types?forceUseCurrentAppointment=false&preview=false'

    headers = {
    'authority': 'sync-cf2-1.canimmunize.ca',
    'accept': 'application/json, text/plain, */*',
    'user-agent': 'Mozilla/5.0 (Macintosh',
    'origin': 'https://novascotia.flow.canimmunize.ca',
    'referer': 'https://novascotia.flow.canimmunize.ca/',
    }

    

    response = requests.request("GET", locationsUrl, headers=headers)

    # allAppts = response.json()['results']
    allAppts = json.loads( response.data )['results']
    
    openAppts = list(filter(lambda x: not x['fullyBooked'], allAppts))
    hrmAppts = list(filter(lambda x: x['gisLocationString'].split(', ')[3] == 'Halifax County', openAppts))

    myAppts = []

    for i in range(1, len(hrmAppts)):
        apptsUrl = 'https://sync-cf2-1.canimmunize.ca/fhir/v1/public/availability/17430812-2095-4a35-a523-bb5ce45d60f1?appointmentTypeId={}&timezone=America%2FHalifax&preview=false'
        url = apptsUrl.format(hrmAppts[i]['id'])

        response = requests.request("GET", url, headers=headers)

        clinicName = hrmAppts[i]['clinicName'].split(' - ')

        # appts = response.json()[0]['availabilities']
        appts = json.loads( response.data )[0]['availabilities']
        
        for appt in appts:
            apptTime = appt['time']

            obj = {}
            obj['utcTime'] = apptTime,
            obj['apptTime'] = getLocal(apptTime),
            obj['id'] = hrmAppts[i]['id'],
            obj['address'] = hrmAppts[i]['gisLocationString'],
            if len(clinicName) == 3:
                obj['vaccine'] = clinicName[2],
                obj['name'] = clinicName[1]
            else:
                obj['name'] = ' '.join(clinicName)

            myAppts.append(obj)

    myAppts.sort(key=lambda x: x['utcTime'])

    return myAppts
        

    print('-------------\n{} locations\n{} w/ appointments\n{} in HRM'.format(len(allAppts), len(openAppts), len(hrmAppts)))

if __name__ == "__main__":
    main()