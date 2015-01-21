import os
import io


class FormatTemplate(object):
    def __init__(self, text):
        self.text = text

    def render(self, **kw):
        return self.text.format(**kw)


class FormatLoader(object):
    def __init__(self, template_directories):
        self.template_directories = template_directories

    def get(self, name):
        for template_directory in self.template_directories:
            path = os.path.join(template_directory, name)
            if not os.path.exists(path):
                continue
            with io.open(path, 'r') as f:
                return FormatTemplate(f.read())
        return None
