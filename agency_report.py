#!/usr/bin/python

'''
A standalone script that builds a report for a given agency about
participation over time on their ideascale site.
'''

import pymongo

def report(agency):
    db = pymongo.Connection().opengovtracker
    collections = db.collection_names()    
    # the first few collections were used for testing, so skip them. 
    collections = collections[12:]
    stats = {'timestamps': [], 'ideas': [], 'comments': [], 'votes': [] }
    for collection in collections:
        current = db[collection]
        stats['timestamps'].append(collection)
        # get the ideas for *this* agency
        cursor = current.find({'agency': agency})
        # iterate over the idea objects and sum up the votes, counts
        # and ideas at this point in time.
        ideas = 0
        votes = 0
        comments = 0
        for idea in cursor:
            ideas += 1
            # the layout of each document changed early on, from
            # storing the idea objects at the top level of the record
            # to storing it in a subdict. checking for the 'idea' key
            # accounts for this.
            if 'idea' in idea.keys():
                votes += abs(idea['idea']['voteCount'])
                comments += idea['idea']['commentCount']
            else:
                votes += abs(idea['voteCount'])
                comments += idea['commentCount']
                
        stats['ideas'].append(ideas)
        stats['votes'].append(votes)
        stats['comments'].append(comments)
    return stats

if __name__ == '__main__':
    agency = raw_input("Agency? ")
    report_type = raw_input("Report type (csv or tsv)? ")
    if report_type == 'csv':
        sep = ','
    else: 
        sep = '\t'
    stats = report(agency)
    rows = zip(stats['timestamps'], stats['ideas'], stats['votes'], stats['comments'])
    print "%s%s%s%s%s%s%s" % ('Time', sep, 'Ideas', sep,'Votes', sep, 'Comments')
    for row in rows:
        print "%s%s%d%s%d%s%d" % (row[0], sep, row[1], sep, row[2], sep, row[3])
