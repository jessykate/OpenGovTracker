#!/usr/bin/python

import tornado.httpserver
import tornado.ioloop
import tornado.web
import urllib, urllib2
import os, datetime
try:
    import json
except:
    import simplejson as json

from lib import display_name, get_logo, open_pages, truncate_words, encode_tweet
from lib import gov_shortener, ideascale_link, agency_ideas
from settings import settings
import pymongo

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        stats_cache = "stats_cache.json"
        #stats_by_agency, top_ideas_by_agency = self.get_stats_from_file()
        timestamp, stats_by_agency, top_ideas_by_agency, all_ideas = self.db_retrieve()

        kwargs = {}
        # get the top ideas in each category across all agencies        
        kwargs['stats_by_agency'] = stats_by_agency
        kwargs['all_ideas'] = all_ideas
        kwargs['pie_charts'] = self.pie_charts(stats_by_agency.keys(), all_ideas)
        kwargs['top_ideas_by_agency'] = top_ideas_by_agency
        kwargs['top_ideas_by_category'] = self.top_ideas_by_category(top_ideas_by_agency)
        kwargs['participation_chart'] = self.construct_participation_chart(stats_by_agency)
        end_date = datetime.datetime(year=2010, month=3, day=19)
        kwargs['days_to_go'] = (end_date - datetime.datetime.now()).days
        kwargs['most_votes'] = self.most_votes(stats_by_agency)
        kwargs['most_ideas'] = self.most_ideas(stats_by_agency) 
        kwargs['most_comments'] = self.most_comments(stats_by_agency)
        kwargs['least_ideas'] = self.least_ideas(stats_by_agency)
        kwargs['least_votes'] = self.least_votes(stats_by_agency) 
        kwargs['least_comments'] = self.least_comments(stats_by_agency)
        kwargs['total_ideas'] = sum([agency_data['ideas'] for agency_data in stats_by_agency.values()])
        kwargs['total_comments'] = sum([agency_data['comments'] for agency_data in stats_by_agency.values()])
        kwargs['total_votes'] = sum([agency_data['votes'] for agency_data in stats_by_agency.values()])
        kwargs['last_updated'] = timestamp
        
        self.render('templates/index.html', truncate_words=truncate_words, display=display_name, 
                    get_logo=get_logo, encode_tweet=encode_tweet, open_pages=open_pages, 
                    gov_shortener=gov_shortener, ideascale_link=ideascale_link, 
                    agency_ideas=agency_ideas, **kwargs)
    
    def db_retrieve(self):
        ''' retrieve most recent ideas and stats from the database'''
        db = pymongo.Connection().opengovtracker
        # if we have a problem using the newest collection, go back to
        # using the *second* newest one. (since the actual newest one
        # might be getting written to right now).
        collection = db.collection_names()[-1]
        
        recent = db[collection]
        idea_cursor = recent.find({'idea': {"$exists": True}})
        all_ideas = [idea for idea in idea_cursor]

        cursor = recent.find({'stats_by_agency': {"$exists": True}})
        stats = cursor[0]['stats_by_agency']

        # for authors and tags, periods have been encoded as four
        # percent signs: %%%%. de-encode them, turning any occurences
        # back to periods.
        for agency, agency_stats in stats.iteritems():
            stats_authors = {}
            for author, count in agency_stats['authors'].iteritems():
                if author.find("%%%%") >= 0:
                    author.replace("%%%%", ".")
                stats_authors[author] = count
            stats[agency]['authors'] = stats_authors

            stats_tags = {}
            for tag, count in agency_stats['tags'].iteritems():
                if tag.find("%%%%") >= 0:
                    tag.replace("%%%%", ".")
                stats_tags[tag] = count
            stats[agency]['tags'] = stats_tags            

        cursor = recent.find({'best_ideas_by_agency': {"$exists": True}})
        best = cursor[0]['best_ideas_by_agency']        

        timestamp = collection
        return timestamp, stats, best, all_ideas

    def get_stats_from_file(self):
        cache_file = open(settings['stats_cache'], "r")
        data = json.load(cache_file)
        stats_by_agency = data["stats_by_agency"]
        best_ideas_by_agency = data["best_ideas_by_agency"]
        return stats_by_agency, best_ideas_by_agency

    def most_votes(self, stats_by_agency):
        most_votes = -1
        agency = None
        for this_agency, data in stats_by_agency.iteritems():
            if data['votes'] > most_votes:
                most_votes = data['votes']
                agency = this_agency
        return {'agency': agency, 'count':most_votes}

    def least_votes(self, stats_by_agency):
        least_votes = 1000000
        agency = None
        for this_agency, data in stats_by_agency.iteritems():
            if data['votes'] < least_votes:
                least_votes = data['votes']
                agency = this_agency
        return {'agency': agency, 'count':least_votes}

    def most_ideas(self, stats_by_agency):
        most_ideas = -1
        agency = None
        for this_agency, data in stats_by_agency.iteritems():
            if data['ideas'] > most_ideas:
                most_ideas = data['ideas']
                agency = this_agency
        return {'agency': agency, 'count':most_ideas}

    def least_ideas(self, stats_by_agency):
        least_ideas = 1000000
        agency = None
        for this_agency, data in stats_by_agency.iteritems():
            if data['ideas'] < least_ideas:
                least_ideas = data['ideas']
                agency = this_agency
        return {'agency': agency, 'count':least_ideas}

    def most_comments(self, stats_by_agency):
        most_comments = -1
        agency = None
        for this_agency, data in stats_by_agency.iteritems():
            if data['comments'] > most_comments:
                most_comments = data['comments']
                agency = this_agency
        return {'agency': agency, 'count':most_comments}

    def least_comments(self, stats_by_agency):
        least_comments = 1000000
        agency = None
        for this_agency, data in stats_by_agency.iteritems():
            if data['comments'] < least_comments:
                least_comments = data['comments']
                agency = this_agency
        return {'agency': agency, 'count':least_comments}


    def pie_charts(self, agencies, all_ideas):
        pie_urls = {}
        for agency in agencies:
            ideas = agency_ideas(all_ideas, agency)
            # make sure each category exists so that we can have some
            # sanity in the generated pie chart
            categories = {'transparency':0, 'participation':0, 'collaboration':0,
                          'innovation':0, 'site_feedback':0}
            for idea in ideas:
                category = idea['category']
                categories[category] = categories.get(category,0) + 1
            # convert the counts to strings for use in the pie chart url
            for category in categories.keys():
                categories[category] = str(categories[category])

            values = '%s,%s,%s,%s,%s' % (categories['transparency'], categories['participation'], 
                                         categories['collaboration'], categories['innovation'], 
                                         categories['site_feedback'])
            keys = '%s|%s|%s|%s|%s' % ('transparency', 'participation', 'collaboration', 
                                       'innovation', 'site_feedback')
            pie_url = '''http://chart.apis.google.com/chart?chs=240x100&chd=t:%s&chco=9999CC|666699|6666FF|6699CC|CCFFFF&cht=p3&amp;chf=bg,s,E3EEF1&chdl=%s&chf=bg,s,FFFFFF''' % (values, keys)
            pie_urls[agency] = pie_url
        return pie_urls

    def construct_participation_chart(self, stats_by_agency):

        # get the agency names out into a list so we can be sure the
        # list ordering for votes, comments and ideas will be
        # consistent.
        agency_names = stats_by_agency.keys()
        votes_by_agency = []
        comments_by_agency = []
        ideas_by_agency = []        
        for agency in agency_names:
            # numbers are saved as strings so we can easily expand the
            # list as a comma separated set of query arguments
            ideas_by_agency.append(str(stats_by_agency[agency]['ideas']))
            votes_by_agency.append(str(stats_by_agency[agency]['votes']))
            comments_by_agency.append(str(stats_by_agency[agency]['comments']))

        # determine max height needed. this is a little extreme but, meh. 
        x = []
        y = []
        z = []
        for agency in agency_names:
            x.append(stats_by_agency[agency]['votes'])
            y.append(stats_by_agency[agency]['comments'])
            z.append(stats_by_agency[agency]['ideas'])
        max_value =  max([sum(tup) for tup in zip(x,y,z)])

        # specify formatting for the x-axis labels
        display_names = []
        for name in agency_names:
            if (len(name) <= 5 and name != 'labor' and name != 'state' 
                and name!='comm' and name !='treas'):
                display_names.append(name.upper())
            else:
                display_names.append(name.title())
            
        # create text markers to annotate each bar with the numeric
        # counts (each marker must be prefixed with a 't'-- *shrug*)
        prefix = ['t'+x for x in ideas_by_agency]
        # remember prefix is already a combination of t and the
        # ideas_by_agency array.
        markers = zip(prefix, votes_by_agency, comments_by_agency)
        markers = ['/'.join(tup) for tup in markers] 

        # construct the participation stacked bar chart url. note that
        # we scale the height as appropriate for the largest values. 
        # e8ecdc
      
        participation_chart = "http://chart.apis.google.com/chart?cht=bvs&chs=1000x300&chds=0,"+str(max_value)+"&chbh=a,7&chco=996666,CC9999,FFCCCC&chd=t:"+','.join(ideas_by_agency)+"|"+','.join(votes_by_agency)+"|"+','.join(comments_by_agency)+"&chxt=x&chxl=0:|"+'|'.join(display_names)+"&chts=40&chdl=Ideas|Votes|Comments&chf=bg,s,e8ecdc"
        
        return participation_chart
            
    def top_ideas_by_category(self, best_ideas_by_agency):
        top_ideas = {            
            'transparency': {'agency': None,  'comments':0, 'votes':-1, 'idea': None},
            'participation': {'agency': None,  'comments':0, 'votes':-1, 'idea': None},
            'collaboration': {'agency': None,  'comments':0, 'votes':-1, 'idea': None},
            'innovation': {'agency': None,  'comments':0, 'votes':-1, 'idea': None},
            }

        # best_ideas_by_agency is a dict for each agency (avoiding the
        # issue of ties right now).
        for agency, agency_ideas in best_ideas_by_agency.iteritems():
            for category  in ['transparency', 'participation', 'collaboration', 'innovation']:
                if top_ideas[category]['votes'] < agency_ideas[category]['votes']:
                    top_ideas[category]['agency'] = agency
                    top_ideas[category]['votes'] = agency_ideas[category]['votes']
                    top_ideas[category]['comments'] = agency_ideas[category]['comments']
                    top_ideas[category]['idea'] = agency_ideas[category]['idea']

        return top_ideas    


application = tornado.web.Application([
        (r'/', MainHandler),
        ], **settings)

if __name__ == '__main__':
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8999)
    tornado.ioloop.IOLoop.instance().start()
