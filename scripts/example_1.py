"""This script is a general example of work Scripton"""

from bs4 import BeautifulSoup as bs

links = []


def request(HttpMessageInfo, extension):
    """Edit cookie of a request.
    """
    cookie_name = "SCRIPTHPNCOOKIE"
    cookie_value = "scripthon1234567890"
    cookie = extension.bHelpers.buildParameter(cookie_name, cookie_value, 2)

    new_reques = extension.bHelpers.updateParameter(
        HttpMessageInfo.getRequest(), cookie)

    HttpMessageInfo.setRequest(new_reques)

    url = extension.bHelpers.analyzeRequest(HttpMessageInfo).getUrl()
    return "Script process request for: %s" % url


def response(HttpMessageInfo, extension):
    """Change title, extract all links of a http response.
    """
    html_page = extension.bHelpers.bytesToString(HttpMessageInfo.getResponse())
    soup = bs(html_page, 'html.parser')

    for tag in soup.find_all():
        try:
            if tag.name == 'title':
                tag.string = 'BurpScripthon change this title!'
                new_request = extension.bHelpers.stringToBytes(str(soup))
                HttpMessageInfo.setResponse(new_request)

            elif tag.name == 'a' and not tag['href'].startswith('#'):
                if tag.string not in links:
                    links.append(tag.string)
                    extension.log("%s: '%s'" % (tag.string, tag['href']))

        except KeyError: pass
