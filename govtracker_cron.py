#!/usr/bin/python

''' cron job to update stats for all agencies in a separate process to
the application itself.

add a line like this to your /etc/crontab file (Vixie Cron)
00,30 * * * * username /path/to/govtracker_cron.py
'''

from lib import cat_id, display_name, truncate_words, truncate_chars
from lib import shorten_url, post_tweet
from secrets import api_keys
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
    for agency in api_keys.keys():             
        agency_ideas = get_ideas(agency)
        all_ideas[agency] = agency_ideas
        stats_by_agency[agency] = get_stats_by_agency(agency, agency_ideas)
        best_ideas_by_agency[agency] = get_best_ideas_by_agency(agency, agency_ideas)

    # for each update, create a new mongo collection with the datetime
    # as the collection name. add each idea as a document, and then
    # add the best_ideas_by_agency and stats_by_agency as their own
    # documents. each ideas's ideascale id is used as it's id in the
    # collection so ideas can be searched across timeslices.
    now = datetime.datetime.now()
    db = pymongo.Connection().opengovtracker
    table = db[now.strftime('%Y-%m-%d %H:%M:%S EST')]        
    num = 1
    for agency, ideas in all_ideas.iteritems():
        for idea in ideas:            
            # use IdeaScale's id for the primary key used by
            # mongo. add the agency name and nominal category name.
            idea_json = {'_id': idea['id'],                        
                         'category': cat_id[agency][idea['categoryID']],
                         'agency' : agency,
                         'idea': idea,
                         }
            table.insert(idea_json, safe=True) 
            num = num+1
            
    table.insert({'stats_by_agency':stats_by_agency}, safe=True)
    table.insert({'best_ideas_by_agency': best_ideas_by_agency}, safe=True)

    db.connection.disconnect()

def twitter_update():

    # check the master list of ideas against the most recent idea
    # list. if there's a new one, tweet about it.
    ogt_db = pymongo.Connection().opengovtracker
    collection = ogt_db.collection_names()[-1]
    newest = ogt_db[collection]
    idea_cursor = newest.find({'idea': {"$exists": True}})
    idea_ids = [idea['_id'] for idea in idea_cursor]
    
    metadata_db = pymongo.Connection().govtrackermeta
    metadata = metadata_db['data']
    master_list_record = metadata.find_one({'master_list': {"$exists": True}})
    if not master_list_record:
        # if this is the first time through, simply initialize the
        # master_list_record and return. this is to avoid generating
        # hundreds of tweets the first time through.
        master_list = None
        master_list_record = {'master_list':idea_ids}
        metadata.insert(master_list_record, safe=True)
        return

    # check for new ideas by comparing the master list against the
    # most recent list.
    master_list = master_list_record['master_list']
    new_ideas = []
    for idea_id in idea_ids:
        if idea_id not in master_list:
            new_ideas.append(idea_id)

    for idea_id in new_ideas:
        # tweet each new idea. if for any reason the url shortening or
        # posting of the tweet fail, the master list is not updated.
        # the function simply returns, and thus the same ideas will
        # attempt to be tweeted next time the script is run.
        idea = newest.find_one({"_id":idea_id})
        
        shortened_url = shorten_url(idea['idea']['url'])
        if not shortened_url: 
            break

        # the agency name, pre-fix text and hashtag take up as many as
        # 60 characters. Truncate the idea title at 50 characters,
        # which leaves room for RTs and the rest.
        tweet = "New Idea for %s: %s %s #opengov" % (display_name(idea['agency']), truncate_chars(idea['idea']['title'], 50), 
                                                     shortened_url)
        try:
            tweet_posted = post_tweet(tweet)
            if not tweet_posted:
                break
            # add it to the master idea list so we don't tweet it again. 
            master_list.append(idea_id)
        except urllib2.HTTPError, e:
            # this can happen if there's a connectivity issue to the
            # API or we go over the posting limit.
            print 'urllib2 HTTPError: %s' % e
            print 'Rate limit probably exceeded'
            break
            
    # update the master_list with the added idea_ids.
    master_list_record['master_list'] = master_list
    metadata.update({'_id':master_list_record['_id']}, master_list_record)

if __name__ == '__main__':
    update_all()
    twitter_update()

