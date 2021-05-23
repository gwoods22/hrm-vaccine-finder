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

    payload={}
    headers = {
    'authority': 'sync-cf2-1.canimmunize.ca',
    'accept': 'application/json, text/plain, */*',
    'user-agent': 'Mozilla/5.0 (Macintosh',
    'origin': 'https://novascotia.flow.canimmunize.ca',
    'referer': 'https://novascotia.flow.canimmunize.ca/',
    }

    

    response = requests.request("GET", locationsUrl, headers=headers, data=payload)

    appts = response.json()['results']
    openAppts = list(filter(lambda x: not x['fullyBooked'], appts))
    hrmAppts = list(filter(lambda x: x['gisLocationString'].split(', ')[3] == 'Halifax County', openAppts))

    output = hrmAppts
    # output = list(map(lambda x: x['gisLocationString'], openAppts))
    output.sort(key=lambda x: x['gisLocationString'])

    myAppts = []

    for i in range(1, len(output)):
        apptsUrl = 'https://sync-cf2-1.canimmunize.ca/fhir/v1/public/availability/17430812-2095-4a35-a523-bb5ce45d60f1?appointmentTypeId={}&timezone=America%2FHalifax&preview=false'
        url = apptsUrl.format(output[i]['id'])

        response = requests.request("GET", url, headers=headers, data=payload)

        clinicName = output[i]['clinicName'].split(' - ')

        apptTime = response.json()[0]['availabilities'][0]['time']
        
        obj = {}
        obj['utcTime'] = apptTime,
        obj['apptTime'] = getLocal(apptTime),
        obj['id'] = output[i]['id'],
        obj['address'] = output[i]['gisLocationString'],
        if len(clinicName) == 3:
            obj['vaccine'] = clinicName[2],
            obj['name'] = clinicName[1]
        else:
            obj['name'] = ' '.join(clinicName)

        myAppts.append(obj)

    myAppts.sort(key=lambda x: x['utcTime'])

    with open('appts.json', 'w') as outfile:
        json.dump(myAppts, outfile)
        

    print('-------------\n{} locations\n{} w/ appointments\n{} in HRM'.format(len(appts), len(openAppts), len(hrmAppts)))

if __name__ == "__main__":
    main()