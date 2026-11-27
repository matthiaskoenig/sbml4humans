"""Bundle the pinned Rust runtime in platform-specific application wheels."""

import importlib.util
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


_spec = importlib.util.spec_from_file_location(
    "sbml4humans_native_build", Path(__file__).with_name("build_native.py")
)
assert _spec is not None and _spec.loader is not None
_builder = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_builder)


class CustomBuildHook(BuildHookInterface):
    """Build once and preserve the native artifact's ABI3 platform tag."""

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        """Include the verified private extension in regular and editable builds."""
        if self.target_name != "wheel":
            return
        payload, tag = _builder.runtime()
        build_data["pure_python"] = False
        build_data["tag"] = tag
        build_data["force_include"][str(payload)] = "_sbml4humans_runtime"
        if version == "editable":
            build_data["force_include_editable"][str(payload)] = "_sbml4humans_runtime"
