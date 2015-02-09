# __author__ = 'traitravinh'
import urllib
import urllib2
import re
from BeautifulSoup import BeautifulSoup
################################## PHIMVANG #########################################
NAME = "Phimvang"
BASE_URL = "http://phimvang.org"
SEARH_URL = 'http://phimvang.org/tim-kiem/tat-ca/%s%s'
DEFAULT_ICO = 'icon-default.png'
SEARCH_ICO = 'icon-search.png'
NEXT_ICO = 'icon-next.png'
##### REGEX #####
RE_MENU = Regex('<div class="division">(.+?)<div id="ad-right">')
RE_INDEX = Regex('<div id="main-content">(.+?)<footer id="footer">')
RE_PAGE = Regex('<div class="loop-nav pag-nav">(.+?)<footer id="footer">')
RE_IFRAME = Regex('<div id="main-content">(.+?)<iframe src=')
RE_PUBID = Regex('data-publisher-id="(.+?)" data-video-id')
RE_VIDID = Regex('data-video-id="(.+?)"')
RE_SRC = Regex('"src":"(.+?)"|\'')
RE_VCODE = Regex('mp4:(.+?)" ')
RE_DAILY = Regex('src="(.+?)"')
# ###################################################################################################

def Start():
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    ObjectContainer.title1 = NAME
    ObjectContainer.view_group = 'List'

    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:22.0) Gecko/20100101 Firefox/22.0'
    HTTP.Headers['X-Requested-With'] = 'XMLHttpRequest'


####################################################################################################
@handler('/video/phimvang', NAME)
def MainMenu():
    oc = ObjectContainer()
    oc.add(InputDirectoryObject(
        key=Callback(Search),
        title='SEARCH'
    ))
    try:
        link = HTTP.Request(BASE_URL,cacheTime=3600).content
        soup = BeautifulSoup(link)
        li_menu = BeautifulSoup(str(soup('div',{'id':'menu'})[0]))('li')
        for m in li_menu:
            mtitle = BeautifulSoup(str(m))('a')[0].contents[0]
            mlink = BASE_URL + BeautifulSoup(str(m))('a')[0]['href']
            oc.add(DirectoryObject(
                key=Callback(Category, title=mtitle, catelink=mlink),
                title=mtitle,
                thumb=R(DEFAULT_ICO)
            ))

    except Exception, ex:
        Log("******** Error retrieving and processing latest version information. Exception is:\n" + str(ex))

    return oc

####################################################################################################

@route('/video/phimvang/search')
def Search(query=None):
    if query is not None:
        url = SEARH_URL % ((String.Quote(query, usePlus=True)), '.html')
        return Category(query, url)

@route('/video/phimvang/category')
def Category(title, catelink):
    oc = ObjectContainer(title2=title)
    link = HTTP.Request(catelink,cacheTime=3600).content
    soup = BeautifulSoup(link)
    h2s = soup('h2')
    for h in h2s:
        hsoup = BeautifulSoup(str(h))
        hlink = BASE_URL+hsoup('a')[0]['href'].replace('phim','xem-phim')
        himage = hsoup('img')[1]['data-original']
        htitle = hsoup('img')[1]['alt']
        oc.add(DirectoryObject(
            key=Callback(Servers, title=htitle, slink=hlink, sthumb=himage),
            title=htitle,
            thumb=himage
        ))
    try:
        paging = soup('div',{'class':'paging'})
        pages = BeautifulSoup(str(paging[0]))('a')

        for p in pages:
            psoup = BeautifulSoup(str(p))
            ptitle = psoup('a')[0].contents[0]
            plink = BASE_URL+psoup('a')[0]['href']
            oc.add(DirectoryObject(
                key=Callback(Category, title=ptitle, catelink=plink),
                title=ptitle,
                thumb=R(NEXT_ICO)
            ))
    except:pass


    return oc

####################################################################################################
@route('/video/phimvang/servers')
def Servers(title, slink, sthumb):
    Log(slink)
    oc = ObjectContainer(title2=title)
    link = HTTP.Request(slink,cacheTime=3600).content
    soup = BeautifulSoup(link)
    epis = soup('p',{'class':'epi'})
    elist = BeautifulSoup(str(epis[0]))('a')
    for i in range(0,len(elist)):
        esoup = BeautifulSoup(str(elist[i]))
        elink = BASE_URL+esoup('a')[0]['href']
        etitle = esoup('a')[0].contents[0]
        oc.add(createMediaObject(
            url=elink,
            title=etitle,
            thumb=sthumb,
            rating_key=etitle
        ))
    return oc

@route('/video/phimvang/media')
def Media(metitle, melink, methumb):
    oc = ObjectContainer(title2=metitle)
    melink = videolinks(melink)
    Log(melink)
    if str(melink).find('youtube')!=-1:
        oc.add(VideoClipObject(
            url=melink,
            title=metitle,
            thumb=methumb
        ))
    else:
        oc.add(createMediaObject(
            url=melink,
            title=metitle,
            thumb=methumb,
            rating_key=metitle
        ))
    return oc
@route('/video/phimvang/createMediaObject')
def createMediaObject(url, title,thumb,rating_key,include_container=False):
    container = Container.MP4
    video_codec = VideoCodec.H264
    audio_codec = AudioCodec.AAC
    audio_channels = 2
    track_object = EpisodeObject(
        key=Callback(
            createMediaObject,
            url=url,
            title=title,
            thumb=thumb,
            rating_key=rating_key,
            include_container=True
        ),
        title = title,
        thumb=thumb,
        rating_key=rating_key,
        items = [
            MediaObject(
                parts=[
                    PartObject(key=Callback(PlayVideo, url=url))
                ],
                container = container,
                video_resolution = '720',
                video_codec = video_codec,
                audio_codec = audio_codec,
                audio_channels = audio_channels,
                optimized_for_streaming = True
            )
        ]
    )
    if include_container:
        return ObjectContainer(objects=[track_object])
    else:
        return track_object


@indirect
def PlayVideo(url):
    url = videolinks(url)
    if str(url).find('youtube')!=-1:
        oc = ObjectContainer(title2='Youtube Video')
        oc.add(VideoClipObject(
            url=url,
            title='Youtube video',
            thumb=R(DEFAULT_ICO)
        ))
        return oc
    else:
        return IndirectResponse(VideoClipObject, key=url)

def videolinks(url):
    url = ''.join(url.split())
    link = urllib2.urlopen(url).read()
    newlink = ''.join(link.splitlines()).replace('\t','')
    if newlink.find('youtube')!=-1:
        # vlink = re.compile("'file' : '(.+?)',").findall(newlink)[0]
        # final_link=vlink
        vlink = re.compile('file : "(.+?)&amp').findall(newlink)[0]
        final_link=vlink
    else:
        # vlink = re.compile("'link':'(.+?)'}").findall(newlink)[0]
        try:
            vlinks = re.compile(',\{file: "(.+?)", label:"720p"').findall(newlink)[0]
        except:
            vlinks = re.compile('file: "(.+?)", label').findall(newlink)[0]
        final_link=vlinks

    return final_link


def medialink(url):
    link = urllib2.urlopen(url).read()
    newlink = ''.join(link.splitlines()).replace('\t','')
    myregex = re.escape(url)+r'(.+?){"rel":"alternate"'
    match=re.compile(myregex).findall(newlink)
    if len(match)<=0:
        if url.find('&feat=directlink'):
            url = str(url).replace('&feat=directlink', '')
        myregex=re.escape(url)+r'(.+)'
        match = re.findall(myregex,newlink)
    if len(match)<=0:
        mlink = re.findall(',{"url":"(.+?)","height"',newlink)
    else:
        mlink = re.findall(',{"url":"(.+?)","height"',match[0])
    # Log(mlink)
    if len(mlink)>1:
        if mlink[1].endswith('png') or mlink[1].endswith('jpg'):
            return mlink[0]
        else:
            return mlink[1]
    else:
        return mlink[0]


####################################################################################################