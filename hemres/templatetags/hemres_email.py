from __future__ import unicode_literals
from future.builtins import open
from django import template
from django.contrib.staticfiles import finders
from django.core.files.storage import default_storage
from django.core.mail import make_msgid
from email.mime.image import MIMEImage

register = template.Library()


@register.simple_tag(takes_context=True, name="emailimage_static")
def emailimage_static(context, image):
    if not context.get('render_mail', False):
        t = template.Template(r"{% load staticfiles %}{% static '" + image + "' %}")
        return t.render(context)

    if 'attachments' not in context:
        context['attachments'] = {}

    if image not in context['attachments']:
        path = finders.find(image)
        if path is not None:
            with open(path, 'rb') as fh:
                image_data = fh.read()
        else:
            return ""  # not found!

        image_cid = make_msgid('img')

        mime = MIMEImage(image_data)
        mime.add_header('Content-ID', image_cid)

        context['attachments'][image] = (mime, image_cid[1:-1])

    return "cid:{}".format(context['attachments'][image][1])


@register.simple_tag(takes_context=True, name="emailimage_media")
def emailimage_media(context, image):
    if not context.get('render_mail', False):
        return default_storage.url(image)

    if 'attachments' not in context:
        context['attachments'] = {}

    if image not in context['attachments']:
        path = default_storage.path(image)
        if path is not None:
            with open(path, 'rb') as fh:
                image_data = fh.read()
        else:
            return ""  # not found!

        image_cid = make_msgid('img')

        mime = MIMEImage(image_data)
        mime.add_header('Content-ID', image_cid)

        context['attachments'][image] = (mime, image_cid[1:-1])

    return "cid:{}".format(context['attachments'][image][1])


class EmptyNode(template.Node):
    def render(self, context):
        return ""


@register.tag
def limit_tags(parser, token):
    bits = token.contents.split()[1:]
    for s in list(parser.tags.keys()):
        if s not in bits:
            del parser.tags[s]
    return EmptyNode()


@register.tag
def limit_filters(parser, token):
    bits = token.contents.split()[1:]
    for s in list(parser.filters.keys()):
        if s not in bits:
            del parser.filters[s]
    return EmptyNode()
