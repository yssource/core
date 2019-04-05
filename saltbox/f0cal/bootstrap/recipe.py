import os
import os.path
import glob
import plugnparse
import itertools
import yaml
import salt.output
import distutils.dir_util
import tempfile
import jinja2
import logging

from .salt_helpers import SaltMaster, SaltMinion, SaltConfig

LOG = logging.getLogger(__name__)


class SaltRecipe(object):
    DEFAULT_SEARCH_PATH = "./recipes"
    SPECIAL_FILENAME = "recipe.sls"

    CMD_TO_CLIENT = {
        "salt-call": "call_client",
        "salt-cloud": "cloud_client",
        "salt-ssh": "ssh_client",
    }

    def __init__(self, **kwargs):
        self._name = kwargs.pop("name")
        self._path = kwargs.pop("path")
        self._actions = kwargs.pop("actions", [])
        self._root_dir = kwargs.pop("root_dir")
        self._config = None
        self._caller_client = None

    # @property
    # def caller_client(self):
    #     if self._caller_client is None:
    #         self._caller_client = self.config.caller_client()
    # return self._caller_client

    @property
    def config(self):
        if self._config is None:
            self._config = SaltConfig.from_root_dir(self._root_dir)
        return self._config

    @property
    def name(self):
        return self._name

    @property
    def path(self):
        return self._path

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        if self._config is not None:
            return self._config.__exit__(*args, **kwargs)
        return False

    def parse_action_str(self, action_str):
        tokens = action_str.split(" ")
        cmd = tokens[0]
        fn = tokens[1]
        dargs = dict(t.split("=") for t in tokens if "=" in t)
        return cmd, fn, [], dargs  # FIXME (br)

    def run_all(self):
        for action_str in self._actions:
            cmd, fn, args, dargs = self.parse_action_str(action_str)
            LOG.debug(">>>> {} {} {} {}".format(cmd, fn, args, dargs))
            client_name = self.CMD_TO_CLIENT[cmd]
            factory = getattr(self.config, client_name)
            client = factory()
            result = client.cmd(fn, *args, **dargs)
            data = {"local": result}  # FIXME (br) won't always be "local"
            salt.output.display_output(data, "highstate", opts=self._config.minion_opts)

    @classmethod
    def _set_blob_defaults(cls, blob):
        filename = blob["path"]
        parent_dir = os.path.dirname(filename)
        if "name" not in blob:
            blob["name"] = os.path.split(parent_dir)[-1]
        if "master" not in blob:
            blob["master"] = None
        if "minion" not in blob:
            blob["minion"] = None
        if "root_dir" not in blob:
            blob["root_dir"] = parent_dir
        return blob

    @classmethod
    def parse(self, file_or_path):
        with open(file_or_path) as recipe_file:
            return yaml.load(recipe_file)

    @classmethod
    def from_filename(cls, filename):
        assert os.path.exists(filename) and os.path.isfile(filename)
        blob = cls.parse(filename)
        blob["path"] = filename
        blob = cls._set_blob_defaults(blob)
        return cls(**blob)

    @classmethod
    def _find(cls, search_path):
        file_or_dir = os.path.abspath(search_path)
        assert os.path.exists(file_or_dir), file_or_dir
        if os.path.isdir(file_or_dir):
            for filename in glob.glob(
                os.path.join(file_or_dir, "**", cls.SPECIAL_FILENAME)
            ):
                yield filename

    @classmethod
    def find(cls, search_paths):
        assert isinstance(search_paths, list)
        filenames = itertools.chain.from_iterable(
            cls._find(path) for path in search_paths
        )
        for filename in set(filenames):
            yield cls.from_filename(filename)


class RecipeTemplate(SaltRecipe):
    TEMPLATE_TEMP_PREFIX = "f0b-recipe-"
    PATTERN = (
        "{ROOT_DIR}/**"
    )  # FIXME (br) this should be narrowed to only certain files

    def __init__(self, defaults=None, **kwargs):
        if defaults == None:
            defaults = {}
        self._defaults = defaults
        super(RecipeTemplate, self).__init__(**kwargs)

    def run_all(self, cli_kwargs):
        new_root_dir = tempfile.mkdtemp(prefix=self.TEMPLATE_TEMP_PREFIX)
        distutils.dir_util.copy_tree(self._root_dir, new_root_dir)
        self._root_dir = new_root_dir
        self._rewrite_templates(cli_kwargs)
        return SaltRecipe.from_filename(
            os.path.join(self._root_dir, self.SPECIAL_FILENAME)
        ).run_all()

    def _update_defaults(self, cli_kwargs):
        if len(self._defaults) == 0:
            return
        new_defaults = {}
        glbls = self._available_globals()
        glbls["cli"] = cli_kwargs
        for k, v in self._defaults.items():
            exec("{} = {}".format(k, v), glbls, new_defaults)
        # assert all(a in new_defaults for a in template_kwargs)
        self._defaults = new_defaults

    def _available_globals(self):
        env = {}
        env["recipe_dir"] = self._root_dir
        env["cwd"] = os.getcwd()
        out = {"env": env}
        return out

    def _rewrite_templates(self, cli_kwargs):
        self._update_defaults(cli_kwargs)
        j_env = jinja2.Environment(loader=jinja2.FileSystemLoader(self._root_dir))
        j_env.block_start_string = "((*"  # FIXME (br) this is unused
        j_env.block_end_string = "*))"  # FIXME (br)
        j_env.variable_start_string = "${"
        j_env.variable_end_string = "}$"
        j_env.comment_start_string = "((="  # FIXME (br)
        j_env.comment_end_string = "=))"  # FIXME (br)
        pattern = self.PATTERN.format(ROOT_DIR=self._root_dir)
        matches = glob.iglob(pattern, recursive=True)
        for possible_template in matches:
            if not os.path.isfile(possible_template):
                continue
            env_path = os.path.relpath(possible_template, self._root_dir)
            new_contents = j_env.get_template(env_path).render(**self._defaults)
            with open(possible_template, "w") as rendered_template:
                rendered_template.write(new_contents)


################################################################################
# CLI entrypoints
################################################################################


def find_argsetter(parser):
    parser.add_argument(
        "-sp",
        "--search-path",
        default=[RecipeTemplate.DEFAULT_SEARCH_PATH],
        action="append",
        dest="search_paths",
    )


@plugnparse.entrypoint(["find"], args=find_argsetter)
def find_entrypoint(ns, parser):
    for recipe in RecipeTemplate.find(ns.search_paths):
        print(recipe.name, recipe.path)


def run_argsetter(parser):
    parser.add_argument("recipe_name")
    parser.add_argument(
        "template_kwargs",
        nargs="*",
        metavar="template_kwarg",
        type=lambda _: tuple(_.split("=")),
    )
    # parser.add_argument('-rv', '--run-var', nargs=2, default=[], action='append', dest='search_paths')
    find_argsetter(parser)


@plugnparse.entrypoint(["run"], args=run_argsetter)
def run_entrypoint(ns, parser):
    template_kwargs = dict(ns.template_kwargs)
    recipes = [
        m for m in RecipeTemplate.find(ns.search_paths) if m.name == ns.recipe_name
    ]
    assert len(recipes) == 1
    with recipes[0] as recipe:
        recipe.run_all(template_kwargs)
