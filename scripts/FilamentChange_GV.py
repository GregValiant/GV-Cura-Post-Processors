# Copyright (c) 2023 Ultimaker B.V.
# The PostProcessingPlugin is released under the terms of the LGPLv3 or higher.

# Modification 06.09.2020
# add checkbox, now you can choose and use configuration from the firmware itself.
# Modified 12.15.23 GregValiant
#    Moved the M600 insertion below ";LAYER:" lines.
#    Edited the ToolTips.
#    Changed the layer numbering to those shown in the Cura preview and account for raft layers.

from typing import List
from ..Script import Script
import re
from UM.Application import Application #To get the current printer's settings.
from UM.Message import Message

class FilamentChange_GV(Script):

    def getSettingDataString(self):
        return """{
            "name": "Filament Change GV",
            "key": "FilamentChange_GV",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "enabled":
                {
                    "label": "Enable",
                    "description": "When checked the post processor will run.  If un-checked then it will not run.",
                    "type": "bool",
                    "default_value": true
                },
                "layer_number":
                {
                    "label": "Layer",
                    "description": "Use the Cura Preview numbers.  The Filament Change will occur at the START of the indicated layer(s).  You can use this script for multiple color changes by delimiting the layer numbers with commas.  (EX:  15,20,25)",
                    "unit": "lay num(s)",
                    "type": "str",
                    "default_value": "10",
                    "enabled": "enabled"
                },
                "firmware_config":
                {
                    "label": "Use Firmware Configuration",
                    "description": "Use the settings in your firmware, or customise the parameters of the filament change here.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enabled"
                },
                "initial_retract":
                {
                    "label": "Initial Retraction",
                    "description": "Initial filament retraction distance. The filament will be retracted with this amount before moving the nozzle away from the ongoing print.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 30.0,
                    "enabled": "enabled and not firmware_config"
                },
                "later_retract":
                {
                    "label": "Later Retraction Distance",
                    "description": "Later filament retraction distance for removal. The filament will be retracted all the way out of the printer so that you can change the filament.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 300.0,
                    "enabled": "enabled and not firmware_config"
                },
                "x_position":
                {
                    "label": "X Position",
                    "description": "Extruder X position. The print head will move here for filament change.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0,
                    "enabled": "enabled and not firmware_config"
                },
                "y_position":
                {
                    "label": "Y Position",
                    "description": "Extruder Y position. The print head will move here for filament change.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0,
                    "enabled": "enabled and not firmware_config"
                },
                "z_position":
                {
                    "label": "Z Position (relative)",
                    "description": "Extruder relative Z position. Move the print head up for filament change.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 0,
                    "minimum_value": 0,
                    "enabled": "enabled"
                },
                "retract_method":
                {
                    "label": "Retract method",
                    "description": "The gcode variant to use for retract.",
                    "type": "enum",
                    "options": {"U": "Marlin (M600 U)", "L": "Reprap (M600 L)"},
                    "default_value": "U",
                    "value": "\\\"L\\\" if machine_gcode_flavor==\\\"RepRap (RepRap)\\\" else \\\"U\\\"",
                    "enabled": "enabled and not firmware_config"
                },
                "machine_gcode_flavor":
                {
                    "label": "G-code flavor",
                    "description": "The type of g-code to be generated. This setting is controlled by the script and will not be visible.",
                    "type": "enum",
                    "options":
                    {
                        "RepRap (Marlin/Sprinter)": "Marlin",
                        "RepRap (Volumetric)": "Marlin (Volumetric)",
                        "RepRap (RepRap)": "RepRap",
                        "UltiGCode": "Ultimaker 2",
                        "Griffin": "Griffin",
                        "Makerbot": "Makerbot",
                        "BFB": "Bits from Bytes",
                        "MACH3": "Mach3",
                        "Repetier": "Repetier"
                    },
                    "default_value": "RepRap (Marlin/Sprinter)",
                    "enabled": "false"
                },
                "enable_before_macro":
                {
                    "label": "Enable G-code Before",
                    "description": "Use this to insert a custom G-code macro before the filament change happens",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enabled"
                },
                "before_macro":
                {
                    "label": "G-code Before",
                    "description": "Any custom G-code to run BEFORE the filament change happens.  (EX: M300 S1000 P10000 for a long beep).  Delimit multi-line commands with newlines (backslash + n).  Some firmware does not understand lower case commands so use upper case G and M for the actual commands.",
                    "unit": "",
                    "type": "str",
                    "default_value": "M300 S1000 P10000",
                    "enabled": "enabled and enable_before_macro"
                },
                "enable_after_macro":
                {
                    "label": "Enable G-code After",
                    "description": "Use this to insert a custom G-code macro after the filament change.  Delimit multi-line commands with newlines (backslash + n)",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enabled"
                },
                "after_macro":
                {
                    "label": "G-code After",
                    "description": "Any custom G-code to run AFTER the filament change happens.  (EX: M117 White PLA).  Delimit multi-line commands with newlines (backslash + n).  Some firmware does not understand lower case commands so use upper case G and M for the actual commands.",
                    "unit": "",
                    "type": "str",
                    "default_value": "M300 S440 P500",
                    "enabled": "enabled and enable_after_macro"
                }
            }
        }"""

    ##  Copy machine name and gcode flavor from global stack so we can use their value in the script stack
    def initialize(self) -> None:
        super().initialize()

        global_container_stack = Application.getInstance().getGlobalContainerStack()
        if global_container_stack is None or self._instance is None:
            return

        for key in ["machine_gcode_flavor"]:
            self._instance.setProperty(key, "value", global_container_stack.getProperty(key, "value"))

    def execute(self, data: List[str]):
        enabled = self.getSettingValueByKey("enabled")
        layer_nums = self.getSettingValueByKey("layer_number")
        adhesion_type = Application.getInstance().getGlobalContainerStack().getProperty("adhesion_type", "value")
        ## Get the raft layer count to adjust the Cura Preview layer to the Gcode layer
        raft_layers = 0
        if "raft" in adhesion_type:
            for num in range(2,10):
                if ";LAYER:-" in data[num]:
                    raft_layers += 1
        ## Get the settings
        initial_retract = self.getSettingValueByKey("initial_retract")
        later_retract = self.getSettingValueByKey("later_retract")
        x_pos = self.getSettingValueByKey("x_position")
        y_pos = self.getSettingValueByKey("y_position")
        z_pos = self.getSettingValueByKey("z_position")
        firmware_config = self.getSettingValueByKey("firmware_config")
        enable_before_macro = self.getSettingValueByKey("enable_before_macro")
        before_macro = self.getSettingValueByKey("before_macro")
        enable_after_macro = self.getSettingValueByKey("enable_after_macro")
        after_macro = self.getSettingValueByKey("after_macro")
        ## Exit if the post isn't enabled
        if not enabled:
            return data
        ## Initialize the main string
        color_change = ";----------Begin Filament Change plugin\n"
        if enable_before_macro:
            color_change = color_change + before_macro + "\n"
        color_change = color_change + "M600"
        ## Add parameters to the M600 command
        if not firmware_config:
            if initial_retract is not None and initial_retract > 0.:
                color_change += (" E%.2f" % initial_retract)

            if later_retract is not None and later_retract > 0.:
                ## Reprap uses 'L': https://reprap.org/wiki/G-code#M600:_Filament_change_pause
                ## Marlin uses 'U' https://marlinfw.org/docs/gcode/M600.html
                retract_method = self.getSettingValueByKey("retract_method")
                color_change += (" %s%.2f" % (retract_method, later_retract))

            if x_pos is not None:
                color_change += (" X%.2f" % x_pos)

            if y_pos is not None:
                color_change += (" Y%.2f" % y_pos)

            if z_pos is not None and z_pos > 0.:
                color_change += (" Z%.2f" % z_pos)

        color_change += "\n"

        if enable_after_macro:
            color_change += after_macro + "\n"

        color_change += ";----------End Filament Change\n"
        ## Insert the color_change script at the indicated layers taking into account raft layers and Base 0 numbering.
        layer_targets = layer_nums.split(",")
        if len(layer_targets) > 0:
            layers_found = 0
            for layer_num in layer_targets:
                actual_num = str(int(layer_num) - raft_layers - 1)
                try:
                    for num in range(2, len(data)-1):
                        if ";LAYER:" + actual_num + "\n" in data[num]:
                            color_change = re.sub("plugin", "(Start of Cura preview layer: " + str(layer_num) + ")", color_change)
                            data[num] = re.sub(";LAYER:" + actual_num + "\n", ";LAYER:" + actual_num + "\n" + color_change, data[num])
                            layers_found += 1
                except:
                    pass
        if layers_found != len(layer_targets):
            Message(title = "[Filament Change]", text = "Some layers were not found.  Please double check the layer numbers.").show()
        return data
