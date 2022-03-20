import requests
from requests.auth import HTTPBasicAuth
import json

import _tkinter
import tkinter
from tkinter import *
from tkinter import ttk

# Replace with auth data from Brewfather
auth = HTTPBasicAuth('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')

def getBatch( batchId ):
    query = {'include' : 'recipe.mash,recipe.equipment,recipe.data'}
    #query = {'include' : ''} # Uncommenting will pull down 'all' batch data

    response = requests.get('https://api.brewfather.app/v1/batches/' + batchId, auth=auth, params=query)
    batch = response.json()
    #print( json.dumps(batch, indent=2) )

    data = '[{"Name":"Recipe","Value":"' + batch['recipe']['name'] + '"}'
    
    # Mash Steps
    indx = 1
    for step in batch['recipe']['mash']['steps']:
        data = data + ', {"Name":"Mash Temp ' + str(indx) + '","Value":"' + str(step['displayStepTemp']) + '"}'
        hours = int(step['stepTime'] / 60)
        minutes = step['stepTime'] % int(60)
        data = data + ', {"Name":"Mash Rest ' + str(indx) + '","Value":"' + str(hours) + ':' + str(minutes) + ':00"}'
        indx = indx + 1
    
    # Zero out any remaining from previous batch
    while indx < 7:
        data = data + ', {"Name":"Mash Temp ' + str(indx) + '","Value":"0.00"}'
        data = data + ', {"Name":"Mash Rest ' + str(indx) + '","Value":"00:00:00"}'
        indx = indx + 1 

    # Boil Time
    hours = int(batch['recipe']['equipment']['boilTime'] / 60)
    minutes = batch['recipe']['equipment']['boilTime'] % int(60)
    if minutes < 10:
        data = data + ', {"Name":"Boil Time","Value":"0' + str(hours) + ':0' + str(minutes) +':00"}'
    else:
        data = data + ', {"Name":"Boil Time","Value":"0' + str(hours) + ':' + str(minutes) +':00"}' 

    # Target pre-boil volume
    boilVol = batch['recipe']['equipment']['boilSize'] * 0.264172 # Liters -> Gallons
    data = data + ', {"Name":"Target Sparge Vol","Value":"' + str(boilVol) + '"}'

    # Water Strike Temp
    strikeTemp =  batch['recipe']['data']['strikeTemp'] * 1.80 + 32.0 # C -> F
    data = data + ', {"Name":"Strike Temp","Value":"' + str(strikeTemp) + '"}'

    # Mash water volume
    strikeVol =  batch['recipe']['data']['mashWaterAmount'] * 0.264172 # Liters -> Gallons
    data = data + ', {"Name":"Strike Volume","Value":"' + str(strikeVol) + '"}'

    data = data + ']'
    headers = {"Content-Type": "application/json"}
    response = requests.put('http://localhost:8000/globals', data=data, headers=headers)
    if response.status_code != 200:
        print('Failed to put batch data to BruControl.')
        print( data )    

def refresh():
    for btn in button_list:
        btn.destroy()

    response = requests.get('https://api.brewfather.app/v1/batches', auth=auth)
    if response.status_code != 200:
        print('Failed to obtain batch list.')

    batches = response.json()
    for batch in batches:
        if batch['status'] == 'Planning' or batch['status'] == 'Brewing':
            button = ttk.Button(frame, text = batch['name'] + " " + str(batch['batchNo']) + ", " + batch['recipe']['name'], command = lambda v = batch['_id']: getBatch(v) )
            button.pack(pady=5)
            button_list.append( button )

# MAIN ########################################################################
root = Tk()
root.title('BruGlu')
root.tk.call("source", "azure.tcl")
root.tk.call("set_theme", "dark")
root.geometry("320x400")
frame = Frame(root)
frame.pack(pady=5)

button = ttk.Button(frame, text = 'Refresh List', command = refresh )
button.pack(pady=5)

button_list = []

refresh()

root.mainloop()