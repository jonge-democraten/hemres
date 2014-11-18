from django import template
from django.contrib.staticfiles import finders
from django.core.mail import make_msgid
from email.mime.image import MIMEImage

register = template.Library()


@register.simple_tag(takes_context=True, name="emailimage_static")
def emailimage_static(context, image):
    if not context.get('emailimages_embed', False):
        t = template.Template(r"{% load staticfiles %}{% static '" + image + "' %}")
        return t.render(context)

    if 'emailimages' not in context:
        context['emailimages'] = {}

    if image not in context['emailimages']:
        path = finders.find(image)
        if path is not None:
            with open(path, 'rb') as fh:
                image_data = fh.read()
        else:
            return ""  # not found!

        image_cid = make_msgid('img')

        mime = MIMEImage(image_data)
        mime.add_header('Content-ID', image_cid)

        context['emailimages'][image] = (mime, image_cid[1:-1])

    return "cid:{}".format(context['emailimages'][image][1])


class EmptyNode(template.Node):
    def render(self, context):
        return ""


@register.tag
def limit_tags(parser, token):
    bits = token.contents.split()[1:]
    for s in parser.tags.keys():
        if s not in bits:
            del parser.tags[s]
    return EmptyNode()


@register.tag
def limit_filters(parser, token):
    bits = token.contents.split()[1:]
    for s in parser.filters.keys():
        if s not in bits:
            del parser.filters[s]
    return EmptyNode()
