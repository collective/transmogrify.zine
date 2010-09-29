from lxml import objectify
from dateutil.parser import parse
from zope.annotation.interfaces import IAnnotations
from zope.interface import implements
from zope.interface import classProvides
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import resolvePackageReferenceOrFile

SETTINGS_KEY = "transmogrify.zine.settings"
ATOM_URL = "http://www.w3.org/2005/Atom"
ATOM_NAMESPACE = "{%s}" % ATOM_URL
BLOGGER_NAMESPACES = {
    'a': ATOM_URL,
    'z': 'http://zine.pocoo.org/',
    'thr': 'http://purl.org/syndication/thread/1.0',
    'app': 'http://purl.org/atom/app#',
    }
# XXX: leaving off the "%z" for now as DateTime fields in
#      Archetypes don't seem to accept it.
RFC822_FMT = "%a, %d %h %Y %T"


class ZineSource(object):
    """A transmogrifier section that can read in a Blogger Atom export.
    """
    implements(ISection)
    classProvides(ISectionBlueprint)

    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        # custom options for this source
        self.filename = resolvePackageReferenceOrFile(options['filename'])
        self.init_xml_obj(self.filename)
        # get the blog settings and add them as an annotation for
        # use later in the pipeline
        self.storage = IAnnotations(transmogrifier).setdefault(
            SETTINGS_KEY, {})
        # grab the settings from the xml feed

    def init_xml_obj(self, filename):
        xml_file = open(filename)
        self.xml_obj = objectify.parse(filename)
        self.xml_root = self.xml_obj.getroot()
        xml_file.close()

    def extract_comments(self, post):
        parsed_comments = []
        comments = post.xpath(
            "z:comment",
            namespaces=BLOGGER_NAMESPACES)
        for comment in comments:
            item = {}
            item['id'] = comment.xpath("@id")[0]
            item['text'] = comment.content.text
            item['author.name'] = comment.author.name.text
            # the uri may not exist, use find to get it
            item['author.url'] = comment.author.find(
                "{%s}uri" % BLOGGER_NAMESPACES['z']
            )
            item['author.email'] = comment.author.email.text
            published = parse(comment.published.text)
            item['published'] = published
            published_rfc822 = published.strftime(RFC822_FMT)
            item['published.rfc822'] = published_rfc822
            parsed_comments.append(item)
        return parsed_comments

    def __iter__(self):
        # add any other sources into the stream

        for item in self.previous:
            yield item
        # process the blog posts
        posts = self.xml_root.xpath(
            "a:entry[contains(@xml:base, 'http://www.sixfeetup.com/blog/')]",
        namespaces=BLOGGER_NAMESPACES)
        for post in posts:
            item = {}
            item['_transmogrify.zine.id'] = post.id.text
            item['_transmogrify.zine.title'] = post.title.text
            item['_transmogrify.zine.content'] = post.content.text
            item['_transmogrify.zine.html'] =\
                    post.xpath("child::*[attribute::type='html']")[0].text
            item['_transmogrify.zine.author.name'] = post.author.name.text
            item['_transmogrify.zine.author.email'] = post.author.email.text
            published = parse(post.published.text)
            item['_transmogrify.zine.published'] = published
            published_rfc822 = published.strftime(RFC822_FMT)
            item['_transmogrify.zine.published.rfc822'] = published_rfc822
            updated = parse(post.updated.text)
            item['_transmogrify.zine.updated'] = updated
            updated_rfc822 = updated.strftime(RFC822_FMT)
            item['_transmogrify.zine.updated.rfc822'] = updated_rfc822
            alt_link = post.xpath(
                "a:link[@rel='alternate']/@href",
                namespaces=BLOGGER_NAMESPACES)
            alt_link = alt_link and alt_link[0] or ""
            item['_transmogrify.zine.link'] = alt_link
            post_state = "published"
            draft = post.xpath(
                "app:control/app:draft",
                namespaces=BLOGGER_NAMESPACES)
            if draft and draft[0] == "yes":
                post_state = "draft"
            item['_transmogrify.zine.state'] = post_state
            comments = self.extract_comments(post)
            item['_transmogrify.zine.comments'] = comments
            yield item
