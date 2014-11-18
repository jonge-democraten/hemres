from __future__ import unicode_literals
from django.db.models.fields.files import FileField
from django.utils.encoding import force_text
from hashlib import sha256
import os


class HashFileField(FileField):
    def get_directory_name(self):
        h = sha256(os.urandom(64)).hexdigest()
        return os.path.normpath(force_text(self.upload_to.format(h)))
