## minecraft-pi-fast-query

Project to speed up queries from the Minecraft Pi edition.


History

Minecraft created a special edition, called the
"Minecraft Pi edition" that shipped with Rasbian Linux.
It is intended for educational purposes and
contained a set of APIs to allow Python code
to interact with the Minecraft world.
These APIs, called the "MCPI" APIs, consisted of 
Python code to interact with a running Minecraft Pi server
via a socket connection.
Fortunately, it had a liberal license agreement and 
replacement libraries such as picraft were created.
However, querying individual Minecraft blocks remained slow.

Note: The Raspberry Juice version has a fast query option
via the getBlocks(plural) API,
but it is not a general solution and
does not apply to the native Raspberry Pi version.
The technique here applies equally to Raspberry Juice,
and I hope someone will be able to test it.


This project

This project significantly speeds up queries
(getting data from the Minecraft world to Python code),
specifically, MCPI APIs getBlock, getBlockWithData, and worldHeight.
In single-threaded mode, performance goes
from an average of 60 blocks per second
to an average of 640 blocks per second.
A peak of over 5000 blocks per second can be achieved
if you are willing to use multiple threads and
receive results in a non-predictable sequence.

The code is in mcpi_fast_query/mcpi_fast_query.py.
I've make it packageable as a Python package,
but do not intend to ship it that way.  (See my intention below.)

For details, read the code, ... or stay tuned.


My intention

I intend to massage this code into an existing Minecraft Pi library
such as picraft.
I think the single-threaded technique will be relatively easy
to incorporate.
See the prototype alt_picraft_* functions. 

If possible, I would also like an option to
boost performance using multiple threads.
When that is done, I intend to end this project.
All I want is to be able to query blocks quickly.


Reference
 - https://www.raspberrypi.org/forums/viewtopic.php?f=32&t=194033
 - https://minecraft.net/en-us/edition/pi/
 - http://www.stuffaboutcode.com/p/minecraft.html
 - https://github.com/waveform80/picraft
 - https://github.com/joseph-reynolds/minecraft-pi-fast-query
