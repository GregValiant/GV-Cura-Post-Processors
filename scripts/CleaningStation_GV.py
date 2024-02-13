# November 2023 by Greg Valiant (Greg Foresi)
# This moves the nozzle to the right and then back and forth over a cleaning brush.

from ..Script import Script
from UM.Message import Message
from UM.Application import Application
import re

class CleaningStation_GV(Script):

    def getSettingDataString(self):
            return """{
            "name": "Cleaning Station GV",
            "key": "CleaningStation_GV",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "clean_frequency":
                {
                    "label": "How often to Clean",
                    "description": "Every so many layers starting with the Start Layer OR just once at a specific layer.",
                    "type": "enum",
                    "options": {
                        "once_only": "One time only",
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
                    "minimum_value": -5
                },
                "end_layer":
                {
                    "label": "Ending Layer",
                    "description": "Layer to end the insertion at. Enter '-1' for entire file (or disable this setting).  Use layer numbers from the Cura Preview.",
                    "type": "int",
                    "default_value": "-1",
                    "enabled": "clean_frequency != 'once_only'"
                },
                "minimum_z":
                {
                    "label": "Minimum Z lift",
                    "description": "The height that will allow the brush to clear the print.  This comes into play if models are within 35mm of the right edge of the build plate.",
                    "type": "int",
                    "default_value": 25,
                    "minimum_value_warning": 5,
                    "minimum_value": 2
                },
                "clean_reps":
                {
                    "label": "Clean Reps",
                    "description": "The number of times to move back and forth across the brush.",
                    "type": "int",
                    "default_value": 1,
                    "minimum_value": 1,
                    "maximum_value": 3
                },
                "clean_stroke":
                {
                    "label": "Cleaning Stroke",
                    "description": "The length of the move at cleaning speed.  If the nozzle initially encounters the brush 35mm from the right edge of the build plate then the stroke is 35.",
                    "type": "int",
                    "default_value": 20,
                    "minimum_value": 10,
                    "maximum_value": 75
                }
            }
        }"""

    def execute(self, data):
    #Initialize variables
        self._print_sequence = Application.getInstance().getGlobalContainerStack().getProperty("print_sequence", "value")
        self._relative_extrusion = bool(Application.getInstance().getGlobalContainerStack().getProperty("relative_extrusion", "value"))
        extruder = Application.getInstance().getGlobalContainerStack().extruderList
        self._travel_speed = int(extruder[0].getProperty("speed_travel", "value")) * 60
        self._retract_dist = float(extruder[0].getProperty("retraction_amount", "value"))
        self._retract_speed = int(extruder[0].getProperty("retraction_retract_speed", "value")) * 60
        self._prime_speed = int(extruder[0].getProperty("retraction_prime_speed", "value")) * 60
        self._machine_width = int(Application.getInstance().getGlobalContainerStack().getProperty("machine_width", "value"))
        self._machine_height = int(Application.getInstance().getGlobalContainerStack().getProperty("machine_height", "value"))
        self._the_start_layer = int(self.getSettingValueByKey("start_layer"))-1
        self._the_end_layer = self.getSettingValueByKey("end_layer")
        self._clean_reps = self.getSettingValueByKey("clean_reps")
        self._clean_stroke = self.getSettingValueByKey("clean_stroke")
        if self._the_end_layer == "-1":
            self._the_end_layer = len(data)-1
        self._time_adj_total = 0
        self._time_adj = round((self._machine_width / self._travel_speed / 60) + (self._clean_reps * self._clean_stroke * 2 /10))
        data[0] += ";  Time Adjustment / instance = " + str(self._time_adj) + "\n"
    #Get the cleaning frequency
        self._clean_frequency = self.getSettingValueByKey("clean_frequency")
        match self._clean_frequency:
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
                freq = 0
            case _:
                freq = 0
                raise Exception("Error.  Insert changed to Once Only.")
        index_list = self._fill_index_list(data, self._the_start_layer, freq)
    # Get the data indexes of all the layers that will be included, create the cleaning string and insert it.
        for num in range(0, len(index_list)):
            cleaning_list = self._create_cleaning_list(data, index_list[num])
            self._time_adj_total += self._time_adj
            layer = data[index_list[num]].split("\n")
            for line in cleaning_list:
                layer.insert(len(layer)-2, line)
            data[index_list[num]] = "\n".join(layer)
        adj_hrs = int(self._time_adj_total / 3600)
        adj_mins = int((self._time_adj_total - self._time_adj_total / 3600)/60)
        Message(title = "[Cleaning Station]", text = "Time Adjustment Total: " + str(adj_hrs) + "hr" + str(adj_mins) + "min").show()
        opening_par = data[0].split("\n")
        for line in opening_par:
            if line.startswith(";TIME:"):
                print_time = int(line.split(":")[1])
                data[0] = re.sub(line, ";TIME:" + str(round(self._time_adj_total + print_time)), data[0])
                break
        return data

    # Fill the index list with the relevant data indexes
    def _fill_index_list(self, data: str, initial_layer: int, clean_frequency: int) -> int:
        index_list = []
        new_layer = initial_layer
    #Single cleaning
        if self._clean_frequency == "once_only":
            for num in range(2,len(data)-1,1):
                if ";LAYER:" + str(new_layer) + "\n" in data[num]:
                    index_list.append(num)
                    if self._print_sequence == "all_at_once":
                        break
            return index_list
        elif self._clean_frequency != "once_only":
            if self._print_sequence == "all_at_once":
                for num in range(2,len(data)-1,1):
                    if ";LAYER:" + str(new_layer) + "\n" in data[num]:
                        index_list.append(num)
                        new_layer += clean_frequency

            elif self._print_sequence == "one_at_a_time":
                for num in range(2,len(data)-1,1):
                    if ";LAYER:0\n" in data[num]:
                        new_layer = initial_layer
                    if ";LAYER:" + str(new_layer) + "\n" in data[num]:
                        index_list.append(num)
                        new_layer += clean_frequency
        return index_list

    # Create the string to be inserted at the end of each relevant layer
    def _create_cleaning_list(self, data: str, num: int) ->str:
        cleaning_list = []
        x_loc = 0
        y_loc = 0
        z_loc = 0
        e_loc = 0
        e_loc_prev = 0
        f_speed = 0
        is_retracted = False
        min_z_lift = self.getSettingValueByKey("minimum_z")
        # Get the X, Y, Z locations thru the previous layer and the current layer
        if self._clean_reps == 1:
            xtra_retract = round(self._retract_dist / 2 / 2, 5)
        elif self._clean_reps == 2:
            xtra_retract = round(self._retract_dist / 2 / 4, 5)
        elif self._clean_reps == 3:
            xtra_retract = round(self._retract_dist / 2 / 6, 5)            
        for index in range(num-1, num+1):
            layer = data[index]
            lines = layer.split("\n")
            for line in lines:
                if line.startswith("G0") or line.startswith("G1") or line.startswith("G2") or line.startswith("G3"):
                    if " X" in line:
                        x_loc = self.getValue(line, "X")
                    if " Y" in line:
                        y_loc = self.getValue(line, "Y")
                    if " Z" in line:
                        z_loc = self.getValue(line, "Z")
                    if " E" in line:
                        e_loc = self.getValue(line, "E")
                        if e_loc < e_loc_prev or e_loc < 0:
                            is_retracted = True
                        else:
                            is_retracted = False
                        e_loc_prev = e_loc
                    if " F" in line:
                        f_speed = self.getValue(line, "F")
        if self._relative_extrusion:
            e_loc = 0
        z_lift = min_z_lift
        # Don't add the cleaning string if the Z move will exceed the machine height
        if float(z_loc) + float(min_z_lift) > self._machine_height:
            cleaning_list.append(f";CleaningStation - Z Lift to {float(z_loc) + float(min_z_lift)} exceeds Machine Height")
            return cleaning_list
            
        cleaning_list.append(";TYPE:CUSTOM CleaningStation")
        
        if not is_retracted:
            cleaning_list.append(f"G1 F{self._retract_speed} E{round(e_loc - (self._retract_dist / 2),5)}")
        else:
            cleaning_list.append(";Retract not required")
        cleaning_list.append("G91")
        if not is_retracted:
            cleaning_list.append("M83")
        cleaning_list.append(f"G0 F1800 Z{z_lift}")
        cleaning_list.append("G90")
        cleaning_list.append(f"G0 F{self._travel_speed} X{self._machine_width - self._clean_stroke}")
        if not is_retracted:
            cleaning_list.append(f"G0 F600 X{self._machine_width}  E-{xtra_retract}")
            cleaning_list.append(f"G0 F600 X{self._machine_width - self._clean_stroke}  E-{xtra_retract}")
        else:
            cleaning_list.append(f"G0 F600 X{self._machine_width}")
            cleaning_list.append(f"G0 F600 X{self._machine_width - self._clean_stroke}")
        
        if self._clean_reps > 1:
            if not is_retracted:
                cleaning_list.append(f"G0 F600 X{self._machine_width} E-{xtra_retract}")
                cleaning_list.append(f"G0 F600 X{self._machine_width-self._clean_stroke} E-{xtra_retract}")
            else:
                cleaning_list.append(f"G0 F600 X{self._machine_width}")
                cleaning_list.append(f"G0 F600 X{self._machine_width-self._clean_stroke}")
        if self._clean_reps > 2:
            if not is_retracted:
                cleaning_list.append(f"G0 F600 X{self._machine_width} E-{xtra_retract}")
                cleaning_list.append(f"G0 F600 X{self._machine_width-self._clean_stroke} E-{xtra_retract}")
            else:
                cleaning_list.append(f"G0 F600 X{self._machine_width}")
                cleaning_list.append(f"G0 F600 X{self._machine_width-self._clean_stroke}")
        cleaning_list.append(f"G0 F{self._travel_speed} X{x_loc} Y{y_loc}")
        cleaning_list.append("G91")
        if not is_retracted:
            cleaning_list.append("M82")
        cleaning_list.append(f"G0 F1800 Z-{z_lift}")
        cleaning_list.append("G90")
        cleaning_list.append(f"G0 F{f_speed}")
        if not is_retracted:
            cleaning_list.append(f"G1 F{self._prime_speed} E{e_loc}")
        else:
            cleaning_list.append(";Prime not required")
        cleaning_list.append(";End of Nozzle Cleaning")
        return cleaning_list