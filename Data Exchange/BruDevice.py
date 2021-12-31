import requests
from requests.auth import HTTPBasicAuth

import _tkinter
import tkinter
from tkinter import *
from tkinter import ttk

blueTemp = 0
blueGrav = 0
purpleTemp = 0
purpleGrav = 0

def pushData():
    r = requests.get('http://localhost:8000/global/SpGr1')
    if r.status_code != 200:
        print( "Error response from BruControl " + str(r.status_code) )
    else:
        blueGrav = r.json()['Value']
    
    r = requests.get('http://localhost:8000/global/Temp1')
    if r.status_code != 200:
        print( "Error response from BruControl " + str(r.status_code) )
    else:
        blueTemp = r.json()['Value']

    r = requests.get('http://localhost:8000/global/SpGr2')
    if r.status_code != 200:
        print( "Error response from BruControl " + str(r.status_code) )
    else:
        purpleGrav = r.json()['Value']

    r = requests.get('http://localhost:8000/global/Temp2')
    if r.status_code != 200:
        print( "Error response from BruControl " + str(r.status_code) )
    else:
        purpleTemp = r.json()['Value']

    print("Purple ", purpleTemp, ", ", purpleGrav)
    print("Blue ", blueTemp, ", ", blueGrav)    

    data = {}
    data['name'] = 'Purplegravity'
    data['temp'] = purpleTemp
    data['aux_temp'] = 0.0
    data['ext_temp'] = 0.0
    data['temp_unit'] = 'F'
    data['gravity'] = purpleGrav
    data['gravity_unit'] = "G" #SpGr
    data['pressure'] = 0
    data['pressure_unit'] = "PSI"
    data['ph'] = 0.0
    data['comment'] = ""
    data['beer'] = ""
    # Replace stream id with brewfather provided custom stream id for account
    r = requests.post('http://log.brewfather.net/stream?id=xxxxxxxxxxxxxxxxxxx', json=data)
    if r.status_code != 200:
        print( "Error response from Brewfather " + str(r.status_code) )

    data = {}
    data['name'] = 'Bluegravity'
    data['temp'] = blueTemp
    data['aux_temp'] = 0.0
    data['ext_temp'] = 0.0
    data['temp_unit'] = 'F'
    data['gravity'] = blueGrav
    data['gravity_unit'] = "G" #SpGr
    data['pressure'] = 0
    data['pressure_unit'] = "PSI"
    data['ph'] = 0.0
    data['comment'] = ""
    data['beer'] = ""
    # Replace stream id with brewfather provided custom stream id for account
    r = requests.post('http://log.brewfather.net/stream?id=xxxxxxxxxxxxxxxxxxx', json=data)
    if r.status_code != 200:
        print( "Error response from Brewfather " + str(r.status_code) )

    root.after(900000, pushData)

# MAIN ########################################################################
root = Tk()
root.title('BruDevice')
root.tk.call("source", "azure.tcl")
root.tk.call("set_theme", "dark")
root.geometry("320x320")
frame = Frame(root)
frame.pack(pady=5)

pushData()

root.mainloop()