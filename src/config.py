from __future__ import annotations

"""Application configuration loading with lazy singleton support."""

import copy
import threading
import tomllib
from pathlib import Path
from typing import Any, cast


DEFAULT_CONFIG_PATH = Path("app_config.toml")
_singleton: "Config | None" = None
_singleton_lock = threading.RLock()


class AttrDict(dict):
    """Dictionary subclass that also exposes keys as attributes."""

    def __getattr__(self, key: str) -> Any:
        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value

    def __delattr__(self, key: str) -> None:
        try:
            del self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc


class Config:
    """Lazy TOML-backed application configuration.

    Creating a ``Config`` instance does not read the TOML file. The file is
    parsed on first access to ``data`` or a section attribute, which keeps
    module imports cheap and makes initialization order more predictable.
    """

    def __init__(
        self,
        path: str | Path = DEFAULT_CONFIG_PATH,
        *,
        lazy: bool = True,
    ) -> None:
        self.path = Path(path)
        self._data: AttrDict | None = None
        if not lazy:
            self.load()

    @classmethod
    def from_toml(cls, path: str | Path) -> "Config":
        return cls(path=path, lazy=True)

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        *,
        path: str | Path = DEFAULT_CONFIG_PATH,
    ) -> "Config":
        config = cls(path=path, lazy=True)
        config._data = AttrDict(_to_attr(data))
        return config

    def load(self) -> "Config":
        with self.path.open("rb") as file:
            raw = tomllib.load(file)
        self._data = AttrDict(_to_attr(raw))
        return self

    def reload(self) -> "Config":
        self._data = None
        return self.load()

    @property
    def loaded(self) -> bool:
        return self._data is not None

    @property
    def data(self) -> AttrDict:
        if self._data is None:
            self.load()
        return cast(AttrDict, self._data)

    def section(self, name: str) -> AttrDict:
        section = self.data.get(name)
        if section is None:
            raise KeyError(f"Configuration section not found: {name}")
        return section

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def to_dict(self) -> dict[str, Any]:
        """Return a plain Python dict suitable for serialization."""
        return _to_plain(self.data)

    def as_dict(self) -> dict[str, Any]:
        return self.to_dict()

    def __getattr__(self, key: str) -> Any:
        data = cast(AttrDict, self.__dict__.get("_data"))
        if data is None:
            self.load()
            data = cast(AttrDict, self._data)
        if key in data:
            return data[key]
        raise AttributeError(key)

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __contains__(self, key: str) -> bool:
        return key in self.data

    def __repr__(self) -> str:
        state = "loaded" if self.loaded else "lazy"
        return f"Config(path={str(self.path)!r}, state={state!r})"


def _to_attr(value: Any) -> Any:
    """Recursively convert dictionaries to attribute-accessible objects."""
    if isinstance(value, dict):
        return AttrDict({key: _to_attr(item) for key, item in value.items()})
    if isinstance(value, list):
        return [_to_attr(item) for item in value]
    return value


def _to_plain(value: Any) -> Any:
    """Recursively convert AttrDict values to plain Python dictionaries."""
    if isinstance(value, AttrDict):
        return {key: _to_plain(item) for key, item in value.items()}
    if isinstance(value, dict):
        return {key: _to_plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_plain(item) for item in value]
    return copy.deepcopy(value)


def cfg(path: str | Path | None = None) -> Config:
    """Return a process-wide lazy singleton Config.

    If ``path`` is provided, replace the cached singleton with a new Config
    pointing to that path. Otherwise, create the default singleton on first
    use and return the same instance on subsequent calls.
    """
    global _singleton
    with _singleton_lock:
        if path is not None:
            _singleton = Config(path=path, lazy=True)
        elif _singleton is None:
            _singleton = Config()
        return _singleton


def reset_cfg() -> None:
    """Clear the cached singleton so the next cfg() call creates a new one."""
    global _singleton
    with _singleton_lock:
        _singleton = None
