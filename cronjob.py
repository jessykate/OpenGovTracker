#!/usr/bin/python

# an extremely poor man's cron job to update stats for all agencies in
# a separate process to the application itself. should really be added
# to actual cron. if for any reason this job crashes (url not
# available, for example), it will not be restarted. ultimately, could
# just use memcache.

from agencies import agencies, cat_id
from settings import settings
import urllib, urllib2, time
try:
    import json
except:
    import simplejson as json

def get_ideas(agency):
    key = agencies[agency]
    api_url = "http://api.ideascale.com/akira/api/ideascale.ideas.getTopIdeas?apiKey="
    url = urllib2.urlopen(api_url+key)
    js = json.loads(url.read())
    ideas = js['response']['ideas']        

    # aggregate stats for this agency
    stats = {}
    stats['categories'] = {}
    stats['authors'] = {}
    stats['tags'] = {}
    for idea in ideas:
        stats['ideas'] = stats.get('ideas', 0) +1
        stats['votes'] = stats.get('votes', 0) + idea['voteCount']
        stats['comments'] = stats.get('comments', 0) + idea['commentCount']
        category_name = cat_id[agency][idea['categoryID']]
        stats['categories'][category_name] = stats['categories'].get(category_name, 0) + 1
        stats['authors'][idea['author']] = stats['authors'].get(idea['author'], 0) + 1
        for tag in idea['tags']:
            stats['tags'][tag] = stats['tags'].get(tag, 0) + 1

    # get rid of site_feedback, we dont really care to track that.
    if 'site_feedback' in stats['categories']:
        del stats['categories']['site_feedback']

    # get the top idea for each category for this agency
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

    # get rid of site_feedback, we dont really care to track that.
    del best_ideas['site_feedback']
    
    return (stats, best_ideas)

while True:
    stats_by_agency = {}
    best_ideas_by_agency = {} 
    try:
        for agency in agencies.keys():
            stats_by_agency[agency], best_ideas_by_agency[agency] = get_ideas(agency)    
        cache_file = open(settings["stats_cache"], "w")
        data = {"stats_by_agency":stats_by_agency, "best_ideas_by_agency": best_ideas_by_agency}
        json.dump(data, cache_file)
        cache_file.close()
    except Exception, e:
        # if anything goes wrong this time around, just pass-- try
        # again in 5 minutes. (should at least add a log here!)
        print '\nError in cronjob.py for IdeaScale Dashboard: %s' % e
        print 'Will try again in 5 minutes'
        pass
    time.sleep(300)
