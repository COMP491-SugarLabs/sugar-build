import os
import subprocess

from devbot import command
from devbot import distro

class PackageManager:
    def __init__(self, test=False, interactive=True):
        self._test = test
        self._interactive = interactive

    def install_packages(self, packages):
        args = ["yum"]

        if not self._interactive:
            args.append("-y")

        args.append("install")
        args.extend(packages)

        command.run_with_sudo(args, test=self._test)

    def remove_packages(self, packages):
        args = ["rpm", "-e"]
        args.extend(packages)

        command.run_with_sudo(args, test=self._test)

    def update(self):
        args = ["yum"]

        if not self._interactive:
            args.append("-y")

        args.append("update")

        command.run_with_sudo(args, test=self._test)

    def find_all(self):
        query_format = "--queryformat=[%{NAME} ]"
        all = subprocess.check_output(["rpm", "-qa", query_format]).strip()
        return all.split(" ")

    def find_with_deps(self, packages):
        result = []

        for package in packages:
            if package not in result:
                result.append(package)

            self._find_deps(package, result)

        return result

    def _find_deps(self, package, result):
        query_format = "--queryformat=[%{REQUIRENAME} ]"

        try:
            capabilities = subprocess.check_output(["rpm", "-q",
                                                    query_format,
                                                    package]).strip()
        except subprocess.CalledProcessError:
            print "Package %s not installed" % package
            return

        filtered = [cap for cap in capabilities.split(" ")
                    if not cap.startswith("rpmlib")]

        if capabilities and filtered:
            args = ["rpm", "-q",
                    "--queryformat=[%{NAME} ]",
                    "--whatprovides"]
            args.extend(filtered)
            
            deps_packages = subprocess.check_output(args).strip()
            for dep_package in deps_packages.split(" "):
                if dep_package not in result:
                    result.append(dep_package)
                    self._find_deps(dep_package, result)

distro.register_package_manager("fedora", PackageManager)

class DistroInfo:
    def __init__(self):
        self.use_lib64 = os.uname()[4] == "x86_64"

        arch = subprocess.check_output(["uname", "-i"]).strip()

        self.name = "fedora"
        self.version = None
        self.system_version = None
        self.valid = False
        
        if arch in ["i386", "i686", "x86_64"]:
            fedora_release = self._get_fedora_release()
            if fedora_release == "Fedora release 17 (Beefy Miracle)":
                self.version = "17"
                self.system_version = "3.4"
                self.valid = True
            elif fedora_release == "Fedora release 18 (Spherical Cow)":
                self.version = "18"
                self.system_version = "3.6"
                self.valid = True

    def _get_fedora_release(self):
        try:
            return open("/etc/fedora-release").read().strip()
        except OSError:
            return None
 
distro.register_distro_info(DistroInfo)