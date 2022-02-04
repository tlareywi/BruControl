import requests
from requests.auth import HTTPBasicAuth

import _tkinter
import tkinter
from tkinter import *
from tkinter import ttk

# See https://api.brewfather.app
auth = HTTPBasicAuth('Get From Brewfather site/account', 'Get From Brewfather site/account')

def getBatch( batchId ):
    query = {'include' : 'recipe.mash,recipe.equipment'}
    #query = {'include' : ''}
    response = requests.get('https://api.brewfather.app/v1/batches/' + batchId, auth=auth, params=query)
    batch = response.json()

    data = '[{"Name":"Recipe","Value":"' + batch['recipe']['name'] + '"}'

    #print(batch['recipe'])
    
    # Mash Steps
    indx = 1
    for step in batch['recipe']['mash']['steps']:
        data = data + ', {"Name":"Mash Temp ' + str(indx) + '","Value":"' + str(step['displayStepTemp']) + '"}'
        data = data + ', {"Name":"Mash Rest ' + str(indx) + '","Value":"00:' + str(step['stepTime']) + ':00"}'
        indx = indx + 1
    
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

    boilVol = batch['recipe']['equipment']['boilSize'] * 0.264172 # Liters -> Gallons
    data = data + ', {"Name":"Target Sparge Vol","Value":"' + str(boilVol) + '"'

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