#!/usr/bin/python

'''
A standalone script that builds agency reports showing participation
over time on their ideascale site.

Add to /etc/crontab to run 05 minutes after midnight each day:
05 00 * * *   username /path/to/agency_report.py

'''

import pymongo, os, datetime

def generate_stats(agency):
    db = pymongo.Connection().opengovtracker
    collections = db.collection_names()    
    # the first few collections were used for testing, so skip them. 
    collections = collections[13:]
    stats = {'timestamps': [], 'ideas': [], 'comments': [], 'votes': [], 'authors': [] }
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
        authors = []
        for idea in cursor:
            ideas += 1
            # the layout of each document changed early on, from
            # storing the idea objects at the top level of the record
            # to storing it in a subdict. checking for the 'idea' key
            # accounts for this.
            if 'idea' in idea.keys():
                idea = idea['idea']
            votes += abs(idea['voteCount'])
            comments += idea['commentCount']
            if idea['author'] not in authors:
                authors.append(idea['author'])
    
        stats['ideas'].append(ideas)
        stats['votes'].append(votes)
        stats['comments'].append(comments)
        stats['authors'].append(len(authors))

    return stats

def interactive():
    agency = raw_input("Agency? ")
    report_type = raw_input("Report type (csv or tsv)? ")
    if report_type == 'csv':
        sep = ','
    else: 
        sep = '\t'
    agency_report(agency, sep)

def agency_report(agency, sep):
    stats = generate_stats(agency)
    rows = zip(stats['timestamps'], stats['ideas'], stats['votes'], stats['comments'], stats['authors'])
    # store agency reports in a subdirectory for the date on which
    # they were generated
    today = datetime.datetime.date(datetime.datetime.now()).isoformat()
    cwd = os.path.abspath(os.path.dirname(__file__))
    report_dir = os.path.join(cwd,'reports/')
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)

    # create a readme file that stores the exact time the report was
    # generated.
    readme = open(os.path.join(report_dir,agency+'.readme'), 'w')
    timestamp = datetime.datetime.now().isoformat('-')
    # remove milliseconds
    timestamp = timestamp[:timestamp.rfind('.')]
    readme.write("%s report generated at %s" % (agency, timestamp))
    readme.close()

    # now write the actual csv file
    filename = agency+'.csv'
    report = open(os.path.join(report_dir,filename), 'w')
    report.write("%s%s%s%s%s%s%s%s%s\n" % ('Time', sep, 'Ideas', sep,'Votes', sep, 'Comments', sep, 'Authors'))
    for row in rows:
        report.write("%s%s%d%s%d%s%d%s%d\n" % (row[0], sep, row[1], sep, row[2], sep, row[3], sep, row[4]))
    report.close()

if __name__ == '__main__':

    agencies =["usaid", "comm", "dod", "ed", "energy", "nasa",
               'dot', "int", "va", "treas", "gsa", "opm", "labor",
               "doj", "ssa", "state", "nsf", "hud", "epa", "sba",
               "dhs", "nrc", "ostp"]
    for agency in agencies:
        agency_report(agency, ',')        


