#!/usr/bin/python

import tornado.httpserver
import tornado.ioloop
import tornado.web
import urllib, urllib2
import os

try:
    import json
except:
    import simplejson as json

from agencies import agencies, cat_id

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        stats_by_agency = {}
        best_ideas_by_agency = {}
        for agency in agencies.keys():
            stats_by_agency[agency], best_ideas_by_agency[agency] = self.get_ideas(agency)        
        # get the top ideas in each category across all agencies
        top_ideas = self.top_ideas_by_category(best_ideas_by_agency)

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
            
        # create text markers to annotate each bar with the numeric
        # counts (each marker must be prefixed with a 't'-- *shrug*)
        prefix = ['t'+x for x in ideas_by_agency]
        # remember prefix is already a combination of t and the
        # ideas_by_agency array.
        markers = zip(prefix, votes_by_agency, comments_by_agency)
        markers = ['/'.join(tup) for tup in markers] 

        # construct the participation stacked bar chart url. note that
        # we scale the height as appropriate for the largest values. 
        participation_chart = "http://chart.apis.google.com/chart?cht=bvs&chs=800x300&chds=0,"+str(max_value)+"&chbh=a&chco=4D89D9,C6D9FD,DD99FD&chd=t:"+','.join(ideas_by_agency)+"|"+','.join(votes_by_agency)+"|"+','.join(comments_by_agency)+"&chxt=x&chxl=0:|"+'|'.join(agency_names)+"&chtt=Participation+Meter&chts=40&chdl=Ideas|Votes|Comments"
        
        print participation_chart
    
        # determine the top agency by number of ideas
        #top_agency = self.top_agency(stats_by_agency)

        # determine the top agency by participation = ideas+votes+comments
        #best_participation = self.top_participation(stats_by_agency)

        self.render('templates/index.html', top_ideas=top_ideas, participation_chart=participation_chart,
                    stats_by_agency=stats_by_agency)
                   # top_agency, best_participation, stats_by_agency)

        
    def top_agency(self, stats_by_agency):
        pass

    def top_ideas_by_category(self, best_ideas_by_agency):
        top_ideas = {            
            'transparency': {'agency': None, 'votes':-1, 'idea': None},
            'participation': {'agency': None, 'votes':-1, 'idea': None},
            'collaboration': {'agency': None, 'votes':-1, 'idea': None},
            'innovation': {'agency': None, 'votes':-1, 'idea': None},
            'site_feedback': {'agency': None, 'votes':-1, 'idea': None}
            }

        # best_ideas_by_agency is a dict for each agency (avoiding the
        # issue of ties right now).
        for agency, agency_ideas in best_ideas_by_agency.iteritems():
            for category  in ['transparency', 'participation', 'collaboration', 'innovation', 'site_feedback']:
                if top_ideas[category]['votes'] < agency_ideas[category]['votes']:
                    top_ideas[category]['agency'] = agency
                    top_ideas[category]['votes'] = agency_ideas[category]['votes']
                    top_ideas[category]['idea'] = agency_ideas[category]['idea']
        return top_ideas

    def get_ideas(self, agency):
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
            stats['categories'][idea['categoryID']] = stats['categories'].get(idea['categoryID'], 0) + 1
            stats['authors'][idea['author']] = stats['authors'].get(idea['author'], 0) + 1
            for tag in idea['tags']:
                stats['tags'][tag] = stats['tags'].get(tag, 0) + 1
            
        # get the top idea for each category for this agency
        best_ideas = {
            # Data Availability, Information Quality, Accountability: 11571
            # Public Feedback & Involvement, Tools & Strategies: 11572
            # Working Together: Governments, Businesses, Non-Profits: 11573
            # New Ways of Doing Business, New Tools: 11928
            # Tell Us How to Improve this Site: 11929
            'transparency' : {'votes':0, 'idea': None},
            'participation' : {'votes':0, 'idea': None},
            'collaboration' : {'votes':0, 'idea': None},
            'innovation' : {'votes':0, 'idea': None},
            'site_feedback' : {'votes':0, 'idea': None}
        }
        for idea in ideas:            
            this_category = cat_id[agency][idea['categoryID']]
            if best_ideas[this_category]['votes'] < idea['voteCount']:
                best_ideas[this_category]['votes'] = idea['voteCount']
                best_ideas[this_category]['idea'] = idea

        return (stats, best_ideas)

settings = {
    "static_path": os.path.join(os.path.dirname(__file__), "static")
    }

application = tornado.web.Application([
        (r'/', MainHandler),
        ], **settings)

if __name__ == '__main__':
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8989)
    tornado.ioloop.IOLoop.instance().start()
