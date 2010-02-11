#!/usr/bin/python

import tornado.httpserver
import tornado.ioloop
import tornado.web
try:
    import json
except:
    import simplejson as json

from agencies import agencies, cat_id
from settings import settings

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        stats_cache = "stats_cache.json"
        stats_by_agency, best_ideas_by_agency = self.get_stats_from_file()

        # get the top ideas in each category across all agencies
        top_ideas = self.top_ideas_by_category(best_ideas_by_agency)

        # now we do some pivots and projections
        participation_chart = self.construct_participation_chart(stats_by_agency)
        #tag_cloud = construct_tag_clouds(stats_by_agency)
        
        self.render('templates/index.html', top_ideas=top_ideas, 
                    participation_chart=participation_chart,
                    stats_by_agency=stats_by_agency, 
                    most_votes = self.most_votes(stats_by_agency), 
                    most_ideas = self.most_ideas(stats_by_agency), 
                    most_comments = self.most_comments(stats_by_agency),
                    least_ideas = self.least_ideas(stats_by_agency), 
                    least_votes = self.least_votes(stats_by_agency), 
                    least_comments = self.least_comments(stats_by_agency), 
                    )
                   # top_agency, best_participation, stats_by_agency)

    def get_stats_from_file(self):
        cache_file = open(settings['stats_cache'], "r")
        data = json.load(cache_file)
        stats_by_agency = data["stats_by_agency"]
        best_ideas_by_agency = data["best_ideas_by_agency"]
        return stats_by_agency, best_ideas_by_agency

    def construct_tag_clouds(self, stats_by_agency):
        for agency,  in stats_by_agency.keys():
            pass

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
            
        # create text markers to annotate each bar with the numeric
        # counts (each marker must be prefixed with a 't'-- *shrug*)
        prefix = ['t'+x for x in ideas_by_agency]
        # remember prefix is already a combination of t and the
        # ideas_by_agency array.
        markers = zip(prefix, votes_by_agency, comments_by_agency)
        markers = ['/'.join(tup) for tup in markers] 

        # construct the participation stacked bar chart url. note that
        # we scale the height as appropriate for the largest values. 
        participation_chart = "http://chart.apis.google.com/chart?cht=bvs&chs=1000x300&chds=0,"+str(max_value)+"&chbh=a&chco=4D89D9,C6D9FD,DD99FD&chd=t:"+','.join(ideas_by_agency)+"|"+','.join(votes_by_agency)+"|"+','.join(comments_by_agency)+"&chxt=x&chxl=0:|"+'|'.join(agency_names)+"&chts=40&chdl=Ideas|Votes|Comments"
        
        return participation_chart
            
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

application = tornado.web.Application([
        (r'/', MainHandler),
        ], **settings)

if __name__ == '__main__':
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8989)
    tornado.ioloop.IOLoop.instance().start()
