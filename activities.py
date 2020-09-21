import requests
import json
from tkinter import *
from functools import partial
import urllib
from urllib.request import urlopen
from PIL import Image, ImageTk
import io
from io import BytesIO
import polyline

'''
View list of Strava activities an select an activity to post to Racemappr
Kate Grossman, July 2020
'''

#Requesting a new authorization key (this only needs to be done when the old one has expired)
def requestAuth():
    url = "https://www.strava.com/oauth/token?client_id=50254&client_secret=9893718c765650f24515828a87b6099b34c817b5&refresh_token=09a57caf0eb4688f143147714dbe07ed0a336547&grant_type=refresh_token"
    response = requests.request("POST", url).json()
    return response.get("access_token")

#Request a list of an athlete's activities
#Strava's defualt is 1 page and 30 activities per page, but can be changed by specifying these parameters in the request
def requestActivity():
    url = "https://www.strava.com/api/v3/athlete/activities/"
    headers = {'Authorization': 'Bearer ' + auth}
    activities = requests.request("GET", url, headers=headers).json()
    return activities

#Request one activity's details
#We specifically need this to get the activity description, as it is not available in the list of activities request
def requestActivityDetails(id):
    url = "https://www.strava.com/api/v3/activities/" + str(id)
    headers = {'Authorization': 'Bearer ' + auth}
    response = requests.request("GET", url, headers=headers).json()
    return response

#Request all photos from one activity
def requestActivityPhotos(id):
    url = "https://www.strava.com/api/v3/activities/" + str(id) + "/photos?photo_sources=true&size=400"
    headers = {'Authorization': 'Bearer ' + auth}
    pics = requests.request("GET", url, headers=headers).json()
    return pics

#Get information about a single acitvity
def getActivityInfo(activity):
    monthList = ["Jan", "Feb", "Mar", "Apr", "May", "June", "July", "Aug", "Sep", "Oct", "Nov", "Dec"]
    act = requestActivityDetails(activity.get("id"))
    name = act.get("name")
    type = act.get("type")
    date = monthList[int(activities[i].get("start_date").split("-")[1])]+" "+activities[i].get("start_date").split("-")[2].split("T")[0]
    distance = str(int(act.get("distance"))/1000)+" km"
    time = str(int(act.get("moving_time"))/60)+" min"
    description = act.get("Description")
    map = getMap(activity.get("map").get("summary_polyline"))
    photos = getPhotos(activity)
    return name, type, date, distance, time, description, map, photos

#Creates map from polyline
def getMap(p):
    if p:
        poly = polyline.decode(p)
        maxLat = max(poly)[0]
        minLat = min(poly)[0]
        maxLong = max(poly)[1]
        minLong = min(poly)[1]
        centerLat = minLat+(maxLat-minLat)/2
        centerLong = minLong+(maxLong-minLong)/2

        #Google maps api request
        url = "https://maps.googleapis.com/maps/api/staticmap?size=200x200&center="+str(centerLat)+" "+str(centerLong)+"&zoom=14&path=weight:3%7Ccolor:blue%7Cenc:"+p+"&key=AIzaSyDlczj1ehGAZ7Gbw8ZFOpt5xlWKfFyT0TI&user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
        response = requests.request("GET", url)

        map = ImageTk.PhotoImage(Image.open(BytesIO(response.content)))
        return map

def getPhotos(activity):
    photos = []
    numPics = activity.get("total_photo_count")
    if (numPics != 0):
        pics = requestActivityPhotos(activity.get("id"))
        urls = []

        i = 0
        while (i < numPics):
            url = pics[i].get("urls").get("400")
            image = Image.open(io.BytesIO(urllib.request.urlopen(url).read()))
            percent = (200/float(image.size[1]))
            width = int((float(image.size[0])*float(percent)))
            img = ImageTk.PhotoImage(image.resize((width, 200), Image.ANTIALIAS))
            photos.append(img)
            i = i + 1

    return photos

#New window with the details of a selected activity
def post(name, type, distance, time, description, map, photos):
    #Create popup
    popup = Toplevel()
    popup.title("Activity")
    Label(popup, text="Your Activity:", font=("Helvetica", 60)).pack()

    Label(popup, text=name).pack()
    Label(popup, text=type).pack()
    Label(popup, text=distance).pack()
    Label(popup, text=time).pack()
    if description:
        Label(popup, text=description).pack()

    #Map
    m = Label(popup, image=map)
    m.image = map #Keep a reference
    m.pack()

    #Photos
    for photo in photos:
        pic = Label(popup, image=photo)
        pic.image = photo #Keep a reference
        pic.pack(side=LEFT)

#---------main-----------------------------------------------------------------

global auth
auth = requestAuth()

#Create main window
app = Tk()
app.title("Post Strava Activities to Feed")
Label(app, text="Choose a Strava Activity:", font=("Helvetica", 60)).pack()

#Create list of Activities
i = 0
activities = requestActivity()
for activity in activities:
    pane = PanedWindow()
    pane.pack(fill=BOTH, expand=1)

    name, type, date, distance, time, description, map, photos = getActivityInfo(activity)

    pane.add(Label(app, text=name, width=25, font=("Helvetica", 26, "bold"), anchor="w"))
    pane.add(Label(app, text=distance + " km " + type + " on " + date, width=30, font=("Helvetica", 28), anchor="w"))
    pane.add(Button(app, text=("POST"), font=("Helvetica", 10), command=partial(post, name, type, distance, time, description, map, photos), justify=CENTER, padx=20, pady=20))

    if i == 10:
        break

    i = i + 1

app.mainloop()
