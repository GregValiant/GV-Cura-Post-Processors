# Copyright (c) 2023 GregValiant (Greg Foresi)
#   This PostProcessingPlugin is released under the terms of the AGPLv3 or higher.
#   This post-processor opens the "Post Processor ReadMe.pdf file in the system viewer.

from UM.Platform import Platform
from ..Script import Script
from UM.Application import Application
import os

class AAA_PostProcessReadMe_GV(Script):

    def initialize(self) -> None:
        super().initialize()

        SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
        if Platform.isWindows:
            text_file = os.startfile(SCRIPT_DIR + "\AAA_Post Processor ReadMe_GV.pdf")
        elif Platform.isOSX():
            text_file = open(SCRIPT_DIR + "\AAA_Post Processor ReadMe_GV.pdf")
        elif Platform.isLinux:
            text_file = os.system(SCRIPT_DIR + "\AAA_Post Processor ReadMe_GV.pdf")

    def getSettingDataString(self):
        return """{
            "name": "Help (PDF file) GV",
            "key": "AAA_PostProcessReadMe_GV",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "auto_open":
                {
                    "label": "Open Description PDF",
                    "description": "",
                    "type": "bool",
                    "value": true,
                    "enabled": false
                }
            }
        }"""
