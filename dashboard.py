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

from agencies import agencies, cat_id, display_name, get_logo, open_pages 
from agencies import gov_shortener, ideascale_link
from settings import settings


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        stats_cache = "stats_cache.json"
        stats_by_agency, top_ideas_by_agency = self.get_stats_from_file()

        kwargs = {}
        # get the top ideas in each category across all agencies        
        kwargs['stats_by_agency'] = stats_by_agency
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
        
        self.render('templates/index.html', truncate=truncate, display=display_name, 
                    get_logo=get_logo, encode_tweet=encode_tweet, open_pages=open_pages, 
                    gov_shortener=gov_shortener, ideascale_link=ideascale_link, **kwargs)
    

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

def truncate(input_string, length):
    words = input_string.split()
    if len(words) > length:
        return ' '.join(words[:length])+'...'
    else: return input_string

def encode_tweet(agency, stats, days_to_go):
    num_ideas = stats['ideas']
    base_url="http://twitter.com/home?"
    query = {"status": "Unprecedented US #opengov discussions happening now: %s has %d ideas. %d days left! Add yours: %s #gov20" 
             % (display_name(agency), num_ideas, days_to_go, gov_shortener[agency])}
    return base_url+urllib.urlencode(query)


application = tornado.web.Application([
        (r'/', MainHandler),
        ], **settings)

if __name__ == '__main__':
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8999)
    tornado.ioloop.IOLoop.instance().start()
