#!/usr/bin/python

# an extremely poor man's cron job to update stats for all agencies in
# a separate process to the application itself. should really be added
# to actual cron. if for any reason this job crashes (url not
# available, for example), it will not be restarted. ultimately, could
# just use memcache.

from agencies import cat_id
from keys import api_keys
from settings import settings
import urllib, urllib2, time, os, datetime, subprocess
try:
    import json
except:
    import simplejson as json


def email_warning(agency, category, num_ideas):
    sendmail = '''echo -e "Subject:OpenGovTracker Warning: %s has %d ideas in category %d <EOM>\nFrom:jessy@f00d.org\n" | sendmail jessy.cowansharp@gmail.com''' % (agency, num_ideas, category)
    subprocess.Popen(args=sendmail, shell=True, executable='/bin/bash',
                     stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    sendmail = '''echo -e "Subject:OpenGovTracker Warning: %s has %d ideas in category %d <EOM>\nFrom:jessy@f00d.org\n" | sendmail rschingler@gmail.com''' % (agency, num_ideas, category)
    subprocess.Popen(args=sendmail, shell=True, executable='bin/bash',
                     stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    print '** Warning Message Sent'

def get_ideas(agency):
    '''retrieve the ideas for each agency from ideascale using that
    agency's api key. unfortunately, ideascale currently limits the
    number of ideas returned by the API call to 50. since several
    agencies have more than 50 ideas submitted, we've bought some time
    by separating the api calls into categories. but if any category
    goes above 50, we're toast :/'''
    
    key = api_keys[agency]
    api_base_url = "http://api.ideascale.com/akira/api/ideascale.ideas.getRecentIdeas"

    ideas = []
    for category in cat_id[agency].keys():
        arguments = "?categoryID=%s&apiKey=%s" % (category, key) 
        api_call = api_base_url+arguments

        url = urllib2.urlopen(api_call)
        js = json.loads(url.read())
        # check if we're getting close to the 50 record limit and warn
        # by email if so.
        num_ideas = len(js['response']['ideas'])
        if num_ideas >= 42:
            email_warning(agency, category, num_ideas)
        ideas.extend(js['response']['ideas'])

    # aggregate stats for this agency
    stats = {}
    stats['categories'] = {}
    stats['authors'] = {}
    stats['tags'] = {}
    for idea in ideas:
        stats['ideas'] = stats.get('ideas', 0) +1
        stats['votes'] = stats.get('votes', 0) + abs(idea['voteCount'])
        stats['comments'] = stats.get('comments', 0) + idea['commentCount']
        category_name = cat_id[agency][idea['categoryID']]
        stats['categories'][category_name] = stats['categories'].get(category_name, 0) + 1
        stats['authors'][idea['author']] = stats['authors'].get(idea['author'], 0) + 1
        for tag in idea['tags']:
            stats['tags'][tag] = stats['tags'].get(tag, 0) + 1

    # get rid of site_feedback, we don't track that.
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

    # get rid of site_feedback, we don't track that.
    del best_ideas['site_feedback']

    # return the aggregate stats, the top ideas, and the full raw idea
    # set.
    return (stats, best_ideas, ideas)

while True:
    stats_by_agency = {}
    best_ideas_by_agency = {} 
    all_ideas = {}
    try:
        for agency in api_keys.keys(): 
            stats_by_agency[agency], best_ideas_by_agency[agency], all_ideas[agency] = get_ideas(agency)    
        if not os.path.exists("cache"):
            os.mkdir("cache")
        # "touch" the files to begin
        if not os.path.exists(os.path.join("cache", settings["stats_cache"])):
            fp = open(settings["stats_cache"], "w").write(" ")
            fp.close()
        if not os.path.exists(os.path.join("cache", settings["ideas_cache"])):
            fp = open(settings["ideas_cache"], "w").write(" ")
            fp.close()

        now = datetime.datetime.now().isoformat('_')
        print '%s: updating cache files' % now

        # archive the current stats file
        old_stats_cache = open(settings["stats_cache"], "r")
        archive = open(settings["stats_cache"]+'.'+now, "w")
        archive.write(old_stats_cache.read())
        archive.close()
        old_stats_cache.close()

        # archive the current ideas file
        old_ideas_cache = open(settings["ideas_cache"], "r")
        archive = open(settings["ideas_cache"]+'.'+now, "w")
        archive.write(old_ideas_cache.read())
        archive.close()
        old_ideas_cache.close()

        # write the new files
        cache_file = open(settings["stats_cache"], "w")
        ideas_file = open(settings["ideas_cache"], "w")
        stats_data = {"stats_by_agency":stats_by_agency, "best_ideas_by_agency": best_ideas_by_agency} 
        ideas_data = {"all_ideas":all_ideas}
        json.dump(stats_data, cache_file)
        json.dump(ideas_data, ideas_file)
        cache_file.close()
        ideas_file.close()

    except Exception, e:
        # if anything goes wrong this time around, just pass-- try
        # again in 5 minutes. (should at least add a log here!)
        print '\nError in cronjob.py for IdeaScale Dashboard: %s' % e
        print 'Will try again in 5 minutes'
    time.sleep(300)
