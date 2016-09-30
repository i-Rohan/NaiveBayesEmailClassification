import base64
import os
import time

import oauth2client
import re
from apiclient import errors
# noinspection PyUnresolvedReferences
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import client
from oauth2client import tools

try:
    # noinspection PyUnresolvedReferences
    import argparse

    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

SCOPES = 'https://mail.google.com/'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Naive Bayes Email Class'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials1 = store.get()
    if not credentials1 or credentials1.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials1 = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatability with Python 2.6
            credentials1 = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials1


credentials = get_credentials()
service = build('gmail', 'v1', http=credentials.authorize(Http()))


def list_messages(service1, user_id):
    """List all Messages of the user's mailbox matching the query.

    Args:
      service1: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
      can be used to indicate the authenticated user.
      Eg.- 'from:user@some_domain.com' for Messages from a particular sender.

    Returns:
      List of Messages that match the criteria of the query. Note that the
      returned list contains Message IDs, you must use get with the
      appropriate ID to get the details of a Message.
    """
    try:
        response = service1.users().messages().list(userId=user_id, maxResults=10, includeSpamTrash=True).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])

        # while 'nextPageToken' in response:
        #     page_token = response['nextPageToken']
        #     response = service.users().messages().list(userId=user_id, pageToken=page_token, maxResults=500,
        #                                                includeSpamTrash=True).execute()
        #     messages.extend(response['messages'])

        return messages
    except errors.HttpError as error1:
        print('An error occurred: %s' % error1)


def get_message(service1, user_id, msg_id):
    """Get a Message with given ID.

    Args:
      service1: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
      can be used to indicate the authenticated user.
      msg_id: The ID of the Message required.

    Returns:
      A Message.
    """
    try:
        message = service1.users().messages().get(userId=user_id, id=msg_id, format='full').execute()

        # print('Message snippet: %s' % message['snippet'])

        return message
    except errors.HttpError as error1:
        print('An error occurred: %s' % error1)


def read_space_separated(f):
    for line in f:
        line_list = []
        for token in line.split():
            line_list.append(token)
        line_tuple = tuple(line_list)
        del line_list
        data_list.append(line_tuple)


startTime = time.time()
print 'Reading Dataset'
data_list = []
# noinspection SpellCheckingInspection
with open('spambase.data', 'r') as data_file:
    read_space_separated(data_file)

data_tuple = tuple(data_list)
del data_list
print len(data_tuple), 'lines read successfully in', time.time() - startTime, 's'

print('Starting Gmail API...\nPlease Wait...')
idList = list_messages(service, 'me')
emailContent = []
success = 0
error = 0
print('Reading email...')
for j in range(0, len(idList), 1):
    idDict = idList[j]
    # print(idDict['id'])
    try:
        msgDict = get_message(service, 'me', idDict['id'])
        headersList = msgDict['payload']['headers']
        indexSubject = 0
        for i in range(0, len(headersList), 1):
            if headersList[i]['name'] == 'Subject':
                indexSubject = i
        indexParts = 0

        body = ''
        if 'body' in msgDict['payload'] and 'parts' not in msgDict['payload']:
            body += msgDict['payload']['body']['data']
        elif 'parts' in msgDict['payload']['parts'][0]:
            if 'data' in msgDict['payload']['parts'][0]['parts'][0]['body']:
                body += msgDict['payload']['parts'][0]['parts'][0]['body']['data']
            elif 'parts' in msgDict['payload']['parts'][0]['parts'][0]:
                body += msgDict['payload']['parts'][0]['parts'][0]['parts'][0]['body']['data']
        else:
            body += msgDict['payload']['parts'][0]['body']['data']

        body = str(base64.b64decode(str(body).replace('-', '+').replace('_', '/')))
        body = body.decode('utf-8')
        # print body
        # body = (body[2:len(body) - 1])
        body = body.replace('\\r\\n', '\\n')
        body = body.replace('\\n', '\n')
        subject = headersList[indexSubject]['value']
        emailContent.append(subject + '\t' + body + '\n')
        email = subject + '\t' + body + '\n'
        temp = ''
        for c in email:
            if c.isalnum() or c.isspace():
                temp += c
            else:
                temp += ' '
        total_words = len(temp.split())
        print temp
        words = ['make']
        count_make = dict((x, 0) for x in words)
        for w in re.findall(r"\w+", temp):
            if w in count_make:
                count_make[w] += 1
        print idList[j]['id'], total_words,count_make
        success += 1
    except Exception as e:
        print 'Error in id %s' % idList[j]['id']
        print e
        error += 1
        pass
    print('\t%f%% complete\t\tsuccess %%age: %f%%\t\telapsed time: %f min' % (
        float((j + 1) * 100) / float(len(idList)), float(success * 100) / float(success + error),
        (time.time() - startTime) / 60))
