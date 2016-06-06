import re
import requests
from lxml import html
from lxml.builder import E
from lxml.etree import tostring

url = "https://data.kb.se/datasets/2014/10/suecia/"
template = "{{Kungliga biblioteket image|libris-id=%s|url=%s}}"

def getmeta(libris_id):
    lurl = "http://libris.kb.se/xsearch/?query=onr:%s&format=json" % libris_id
    r = requests.get(lurl)
    if r.status_code == 200:
        return r.json()


r = requests.get(url)
tree = html.fromstring(r.content)
linkels = tree.xpath("//a[contains(@href, '.tif')]/@href")
image_urls = map(lambda el: {"url": url + el[2:], "id": el.split("%")[0].replace(".","").replace("/","")}, linkels)

def getdesc(meta, img):
    desc = meta["xsearch"]["list"][0]["title"].replace(" [Elektronisk resurs]","")
    if "creator" in meta["xsearch"]["list"][0]:
        desc += " by " + meta["xsearch"]["list"][0]["creator"] + "."
    desc += "\n\n{{Kungliga biblioteket image|libris-id=%s}}\n" % img["id"]
    return cleanbibblo(desc)


def getdate(meta):
    if "date" in meta["xsearch"]["list"][0]:
        return meta["xsearch"]["list"][0]["date"]
    else:
        return "{{between|1600|1715}}" # default date if unknown


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
            E.filename(img["url"].replace(url,"").replace("/","").replace("%2C","_")),
            E.description(getdesc(meta, img)),
            E.date(getdate(meta))
        ))

    return filesxml


xml = E.metadata(
    E.records(
        *filedata()
    )
)

print tostring(xml, pretty_print=True, xml_declaration=True, encoding='utf-8')
