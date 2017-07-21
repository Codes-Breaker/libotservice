from __future__ import print_function

#import pkg_resources
#pkg_resources.require('boto3==1.4.4')

import json
import logging
import os
import urlparse
import urllib2
import boto3
import requests



from base64 import b64decode
from urllib2 import Request, urlopen, URLError, HTTPError

from datetime import datetime

# The base-64 encoded, encrypted key (CiphertextBlob) stored in the kmsEncryptedHookUrl environment variable
#ENCRYPTED_HOOK_URL = os.environ['kmsEncryptedHookUrl']
ENCRYPTED_HOOK_URL = 'AQECAHgN+EO3/WK4OSQ6+LT8mb9dh3Ezn+Z3rRV2zmeLIEO3fQAAAKcwgaQGCSqGSIb3DQEHBqCBljCBkwIBADCBjQYJKoZIhvcNAQcBMB4GCWCGSAFlAwQBLjARBAy5xgpW/y3Ln4+zS34CARCAYMxTluEn89V0IBRlr7rrmxCDz8I/DNCn2/GbnS1iKunohqS6fPzSDPQJaZQoElyZpRcu2iWXoArypeDv75pJ5qpxcOdV5jlpfj2g2LdNAiVanQqJJhKCl3eL6a1f1Q49GA==' 
# The Slack channel to send a message to stored in the slackChannel environment variable
SLACK_CHANNEL = os.environ['slackChannel']

MY_HOOK = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
SLACK_BOT_HOOK = 'xxxxxxxxxxxxxxxxxxxxxxxxxxx'
#HOOK_URL = SLACK_BOT_HOOK
#SLACK_CHANNEL = '@li-ha' 
valid_channel = ["C0MBBM4FJ"]

#This is hook is for lovelive-pj-unit channel
HOOK_URL = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
logger = logging.getLogger()
logger.setLevel(logging.INFO)
TOKEN = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"



RDS_LIST = os.environ['RDSList'].split(',')
#RDS_LIST = {'li-db','gao-test01'}
RESOURCE_ARN = os.environ['ResourceARN']
#RESOURCE_ARN = 'arn:aws:rds:ap-northeast-1:655825577598:db:'
TAG_NAME = os.environ['TagName']
#TAG_NAME = 'using'
INTERVAL_MINUTES = int(os.environ['IntervalMinutes'])
#INTERVAL_MINUTES = 10
AUTH_USERS = os.environ['AuthUsers'].split(',')
client = boto3.client("rds")
channel = "C0MBBM4FJ"

def key_list(client, rds):
    response = client.list_tags_for_resource(
        ResourceName=RESOURCE_ARN + rds,
    )

    return [x['Key'] for x in response['TagList']]


def has_key(client, rds):
    keys = key_list(client, rds)

    if TAG_NAME in keys:
        return True
    else:
        return False


def key_remove(client, rds):
    response = client.remove_tags_from_resource(
        ResourceName=RESOURCE_ARN + rds,
        TagKeys=[
            TAG_NAME,
        ]
    )
    return response['ResponseMetadata']['HTTPStatusCode']

def key_add(client, rds):
    response = client.add_tags_to_resource(
        ResourceName=RESOURCE_ARN + rds,
        Tags=[
            {
                'Key':TAG_NAME,
                'Value':'yes'
            }
        ]
    )

    return response['ResponseMetadata']['HTTPStatusCode']

def db_instance_status(client, rds):
    response = client.describe_db_instances(
        DBInstanceIdentifier=rds,
    )

    return response['DBInstances'][0]['DBInstanceStatus']

def slack_send(text):
    slack_message = {
        'channel': SLACK_CHANNEL,
        'text': text
    }
    
    req = Request(HOOK_URL, json.dumps(slack_message))
    try:
        response = urlopen(req)
        response.read()
        logger.info("Message posted to %s", slack_message['channel'])
    except HTTPError as e:
        logger.error("Request failed: %d %s", e.code, e.reason)
    except URLError as e:
        logger.error("Server connection failed: %s", e.reason)

def warning_db_start(client, rds):
    data = {
                "text": "Warning!",
                "response_type": "ephemeral",
                "attachments": [
                    {
                        "text": "Please confirm if you want to start " + rds,
                        "fallback": "You are unable to choose",
                        "callback_id": "wopr_game",
                        "color": "#3AA3E3",
                        "attachment_type": "default",
                        "actions": [
                            {
                                "name": "game",
                                "text": "Yes",
                                "style": "primary",
                                "type": "button",
                                "value": rds +",start, warning",

    
                            },
                            {
                                "name": "game",
                                "text": "No",
                                "type": "button",
                                "value": "no",
                            }
                        ]
                    }
                ]
            }
    req = urllib2.Request(HOOK_URL)
    req.add_header('Content-Type', 'application/json')
    res = urllib2.urlopen(req, json.dumps(data))
    return "success"

        
def warning_db_stop(client, rds):
    data = {
                "text": "Warning!",
                "response_type": "ephemeral",
                "attachments": [
                    {
                        "text": "Please confirm if you want to stop " + rds,
                        "fallback": "You are unable to choose",
                        "callback_id": "wopr_game",
                        "color": "#3AA3E3",
                        "attachment_type": "default",
                        "actions": [
                            {
                                "name": "game",
                                "text": "Yes",
                                "style": "primary",
                                "type": "button",
                                "value": rds +",stop, warning",

    
                            },
                            {
                                "name": "game",
                                "text": "No",
                                "type": "button",
                                "value": "no",
                            }
                        ]
                    }
                ]
            }
    req = urllib2.Request(HOOK_URL)
    req.add_header('Content-Type', 'application/json')
    res = urllib2.urlopen(req, json.dumps(data))
    return "success"

def get_lastest_start_time(client, rds):
    response = client.describe_events(
        SourceIdentifier=rds,
        SourceType='db-instance',
        StartTime=datetime.fromtimestamp(int(datetime.now().strftime('%s'))-3600 * 20),
    )

    
    events = [x for x in response['Events'] if x['Message']=="DB instance started"]
    if len(events) > 0:
        start_time = events[-1]['Date']
        start_time = int(start_time.strftime('%s'))
    else:
        start_time = 0

    return start_time

def lambda_handler(event, context):
    keys = event.keys()

    user = ""
    
    if 'action' not in keys:
        # Slack->GatewayApi->lambda 
        if 'body' not in keys:
            return False
        else:
            
            params = urlparse.parse_qs(event['body'])
            ### gao's method
            if params.has_key('user_name'):
                user = params['user_name'][0]
                if not check_valid(user):
                    err = 'Invalid user!'
                    slack_send(err)
                    ret = user + " is trying to perform action!"
                    notify(ret)
                    return err

                command_args = params['text'][0].split(' ')

                command_args = map(lambda n:n.strip(' ').strip('"').strip("'"), command_args)

                if len(command_args) == 10:
                    err = "Wrong Parameters!"
                    slack_send(err)
                    return err
                else:
                    action = command_args[0]
                    if action.lower() == 'start' or action.lower() == 'stop':
                        rds = command_args[1]
                    else:
                        rds = ""
            ### li's list method with action url trigger
            else:
                name = params["payload"][0].split("\"")[47]
                choice = params["payload"][0].split("\"")[13]
                response_url = params["payload"][0].split("\"")[-2].replace("\\/","/")
                if (choice.lower() == "no"):
                    data = {
                        "text":"bye",
                        "token": TOKEN,
                        "delete_original": True
                    }
                    r = requests.post(response_url, data=json.dumps(data))
                    #show_current_db_status(response_url)
                    return 
                if (choice.lower() == "update"):
                    show_current_db_status(response_url)
                    return
                if (choice.lower() == "progress"):
                    return "This instance is still in progress! Please wait"

                #check if the instance is already available
                task_tuple = choice.split(",")
                rds = task_tuple[0]
                action = task_tuple[1]
                status = db_instance_status(client, rds)
                if (action == "start"):
                    if (status == "available"):
                        response = "This instance is already started! Please pick another one."
                        return response
                    if (status == "stopping" or status == "starting"):
                        response = "This instance is in progress"
                        return response
                    if check_valid(name):
                        db_start(client, rds)
                        response = name + " picked "+ rds + " to start. Starting now."
                        if (len(task_tuple) == 2): 
                            show_current_db_status(response_url)
                        slack_send(response)
                        return "success"
                    else:
                        response = "Invalid User."
                        return response
                elif (action == "stop"):
                    if (status == "stopped"):
                        response = "This instance is already stopped! Please pick another one."
                        return response
                    if (status == "stopping" or status == "starting"):
                        response = "This instance is in progress"
                        return response  

                    if check_valid(name):
                        db_stop(client, rds)
                        response = name + " picked "+ rds + " to stop. Stopping now."
                        if (len(task_tuple) == 2):  
                            show_current_db_status(response_url)
                        slack_send(response)
                        return "success"
                    else:
                        response = "Invalid User."
                        return response
                else:
                    response = "Please use start/stop"
                
                return
    ### others 
    else:
        action = event['action']
    
    if 'rds' in keys:
        rds = event['rds']

    if action.lower() not in {'start', 'stop', 'scan', 'list'}:
        err = 'Wrong commands!'
        slack_send(err)
        return err
    else:
        if action.lower() != 'scan' and action.lower() != 'list':
            if rds not in RDS_LIST:
                err = 'Please provide a valid database name.'
                slack_send(err)
                return err

    
    
    if action.lower() == 'start':
        if db_instance_status(client, rds) != 'stopped':
            err = "RDS %s is not stopped. Can't be started" % rds
            slack_send(err)
            return err

        if has_key(client, rds):
            status = key_remove(client, rds)
            if status != 200:
                err = "Can't delete the old key"
                slack_send(err)
                return err
                
        key_add(client, rds)
        
        warning_db_start(client, rds)
        
        #ret = 'RDS %s is starting by %s' % (rds, user)
        ret = "showing confirmation"
        #slack_send(ret)
        return ret
    elif action.lower() == 'stop':
        if db_instance_status(client, rds) != 'available':
            err = "RDS %s is not available. Can't be stopped" % rds
            slack_send(err)
            return err 

        if has_key(client, rds):
            status = key_remove(client, rds)
            if status != 200:
                err = "Can't delete the old key"
                slack_send(err)
                return err

        warning_db_stop(client, rds)
        #ret = 'RDS %s is stopping by %s' % (rds, user)
        ret = "showing confirmation"
        #slack_send(ret)
        return ret
        
    elif action.lower() == 'scan':
        for instance in RDS_LIST:
            if db_instance_status(client, instance) == 'available':
                if has_key(client, instance):
                    continue

                start_time = get_lastest_start_time(client, instance)
                now = int(datetime.now().strftime('%s'))
                if now - start_time > INTERVAL_MINUTES * 60:
                    db_stop(client, instance)
                    ret = "RDS %s is stopping" % instance
                    slack_send(ret)
                else:
                    ret = "RDS %s will be stopped in %d minutes" % (instance, INTERVAL_MINUTES)
                    slack_send(ret)
    
    elif action.lower() == 'list':
    	show_current_db_status(HOOK_URL)
    	return "Showing list of rds(s)"


def notify(result):
    data = {
        "text":result
    }
    req = urllib2.Request(MY_HOOK)
    req.add_header('Content-Type', 'application/json')
    res = urllib2.urlopen(req, json.dumps(data))

def show_current_db_status(url):
    data = {
                "text": "Status",
                "attachments": [
                    {
                        "text": "Running rds(s)",
                        "fallback": "failed",
                        "callback_id": "wopr_game",
                        "color": "#3AA3E3",
                        "attachment_type": "default",
                        "actions": [
                            
                        ]
                    },
                    {
                        "text": "Stopped rds(s)",
                        "fallback": "failed",
                        "callback_id": "wopr_game",
                        "color": "#3AA3E3",
                        "attachment_type": "default",
                        "actions": [
                            
                        ]
                    },
                    {
                        "text": "In Progress rds(s)",
                        "fallback": "failed",
                        "callback_id": "wopr_game",
                        "color": "#3AA3E3",
                        "attachment_type": "default",
                        "actions": [
                            
                        ]
                    },
                    {
                        "text": "Option",
                        "fallback": "failed",
                        "callback_id": "wopr_game",
                        "color": "#3AA3E3",
                        "attachment_type": "default",
                        "actions": [
                            
                        ]
                    }

                ],
                "token":TOKEN,
                "delete_original": True
            }
            
    for database in RDS_LIST:
        if db_instance_status(client, database) == 'available':
            data["attachments"][0]["actions"].append({ 
                        "name": "game",
                        "text": database,
                        "type": "button",
                        "value": database+",stop",
                        "style": "primary",
                        "confirm": {
                            "title": "Are you sure?",
                            "text": "This will stop "+database,
                            "ok_text": "Yes",
                            "dismiss_text": "No"
                            }

                        })
        elif db_instance_status(client,database)== 'stopped':
            data["attachments"][1]["actions"].append({ 
                        "name": "game",
                        "text": database,
                        "type": "button",
                        "value": database+",start",
                        "style": "danger",
                        "confirm": {
                            "title": "Are you sure?",
                            "text": "This will start "+database,
                            "ok_text": "Yes",
                            "dismiss_text": "No"
                            }
                        })
        else:
            data["attachments"][2]["actions"].append({ 
                        "name": "game",
                        "text": database,
                        "type": "button",
                        "value": "progress",
                        "confirm": {
                            "title": "Sorry!",
                            "text": database + " is still in progress, please wait",
                            "ok_text": "Send",
                            "dismiss_text": "Cancel"
                            }
                        })


    data["attachments"][3]["actions"].append({ 
                "name": "game",
                "text": "cancel",
                "type": "button",
                "value": "no"
                })

    data["attachments"][3]["actions"].append({ 
                "name": "game",
                "text": "update",
                "type": "button",
                "value": "update"
                })




    requests.post(url, data=json.dumps(data))
    return

def db_start(client, db_name):
    response = client.start_db_instance(
            DBInstanceIdentifier=db_name
        )    

def db_stop(client, db_name):
    response = client.stop_db_instance(
            DBInstanceIdentifier=db_name
        )



def check_valid(user):
    if user in AUTH_USERS:
        return True
    else:
        return False
