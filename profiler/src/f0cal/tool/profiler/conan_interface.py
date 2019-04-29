import os
import shutil

import f0cal

F0CAL_REMOTE_NAME = "f0cal"

HERE = os.path.dirname(__file__)

@f0cal.plugin(name="conan", sets="config_file")
def config_file():
    return """
    [env]
    CONAN_USER_HOME=${conan:user_home}

    [conan]
    user_home=${f0cal:prefix}/home/conan
    hook_name=f0cal-hook
    """

def install_hook(user_home, hook_name):
    env_path = os.path.join(user_home, ".conan", "hooks", f"{hook_name}.py")
    if os.path.exists(env_path):
        return
    _d = os.path.dirname(env_path)
    if not os.path.exists(_d):
        os.makedirs(_d)
    pkg_path = os.path.join(HERE, "conan_hooks.py")
    shutil.copy(pkg_path, env_path)
    os.system("conan config set hooks.f0cal-hook")

def initialize_home(user_home):
    if os.path.exists(user_home):
        return
    os.system("conan profile new default --detect")
    os.system("conan profile update settings.compiler.libcxx=libstdc++11 default")
    os.system("conan remote add f0cal https://api.bintray.com/conan/f0cal/conan")

def install_packages():
    os.system("conan install babeltrace/1.53@f0cal/testing --build=missing")

@f0cal.plugin(name="conan", sets="ini")
def ini(user_home, hook_name):
    initialize_home(user_home)
    install_hook(user_home, hook_name)
    install_packages()

