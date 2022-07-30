"""Lua script calls and namespaces."""
import time
import types
import typing

import lupa  # type: ignore

from secsgem_simulator.secs_script import SecsgemPackages


class ScriptBaseObject:
    """Base access object for script."""

    @staticmethod
    def setup(version: str):
        """Set the secsgem package up.

        Args:
            version: version of the package

        """
        return SecsgemPackages().version(version)

    @staticmethod
    def sleep(duration: float):
        """Do nothing for a amount of time.

        Args:
            duration: time to sleep

        """
        time.sleep(duration)


class ScriptRunner:  # pylint: disable=too-few-public-methods
    """Wrapper for running a lua script."""

    def __init__(self):
        """Initialize script runner object."""
        self.lua = lupa.LuaRuntime(
            unpack_returned_tuples=True,
            attribute_filter=self._lua_attribute_filter,
            register_eval=False,
            register_builtins=False,)

        self.lua.globals()["base"] = ScriptBaseObject()

    def _lua_attribute_filter(self, obj: typing.Any, attr_name: str, is_setting: bool):
        """Deny forbidden python functions.

        Args:
            obj: called object
            attr_name: called attribute
            is_setting: True if write access.

        """
        print("## laf", obj, attr_name, is_setting)
        if isinstance(obj, types.ModuleType) and obj.__name__ == "builtins":
            self._lua_attribute_filter_builtins(attr_name)

        return attr_name

    @staticmethod
    def _lua_attribute_filter_builtins(attr_name: str):
        """Deny forbidden python functions in the builtins module.

        Args:
            attr_name: name of the function

        """
        if attr_name in ("globals", "eval", "exec"):
            raise PermissionError("Access denied")

    def run_string(self, script: str) -> typing.Any:
        """Run a passed script.

        Args:
            script: lua script to execute

        Returns:
            data returned from script

        """
        return self.lua.execute(script)
