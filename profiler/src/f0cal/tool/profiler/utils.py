import gpustat
import cpuinfo
import psutil


GB = 1024 ** 3

# The f0lder where all bins and data will go
F0CAL_FOLDER = "f0cal"
ALLOW_NONE_VENV = False


class NonVirtaulEnvError(Exception):
    pass


class NoneSetUpError(Exception):
    pass


class SystemDetector:
    @staticmethod
    def get_gpu_info():
        # Note this only works for nvidia gpus atm
        try:
            stats = gpustat.new_query()
        except:
            return {"have_gpu": False, "gpus": []}
        return {
            "have_gpu": bool(len(stats.gpus)),
            "gpus": [x["name"] for x in stats.gpus],
        }

    @staticmethod
    def get_cpu_info():

        return cpuinfo.get_cpu_info()

    @staticmethod
    def get_mem_info():
        # Returns in GB at the moment
        mem = psutil.virtual_memory()
        return {"memory": mem.total / GB}

    @classmethod
    def get_all_stats(cls):
        ret = {}
        ret.update(cls.get_cpu_info())
        ret.update(cls.get_gpu_info())
        ret.update(cls.get_mem_info())

        return ret

    @staticmethod
    def get_conan_home():
        pass
