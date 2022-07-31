"""Secs scripting objects."""
import pathlib
import site
import sys
import typing

import appdirs  # type: ignore
import pip  # type: ignore

from secsgem_simulator.secsgem_package_0_1 import SecsgemPackage01
from secsgem_simulator.secsgem_package_base import SecsgemPackage


class SecsgemPackages:  # pylint: disable=too-few-public-methods
    """Manages custom site-packages for multiple secsgem version.

    Attention:
        Only one secsgem version can be loaded at a single time!

    """

    version_interfaces: typing.List[typing.Type[SecsgemPackage]] = [
        SecsgemPackage01
    ]

    def __init__(self):
        """Initialize the site packages base directory."""
        # get secsgem custom site-package path
        self.simulator_config = pathlib.Path(appdirs.user_data_dir("secsgem_simulator"))

        self.package_dir = self.simulator_config / "packages"
        self.package_dir.mkdir(parents=True, exist_ok=True)

    def version(self, version: str) -> SecsgemPackage:
        """Install and return a module for the selected version.

        Args:
            version: version number of the package

        Returns:
            Package class

        """
        package_version_dir = self._install_package(version)

        self._enable_package_site_path(package_version_dir)

        for version_interface in self.version_interfaces:
            if version_interface.matches(version):
                return version_interface(package_version_dir)

        raise ValueError(f"Unsupported secsgem version '{version}'")

    def _enable_package_site_path(self, package_version_path: pathlib.Path):
        """Enable the package site path in sys.path.

        Args:
            package_version_path: path to the package version site-packages

        """
        # update import paths
        for path in sys.path:
            if path.startswith(str(self.package_dir)):
                sys.path.remove(path)

        site.addsitedir(str(package_version_path))

    def _install_package(self, version: str) -> pathlib.Path:
        """Install the secsgem package to a custom site-package path.

        Args:
            version: package version number

        Returns:
            path to te site-package

        """
        # get secsgem custom site-package path
        package_version_dir = self.package_dir / version

        # install secsgem version if not installed
        if not package_version_dir.is_dir():
            pip.main(["install", "--target", str(package_version_dir), f"secsgem=={version}"])

        return package_version_dir
