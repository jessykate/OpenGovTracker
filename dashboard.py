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


        self.render('templates/index.html', top_ideas, stats_by_agency)
                   # top_agency, best_participation, stats_by_agency)

        
    def top_agency(self, stats_by_agency):
        pass

    def top_ideas_by_category(self, best_ideas_by_agency):
        top_ideas = {            
            'transparency' : {'agency': None, 'votes':0, 'idea': None},
            'collaboration' : {'agency': None, 'votes':0, 'idea': None},
            'innovation'  : {'agency': None, 'votes':0, 'idea': None},
            'participation' : {'agency': None, 'votes':0, 'idea': None}
            }

        # best_ideas_by_agency is a dict for each agency
        for agency, agency_ideas in best_ideas_by_agency.iteritems():
            for category in ['transparency', 'collaboration', 'innovation', 'participation']:
                if top[category]['votes'] < best_ideas[category]['votes']:
                    top[category]['agency'] = agency
                    top[category]['votes'] = best_ideas[category]['votes']
                    top[category]['idea'] = best_ideas[category]['idea']
        return top_ideas

    def get_ideas(self, agency):
        key = agencies[agency]
        api_url = "http://api.ideascale.com/akira/api/ideascale.ideas.getTopIdeas?apiKey="
        url = urllib2.urlopen(api_url+key)
        js = json.loads(url.read())
        ideas = js['response']['ideas']        

        # aggregate stats for this agency
        stats = {}
        stats['ideas'] = 0
        stats['categories'] = {}
        stats['authors'] = {}
        stats['tags'] = {}
        for idea in ideas:
            stats['ideas'] +=1
            stats['votes'] = idea['voteCount']
            stats['comments'] = idea['commentCount']
            stats['categories'][idea['categoryID']] += 1
            stats['authors'][idea['author']] += 1
            stats['tags'][idea['tags']] += 1
            
        # get the top idea for each category for this agency
        for idea in ideas:            
            best_ideas = {
            'transparency' : {'votes':0, 'idea': None},
            'collaboration' : {'votes':0, 'idea': None},
            'innovation'  : {'votes':0, 'idea': None},
            'participation' : {'votes':0, 'idea': None}
            }
            this_category = idea['categoryID'] 
            if best_ideas[this_category]['votes'] < idea['votes']:
                best_ideas[this_category]['votes'] = idea['votes']
                best_ideas[this_category]['idea'] = idea

        return (stats, best_ideas)

application = tornado.web.Application([
        (r'/', MainHandler),
        ])

if __name__ == '__main__':
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8989)
    tornado.ioloop.IOLoop.instance().start()
