from __future__ import print_function


def read_by_tokens(fileobj):
    for line in fileobj:
        lineList = []
        for token in line.split():
            lineList.append(token)
        data.append(lineList)


readFile = open('spambase.data', 'r')
data = []
with open('spambase.data') as f:
    read_by_tokens(f)
