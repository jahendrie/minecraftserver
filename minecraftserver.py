#!/usr/bin/env python3
#===============================================================================
#   minecraftserver.py  |   version 1.41    |   zlib license    |   2021-02-21
#   James Hendrie       |   hendrie.james@gmail.com
#
#   Script I use to make running my minecraft servers easier.
#===============================================================================
import sys, os
import subprocess
import shutil
import time
import requests
import configparser

MCS_VERSION = "1.41"


def print_help():
    print( "Usage:  minecraftserver.py [arg] [world]\n" )
    print( "Arguments:" )
    print( "  -h or --help\t\tPrint this help text" )
    print( "  -V or --version\tPrint Version and author info" )
    print( "  -n or --nogui\t\tDisable server GUI (use terminal) (default)" )
    print( "  -g or --gui\t\tEnable server GUI (java GUI interface)" )
    print( "  -p or --port\t\tSpecify server port (default 25565)" )
    print( "  -l or --list\t\tList worlds you can run on the server" )
    print( "  -b or --backup\tMake a backup of the given world (default 'main')" )
    print( "  -a or --autobackup\tEnable autobackup on server exit" )
    print( "  -A or --nobackup\tDisable autobackup on server exit" )
    print( "  -u or --update\tUpdate the server.jar file of the given world" )
    print( "  -U or --noupdate\tDisable auto-update, if it's enabled" )
    print( "  -P or --purge\t\tPurge all but the last three backups" )
    print( "  -c or --config\tList current settings" )
    print( "  -C or --edit\t\tEdit the launcher settings config file" )
    print( "  -s or --settings\tEdit server properties file for a given world" )
    print( "\nExamples:" )
    print( "  minecraftserver.py -n" )
    print( "\tRuns the 'main' world without a GUI" )
    print( "  minecraftserver.py -n pierce" )
    print( "\tRuns Pierce's world without a GUI" )


def print_version():
    print( "minecraftserver.py, version %s" % MCS_VERSION )
    print( "James Hendrie (hendrie.james@gmail.com)" )


def check_requirements():
    ##  Go through a list of programs required (currently just java) and bail
    ##  out if we're missing any

    ##  Mandatory
    for prog in ( "java", ):
        r = shutil.which( prog )
        if r == None:
            print( "ERROR:  '%s' not found" % prog )
            return( False )

    return( True )


def list_worlds( base ):
    os.chdir( base )
    worlds = {}

    ##  Get all of the directories in the base dir, sort them by access time
    for d in os.listdir( '.' ):
        if os.path.isdir( d ) and d != '.' and d != '..' and d != "bkp" \
                and d != "server.jar"  and not os.path.islink( d ):
            worlds[ d ] = os.path.getatime( d )

    ##  Make sure there's more than 0, then print the results with a formatted
    ##  date of the access time
    count = len( worlds )
    if( count ) > 0:
        print( "Worlds (%s):\n" % base )
        sWorlds = dict( sorted( worlds.items(), key=lambda item: item[1],
            reverse=True))
        for w in sWorlds:
            t = time.strftime("%Y-%m-%d  %H:%M:%S",time.localtime( sWorlds[w]))
            print( " %s\t%s" % (t, w ))



def run_server( serverDir, opts ):

    ##  Build the command list
    cmd = [ "java", "-Xmx2048M", "-Xms2048M", "-jar", "server.jar" ]
    if not opts[ "gui" ]:
        cmd.append( "nogui" )

    ##  Print server directory
    print( "Server directory:\t%s" % serverDir )

    ##  Print server port
    print( "Port:\t\t\t%s" % opts[ "port" ] )

    ##  Print autobackup option
    print( "Autobackup:\t\t%s" %
            ( "enabled" if opts[ "autobackup" ] else "disabled"))


    if opts[ "port" ] != None:
        cmd.append( "--port" )
        cmd.append( opts[ "port" ] )

    ##  Run the server
    subprocess.call( cmd )

    ##  If autobackup is on, do it
    if opts[ "autobackup" ]:
        print( "\n\n" )
        print( '-' * 20 )
        print( "AUTO-BACKUP ENABLED" )
        print( '-' * 20 )
        backup_world( os.path.basename( serverDir ), opts )

            

def human_readable_size( num ):
    for unit in ( '','KiB','MiB','GiB','TiB','PiB' ):
        if abs( num ) < 1024.0:
            return "%3.1f %s" % (num, unit )
        num /= 1024.0

    return( "ERROR:  Size too fuckin' big, get outta heeeeyah" )


def external_backup( bkpPath, world, opts ):
    os.chdir( server_base_dir() )

    bkpPath += opts[ "external_backup_extension" ]
    cmd = opts[ "external_backup_command" ].strip().split()
    cmd.append( bkpPath )
    cmd.append( world )
    p = subprocess.call( cmd )
    return( bkpPath )


def internal_backup( bkpPath, world, opts ):

    supported_formats = []
    for fmt, desc in shutil.get_archive_formats():
        supported_formats.append( fmt )

    if opts[ "internal_backup_format" ] not in supported_formats:
        print( "WARNING:  Unsupported archive format:  '%s'" %
                opts[ "internal_backup_format" ])
        print( "UNABLE TO PERFORM BACKUP" )
        return( None )
    else:
        shutil.make_archive( bkpPath, "zip", server_base_dir(), world )
        return( ( bkpPath + ".zip" ))


def backup_world( world, opts ):

    ##  First, make sure bkp_dir exists
    if not os.path.exists( bkp_dir( world )):
        try:
            os.mkdir( bkp_dir( world ))
        except PermissionError:
            print( "ERROR:  Cannot create directory '%s'" % bkp_dir( world ))
            print( "Aborting." )
            sys.exit( 1 )

    bkpName = "%s_" % world
    bkpName += time.strftime( "%Y-%m-%d_%H-%M-%S", time.localtime() )
    bkpPath = os.path.join( bkp_dir( world ), bkpName )

    ##  Reporting
    print( "Backup of world '%s' in progress, please wait..." % world )

    ##  Make it baby
    if opts[ "backup" ] == "internal":
        r = internal_backup( bkpPath, world, opts )

    elif opts[ "backup" ] == "external":
        r = external_backup( bkpPath, world, opts )

    ##  More reporting
    if r == None:
        print( "ERROR:  Backup failed." )
    else:
        s = human_readable_size( os.stat( r ).st_size )
        print( "All done!  World backed up to '%s' (%s)." % ( r, s))




def get_editor():

    opts = get_options()
    ed = opts[ "editor" ]
    if (not os.path.exists( ed ) and shutil.which( ed ) == None) or ed == '':

        ##  Will return 'None' if not found
        ed = os.getenv( "EDITOR" )

        ##  If the user hasn't set an editor (or it doesn't work),
        ##  see if we can't find a common one that works
        if ed == None or shutil.which( ed ) == None:

            ##  Try some common editors
            for e in ( "nano", "vim", "vi", "C:\Windows\System32\\notepad.exe"):
                if shutil.which( e ) != None or os.path.exists( e ):
                    return shutil.which( e )

    ##  Will return the user's env editor or None
    return ed


def edit_file( path ):
    ed = get_editor()
    if ed != None:
        cmd = [ ed, path ]
        subprocess.call( cmd )
        return( True )
    else:
        print( "ERROR:  Can't find a text editor." )
        print( "The file you want to edit is:  '%s'" % path )
        return( False )


def new_server( s, opts ):
    try:
        os.mkdir( s )
        update_server_jar( s, os.path.basename( s ))

        os.chdir( s )

        ##  Do the first thing to create a EULA
        bkp = opts[ "autobackup" ]
        opts[ "autobackup" ] = False
        run_server( s, opts )
        opts[ "autobackup" ] = bkp

        ##  Let the user know they need to edit a EULA
        i = input("Press ENTER to edit eula.txt.  Server will restart afterward.")

        eula = os.path.join( s, "eula.txt" )
        if edit_file( eula ):
            run_server( s, opts )
        else:
            return( 1 )

    except ( PermissionError, IOError ):
        print( "ERROR:  Could not create directory '%s'.  Aborting." % s )
        return( 1 )

    return( 0 )



def get_server_jar_url(src="https://www.minecraft.net/en-us/download/server/"):
    r = requests.get( src )
    lines = r.content.decode().split( '\n' )
    for line in lines:
        if "minecraft_server." in line:
            url = line.partition( 'href="' )[2].partition( '"' )[0]
            return( url )

    return( None )


def update_server_jar( baseDir, world ):
    """
    Downloads a new copy of server.jar from minecraft.net into the server's
    base directory.
    """
    ##  If it doesn't exist, abort
    if not os.path.exists( baseDir ):
        print( "ERROR:  %s does not exist; cannot update server." % baseDir )
        print( "Aborting" )
        sys.exit( 1 )


    ##  Go into that directory
    os.chdir( baseDir )

    ##  Tell the user what's up
    print( "Downloading a fresh server.jar for world '%s'..." % world )
    
    ##  Download the index file that has a link to the jar file, then parse
    ##  it to get said link
    serverJarURL = get_server_jar_url()

    if serverJarURL != None:

        ##  Download the jar itself
        jar = requests.get( serverJarURL )

        ##  Make sure we've got a least a 10 MiB file, otherwise something has
        ##  gone wrong and we should abort
        if len( jar.content ) > 10e6:
            jarFile = open( "server.jar", "wb" )
            jarFile.write( jar.content )
            print( "Server updated successfully." )
        else:
            print( "ERROR:  Jar file too small.  Something is amiss!" )
            sys.exit( 1 )

    else:
        print( "ERROR:  Cannot get server jar URL." )
        sys.exit( 1 )





def purge_backups( baseDir, world ):
    """
    Function to remove all but the last three backups for a given world.
    """
    sDir = os.path.join( baseDir, world )

    ##  If the path doesn't exist, abort, baby
    if not os.path.exists( sDir ):
        print( "ERROR:  %s does not exist; cannot purge directory." % sDir )
        print( "Aborting" )
        sys.exit( 1 )

    try:
        os.chdir( sDir )
        backups = os.listdir( "." )
        backups.sort()

        if len( backups ) > 3:
            print( "TO BE REMOVED:\n" )
            for b in backups[ 0 : -3 ]:
                print( b )

            r = input( "\nRemove these backups?  [y/N] " )

            if r.lower() == "y":
                for b in backups[ 0: -3 ]:
                    print( "Purging '%s'" % b )
                    os.remove( b )
                print( "\nAll done!" )

            else:
                print( "\nNevermind, then." )

        else:
            print( "There are only %d backups; will not purge." %
                    len( backups ))
            return

    except PermissionError:
        print("ERROR:  Cannot remove files from '%s':  Permission denied" % sDir)
        print( "Aborting." )
        sys.exit( 1 )

def base_dir():
    ##  Windows
    if sys.platform == "win32" or sys.platform == "win64":
        return( os.path.join( os.getenv( "APPDATA" ), ".minecraft" ))

    ##  Linux
    elif sys.platform == "linux":
        return( os.path.join( os.getenv( "HOME" ), ".minecraft" ))

    else:
        return( "" )

def server_base_dir():

    baseDir = base_dir()
    if baseDir != None:
        return( os.path.join( baseDir, "server" ))
    else:
        return( None )

def bkp_base_dir():
    return( os.path.join( server_base_dir(), "bkp" ))

def bkp_dir( world ):
    return( os.path.join( bkp_base_dir(), world ))


def server_dir_name( world ):
    ##  The base server directory
    serverBaseDir = server_base_dir()
    if serverBaseDir == None:
        return( "" )

    if not os.path.exists( serverBaseDir ):
        try:
            os.mkdir( serverBaseDir )
        except (OSError, PermissionError ):
            print( "ERROR:  Cannot create directory '%s'.  Aborting." %
                    serverBaseDir )
            sys.exit( 1 )

    ##  Server directory
    serverDir = os.path.join( serverBaseDir, world )

    return( serverDir )


def server_dir( world = "main" ):

    serverDir = server_dir_name( world )

    if os.path.exists( serverDir ):
        return( serverDir )
    else:
        return( None )


def default_options():
    ##  Default options, in case settings file can't be read or whatever
    opts = {
            "gui" : False,
            "port" : "25565",
            "autobackup" : True,
            "autoupdate" : False,
            "backup" : "internal",
            "internal_backup_format" : "zip",
            "external_backup_command" : "",
            }

    return( opts )


def get_options():

    settingsFile = os.path.join( server_base_dir(), "settings.ini" )

    if os.path.exists( settingsFile ):
        print( "Reading options from '%s'" % settingsFile )
        config = configparser.ConfigParser()
        null = config.read( settingsFile )
        
        ##  Set the options from the settings file
        opts = {
                "port" : config[ "defaults" ][ "port" ],
                "editor" : config[ "defaults" ][ "editor" ],
                "autobackup" : config.getboolean( "defaults", "autobackup"),
                "autoupdate" : config.getboolean( "defaults", "autoupdate"),
                "backup" : config[ "defaults" ][ "backup" ],
                "internal_backup_format" : config[ "defaults" ][ "internal_backup_format" ],
                "external_backup_command" : config[ "defaults" ][ "external_backup_command" ],
                "external_backup_extension" : config[ "defaults" ][ "external_backup_extension" ],
                }

        ##  Backup option check
        if opts[ "backup" ] != "external":
            opts[ "backup" ] = "internal"

        ##  Make sure the backup format is supported
        supported_formats = []
        for fmt, desc in shutil.get_archive_formats():
            supported_formats.append( fmt )
        if opts[ "internal_backup_format" ] not in supported_formats:
            print( "WARNING:  Unsupported archive format:  '%s'" %
                    opts[ "internal_backup_format" ])
            print( "UNABLE TO PERFORM BACKUP" )


        ##  Deal with GUI shit
        if config[ "defaults" ][ "gui" ].lower() == "default":
            ##  If they're running windows, turn the GUI on
            if sys.platform == "win32" or sys.platform == "win64":
                opts[ "gui" ] = True
            ##  Otherwise, turn it off
            else:
                opts[ "gui" ] = False

        else:
            opts[ "gui" ] = config.getboolean( "defaults", "gui" )


        return( opts )

    else:
        print( "Initializing with default options" )
        return( default_options() )


def print_options():

    opts = get_options()

    print( "Server port:\t\t%s" % opts[ "port" ] )
    print( "Use GUI?\t\t%s" % ("YES" if opts[ "gui" ] else "NO" ))
    print( "Autobackup?\t\t%s" % ( "YES" if opts[ "autobackup" ] else "NO"))


def edit_options():
    return( edit_file( os.path.join( server_base_dir(), "settings.ini" )))


def edit_server_properties( world ):
    worldDir = os.path.join( server_base_dir(), world )
    properties = os.path.join( worldDir, "server.properties" )
    return( edit_file( properties ))

def main():

    ##  Manual backup?
    backup = False

    ##  Result from creating a new server
    r = -1

    ##  See which world we're going to use
    if len( sys.argv ) < 2:
        world = "main"
    else:
        try:
            int( sys.argv[-1] )
            world = "main"
        except ValueError:
            if '-' in sys.argv[-1] or "--" in sys.argv[-1]:
                world = "main"
            else:
                world = sys.argv[-1]



    ##  Server directory
    serverDir = server_dir( world )

    argOpts = {}

    ##  Check args
    for arg in sys.argv[1:]:
        if arg == "-h" or arg == "--help":
            print_help()
            return( 0 )

        if arg == "-V" or arg == "--version":
            print_version()
            return( 0 )

        elif arg == "-n" or arg == "--nogui":
            argOpts[ "gui" ] = False

        elif arg == "-g" or arg == "--gui":
            argOpts[ "gui" ] = True

        elif arg == "-l" or arg == "--list":
            list_worlds( os.path.dirname( server_dir() ))
            return 0

        elif arg == "-b" or arg == "--backup":
            if serverDir != None and world != None:
                opts = get_options()
                backup_world( world, opts )
                return 0
            else:
                return 1

        elif arg == '-a' or arg == "--autobackup":
            argOpts[ "autobackup" ] = True

        elif arg == "-A" or arg == "--nobackup":
            argOpts[ "autobackup" ] = False

        elif arg == "-U" or arg == "--noupdate":
            argOpts[ "autoupdate" ] = False

        elif arg == "-c" or arg == "--config":
            print_options()
            return( 0 )

        elif arg == "-C" or arg == "--edit":
            edit_options()
            return( 0 )

        elif arg == "-s" or arg == "--settings":
            edit_server_properties( world )
            return( 0 )

        elif arg == "-u" or arg == "--update":
            if serverDir != None and world != None:
                update_server_jar( serverDir, world )
                return 0
            else:
                print( "ERROR:  '%s' does not exist." % serverDir )
                return( 1 )

        elif arg == "-P" or arg == "--purge":
            if serverDir != None and world != None:
                bkpDir = "%s/bkp" % os.path.dirname( serverDir )
                purge_backups( bkpDir, world )
                return 0
            else:
                return 1

        elif arg == "-p" or arg == "--port":
            if len( sys.argv ) >= sys.argv.index( arg ):
                argOpts[ "port" ] = sys.argv[ sys.argv.index( arg ) + 1 ]


    ##  Make sure they meet the requirements, like having Java
    if not check_requirements():
        print( "ERROR:  Requirements not met.  Aborting." )
        sys.exit( 1 )

    ##  Get our options from the settings.ini file (or defaults if that's gone)
    opts = get_options()

    ##  Overwrite the opts with arguments passed
    for key in argOpts:
        if key in opts:
            opts[ key ] = argOpts[ key ]


    if serverDir == None:
        serverDir = server_dir_name( world )
        r = new_server( serverDir, opts )
        if r!= 0:
            sys.exit( 1 )


    ##  Change to server directory
    os.chdir( serverDir )

    ##  If auto-update is enabled, do it
    if opts[ "autoupdate" ]:
        print( '-' * 20 )
        print( "AUTO-UPDATE ENABLED" )
        print( '-' * 20 )
        print( "\n" )
        update_server_jar( serverDir, world )

    ##  Run it
    if r == -1:
        run_server( serverDir, opts )

    return 0



if __name__ == "__main__":
    main()
