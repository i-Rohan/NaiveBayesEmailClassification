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
from pymongo import MongoClient

try:
    import argparse

    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

###############################################################################
# CONSTANTS
# For use in gmail API
###############################################################################
SCOPES = 'https://mail.google.com/'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Naive Bayes Email Class'

###############################################################################
# CONSTANTS
# For use as dictionary keys in dataset
###############################################################################
attributeList = []


###############################################################################
# get_credentials
#
# Gets valid user credentials from storage.
#
#     If nothing has been stored, or if the stored credentials are invalid,
#     the OAuth2 flow is completed to obtain the new credentials.
#
#     Returns:
#         Credentials, the obtained credential.
###############################################################################
def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, 'gmail-quickstart.json')
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


###############################################################################
# list_message
#
# List all Messages of the user's mailbox matching the query.
#
#     Args:
#       service1: Authorized Gmail API service instance.
#       user_id: User's email address. The special value "me"
#       can be used to indicate the authenticated user.
#       Eg.- 'from:user@some_domain.com' for Messages from a particular sender.
#
#     Returns:
#       List of Messages that match the criteria of the query. Note that the
#       returned list contains Message IDs, you must use get with the
#       appropriate ID to get the details of a Message.
###############################################################################
def list_messages(service1, user_id):
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


###############################################################################
# get_message
#
# Get a Message with given ID.
#
#     Args:
#       service1: Authorized Gmail API service instance.
#       user_id: User's email address. The special value "me"
#       can be used to indicate the authenticated user.
#       msg_id: The ID of the Message required.
#
#     Returns:
#       A Message.
###############################################################################
def get_message(service1, user_id, msg_id):
    try:
        message = service1.users().messages().get(userId=user_id, id=msg_id, format='full').execute()
        return message
    except errors.HttpError as error1:
        print 'An error occurred: %s' % error1


###############################################################################
# read_dataset
#
# Reads data from file and stores in a list
# parameters:
#     - collection_name: name of the data file containing the training data records
#
# returns: trainingSet: a list of training records (each record is a dict,
#                       that contains attribute values for that record.)
###############################################################################
def read_dataset(collection_name):
    dataset = []

    mongo_client = MongoClient('localhost:27017')  # make server connection
    db = mongo_client.spambase  # access database
    collection = db[collection_name]  # access collection
    result = collection.find()
    for row in result:
        dataset.append(row)

    return dataset


###############################################################################
# main - starts the program
###############################################################################
def main():
    global attributeList

    attributeList = read_dataset('names')  # getting attributes from mongodb collection

    credentials = get_credentials()
    service = build('gmail', 'v1', http=credentials.authorize(Http()))

    print 'Reading dataset'
    dataset = read_dataset('data')  # reading dataset from mongodb collection
    print 'Done reading dataset'

    print 'Discretising continuous data'
    dataset_division_dict = dict(
        (x['name'], []) for x in attributeList)  # {'attribute_name':[q01,q1,,q12,q2,q23,q3,q3max,max_value]}
    for attribute in attributeList:
        q01 = 0.0  # mid point of 0 and q1
        count_q01 = 0  # count of data elements that lies in range
        q1 = 0.0  # mid point of 0 and mean
        count_q1 = 0
        q12 = 0.0  # mid point of q1 and q2
        count_q12 = 0
        q2 = 0.0  # mean
        q23 = 0.0  # mid point of q2 and q3
        count_q23 = 0
        q3 = 0
        count_q3 = 0.0
        q3max = 0.0  # mid point of q3 and max_value
        count_q3max = 0
        max_value = 0.0

        for data_row in dataset:
            q2 += data_row[attribute['name']]
        q2 /= len(dataset)

        for data_row in dataset:
            if 0 <= data_row[attribute['name']] < q2:
                q1 += data_row[attribute['name']]
                count_q1 += 1
        q1 /= count_q1

        for data_row in dataset:
            if data_row[attribute['name']] >= q2:
                q3 += data_row[attribute['name']]
                count_q3 += 1
        q3 /= count_q3

        for data_row in dataset:
            if max_value < data_row[attribute['name']]:
                max_value = data_row[attribute['name']]

        for data_row in dataset:
            if 0 <= data_row[attribute['name']] < q1:
                q01 += data_row[attribute['name']]
                count_q01 += 1
        if count_q01 != 0:
            q01 /= count_q01

        for data_row in dataset:
            if q1 <= data_row[attribute['name']] < q2:
                q12 += data_row[attribute['name']]
                count_q12 += 1
        if count_q12 != 0:
            q12 /= count_q12

        for data_row in dataset:
            if q2 <= data_row[attribute['name']] < q3:
                q23 += data_row[attribute['name']]
                count_q23 += 1
        if count_q23 != 0:
            q23 /= count_q23

        for data_row in dataset:
            if q3 <= data_row[attribute['name']] <= max_value:
                q3max += data_row[attribute['name']]
                count_q3max += 1
        if count_q3max != 0:
            q3max /= count_q3max

        dataset_division_dict[attribute['name']] = [q01, q1, q12, q2, q23, q3, q3max, max_value]

    for dataset_index in xrange(len(dataset)):
        for attribute in attributeList:
            if 0.0 <= dataset[dataset_index][attribute['name']] < dataset_division_dict[attribute['name']][0]:
                dataset[dataset_index][attribute['name']] = 1
            elif dataset_division_dict[attribute['name']][0] <= dataset[dataset_index][attribute['name']] < \
                    dataset_division_dict[attribute['name']][1]:
                dataset[dataset_index][attribute] = 2
            elif dataset_division_dict[attribute['name']][1] <= dataset[dataset_index][attribute['name']] < \
                    dataset_division_dict[attribute['name']][2]:
                dataset[dataset_index][attribute] = 3
            elif dataset_division_dict[attribute['name']][2] <= dataset[dataset_index][attribute['name']] < \
                    dataset_division_dict[attribute['name']][3]:
                dataset[dataset_index][attribute] = 4
            elif dataset_division_dict[attribute['name']][3] <= dataset[dataset_index][attribute['name']] < \
                    dataset_division_dict[attribute['name']][4]:
                dataset[dataset_index][attribute] = 5
            elif dataset_division_dict[attribute['name']][4] <= dataset[dataset_index][attribute['name']] < \
                    dataset_division_dict[attribute['name']][5]:
                dataset[dataset_index][attribute] = 6
            elif dataset_division_dict[attribute['name']][5] <= dataset[dataset_index][attribute['name']] < \
                    dataset_division_dict[attribute['name']][6]:
                dataset[dataset_index][attribute] = 7
            elif dataset_division_dict[attribute['name']][6] <= dataset[dataset_index][attribute['name']] < \
                    dataset_division_dict[attribute['name']][7]:
                dataset[dataset_index][attribute] = 8
            else:
                dataset[dataset_index][attribute] = 9

    for data_row in dataset:
        if int(data_row['class']) == 1:
            data_row['class'] = True
        else:
            data_row['class'] = False

    print 'Done discretising'

    print 'Retrieving email list'
    id_list = list_messages(service, 'me')
    print 'Done retrieving email list'

    emails_list = []

    for data_row in xrange(len(id_list)):
        id_dict = id_list[data_row]
        try:
            msg_dict = get_message(service, 'me', id_dict['id'])
            headers_list = msg_dict['payload']['headers']
            index_subject = 0
            for attribute in range(0, len(headers_list), 1):
                if headers_list[attribute]['name'] == 'Subject':
                    index_subject = attribute

            body = ''
            if 'body' in msg_dict['payload'] and msg_dict['payload']['mimeType'] == 'text/plain':
                body += msg_dict['payload']['body']['data']
            elif 'parts' in msg_dict['payload'] and msg_dict['payload']['parts'][0]['mimeType'] == 'text/plain':
                body += msg_dict['payload']['parts'][0]['body']['data']
            elif 'parts' in msg_dict['payload']['parts'][0] and \
                            msg_dict['payload']['parts'][0]['parts'][0]['mimeType'] == 'text/plain':
                body += msg_dict['payload']['parts'][0]['parts'][0]['body']['data']
            elif 'parts' in msg_dict['payload']['parts'][0]['parts'][0] and \
                            msg_dict['payload']['parts'][0]['parts'][0]['parts'][0]['mimeType'] == 'text/plain':
                body += msg_dict['payload']['parts'][0]['parts'][0]['parts'][0]['body']['data']
            else:
                print 'Error in id: ', id_dict['id']

            body = str(base64.b64decode(str(body).replace('-', '+').replace('_', '/')))
            body = body.decode('utf-8')
            # body = body.replace('\\r\\n', '\\n')
            # body = body.replace('\\n', '\n')
            subject = headers_list[index_subject]['value']
            email = subject + '\t' + body + '\n'

            if len(body) > 0:
                emails_list.append(email)

            temp = ''
            for c in email:
                if c.isalnum() or c.isspace():
                    temp += c
                else:
                    temp += ' '
            total_words = len(temp.split())
            words = ['make', 'address', 'all', '3d', 'our', 'over', 'remove', 'internet', 'order', 'mail', 'receive',
                     'will', 'people', 'report', 'addresses', 'free', 'business', 'email', 'you', 'credit', 'your',
                     'font',
                     '000', 'money', 'hp', 'hpl', 'george', '650', 'lab', 'labs', 'telnet', '857', 'data', '415', '85',
                     'technology', '1999', 'parts', 'pm', 'direct', 'cs', 'meeting', 'original', 'project', 're', 'edu',
                     'table', 'conference']
            count_words = dict((x, 0) for x in words)
            for w in re.findall(r"\w+", temp):
                if w in count_words:
                    count_words[w] += 1
            total_chars = 0
            for attribute in email:
                if not attribute == ' ':
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

            attribute_value_list = []

            for attribute in xrange(0, len(words)):
                attribute_value_list.append(percent_words[words[attribute]])

            for attribute in xrange(0, len(chars)):
                attribute_value_list.append(percent_chars[chars[attribute]])

            for attribute in xrange(0, len(attributeList)):
                if 0.0 <= attribute_value_list[attribute] < dataset_division_dict[attributeList[attribute]][0]:
                    attribute_value_list[attribute] = 1
                elif dataset_division_dict[attributeList[attribute]][0] <= attribute_value_list[attribute] < \
                        dataset_division_dict[attributeList[attribute]][1]:
                    attribute_value_list[attribute] = 2
                elif dataset_division_dict[attributeList[attribute]][1] <= attribute_value_list[attribute] < \
                        dataset_division_dict[attributeList[attribute]][2]:
                    attribute_value_list[attribute] = 3
                elif dataset_division_dict[attributeList[attribute]][2] <= attribute_value_list[attribute] < \
                        dataset_division_dict[attributeList[attribute]][3]:
                    attribute_value_list[attribute] = 4
                else:
                    attribute_value_list[attribute] = 5

            probability_true = 1.0
            probability_false = 1.0
            prob_true = []
            prob_false = []
            count_true = 0.0
            count_false = 0.0
            total = float(len(dataset))

            for attribute in dataset:
                if attribute[-1]:
                    count_true += 1
                else:
                    count_false += 1

            for attribute in xrange(0, len(dataset[0]) - 1):
                count = 0.0
                for k in dataset:
                    if k[attribute] == attribute_value_list[attribute] and k[-1]:
                        count += 1
                probability = count / count_true
                prob_true.append(probability)

            prob_true.append(count_true / total)

            for attribute in xrange(0, len(dataset[0]) - 1):
                count = 0.0
                for k in dataset:
                    if k[attribute] == attribute_value_list[attribute] and not k[-1]:
                        count += 1
                probability = count / count_false
                prob_false.append(probability)

            prob_false.append(count_false / total)

            for attribute in prob_true:
                probability_true *= attribute

            for attribute in prob_false:
                probability_false *= attribute

            if probability_true > probability_false:
                print id_dict['id'], 'spam'
            elif probability_true == probability_false:
                random_no = randint(0, 1)
                if random_no == 1:
                    print id_dict['id'], 'spam'

        except Exception as e:
            print 'Error in id %s' % id_list[data_row]['id']
            print 'Error Description: ', e
            pass


main()
