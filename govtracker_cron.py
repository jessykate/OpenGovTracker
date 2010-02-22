#!/usr/bin/python

''' cron job to update stats for all agencies in a separate process to
the application itself.

add a line like this to your /etc/crontab file (Vixie Cron)
00,30 * * * * username /path/to/govtracker_cron.py

'''

from agencies import cat_id
from keys import api_keys
from settings import settings
import pymongo, sys
import urllib, urllib2, time, os, datetime, subprocess
try:
    import json
except:
    import simplejson as json

def get_ideas(agency):
    '''retrieve the ideas for each agency from ideascale using that
    agency's api key.'''
    
    key = api_keys[agency]
    api_base_url = "http://api.ideascale.com/akira/api/ideascale.ideas.getRecentIdeas"

    ideas = []
    for category_id, category_name in cat_id[agency].iteritems():
        arguments = "?categoryID=%s&apiKey=%s" % (category_id, key) 
        api_call = api_base_url+arguments
        url = urllib2.urlopen(api_call)
        js = json.loads(url.read())
        ideas.extend(js['response']['ideas'])
    return ideas

def get_stats_by_agency(agency, ideas):
    '''aggregate stats for this agency'''

    stats = {}
    stats['categories'] = {}
    stats['authors'] = {}
    stats['tags'] = {}
    print 'num ideas = %d' % len(ideas)
    for idea in ideas:
        stats['ideas'] = stats.get('ideas', 0) +1
        stats['votes'] = stats.get('votes', 0) + abs(idea['voteCount'])
        stats['comments'] = stats.get('comments', 0) + idea['commentCount']
        category_name = cat_id[agency][idea['categoryID']]
        stats['categories'][category_name] = stats['categories'].get(category_name, 0) + 1

        # get stats on authors and tags. keys with periods are not
        # allowed, so encode them as four percent signs: %%%%
        author = idea['author']
        if author.find(".") >= 0:
            author = author.replace(".", "%%%%")
        stats['authors'][author] = stats['authors'].get(author, 0) + 1
        for tag in idea['tags']:
            if tag.find(".") >= 0:
                tag = tag.replace(".", "%%%%")
            stats['tags'][tag] = stats['tags'].get(tag, 0) + 1            

    # don't bother tracking stats on site feedback
    if 'site_feedback' in stats['categories']:
        del stats['categories']['site_feedback']

    return stats

def get_best_ideas_by_agency(agency, ideas):
    '''get the top idea for each category for this agency.'''

    best_ideas = {
        'transparency' : {'votes':-1, 'comments':0, 'idea': None},
        'participation' : {'votes':-1,  'comments':0, 'idea': None},
        'collaboration' : {'votes':-1,  'comments':0, 'idea': None},
        'innovation' : {'votes':-1,  'comments':0, 'idea': None},
        'site_feedback' : {'votes':-1,  'comments':0, 'idea': None}
    }
    for idea in ideas:            
        this_category = cat_id[agency][idea['categoryID']]
        if best_ideas[this_category]['votes'] < idea['voteCount']:
            best_ideas[this_category]['votes'] = idea['voteCount']
            best_ideas[this_category]['comments'] = idea['commentCount']
            best_ideas[this_category]['idea'] = idea

    # don't bother tracking stats on site feedback
    del best_ideas['site_feedback']
    return best_ideas

def update_all():
    stats_by_agency = {}
    best_ideas_by_agency = {} 
    all_ideas = {}
#    try:
    for agency in api_keys.keys():             
        print 'getting stats for %s' % agency        
        agency_ideas = get_ideas(agency)
        all_ideas[agency] = agency_ideas
        stats_by_agency[agency] = get_stats_by_agency(agency, agency_ideas)
        best_ideas_by_agency[agency] = get_best_ideas_by_agency(agency, agency_ideas)

#    except Exception, e:
        # if anything goes wrong, just pass-- try again next round.
#        print '\nError in cronjob.py for IdeaScale Dashboard: %s' % e
#        print ' Will try again in 30 minutes'
#        sys.exit()

        # for each update, create a new mongo collection with the
    # datetime as the collection name. add each idea as a
    # document, and then add the best_ideas_by_agency and
    # stats_by_agency as their own documents. each ideas's
    # ideascale id is used as it's id in the collection so ideas
    # can be searched across timeslices.
    now = datetime.datetime.now()
    conn = pymongo.Connection()
    table = conn.opengovtracker[now.strftime('%Y-%m-%d %H:%M:%S EST')]        
    for agency, ideas in all_ideas.iteritems():
        for idea in ideas:            
            # use IdeaScale's id for the primary key used by
            # mongo. add the agency name and nominal category name.
            idea_json = {'_id': idea['id'],                        
                         'category': cat_id[agency][idea['categoryID']],
                         'agency' : agency,
                         'idea': idea,
                         }
            try:
                print 'inserting idea %s' % idea['title']
                table.insert(idea_json, safe=True) 
            except pymongo.errors.InvalidName, e:
                print e
                print idea
                sys.exit()

    # store the stats and top ideas for each agency
    try:
        table.insert({'stats_by_agency':stats_by_agency}, safe=True)
    except pymongo.errors.InvalidName, e:
        print e
        print "error in stats_by_agency"
        sys.exit()
    try:
        table.insert({'best_ideas_by_agency': best_ideas_by_agency}, safe=True)
    except pymongo.errors.InvalidName, e:
        print e
        print "error in best_ideas_by_agency"
        sys.exit()

    conn.disconnect()

if __name__ == '__main__':
    update_all()
