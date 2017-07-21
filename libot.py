import os
import time
from slackclient import SlackClient
from weather import weather
from hello import hello
import json
import urllib2

# starterbot's ID as an environment variable
BOT_ID = "U62PWJXPA"

# constants
AT_BOT = "<@" + BOT_ID + ">"
#AT_BOT = "!"
EXAMPLE_COMMAND = "do"

# instantiate Slack & Twilio clients

valid_user = ["li-ha"]
admin_user = ["li-ha"]
command_list = ["start rds", "stop rds", "weather [location]", "my id", "channel id", "hello", "bye"]
valid_channel = ["C0MBBM4FJ"]
running = True



def handle_command(command, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    print("start handling...")
    print(command)
    print(channel)
    response = "Not sure what you mean. Use the *" + EXAMPLE_COMMAND + \
               "* command with numbers, delimited by spaces."
    #determine user
    user = ""
    msg = ""
    att = []


    if (channel in valid_channel):
        for msg in slack_client.rtm_read():
            print(msg)
     

            if msg.get("content"):
                #print(msg.get("content"))
                um = msg.get("content").split(":")
                print("user: " + um[0])
                print("msg: " + um[1])
                user = um[0]
                msg = um[1]
            else:
            	print("invalid rtm read. Please try again")

        #do stuff command, allow you to execute scripts etc
        if command.startswith(EXAMPLE_COMMAND):
            real_command = command[3:]
            if (real_command == "start rds"):
                if validate_user_command(user):
    
                    response = "starting rds..."
                else:
                    response = "Not a valid user..."
            elif (real_command == "stop rds"):
                if validate_user_command(user):
                    response = "stopping rds..."
                else:
                    response = "Not a valid user..."
            else:
                response = "please code this command first!"
    else:
        response = "please use 'libot' in a proper channel!"


###test
    users_list = slack_client.api_call("users.list")
    for mem in users_list["members"]:
        if(mem.get("name") == user):
            user_name = mem.get("profile").get("first_name") 
###




    if command[:] == "my id":
        user_dict = slack_client.api_call("users.list")
        for mem in user_dict["members"]:
            if(mem.get("name") == user):
                response = "Your first name is " + mem.get("profile").get("first_name") + ", Last name is " + mem.get("profile").get("last_name") + ". Your ID is " + mem.get("id") +"."

    #trivial command
    if command[:] == "hello":
        response = hello(user_name)
    if command[:] == "help":
        response = "Please use 'do' with the following avaliable commands " + str(command_list)
    if command[:] == "channel id":
        response = channel
    if command[0:7] == "weather":
    	location = command[8:]
    	response = weather(location)
    	if response == None:
    		response = "Please input an existed location!"
    if command[:] == "bye":
        if validate_user_command(user):
            response = "Shutting down..."
            global running
            running = False
        else:
            response = "Not a valid user."
    if command[:] == "notify":
        data = {
            "text":"Testing."
        }
        req = urllib2.Request('https://hooks.slack.com/services/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')
        req.add_header('Content-Type', 'application/json')
        res = urllib2.urlopen(req, json.dumps(data))

        response = "ok"
    if command[:] == "game":
        data = {
                "text": "Which rds would you like to start?",
                "attachments": [
                    {
                        "text": "Choose a rds to start",
                        "fallback": "You are unable to choose a game",
                        "callback_id": "wopr_game",
                        "color": "#3AA3E3",
                        "attachment_type": "default",
                        "actions": [
                            {
                                "name": "game",
                                "text": "li-db",
                                "type": "button",
                                "value": "li-db",
                                "confirm": {
                                    "title": "Are you sure?",
                                    "text": "This will start li-db rds",
                                    "ok_text": "Yes",
                                    "dismiss_text": "No"
                                }

                            },
                            {
                                "name": "game",
                                "text": "li-db01",
                                "type": "button",
                                "value": "li-db01",
                                "confirm": {
                                    "title": "Are you sure?",
                                    "text": "This will start li-db01 rds",
                                    "ok_text": "Yes",
                                    "dismiss_text": "No"
                                }
                            },
                            {
                                "name": "game",
                                "text": "gao-test01",
                                "type": "button",
                                "value": "gao-test01",
                                "confirm": {
                                    "title": "Are you sure?",
                                    "text": "This will start gao-test01 rds",
                                    "ok_text": "Yes",
                                    "dismiss_text": "No"
                                }
                            }
                        ]
                    }
                ]
            }
        #req = urllib2.Request('https://hooks.slack.com/services/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')
        #req.add_header('Content-Type', 'application/json')
        #res = urllib2.urlopen(req, json.dumps(data))
        att = data.get("attachments")
        response = "game started"




    
    

    slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True, attachments=att)


def validate_user_command(user):
    if user in valid_user:
        return True
    else:
        return False

def notify_adminiser(user, command):
    return None




def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']
    return None, None


if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("StarterBot connected and running!")
        while running:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:

                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")