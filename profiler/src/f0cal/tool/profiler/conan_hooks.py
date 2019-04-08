import os
import sys
import glob

import logging

LOG = logging.getLogger(__name__)

from conans.model.ref import ConanFileReference


class Hooker:
    def pre_export(self, output, conanfile, conanfile_path, reference, **kwargs):
        assert conanfile
        output.info("conanfile_path=%s" % conanfile_path)
        output.info("reference=%s" % str(reference))

    def post_export(self, output, conanfile, conanfile_path, reference, **kwargs):
        assert conanfile
        output.info("conanfile_path=%s" % conanfile_path)
        output.info("reference=%s" % str(reference))

    def pre_source(self, output, conanfile, conanfile_path, **kwargs):
        assert conanfile
        output.info("conanfile_path=%s" % conanfile_path)
        if conanfile.in_local_cache:
            output.info("reference=%s" % str(kwargs["reference"]))

    def post_source(self, output, conanfile, conanfile_path, **kwargs):
        assert conanfile
        output.info("conanfile_path=%s" % conanfile_path)
        if conanfile.in_local_cache:
            output.info("reference=%s" % str(kwargs["reference"]))

    def pre_build(self, output, conanfile, **kwargs):
        assert conanfile
        if conanfile.in_local_cache:
            output.info("reference=%s" % str(kwargs["reference"]))
            output.info("package_id=%s" % kwargs["package_id"])
        else:
            output.info("conanfile_path=%s" % kwargs["conanfile_path"])

    def post_build(self, output, conanfile, **kwargs):
        assert conanfile
        if conanfile.in_local_cache:
            output.info("reference=%s" % str(kwargs["reference"]))
            output.info("package_id=%s" % kwargs["package_id"])
        else:
            output.info("conanfile_path=%s" % kwargs["conanfile_path"])

    def pre_package(self, output, conanfile, conanfile_path, **kwargs):
        assert conanfile
        output.info("conanfile_path=%s" % conanfile_path)
        if conanfile.in_local_cache:
            output.info("reference=%s" % str(kwargs["reference"]))
            output.info("package_id=%s" % kwargs["package_id"])

    def post_package(self, output, conanfile, conanfile_path, **kwargs):
        assert conanfile
        output.info("conanfile_path=%s" % conanfile_path)
        if conanfile.in_local_cache:
            output.info("reference=%s" % str(kwargs["reference"]))
            output.info("package_id=%s" % kwargs["package_id"])

    def pre_upload(self, output, conanfile_path, reference, remote, **kwargs):
        output.info("conanfile_path=%s" % conanfile_path)
        output.info("reference=%s" % str(reference))
        output.info("remote.name=%s" % remote.name)

    def post_upload(self, output, conanfile_path, reference, remote, **kwargs):
        output.info("conanfile_path=%s" % conanfile_path)
        output.info("reference=%s" % str(reference))
        output.info("remote.name=%s" % remote.name)

    def pre_upload_recipe(self, output, conanfile_path, reference, remote, **kwargs):
        output.info("conanfile_path=%s" % conanfile_path)
        output.info("reference=%s" % str(reference))
        output.info("remote.name=%s" % remote.name)

    def post_upload_recipe(self, output, conanfile_path, reference, remote, **kwargs):
        output.info("conanfile_path=%s" % conanfile_path)
        output.info("reference=%s" % str(reference))
        output.info("remote.name=%s" % remote.name)

    def pre_upload_package(
        self, output, conanfile_path, reference, package_id, remote, **kwargs
    ):
        output.info("conanfile_path=%s" % conanfile_path)
        output.info("reference=%s" % str(reference))
        output.info("package_id=%s" % package_id)
        output.info("remote.name=%s" % remote.name)

    def post_upload_package(
        self, output, conanfile_path, reference, package_id, remote, **kwargs
    ):
        output.info("conanfile_path=%s" % conanfile_path)
        output.info("reference=%s" % str(reference))
        output.info("package_id=%s" % package_id)
        output.info("remote.name=%s" % remote.name)

    def pre_download(self, output, reference, remote, **kwargs):
        output.info("reference=%s" % str(reference))
        output.info("remote.name=%s" % remote.name)

    def post_download(self, output, conanfile_path, reference, remote, **kwargs):
        output.info("conanfile_path=%s" % conanfile_path)
        output.info("reference=%s" % str(reference))
        output.info("remote.name=%s" % remote.name)

    def pre_download_recipe(self, output, reference, remote, **kwargs):
        output.info("reference=%s" % str(reference))
        output.info("remote.name=%s" % remote.name)

    def post_download_recipe(self, output, conanfile_path, reference, remote, **kwargs):
        output.info("conanfile_path=%s" % conanfile_path)
        output.info("reference=%s" % str(reference))
        output.info("remote.name=%s" % remote.name)

    def pre_download_package(
        self, output, conanfile_path, reference, package_id, remote, **kwargs
    ):
        output.info("conanfile_path=%s" % conanfile_path)
        output.info("reference=%s" % str(reference))
        output.info("package_id=%s" % package_id)
        output.info("remote.name=%s" % remote.name)

    def post_download_package(
        self, output, conanfile_path, reference, package_id, remote, **kwargs
    ):
        output.info("conanfile_path=%s" % conanfile_path)
        output.info("reference=%s" % str(reference))
        output.info("package_id=%s" % package_id)
        output.info("remote.name=%s" % remote.name)

    @property
    def exports(self):
        self_dict = dir(self)
        _test = lambda _attr: _attr.startswith("pre") or _attr.startswith("post")
        keys = [attr for attr in self_dict if _test(attr)]
        values = [getattr(self, attr) for attr in self_dict if _test(attr)]
        return dict(zip(keys, values))


class VenvHooker(Hooker):
    def __init__(self, prefix):
        self._prefix = prefix
        self._output = None
        self._conanfile = None

    def _package_dir(self, conanfile_path, package_id):
        _d = os.path.dirname(conanfile_path)
        _p = os.path.abspath(os.path.join(_d, "..", "package", package_id))
        assert os.path.exists(_p), _p
        return _p

    def _symlink_one(self, src, dst):
        self._output.info(f"{src} --> {dst}")
        _p, _ = os.path.split(dst)
        if not os.path.exists(_p):
            os.makedirs(_p)
        assert not os.path.exists(dst), dst
        os.symlink(src, dst)

    def _symlink_tree(self, src, dst):
        src_glob = os.path.join(*src)
        dst_glob = os.path.join(*dst)
        for src_path in glob.glob(src_glob):
            _, src = os.path.split(src_path)
            dst_path = dst_glob.format(src=src)
            self._symlink_one(src_path, dst_path)

    def _update_venv(self, pkg_name, pkg_dir):
        assert os.path.exists(pkg_dir), pkg_dir
        self._symlink_tree([pkg_dir, "bin", "*"], [self._prefix, "bin", "{src}"])
        self._symlink_tree([pkg_dir, "lib", "*.so*"], [self._prefix, "lib", "{src}"])
        self._symlink_tree([pkg_dir, "include"], [self._prefix, "include", pkg_name, "{src}"])
        self._symlink_tree([pkg_dir, "etc", "*"], [self._prefix, "etc", "{src}"])

    def _parse_reference(self, ref):
        return ConanFileReference.loads(ref)

    def post_package(
        self,
        output,
        conanfile,
        conanfile_path,
        reference=None,
        package_id=None,
        **kwargs,
    ):
        assert conanfile
        assert conanfile.in_local_cache
        self._output = output
        self._conanfile = conanfile
        self._update_venv(reference.name, conanfile.package_folder)

    def post_download_package(
        self, output, conanfile_path, reference, package_id, remote, **kwargs
    ):
        self._output = output
        self._output.info(kwargs)
        pkg_dir = self._package_dir(conanfile_path, package_id)
        self._update_venv(reference.name, pkg_dir)

    @classmethod
    def from_environment(cls, env_dict, prefix=None):
        prefix = sys.prefix if prefix is None else prefix
        real_prefix = getattr(sys, "real_prefix", None)
        virtualenv = env_dict.get("VIRTUAL_ENV", None)
        debug_dict = dict(prefix=prefix, real_prefix=real_prefix, virtualenv=virtualenv)
        assert real_prefix is not None or virtualenv is not None, debug_dict
        if virtualenv is not None:
            assert prefix == virtualenv, debug_dict
        if real_prefix is not None:
            assert prefix != real_prefix, debug_dict
        # conan_user_home = env_dict.get('CONAN_USER_HOME', None)
        return cls(prefix)

    @property
    def exports(self):
        _exports = ["post_package", "post_download_package"]
        super_exports = super().exports
        return {k: super_exports[k] for k in _exports}


locals().update(VenvHooker.from_environment(os.environ).exports)

