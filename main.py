import cherrypy
import json
import tweepy

data = json.loads(open("data").read())
cherrypy.config.update({'server.socket_host': data["info"]["host"],
                        'server.socket_port': data["info"]["port"],
})
from auth import AuthController, require, member_of, name_is


def display_tweet(tw):
    return """{} - <a href"http://twitter.com/{}">@{}</a> {}<br>
{}<br>
<a href="http://twitter.com/{}/status/{}">Details</a>  Favourite | Retweet<br>
""".format(tw.author.name.encode('ascii', 'replace'), tw.author.screen_name.encode('ascii', 'replace'),
           tw.author.screen_name.encode('ascii', 'replace'), tw.created_at.strftime("%H:%M %b %d"),
           tw.text.encode('ascii', 'replace'), tw.author.screen_name.encode('ascii', 'replace'), tw.id)


def display_user(user):
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
    return dis


def twlogin(twname):
    login = data["accounts"][twname]
    auth = tweepy.OAuthHandler(login["consumer_key"], login["consumer_secret"])
    auth.set_access_token(login["access_token"], login["access_token_secret"])
    api = tweepy.API(auth)
    user = api.get_user(twname)
    return api, user


def header():
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


def nav(user, page):
    dis = "Pirate Party Australia Twitter Management System<br>Accessible accounts: "
    for y in data["perms"][user]:
        dis += """<a href="http://fboyd.me:9005/{}">@{}</a> """.format(y, y)
    return dis


class RestrictedArea:
    # all methods in this controller (and subcontrollers) is
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

    @cherrypy.expose
    @require()
    def index(self):
        dis = header()
        dis += nav(cherrypy.request.login, "index")
        return dis

    # available to those with access to FletcherAU
    @cherrypy.expose
    @require(member_of("FletcherAU"))
    def FletcherAU(self):
        t = twlogin("FletcherAU")
        api = t[0]
        user = t[1]
        dis = header() + nav(cherrypy.request.login, "timeline")
        dis += display_user(user)
        dis += "-Timeline- | Mentions | Self<br><br>"
        for x in api.home_timeline():
            dis += display_tweet(x)
            dis += "<br>-<br><br>"
        return dis

    @cherrypy.expose
    @require(member_of("FletcherAU"))
    def FletcherAU_men(self):
        t = twlogin("FletcherAU")
        api = t[0]
        user = t[1]
        dis = header() + nav(cherrypy.request.login, "mentions")
        dis += display_user(user)
        dis += "Timeline | -Mentions- | Self<br><br>"
        for x in api.mentions_timeline():
            dis += display_tweet(x)
            dis += "<br>-<br><br>"
        return dis

    @cherrypy.expose
    @require(member_of("FletcherAU"))
    def FletcherAU_me(self):
        t = twlogin("FletcherAU")
        api = t[0]
        user = t[1]
        dis = header() + nav(cherrypy.request.login, "self")
        dis += display_user(user)
        dis += "Timeline | -Mentions- | Self<br><br>"
        for x in api.user_timeline():
            dis += display_tweet(x)
            dis += "<br>-<br><br>"
        return dis


if __name__ == '__main__':
    cherrypy.quickstart(Root())
