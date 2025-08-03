import importlib

__version__ = "1.0.0b1"

__all__ = [
    "add_data",
    "app",
    "delete_data",
    "fetch_data",
    "insert_data",
    "mysql_connector",
    "show_data",
    "triggers",
    "typehints",
    "views"
]

import add_data
import app
import delete_data
import fetch_data
import insert_data
import mysql_connector
import show_data
import triggers
import typehints
import views


def __getattr__(name):
    if name in __all__:
        return importlib.import_module(f".{name}", __name__)
    raise AttributeError(f"module {__name__} has no attribute {name}")
