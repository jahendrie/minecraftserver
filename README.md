# Minecraftserver.py

**version 1.41**, 2021-02-21

## Contents

```
1.  Description
2.  Requirements
3.  Usage
4.  Examples
5.  Configuration
6.  Contact, etc.
```


## 1. Description

minecraftserver.py is a python script that expedites the process of running
a Minecraft server.  You can use it to run a server, back up the servers you
run, etc.

## 2. Requirements

- java (same version used for Minecraft)
- Python 3 (I'd recommend at least 3.6, 3.9.1 tested)

## 3. Usage

**minecraftserver.py** *[OPTION]* [WORLD]


If run without any options or world arguments, it will run the 'main'
server.

Options:

```
-h or --help        Print help text
-V or --version		Print version and author info
-n or --nogui       Disable server GUI (use terminal) (default)
-g or --gui         Enable server GUI (java GUI interface)
-p or --port        Specify server port (default 25565)
-l or --list        List worlds you can run on the server
-b or --backup      Make a backup of the given world (default 'main')
-a or --autobackup  Enable autobackup on server exit
-A or --nobackub    Disable autobackup on server exit
-u or --update      Update the server.jar file of the given world
-U or --noupdate    Disable autoupdate, if it's enabled
-P or --purge       Purge all but the last three backups for given world
-c or --config      List current settings
-C or --edit        Edit the launcher settings config file
-s or --settings    Edit server properties file for a given world
```



## 4. Examples

```
minecraftserver.py
    Runs the 'main' server, or creates it if it doesn't exist

minecraftserver.py flatland
    Runs the server named 'flatland', or creates it if it doesn't exist

minecraftserver.py -b flatland
    Manually create a backup of the 'flatland' server

minecraftserver.py -p 25000 flatland
    Run 'flatland' on port 25000, if you wanted to do that for some reason
```



## 5. Configuration

There is a 'settings.ini' file for this program which is kept in the base
Minecraft server directory:

```
    Windows:	%APPDATA%\.minecraft\server
    Linux:	    $HOME/.minecraft/server
```

The default options (with descriptive comments) for the launcher are kept in this file, so consult that for
more information.


## 6. Contact, etc.

- License: [zlib license](https://www.zlib.net/zlib_license.html)
- Author: James Hendrie (hendrie dot james at gmail dot com)
