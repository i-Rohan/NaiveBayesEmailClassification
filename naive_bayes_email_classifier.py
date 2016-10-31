import base64
import os
import re
from random import randint

import oauth2client
from apiclient import errors
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
        print 'Storing credentials to ' + credential_path
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
        print 'An error occurred: %s' % error1


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
        return message
    except errors.HttpError as error1:
        print 'An error occurred: %s' % error1


def read_space_separated(input_file):
    for line in input_file:
        line_list = []
        for token in line.split():
            line_list.append(float(token))
        data_list.append(line_list)


print 'Reading Dataset'
data_list = []
# noinspection SpellCheckingInspection
with open('spambase.data', 'r') as data_file:
    read_space_separated(data_file)

print len(data_list), 'entries read from dataset'

print 'Retrieving Email List'
idList = list_messages(service, 'me')
print 'Email list retrieved'

emailsList = []

columnNames = []

with open('spambase.names') as f:
    for i in f:
        columnNames.append(i.replace('\n', ''))

datasetDivisionDict = dict((x, []) for x in columnNames)  # {'attribute_name':[q1,mean,q3,max_value]}

for i in xrange(0, len(columnNames)):
    q1 = 0.0
    count_q1 = 0
    mean = 0.0
    q3 = 0
    count_q3 = 0.0
    max_value = 0.0
    for j in xrange(0, len(data_list)):
        mean += data_list[j][i]
    mean /= len(data_list)

    for j in xrange(0, len(data_list)):
        if 0 <= data_list[j][i] < mean:
            q1 += data_list[j][i]
            count_q1 += 1
    q1 /= count_q1

    for j in xrange(0, len(data_list)):
        if data_list[j][i] >= mean:
            q3 += data_list[j][i]
            count_q3 += 1
    q3 /= count_q3

    for j in xrange(0, len(data_list)):
        if max_value < data_list[j][i]:
            max_value = data_list[j][i]

    datasetDivisionDict[columnNames[i]] = [q1, mean, q3, max_value]

for i in xrange(0, len(data_list)):
    for j in xrange(0, len(columnNames)):
        if 0.0 <= data_list[i][j] < datasetDivisionDict[columnNames[j]][0]:
            data_list[i][j] = 1
        elif datasetDivisionDict[columnNames[j]][0] <= data_list[i][j] < datasetDivisionDict[columnNames[j]][1]:
            data_list[i][j] = 2
        elif datasetDivisionDict[columnNames[j]][1] <= data_list[i][j] < datasetDivisionDict[columnNames[j]][2]:
            data_list[i][j] = 3
        elif datasetDivisionDict[columnNames[j]][2] <= data_list[i][j] < datasetDivisionDict[columnNames[j]][3]:
            data_list[i][j] = 4
        else:
            data_list[i][j] = 5

for i in data_list:
    if int(i[len(data_list[0]) - 1]) == 1:
        i[len(data_list[0]) - 1] = True
    else:
        i[len(data_list[0]) - 1] = False

for j in xrange(0, len(idList)):
    idDict = idList[j]
    # print 'Reading email with id', idDict['id']
    try:
        msgDict = get_message(service, 'me', idDict['id'])
        headersList = msgDict['payload']['headers']
        indexSubject = 0
        for i in range(0, len(headersList), 1):
            if headersList[i]['name'] == 'Subject':
                indexSubject = i

        body = ''
        if 'body' in msgDict['payload'] and msgDict['payload']['mimeType'] == 'text/plain':
            body += msgDict['payload']['body']['data']
        elif 'parts' in msgDict['payload'] and msgDict['payload']['parts'][0]['mimeType'] == 'text/plain':
            body += msgDict['payload']['parts'][0]['body']['data']
        elif 'parts' in msgDict['payload']['parts'][0] and \
                        msgDict['payload']['parts'][0]['parts'][0]['mimeType'] == 'text/plain':
            body += msgDict['payload']['parts'][0]['parts'][0]['body']['data']
        elif 'parts' in msgDict['payload']['parts'][0]['parts'][0] and \
                        msgDict['payload']['parts'][0]['parts'][0]['parts'][0]['mimeType'] == 'text/plain':
            body += msgDict['payload']['parts'][0]['parts'][0]['parts'][0]['body']['data']
        else:
            print 'Error in id: ', idDict['id']

        body = str(base64.b64decode(str(body).replace('-', '+').replace('_', '/')))
        body = body.decode('utf-8')
        # body = body.replace('\\r\\n', '\\n')
        # body = body.replace('\\n', '\n')
        subject = headersList[indexSubject]['value']
        email = subject + '\t' + body + '\n'

        if len(body) > 0:
            emailsList.append(email)

        temp = ''
        for c in email:
            if c.isalnum() or c.isspace():
                temp += c
            else:
                temp += ' '
        total_words = len(temp.split())
        words = ['make', 'address', 'all', '3d', 'our', 'over', 'remove', 'internet', 'order', 'mail', 'receive',
                 'will', 'people', 'report', 'addresses', 'free', 'business', 'email', 'you', 'credit', 'your', 'font',
                 '000', 'money', 'hp', 'hpl', 'george', '650', 'lab', 'labs', 'telnet', '857', 'data', '415', '85',
                 'technology', '1999', 'parts', 'pm', 'direct', 'cs', 'meeting', 'original', 'project', 're', 'edu',
                 'table', 'conference']
        count_words = dict((x, 0) for x in words)
        for w in re.findall(r"\w+", temp):
            if w in count_words:
                count_words[w] += 1
        total_chars = 0
        for i in email:
            if not i == ' ':
                total_chars += 1
        chars = [';', '(', '[', '!', '$', '#']
        count_chars = dict((x, 0) for x in chars)
        for w in email:
            if w in count_words:
                count_chars[w] += 1
        percent_words = dict((x, 0) for x in words)
        for k in percent_words.iterkeys():
            percent_words[k] = 100.0 * float(count_words[k]) / float(total_words)
        percent_chars = dict((x, 0) for x in chars)
        for k in percent_chars.iterkeys():
            percent_chars[k] = 100.0 * float(count_chars[k]) / float(total_chars)

        attributeValueList = []

        for i in xrange(0, len(words)):
            attributeValueList.append(percent_words[words[i]])

        for i in xrange(0, len(chars)):
            attributeValueList.append(percent_chars[chars[i]])

        for i in xrange(0, len(columnNames)):
            if 0.0 <= attributeValueList[i] < datasetDivisionDict[columnNames[i]][0]:
                attributeValueList[i] = 1
            elif datasetDivisionDict[columnNames[i]][0] <= attributeValueList[i] < \
                    datasetDivisionDict[columnNames[i]][1]:
                attributeValueList[i] = 2
            elif datasetDivisionDict[columnNames[i]][1] <= attributeValueList[i] < \
                    datasetDivisionDict[columnNames[i]][2]:
                attributeValueList[i] = 3
            elif datasetDivisionDict[columnNames[i]][2] <= attributeValueList[i] < \
                    datasetDivisionDict[columnNames[i]][3]:
                attributeValueList[i] = 4
            else:
                attributeValueList[i] = 5

        probability_true = 1.0
        probability_false = 1.0
        prob_true = []
        prob_false = []
        count_true = 0.0
        count_false = 0.0
        total = float(len(data_list))

        for i in data_list:
            if i[-1]:
                count_true += 1
            else:
                count_false += 1

        for i in xrange(0, len(data_list[0]) - 1):
            count = 0.0
            for k in data_list:
                if k[i] == attributeValueList[i] and k[-1]:
                    count += 1
            probability = count / count_true
            prob_true.append(probability)

        prob_true.append(count_true / total)

        for i in xrange(0, len(data_list[0]) - 1):
            count = 0.0
            for k in data_list:
                if k[i] == attributeValueList[i] and not k[-1]:
                    count += 1
            probability = count / count_false
            prob_false.append(probability)

        prob_false.append(count_false / total)

        for i in prob_true:
            probability_true *= i

        for i in prob_false:
            probability_false *= i

        if probability_true > probability_false:
            print idDict['id'], 'spam'
        elif probability_true == probability_false:
            random_no = randint(0, 1)
            if random_no == 1:
                print idDict['id'], 'spam'

    except Exception as e:
        print 'Error in id %s' % idList[j]['id']
        print 'Error Description: ', e
        pass
