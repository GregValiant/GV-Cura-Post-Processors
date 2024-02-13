# By GregValiant (Greg FOresi) September 2023
# This post will alter gcode and change it from a Multi-extruder print to a single extruder print with manual tool changes.

from ..Script import Script
from cura.CuraApplication import CuraApplication
import re
from typing import List, Tuple
from UM.Message import Message

class EmulateMultiExtruder_GV(Script):

    def initialize(self) -> None:
        super().initialize()
        mycura = CuraApplication.getInstance().getGlobalContainerStack()
        extruder = mycura.extruderList
        ext_count = int(mycura.getProperty("machine_extruder_count", "value"))
        machine_width = int(mycura.getProperty("machine_width", "value"))
        self._instance.setProperty("park_x", "maximum_value", machine_width)
        machine_depth = int(mycura.getProperty("machine_depth", "value"))
        self._instance.setProperty("park_y", "maximum_value", machine_depth)
        self._instance.setProperty("t0_temp", "value", extruder[0].getProperty("material_print_temperature", "value"))
        if ext_count == 1:
            Message(title = "Emulate a Multi-Extruder Printer", text = "Your printer must be configured with dual extruders to use this post.").show()
        else:
            self._instance.setProperty("t1_temp", "value", extruder[1].getProperty("material_print_temperature", "value"))

    def getSettingDataString(self):
            return """{
            "name": "Emulate a Multi-Extruder printer GV",
            "key": "EmulateMultiExtruder_GV",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "pause_method":
                {
                    "label": "Pause Method",
                    "description": "The method or gcode command to use for pausing.",
                    "type": "enum",
                    "options": {"marlin": "Marlin (M0)", "griffin": "Griffin (M0, firmware retract)", "bq": "BQ (M25)", "reprap": "RepRap (M226)", "repetier": "Repetier/OctoPrint (@pause)"},
                    "default_value": "marlin"
                },
                "t0_str":
                {
                    "label": "Message to LCD for Ext#1",
                    "description": "Message to appear on the LCD for the filament change.",
                    "type": "str",
                    "enabled": true,
                    "default_value": "Red"
                },
                "t0_temp":
                {
                    "label": "Ext#1 print temperature",
                    "description": "The temperature to use during the pause and for the new filament.",
                    "type": "int",
                    "enabled": true,
                    "value": 205,
                    "default_value": 205
                },
                "t1_str":
                {
                    "label": "Message to LCD for Ext#2",
                    "description": "Message to appear on the LCD for the filament change.",
                    "type": "str",
                    "enabled": true,
                    "default_value": "Blue"
                },
                "t1_temp":
                {
                    "label": "Ext#2 print temperature",
                    "description": "The temperature to use during the pause and for the new filament.",
                    "type": "int",
                    "enabled": true,
                    "value": 205,
                    "default_value": 205
                },
                "t2_enable":
                {
                    "label": "enable extruder 3",
                    "description": "If the extruder count is 3 then enable the Extruder 3 setting.",
                    "type": "bool",
                    "enabled": false,
                    "default_value": false
                },
                "t2_str":
                {
                    "label": "Message to LCD for Ext#3",
                    "description": "Message to appear on the LCD for the filament change.",
                    "type": "str",
                    "enabled": "t2_enable",
                    "default_value": "White"
                },
                "t2_temp":
                {
                    "label": "Ext#3 print temperature",
                    "description": "The temperature to use during the pause and for the new filament.",
                    "type": "int",
                    "enabled": "t2_enable",
                    "value": 205,
                    "default_value": 205
                },
                "t3_enable":
                {
                    "label": "enable extruder 4",
                    "description": "Whether to enable the Extruder 3 setting.",
                    "type": "bool",
                    "enabled": false,
                    "default_value": false
                },
                "t3_str":
                {
                    "label": "Message to LCD for Ext#4",
                    "description": "Message to appear on the LCD for the filament change.",
                    "type": "str",
                    "enabled": "t3_enable",
                    "default_value": "Green"
                },
                "t3_temp":
                {
                    "label": "Ext#4 print temperature",
                    "description": "The temperature to use during the pause and for the new filament.",
                    "type": "int",
                    "enabled": "t3_enable",
                    "value": 205,
                    "default_value": 205
                },
                "skip_skirt":
                {
                    "label": "Skip Skirt Changes",
                    "description": "Cura will use all extruders on the skirt to get them flowing.  If more than 1 extruder is used for models on LAYER:0 then you CANNOT skip the skirt else you may skip it and save at least 2 tool changes.",
                    "type": "bool",
                    "enabled": true,
                    "default_value": true
                },
                "park_head":
                {
                    "label": "Park Head for changes?",
                    "description": "Whether to park the head when switching any filament. The park position is the same for all pauses.",
                    "type": "bool",
                    "enabled": true,
                    "default_value": true
                },
                "park_x":
                {
                    "label": "Park X",
                    "description": "The X location to park the head for all pauses.",
                    "type": "int",
                    "enabled": "park_head",
                    "default_value": 0,
                    "maximum_value": 500
                },
                "park_y":
                {
                    "label": "Park Y",
                    "description": "The Y location to park the head for all pauses.",
                    "type": "int",
                    "enabled": "park_head",
                    "default_value": 0,
                    "maximum_value": 500
                },
                "m300_add":
                {
                    "label": "Beep at Pauses",
                    "description": "Add M300 line to beep at each pause.",
                    "type": "bool",
                    "enabled": true,
                    "default_value": false
                },
                "m118_add":
                {
                    "label": "Add M118",
                    "description": "M118 will bounce the M117 messages to a print server.",
                    "type": "bool",
                    "enabled": true,
                    "default_value": false
                }
            }
        }"""

    def execute(self, data):
        mycura = CuraApplication.getInstance().getGlobalContainerStack()
        extruder = mycura.extruderList
        prime_tower_enable = bool(mycura.getProperty("prime_tower_enable", "value"))
        prime_tower_size = int(mycura.getProperty("prime_tower_size", "value"))
        prime_tower_position_x = int(mycura.getProperty("prime_tower_position_x", "value"))
        prime_tower_position_y = int(mycura.getProperty("prime_tower_position_y", "value"))
        prime_tower_ctr = f"X{prime_tower_position_x - prime_tower_size / 2} Y{prime_tower_position_y + prime_tower_size / 2}"
        ext_count = int(mycura.getProperty("machine_extruder_count", "value"))
        if ext_count == 1:
            Message(title = "Emulate Multi-Extruder Printer", text = "Your printer must be configured with dual extruders to use this post because the tool changes are used to enter the pauses.  The post will exit.").show()
            return data
        m84_line = "M84 S3600"
        speed_travel = int(extruder[0].getProperty("speed_travel", "value")) * 60
        retract_enabled = bool(extruder[0].getProperty("retraction_enable", "value"))
        retract_dist = str(extruder[0].getProperty("retraction_amount", "value"))
        retract_speed = str(extruder[0].getProperty("retraction_retract_speed", "value"))
        unretract_speed = str(extruder[0].getProperty("retraction_prime_speed", "value"))
        if retract_enabled:
            retract_line = "G1 F" + str(retract_speed) + " E-" + str(retract_dist) + "\n"
            unretract_line = "G1 F" + str(unretract_speed) + " E" + str(retract_dist) + "\n"
        pause_method = self.getSettingValueByKey("pause_method")
        if pause_method == "marlin":
            pause_cmd = "M0\n"
        elif pause_method == "griffin":
            pause_cmd = "M0\n"
        elif pause_method == "bq":
            pause_cmd = "M25\n"
        elif pause_method == "reprap":
            pause_cmd == "M226\n"
        elif pause_method == "repetier":
            pause_cmd = "@pause\n"
        else:
            pause_cmd = "M0\n"
        relative_ext_mode = bool(mycura.getProperty("relative_extrusion", "value"))
        if relative_ext_mode:
            ext_mode_str = "M83\n"
        else:
            ext_mode_str = "M82\n"
        park_head = self.getSettingValueByKey("park_head")
        park_x = self.getSettingValueByKey("park_x")
        park_y = self.getSettingValueByKey("park_y")
        t0_str = "M117 " + str(self.getSettingValueByKey("t0_str")) + "\n"
        t1_str = "M117 " + str(self.getSettingValueByKey("t1_str")) + "\n"
        t2_str = "M117 " + str(self.getSettingValueByKey("t2_str")) + "\n"
        t3_str = "M117 " + str(self.getSettingValueByKey("t3_str")) + "\n"
        t0_temp = "M104 S" + str(self.getSettingValueByKey("t0_temp")) + "\n"
        t1_temp = "M104 S" + str(self.getSettingValueByKey("t1_temp")) + "\n"
        t2_temp = "M104 S" + str(self.getSettingValueByKey("t2_temp")) + "\n"
        t3_temp = "M104 S" + str(self.getSettingValueByKey("t3_temp")) + "\n"
        m118_add = bool(self.getSettingValueByKey("m118_add"))
        if m118_add:
            m118_t0_str = "M118 " + str(self.getSettingValueByKey("t0_str")) + " @ " + str(self.getSettingValueByKey("t0_temp")) + "°\n"
            m118_t1_str = "M118 " + str(self.getSettingValueByKey("t1_str")) + " @ " + str(self.getSettingValueByKey("t1_temp")) + "°\n"
            m118_t2_str = "M118 " + str(self.getSettingValueByKey("t2_str")) + " @ " + str(self.getSettingValueByKey("t2_temp")) + "°\n"
            m118_t3_str = "M118 " + str(self.getSettingValueByKey("t3_str")) + " @ " + str(self.getSettingValueByKey("t3_temp")) + "°\n"
        else:
            m118_t0_str = ""
            m118_t1_str = ""
            m118_t2_str = ""
            m118_t3_str = ""

        if park_head:
            park_string = f"G0 X{park_x} Y{park_y} F{speed_travel} ;Move to park position\n"
        else:
            park_string = ""
        
        if self.getSettingValueByKey("m300_add"):
            m300_str = "M300 P500\n"
        else:
            m300_str = ""

        t0_replacement_pre_string_1 = ";TYPE:CUSTOM  T0 Tool Change replacement code\n" + m84_line + "\nG91 ;Relative positioning\n"
        t0_replacement_pre_string_2 = "G1 F600 Z3 ;Move Up\nG90 ;Absolute movement\n" + park_string + m300_str + t0_temp + t0_str + m118_t0_str + pause_cmd

        t1_replacement_pre_string_1 = ";TYPE:CUSTOM  T1 Tool Change replacement code\n" + m84_line + "\nG91 ;Relative positioning\n"
        t1_replacement_pre_string_2 = "G1 F600 Z3 ;Move Up\nG90 ;Absolute movement\n" + park_string + m300_str + t1_temp + t1_str + m118_t1_str + pause_cmd

        t2_replacement_pre_string_1 = ";TYPE:CUSTOM  T2 Tool Change replacement code\n" + m84_line + "\nG91 ;Relative positioning\n"
        t2_replacement_pre_string_2 = "G1 F600 Z3 ;Move Up\nG90 ;Absolute movement\n" + park_string + m300_str + t2_temp + t2_str + m118_t2_str + pause_cmd
        t3_replacement_pre_string_1 = ";TYPE:CUSTOM  T3 Tool Change replacement code\n" + m84_line + "\nG91 ;Relative positioning\n"
        t3_replacement_pre_string_2 = "G1 F600 Z3 ;Move Up\nG90 ;Absolute movement\n" + park_string + m300_str + t3_temp + t3_str + m118_t3_str + pause_cmd
        purge_line = "M83\nG1 F200 E10\n" + retract_line + "G92 E0\n"
        # Comment out the first tool changes-----------------------------------
        lines = data[1].split("\n")
        for index, line in enumerate(lines):
            if line in ["T0","T1","T2","T3"]:
                lines[index] = ";" + line
        data[1] = "\n".join(lines)
        skip_it = 2 if bool(self.getSettingValueByKey("skip_skirt")) else 0
        for num in range(2,len(data)-1,1):
            lines = data[num].split("\n")
            for index, line in enumerate(lines):
                if lines[index].startswith("M109"):
                    lines[index] = "M104 S" + lines[index].split("S")[1]
                    data[num] = "\n".join(lines)
                if line.startswith("T0"):
                    if skip_it > 0:
                        skip_it -= 1
                        continue
                    return_location_list = []
                    return_location_list = self.getReturnLocation(data, num, index, retract_speed)
                    return_location = str(return_location_list[0])
                    is_retraction = bool(return_location_list[1])
                    if is_retraction:
                        retract_str = retract_line
                        unretract_str = unretract_line
                    else:
                        retract_str = ""
                        unretract_str = ""
                    return_to_str = f"G0 F{speed_travel}{return_location}\n"
                    final_str = t0_replacement_pre_string_1 + retract_str + t0_replacement_pre_string_2 + purge_line + return_to_str + "G91\nG0 F600 Z-3\nG90\n" + unretract_str + ext_mode_str + "; End of change"
                    lines[index] = final_str
                    data[num] = "\n".join(lines)
                if line.startswith("T1"):
                    if skip_it > 0:
                        skip_it -= 1
                        continue
                    return_location = self.getReturnLocation(data, num, index, retract_speed)[0]
                    is_retraction = bool(self.getReturnLocation(data, num, index, retract_speed)[1])
                    if is_retraction:
                        retract_str = retract_line
                        unretract_str = unretract_line
                    else:
                        retract_str = ""
                        unretract_str = ""
                    return_to_str = f"G0 F{speed_travel}{return_location}\n"
                    final_str = t1_replacement_pre_string_1 + retract_str + t1_replacement_pre_string_2 + purge_line + return_to_str + "G91\nG0 F600 Z-3\nG90\n" + unretract_str + ext_mode_str + "; End of change"
                    lines[index] = final_str #lines.insert(index+1,final_str)
                    data[num] = "\n".join(lines)
                if line.startswith("T2"):
                    if skip_it > 0:
                        skip_it -= 1
                        continue
                    return_location_list = self.getReturnLocation(data, num, index, retract_speed)
                    return_location = return_location_list[0]
                    is_retraction = bool(return_location_list[1])
                    if is_retraction:
                        retract_str = retract_line
                        unretract_str = unretract_line
                    else:
                        retract_str = ""
                        unretract_str = ""
                    return_to_str = f"G0 F{speed_travel}{return_location}\n"
                    final_str = t2_replacement_pre_string_1 + retract_str + t2_replacement_pre_string_2 + purge_line + return_to_str + "G91\nG0 F600 Z-3\nG90\n" + unretract_str + ext_mode_str + "; End of change"
                    lines[index] = final_str #lines[index].replace(lines[index],final_str)
                    data[num] = "\n".join(lines)
                if line.startswith("T3"):
                    if skip_it > 0:
                        skip_it -= 1
                        continue
                    return_location_list = self.getReturnLocation(data, num, index, retract_speed)
                    return_location = return_location_list[0]
                    is_retraction = bool(return_location_list[1])
                    if is_retraction:
                        retract_str = retract_line
                        unretract_str = unretract_line
                    else:
                        retract_str = ""
                        unretract_str = ""
                    return_to_str = f"G0 F{speed_travel}{return_location}\n"
                    final_str = t3_replacement_pre_string_1 + retract_str + t3_replacement_pre_string_2 + purge_line + return_to_str + "G91\nG0 F600 Z-3\nG90\n" + unretract_str + ext_mode_str + "; End of change"
                    lines[index] = final_str #lines[index] = final_str
                    data[num] = "\n".join(lines)
        return data

    def getReturnLocation(self, data: str, num: int, index: int, retract_speed: str) -> str:
        lines = data[num].split("\n")
        is_retraction = None
        ret_x = 0
        ret_y = 0
        for back_num in range(index,0, -1):
            if lines[back_num].startswith("G1 F" + str(retract_speed) + " E"):
                if is_retraction is None: is_retraction = True
            if " X" in lines[back_num] and " Y" in lines[back_num]:
                ret_x = self.getValue(lines[back_num], "X")
                ret_y = self.getValue(lines[back_num], "Y")
                break
        if ret_x == 0:
            lines = data[num - 1].split("\n")
            ret_x = 0
            ret_y = 0
            for back_num in range(len(lines) - 1,0, -1):
                if lines[back_num].startswith("G1 F" + str(retract_speed) + " E"):
                    is_retraction = True
                if " X" in lines[back_num] and " Y" in lines[back_num]:
                    ret_x = self.getValue(lines[back_num], "X")
                    ret_y = self.getValue(lines[back_num], "Y")
                    break
        ret_loc = " X" + str(ret_x) + " Y" + str(ret_y)
        return [ret_loc, is_retraction]