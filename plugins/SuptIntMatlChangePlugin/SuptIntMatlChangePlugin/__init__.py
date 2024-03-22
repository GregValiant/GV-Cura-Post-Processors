# Copyright (c) 2024 GregValiant
# Support Interface Material Change is released under the terms of the AGPLv3 or higher.

from . import SuptIntMatlChangePlugin


def getMetaData():
    return {}

def register(app):
    return {"extension": SuptIntMatlChangePlugin.SuptIntMatlChangePlugin()}
