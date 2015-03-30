Hemres
====
Newsletters for the Jonge Democraten.

Installation notes
----
Depends on Mezzanine (optional) for TinyMCE.

Requires Janeus for LDAP integration.

Settings in `settings.py`:
- `HEMRES_DONT_EMAIL`  
set to True to not actually send any email from the Hemres app.
- `HEMRES_FROM_ADDRESS`  
set to the "From" email address for all messages, typically a noreply email address

Subscription management
----

Via the root page `/` a user can enter their email address and
receive an automatically generated email which contains one link to manage
the email-bound subscriptions and one link for each LDAP user
that is associated with that exact email address to manage the subscriptions
associated with that LDAP user.

Users subscribe to mailing lists.

Mailing lists have extra options. Certain LDAP groups can be automatically
subscribed to certain mailing lists. Also, LDAP group membership can be required
for certain mailing lists.

Templates, files and newsletters
----

Hemres stores mailing templates, mailing files and newsletters. Newsletters
are created as a clone of a template, and have no link to the template after
creation.

Template have fields `template` (HTML template), `title` (to identify it) and
zero or more files. The HTML template is a Django template that supports the
tags `{{subscriptions_url}}` (absolute URL to subscriptions page), `{{subject}}`
(subject of the newsletter), `{{name}}` (name of the recipient), `{{content}}`
(the rendered content to be embedded in the template) and `{{filelist}}`,
which will be rendered to an unordered list of attachments when viewing the
online version of the newsletter.

Newsletters have the same fields as templates, with additional fields `subject`
, `content`.  `date` (date of the newsletter) and `public` (whether
a newsletter can be viewed online).
The field `content` contains HTML text, with only a subset of
HTML whitelisted. The whitelisted tags are 
'a', 'b', 'code', 'em', 'h1', 'h2', 'h3', 'i', 'img', 'strong', 'ul', 'ol', 'li',
'p', 'br', 'span', 'table', 'tbody', 'tr', 'td', 'thead', 'div', 'span'.
The whitelisted attributes are 'class' and 'style' on all HTML tags,
'href' and 'target' on hyperlinks and 'src' and 'alt' on images.

Mailing files are images (that are embedded in the emails) and attachments.
There can also be files that are not attached, but that are linked to from
the newsletter.

Mailing files are included in newsletters in several ways:

1. Images are embedded using `{% emailimage 'identifier' %}`. Images
   should not have the "attach to email" checkbox checked.
2. Files that should be attached should have the "attach to email"
   checkbox checked (in the mailing template or the newsletter admin).
3. Files that should not be attached but linked to from the email can be
   linked to using `{% emailfile 'identifier' %}`.
4. For the `content` field of the newsletter only,
   the string `str="{{identifier}}"` will be automatically replaced by embedded
   images and `href="{{identifier}}"` will be automatically replaced by file
   links. When using the TinyMCE editor, this means that the image source
   `{{identifier}}` or the hyperlink URL `{{identifier}}` will be replaced
   by the embedded image or by a hyperlink to the file on the server.

Newsletter workflow
----

First, mailing templates must be defined. They may require mailing files,
for example as embedded images in the style.

Then, a newsletter is created based on a mailing template. This is done
by clicking the link "Create newsletter" from the list of mailing templates.
The full template
is copied by the system. The newsletter subject and content are defined
by the user. Additional attachments are added to the newsletter. Also, the
user may add files that remain on the server and are linked to from the content.

In the newsletter, there is still a separation of the template and the
newsletter itself. The idea here is that the newsletter content is sent by
a content manager, while the template is created by a designer or by someone
who has experience with HTML.

From the page in the admin that lists all newsletters, the user has several
options. They can view the newsletter in the browser. They can send a test
email to a supplied email address. They can also send the email to a list.

Sending the email to a list has the effect that a "Newsletter To List" object
is created. The idea is that a supervisor or administrator can check the
newsletter before sending it to the subscribers.

From the admin page that lists the "Newsletter To List" objects, an
administrator send the email to the subscribers. This creates a "Newsletter
To Subscriber" object for each subscriber.

Finally, each "Newsletter To Subscriber" object is processed either automatically
or manually (from the admin page). The newsletter is rendered and sent to that
subscriber and the "Newsletter To Subscriber" object is removed from the database.
