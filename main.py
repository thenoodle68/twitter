import cherrypy
import json
import tweepy

# load all the perms/api stuff.
# Should probably change to something that doesn't expose all the API/passwords to every page
data = json.loads(open("data").read())

# Generates an error but still seems to run
cherrypy.config.update({'server.socket_host': data["info"]["host"],
                        'server.socket_port': data["info"]["port"],
})
from auth import AuthController, require, member_of, name_is

# will need to be changed when the site is prettyfied.
def display_tweet(tw):
    """Formats a bunch of data from a status object"""
    return """{} - <a href"http://twitter.com/{}">@{}</a> {}<br>
{}<br>
<a href="http://twitter.com/{}/status/{}">Details</a>  Favourite | Retweet<br>
""".format(tw.author.name.encode('ascii', 'replace'), tw.author.screen_name.encode('ascii', 'replace'),
           tw.author.screen_name.encode('ascii', 'replace'), tw.created_at.strftime("%H:%M %b %d"),
           tw.text.encode('ascii', 'replace'), tw.author.screen_name.encode('ascii', 'replace'), tw.id)

# formatting same as above.
def display_user(user):
    """Format data from user object"""
    v = ""
    if user.verified:
        v = "+"
    dis = "<br>"
    dis += """Account information for {} (<a href="http://twitter.com/{}">@{}{}</a>)<br>
{}<br>
Location: {} Following: {} Followers: {}<br>""".format(user.name.encode('ascii', 'replace'),
                                                       user.screen_name.encode('ascii', 'replace'),
                                                       user.screen_name.encode('ascii', 'replace'), v, user.description,
                                                       user.location, user.friends_count,
                                                       user.followers_count)
    return dis + "<br>"

# could be moved somewhere else for security, auth?
def twlogin(twname):
    """ Generates tweepy API object based on stored credentials and account name
    Also generates a user object since it's basically used everywhere"""
    login = data["accounts"][twname]
    auth = tweepy.OAuthHandler(login["consumer_key"], login["consumer_secret"])
    auth.set_access_token(login["access_token"], login["access_token_secret"])
    api = tweepy.API(auth)
    user = api.get_user(twname)
    return api, user

# should probably figure out how cherrypy does favicons
# possibly remove metadata?
def header():
    """Generates header"""
    return """
    <html>
        <head>
            <title>PPAU Twitter Management</title>
            <meta http-equiv="content-type" content="text/html; charset=utf-8" />
            <meta name="description" content="Pirate Party Australia Twitter Platform" />
            <meta name="keywords" content="Twitter, PPAU, Pirate Party Australia" />
            <link href="http://fonts.googleapis.com/css?family=Open+Sans:300,600,700" rel="stylesheet" />
            <link rel="icon"
                type="image/png"
                href="favicon.png">
            <link rel="stylesheet" href="css/style.css" />
        </head>
    """

# needs "currently logged in as" + logout
def nav(user, page):
    """Generates navbar"""
    dis = "Pirate Party Australia Twitter Management System<br>Accessible accounts: "
    for y in data["perms"][user]:
        dis += """<a href="http://fboyd.me:9005/user/{}">@{}</a> """.format(y, y)
    return dis + "<br>"

# lol why is this even
class RestrictedArea:
    # all methods in this controller (and subcontrollers) are
    # open only to members of the admin group

    _cp_config = {
        'auth.require': [member_of('admin')]
    }

    @cherrypy.expose
    def index(self):
        return """index woo"""


class Root:
    _cp_config = {
        'tools.sessions.on': True,
        'tools.auth.on': True
    }

    auth = AuthController()

    restricted = RestrictedArea()

    # Makes the index a login page, adds navbar
    @cherrypy.expose
    @require()
    def index(self):
        dis = header()
        dis += nav(cherrypy.request.login, "index")
        return dis

    @cherrypy.expose
    @require()
    def user(self, name=None, typ=None, *args, **kw):
        """Display information from the viewpoint of a specific user"""
        dis = header() + nav(cherrypy.request.login, typ)
        # Can they view the user?
        if name in data["perms"][cherrypy.request.login]:
            t = twlogin(name)
            # hnnnngwat
            api = t[0]
            user = t[1]
            # Might want to default to something with a higher limit
            if not typ:
                typ = "timeline"
                ap = api.home_timeline() # Pretty sure this isn't the timeline I think it is
            if typ == "mentions":
                ap = api.mentions_timeline()
            elif typ == "self":
                ap = api.user_timeline()
            dis += display_user(user)
            for x in ["Timeline", "Mentions", "Self"]: # Should be drawn from some form of API thing
                if x == typ.title():
                    dis += """ |<a href="http://fboyd.me:9005/user/{}/{}"> -{}- </a>""".format(name, x.lower(), x) # Bold?
                else:
                    dis += """ |<a href="http://fboyd.me:9005/user/{}/{}"> {} </a>""".format(name, x.lower(), x)
            dis += " |<br><br>" # Fucking breaks man
            for x in ap:
                dis += display_tweet(x)
                dis += "<br>-<br><br>" #breeeeak
        # Currently a non expected type will just default, not sure if best solution
        else:
            dis += "<br>You do not have permission to view that user."
        return dis

if __name__ == '__main__':
    # Maybe put the server/port here instead.
    cherrypy.quickstart(Root())
