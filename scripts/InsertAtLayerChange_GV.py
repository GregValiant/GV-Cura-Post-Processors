# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
# Created by Wayne Porter.
# Altered January of 2023 by GregValiant (Greg Foresi)
#     Support for multi-line insertions
#     Insertion start and end layers.  Numbers are consistent with the Cura Preview (base1)
#     Frequency of Insertion (one time, every layer, every 2nd, 3rd, 5th, 10th, 25th, 50th, 100th)

from ..Script import Script
import re
from UM.Application import Application


class InsertAtLayerChange_GV(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Insert at Layer Change GV",
            "key": "InsertAtLayerChange_GV",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "insert_frequency":
                {
                    "label": "How often to insert",
                    "description": "Every so many layers starting with the Start Layer OR as single insertion at a specific layer.",
                    "type": "enum",
                    "options": {
                        "once_only": "One insertion only",
                        "every_layer": "Every Layer",
                        "every_2nd": "Every 2nd",
                        "every_3rd": "Every 3rd",
                        "every_5th": "Every 5th",
                        "every_10th": "Every 10th",
                        "every_25th": "Every 25th",
                        "every_50th": "Every 50th",
                        "every_100th": "Every 100th"},
                    "default_value": "every_layer"
                },
                "start_layer":
                {
                    "label": "Starting Layer",
                    "description": "Layer to start the insertion at.  Use layer numbers from the Cura Preview.  Enter '1' to start at gcode LAYER:0.  If you need to start from the beginning of a raft enter '-5'.",
                    "type": "int",
                    "default_value": 1,
                    "minimum_value": -5,
                    "enabled": "insert_frequency != 'once_only'"
                },
                "end_layer_enabled":
                {
                    "label": "Enable End Layer",
                    "description": "Check to use an ending layer for the insertion.  Use layer numbers from the Cura Preview.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "insert_frequency != 'once_only'"
                },
                "end_layer":
                {
                    "label": "Ending Layer",
                    "description": "Layer to end the insertion at. Enter '-1' for entire file (or disable this setting).  Use layer numbers from the Cura Preview.",
                    "type": "str",
                    "default_value": "-1",
                    "enabled": "end_layer_enabled and insert_frequency != 'once_only'"
                },
                "single_end_layer":
                {
                    "label": "Layer # for Single Insertion.",
                    "description": "Layer for a single insertion of the Gcode.  Use the layer numbers from the Cura Preview.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "insert_frequency == 'once_only'"
                },
                "gcode_to_add":
                {
                    "label": "G-code to insert.",
                    "description": "G-code to add at start of the layer. Use a comma to delimit multi-line commands. EX: G28 X Y,M220 S100,M117 HELL0.  NOTE:  All inserted text will be converted to upper-case as some firmwares don't understand lower-case.",
                    "type": "str",
                    "default_value": ""
                }
            }
        }"""

    def execute(self, data):
#Initialize variables
        mycode = self.getSettingValueByKey("gcode_to_add").upper()
        the_start_layer = int(self.getSettingValueByKey("start_layer"))-1
        the_end_layer = self.getSettingValueByKey("end_layer").lower()
        the_end_is_enabled = self.getSettingValueByKey("end_layer_enabled")
        when_to_insert = self.getSettingValueByKey("insert_frequency")
        start_here = False
        real_num = 0
        if the_end_layer == "-1" or not the_end_is_enabled:
            the_end_layer = str(len(data)-1)
    #If the gcode_to_enter is multi-line then replace the commas with newline characters
        if mycode != "":
            if "," in mycode:
                mycode = re.sub(",", "\n",mycode)
            gcode_to_add = mycode + "\n"
    #Get the insertion frequency
        match when_to_insert:
            case "every_layer":
                freq = 1
            case "every_2nd":
                freq = 2
            case "every_3rd":
                freq = 3
            case "every_5th":
                freq = 5
            case "every_10th":
                freq = 10
            case "every_25th":
                freq = 25
            case "every_50th":
                freq = 50
            case "every_100th":
                freq = 100
            case "once_only":
                the_search_layer = int(self.getSettingValueByKey("single_end_layer"))-1
            case _:
                the_search_layer = int(self.getSettingValueByKey("single_end_layer"))-1
                raise Exception("Error.  Insert changed to Once Only.")

#Single insertion
        if when_to_insert == "once_only":
            if Application.getInstance().getGlobalContainerStack().getProperty("print_sequence", "value") == "all_at_once":
                for index, layer in enumerate(data):
                    if ";LAYER:" + str(the_search_layer) + "\n" in layer:
                        lines = layer.split("\n")
                        lines.insert(1,gcode_to_add[0:-1])
                        data[index] = "\n".join(lines)
                        return data

            else:
                for index, layer in enumerate(data):
                    if ";LAYER:" + str(the_search_layer) + "\n" in layer:
                        lines = layer.split("\n")
                        lines.insert(1,gcode_to_add[0:-1])
                        data[index] = "\n".join(lines)
                        continue
                return data

#Multiple insertions
        if when_to_insert != "once_only":
            for index, layer in enumerate(data):
                lines = layer.split("\n")
                for l_index, line in enumerate(lines):
                    if ";LAYER:" in line:
                        layer_number = int(line.split(":")[1])
                        if layer_number >= int(the_start_layer)-1 and layer_number <= int(the_end_layer)-1:
                            real_num = layer_number - int(the_start_layer)
                            if int(real_num / freq) - (real_num / freq) == 0:
                                lines.insert(1,gcode_to_add[0:-1])
                                data[index] = "\n".join(lines)
                                break
        return data
