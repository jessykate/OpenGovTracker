#!/usr/bin/python

import tornado.httpserver
import tornado.ioloop
import tornado.web
import urllib, urllib2
import json

agencies = {
    "nasa":"519f0a2f-4ac7-4ae2-ac11-8a11d0d9657e",   
}

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        stats_by_agency = {}
        best_ideas_by_agency = {}
        for agency in agencies.keys():
            stats_by_agency[agency], best_ideas_by_agency[agency] = self.get_ideas(agency)        
        # get the top ideas in each category across all agencies
        top_ideas = self.top_ideas_by_category(best_ideas_by_agency)

        # determine the top agency by number of ideas
        #top_agency = self.top_agency(stats_by_agency)

        # determine the top agency by participation = ideas+votes+comments
        #best_participation = self.top_participation(stats_by_agency)

        self.render('templates/index.html', top_ideas=top_ideas, 
                    stats_by_agency=stats_by_agency)
                   # top_agency, best_participation, stats_by_agency)

        
    def top_agency(self, stats_by_agency):
        pass

    def top_ideas_by_category(self, best_ideas_by_agency):
        top_ideas = {            
            11571: {'agency': None, 'votes':-1, 'idea': None},
            11572: {'agency': None, 'votes':-1, 'idea': None},
            11573: {'agency': None, 'votes':-1, 'idea': None},
            11928: {'agency': None, 'votes':-1, 'idea': None},
            11929: {'agency': None, 'votes':-1, 'idea': None}
            }

        # best_ideas_by_agency is a dict for each agency (avoiding the
        # issue of ties right now).
        for agency, agency_ideas in best_ideas_by_agency.iteritems():
            for category in [11571, 11572, 11573, 11928, 11929]:
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
            11571 : {'votes':0, 'idea': None},
            11572 : {'votes':0, 'idea': None},
            11573  : {'votes':0, 'idea': None},
            11928 : {'votes':0, 'idea': None},
            11929 : {'votes':0, 'idea': None}
        }
        for idea in ideas:            
            this_category = idea['categoryID'] 
            if best_ideas[this_category]['votes'] < idea['voteCount']:
                best_ideas[this_category]['votes'] = idea['voteCount']
                best_ideas[this_category]['idea'] = idea

        return (stats, best_ideas)

application = tornado.web.Application([
        (r'/', MainHandler),
        ])

if __name__ == '__main__':
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8989)
    tornado.ioloop.IOLoop.instance().start()
