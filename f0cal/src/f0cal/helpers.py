import os

import jinja2 as j2


class Jinja2Renderer:
    _JINJA_ENV_ARGS = dict(trim_blocks=True, lstrip_blocks=True)

    def __init__(self, template_dir, template=None):
        self._template_dir = template_dir
        self._template_name = template

    def render_blob(self, blob):
        return self._render_template(self._template_dir, self._template_name, data=blob)

    @classmethod
    def _render_template(cls, template_dir, template_name, **dargs):
        env = j2.Environment(
            loader=j2.FileSystemLoader(template_dir), **cls._JINJA_ENV_ARGS
        )
        env.undefined = j2.StrictUndefined
        return env.get_template(template_name).render(**dargs)

    @classmethod
    def from_template_path(cls, template_path):
        assert os.path.exists(template_path), template_path
        assert os.path.isfile(template_path), template_path
        dir_path, template_name = os.path.split(template_path)
        dir_path = os.path.abspath(dir_path)
        return cls(dir_path, template=template_name)
