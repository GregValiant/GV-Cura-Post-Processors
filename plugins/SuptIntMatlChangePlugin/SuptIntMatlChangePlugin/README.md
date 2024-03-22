# GregValiant

This Plugin is new in March of 2024.

This plugin adds a setting named "Support-Interface Mat'l Change" to the Support settings in the Custom print setup of Cura. It allows a user to change to support interface material and then revert to the model material.

**This plugin assumes that a pause command will work with your printer.**

The SuptIntMatlChange settings can be found in the Custom print setup by using the Search field on top of the settings. If you want to make the setting permanently visible in the sidebar, right click and select "Keep this setting visible".

***WARNING***
There must be a ";TYPE:SUPPORT-INTERFACE" comment on each layer that is specified.  Two pauses (to change and then revert) will be added for each specified layer.  Take care to only include the top interface layer numbers.  This works very well for large flat supported surfaces.  Not so good for horizontal holes as too many pauses can be highly annoying.

## Options

        Enable Support Interface Mat'l Change : Activate the change settings.
        Slow Z percentage : Positive value to slow the print as the z value rises up to this percentage.
        Slow Z height : Positive value to define the start height of the speed reduction.
        

![Speed Option](./images/speed.png)
