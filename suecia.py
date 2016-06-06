import re
import requests
from lxml import html
from lxml.builder import E
from lxml.etree import tostring
import sys

url = "https://data.kb.se/datasets/2014/10/suecia/"

def getmeta(libris_id):
    lurl = "http://libris.kb.se/xsearch/?query=onr:%s&format=json" % libris_id
    r = requests.get(lurl)
    if r.status_code == 200:
        return r.json()



def getdesc(meta, img):
    desc = meta["xsearch"]["list"][0]["title"].replace(" [Elektronisk resurs]","")
    if "creator" in meta["xsearch"]["list"][0]:
        desc += " by " + meta["xsearch"]["list"][0]["creator"] + "."
    desc += "\n\n{{Kungliga biblioteket image|libris-id=%s}}\n" % img["id"]
    return cleanbibblo(desc)


def getdate(meta):
    if "date" in meta["xsearch"]["list"][0]:
        d = meta["xsearch"]["list"][0]["date"].strip()

        # simple year
        if re.search("^\d\d\d\d$", d):
            return d

        #check between dates
        res = re.search("\[\s*mellan\s*(\d\d\d\d)[\s\w]*(\d\d\d\d)\s*\]", d)
        if res:
            if res.group(1) and res.group(2):
                return "{{between|%s|%s}}" % (res.group(1), res.group(2))

        #check single circa year
        res = re.search("\[(\d\d\d\d)\]", d)
        if res:
            if res.group(1):
                return "{{circa|%s}}" % res.group(1)

        # fallback to default
        return "{{between|1661|1715}}" # default date if unknown


def getfilename(meta, img):
    """Return a clean filename based on libris identifier"""
    return "Suecia antiqua (%s)" % img["url"].replace(url,"").replace("/","").replace("%2C","_").replace(".tif", "")


def cleanbibblo(text):
    """Remove bibliographic notation in []"""
    return re.sub(r' \[[^\]]*\]', '',text)


def filedata():
    filesxml = []
    for img in image_urls:
        meta = getmeta(img["id"])

        filesxml.append(E.record(
            E.source(img["url"]),
            E.title(cleanbibblo(meta["xsearch"]["list"][0]["title"])),
            E.filename(getfilename(meta,img)),
            E.description(getdesc(meta, img)),
            E.date(getdate(meta))
        ))

    return filesxml



# Download and build xml

r = requests.get(url)
tree = html.fromstring(r.content)
linkels = tree.xpath("//a[contains(@href, '.tif')]/@href")

image_urls = map(lambda el: {"url": url + el[2:], "id": el.split("%")[0].replace(".","").replace("/","")}, linkels)

# for debug
if sys.argv[1] and sys.argv[2]:
    image_urls = [{"url": sys.argv[1], "id": sys.argv[2]}]


xml = E.metadata(
    E.records(
        *filedata()
    )
)

print tostring(xml, pretty_print=True, xml_declaration=True, encoding='utf-8')
