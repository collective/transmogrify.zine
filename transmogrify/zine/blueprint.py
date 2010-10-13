import datetime

from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import Matcher
from collective.transmogrifier.utils import defaultKeys
try:
    from plone.app.discussion.comment import CommentFactory
    from plone.app.discussion.interfaces import IConversation
    PAD_INSTALLED = True
except ImportError:
    PAD_INSTALLED = False
from plone.intelligenttext.transforms import\
        convertHtmlToWebIntelligentPlainText

def title_keep_caps(string):
    """ Applies the title function but keeps the upper case """
    result = ''
    title = string.title()
    length = len(title)
    for i in range(length):
        result+= string[i].isupper() and string[i] or title[i]
    return result


class PloneFieldsFC(object):
    """ This section edits the post's fields to be ready for item creation.
    """
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous

    def __iter__(self):
        for item in self.previous:
            item['_id'] = \
                item['_transmogrify.zine.id'].split('/')[-1].replace(':','')
            item['_path'] = '/blog/%s' %(item['_id'])
            item['_raw_title'] = item['_transmogrify.zine.title']
            item['creators'] = [item['_transmogrify.zine.author.name']]
            item['effectiveDate'] = item['_transmogrify.zine.published.rfc822']
            item['modificationDate'] =\
                    item['_transmogrify.zine.updated.rfc822']
            item['creationDate'] = item['_transmogrify.zine.published.rfc822']
            item['_transitions'] = item['_transmogrify.zine.state'] ==\
                    'published' and 'publish' or None
            item['_comments'] = item['_transmogrify.zine.comments']
            item['allow_discussion'] = True
            tagdict = {}
            taglist = [title_keep_caps(term.replace('-',' ')) for\
                term in (item['_transmogrify.zine.tag'] +\
                item['_transmogrify.zine.category']) if term]
            for tag in taglist:
                tagdict[tag] = 1
            item['subject'] = list(tagdict.keys())
            yield item


class Format(object):
    """ This section edits the post's body text before item creation.
    """
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.image_base = options['image_base']

    def __iter__(self):
        for item in self.previous:
            text = item['_transmogrify.zine.html']
            images = text.split('<img')[1:]
            for image in images:
                image = image.split('>')[0]
                if 'src="/' in image:
                    text = text.replace(image,
                        image.replace('src="/',
                        'src="%s' %(self.image_base))
                                       )
            parasplit = text.split('<p>')
            if len(parasplit) > 1:
                first_para = '<p>%s' %(parasplit[1])
                text = text.replace(first_para, '')
                item['description'] = convertHtmlToWebIntelligentPlainText(
                    first_para)
            item['text'] = text
            yield item


class CommentsSection(object):
    """A blueprint for importing comments into plone
"""
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.context = transmogrifier.context
        if 'path-key' in options:
            pathkeys = options['path-key'].splitlines()
        else:
            pathkeys = defaultKeys(options['blueprint'], name, 'path')
        self.pathkey = Matcher(*pathkeys)
        self.comment_type = options.get("comment-type", "plone")
        self.enabled = True
        if self.comment_type == "plone.app.discussion" and not PAD_INSTALLED:
            # TODO: log a note
            self.enabled = False


    def __iter__(self):
        for item in self.previous:
            pathkey = self.pathkey(*item.keys())[0]
            # item doesn't exist or the type of comment cannot be
            # created
            if not self.enabled or not pathkey:
                yield item
                continue

            path = item[pathkey]
            obj = self.context.unrestrictedTraverse(path.lstrip('/'), None)
            # path doesn't exist
            if obj is None:
                yield item
                continue

            # TODO: check to see if the object supports commenting...
            comments = item.get('_comments', [])
            for comment in comments:
                title = comment.get('title', '')
                text = comment.get('text', '')
                creator = comment.get('author.name', '')
                creation_date = comment.get('published', '')
                modification_date = comment.get('updated', '')
                if self.comment_type == "plone.app.discussion":
                    conversation = IConversation(obj)
                    # create a reply object
                    comment = CommentFactory()
                    comment.title = title
                    comment.text = convertHtmlToWebIntelligentPlainText(text)
                    comment.creator = creator
                    # TODO: check if the date is a datetime instance
                    comment.creation_date = creation_date or\
                            datetime.datetime.now()
                    comment.modification_date = modification_date or\
                            datetime.datetime.now()
                    conversation.addComment(comment)
                    # TODO: fire events
                if self.comment_type == "plone":
                    # TODO: create default plone content
                    pass
            yield item
