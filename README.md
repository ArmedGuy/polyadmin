polyadmin
=========

A BF2 ModManager module that adds polygon triggers for automatic administration of certain areas

Installation
------------
Extract the zipped folder inside your gameserver folder. The files will be extracted to the correct paths
Then, add the line `modmanager.loadModule "mm_polyadmin"` inside your modmanager configuration file, generally at `*gameserver*/mods/bf2/settings/modmanager.ini`



Usage
-----
You can configure safebase/glitch areas using the polyadmin web-app located at (http://apps.pie-studios.com/polyadmin/).
Simply put any created areas as a new file in `polyadmin/map_name/` and edit mm_polyadmin to include the file.