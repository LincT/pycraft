#!/usr/bin/env python3
# standard libraries included in python
import datetime
import os
import platform
import subprocess
import sys
import tarfile

# local file imports
from core.LogIO import LogHandler
from core.Custom_Errors import *
from core.FileIO import FileIO

# special libraries (pip install requirements.txt)
# none as of 28/NOV/2021 needed for this file

# variables initialized at start and remain constant through out runtime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGGING_DIR = f"{ROOT}{os.path.sep}logs"

# Logging setup

# verify our logging directory exists, otherwise the script tends to break.
if FileIO.verify_dir(LOGGING_DIR) != 1:
    try:
        FileIO.mkdir(LOGGING_DIR)
        
    except Exception as e:
        print(f"failure to create logging directory at: \n\t{LOGGING_DIR}\nexiting")
        print(f"{e}")
        exit(-1)

# initialize logger
logger = LogHandler(file_name=f"{LOGGING_DIR}{os.path.sep}py_backup_util_log.txt", logging_level="warning")


def testing():
    print("success")
    print(f"ROOT = {ROOT}\nlog_dir = {LOGGING_DIR}")
    exit(0)


def docker_exec(command: str, container: str = "mc-server") -> [str]:
    parse_sub_process(f"docker exec {container} {command}")


def parse_sub_process(command: str,) -> [str]:  # get command, return list of strings
    # execute the command, return any output (formatted in utf-8),
    # this makes searching for newlines easier, as well as strip() can remove dead-space even easier
    # tl;dr strings to use builtins
    result = bytes(subprocess.Popen([command], stdout=subprocess.PIPE, shell=True).communicate()[0]).decode("utf-8")

    # turn multi line responses into lists so we can iterate over them more easily
    result_list = [(str(each).strip()) for each in str(result).split("\n")
                   if len(str(each).strip(r"\r").strip()) != 0]
    return result_list


def exit_check(prompt: str):
    response = input("{}\n".format(prompt))
    user = os.environ.get("USERNAME")if "USERNAME" in os.environ.keys() else "undefined_user"

    if "y" not in response:
        logger.write("{}\n\tOperation aborted by user:\n{}".format(logger.timestamp(), user))

        print("Operation aborted by user.\nPlease consult your dealer.")
        exit(0)  # exit code 0 to define user initiated shutdown.


def time_string(format_string: str = "%Y-%b-%d-%H%M%S", timezone: str = "Local") -> str:
    """
    :param format_string: (defaults to 2021-Nov-21-024514)
    :param timezone: local or UTC, full timezone support not implemented yet.
    :return: string
    """
    # tar file name creation
    # currently in local

    if timezone.upper() == "UTC":  # force input as uppercase to help prevent human error
        formatted_time = datetime.datetime.now(datetime.timezone.utc).strftime(format_string)

    else:
        formatted_time = datetime.datetime.now().strftime(format_string)

    return formatted_time


def tar_archive(name: str, mode: str, source: str, recursive: bool = True) -> list:
    # return list as we care about representations of the members, not the actual items themselves
    # 28176904 & 4180384
    # the actual archive creation/compression line using tar
    # tar using options:
    # c - CREATE, z - filter through gzip, v - verbose, f - --file = ARCHIVE use file or device ARCHIVE
    with tarfile.open(name=name, mode=mode) as archive:
        archive.add(source, recursive=recursive)
        return archive.getmembers()


def help_info():
    help_message = """
    This utility automates archiving minecraft worlds and more.
    Archiving is recursive, you only need to specify the path to the source directory to archive.
    Script may be executed either via:
    sudo python3 -m world_backup.py
    -or-
    sudo python3 world_backup.py
    -or-
    after doing sudo chmod u+x ./world_backup.py, running sudo ./world_backup.py

    USAGE: Any of the following examples should work.
    <dir_to_archive>
    -<flags> <dir_to_archive>
    -<single letter flags> -<flag_n> <parm_n> <dir_to_archive>

    VARIOUS OPTIONS:
    -d, -debug: runs program in debug mode, to have the program display more information,
    also allowing more manual control.
    
    -o, overwrite: allows one to overwrite an existing backup in case the first attempt was incomplete.

    -h, help: displays this message.
    (-h also forces exit of the script, with no further execution.)
    
    -v, -version: shows version message
    (also forces exit of the script, with no further execution.)

    -in: explicit archive specification
    
    -out: change output directory for current execution
   
    FURTHER INFO:
    Supports relative directories i.e. ../

    The log will be written to the same place this file was deployed.
    A backup directory and archive file will also be in a directory defined by os.
    (can be overridden using options, scrollback)
    ./backups
    
    "IntegrityValidationException" indicates a file was not successfully added to the tar archive.
    Such issues might be caused by write permissions.

    The user assumes all liability for execution on production servers.

    Please consult your software dealer for any further concerns.
    ropelinc@gmail.com
    """
    print(help_message)
    exit(0)


def version() -> str:
    release_version = 1.0
    release_date = "01-DEC-2021"
    print(f"Version: {release_version}\t Released: {release_date}")
    exit(0)


def main():
    # business logic here:
    # possibly a way to execute this all from cli w/out needing to edit the script
    # need to import sys to work
    # debating on whether to implement argparse, might have more built in, but might complicate deployment
    
    options_dict: dict = {
        "-in": None,
        "-out": None,
        "-help": help_info,
        "-version": version,
        "-debug": False,
        "-overwrite": False,
        "-test.py": testing,
    }
    
    # caching any args, preventing break on no args
    args_list = [each for each in sys.argv]

    if len(args_list) > 1:
        # no args is still going to have an array of 1,
        # as sys args includes the calling file as arg0
        logger.write(f'Argument List:{str(args_list)}\nArg Count: {len(args_list)}')
        # DONE: relative file search

        # directory should always be last element, regardless of list length
        # admittedly not 100% user error proof
        # WIP: enhanced flag args
        options_dict["-in"] = str(args_list[-1])  # default if not overridden in controls
        for each in args_list:
            if str(each[0]).startswith("-"):
                if each in options_dict.keys():
                    # should only treat separate args as flags if both conditions true
                    # spoofing linux cli common practice
                    if callable(options_dict.get(each, None)):
                        options_dict[each]()

                    elif each is bool:
                        # booleans are always set to false on setup,
                        # so calling them would be necessary only to enable certain flags
                        options_dict[each] = True

                    else:  # allowing some variables to be set by user directly
                        if len(args_list) > (args_list.index(each) + 1):
                            options_dict[each] = args_list[args_list.index(each) + 1]

                else:
                    for char in str(each)[1:]:
                        logger.write("Flag: {}".format(each))
                        if char == 'd':
                            options_dict["-debug"] = True
                            logger.adjust_logging_level("debug")
                        elif char == 'v':
                            options_dict["-version"]()
                        elif char == 'h':
                            options_dict["-help"]()
                        elif char == 'o':
                            options_dict["-overwrite"] = True
                        elif char == 't':
                            options_dict["-test.py"]()
                        else:
                            print("Flag not found:{}".format(each))

    else:
        options_dict["-help"]()

    if FileIO.verify_dir(options_dict["-in"]) == 1:
        # Constants (now less constant!) # allows for testing on windows machines without any extra edits
        if "windows" in platform.platform().lower():
            backup_directory = "./backups"
        else:
            backup_directory = os.path.join(os.path.sep, os.path.dirname(ROOT))
        # list files in directory.
        directory_data = "\n".join(each for each in FileIO.long_list_files(options_dict["-in"]))
        output = "Files in {}:\n{}".format(options_dict["-in"], directory_data)
        logger.write(output)

        if options_dict["-debug"]:
            print(output)
            exit_check(prompt="continue?")
            # query user to verify path correct.
            # made this a debug option.
            exit_check(prompt="Is this path correct for the BACKUP directory?\n\t{}".format(backup_directory))

        verify_path = FileIO.verify_dir(backup_directory)

        if verify_path == 1:
            logger.write("Directory successfully found.")
        else:
            logger.write("No path found, creating")
            created = FileIO.mkdir(backup_directory)
            if created != -1:
                logger.write("path created, using \n\t{}".format(backup_directory))
            else:
                logger.write("{}\nDirectory creation error, aborting".format(logger.timestamp()))
                sys.exit(1)  # Emergency Exit

        # Call archive method with options specified.
        # https://docs.python.org/3/library/tarfile.html
        archive = tar_archive(
            # defaults to local, can be changed to "UTC"
            name=FileIO.path_join(backup_directory, time_string() + '.tar.gz'),
            # x:gz Create tarfile w/ gzip compression. FileExistsError exception if file exists.
            # w:gz if options_dict["-overwrite"] is true, Create/overwrite tarfile w/ gzip compression.
            mode='w:gz' if options_dict["-overwrite"] else 'x:gz',
            source=options_dict["-in"],
            recursive=True
        )

        # write results to log file in a formatted text block
        archive_results = "\n\tArchive created:{}".format(time_string() + '.tar.gz')
        source_files = FileIO.long_list_files(options_dict["-in"])
        # DONE: refine logic to verify contents and name automatically
        for each in archive:
            archive_results += "\n\t{}".format(str(each))
        logger.write(archive_results)

        for each in source_files:
            item = str(each).split()[1]
            if item not in str(archive_results):
                print("failure: {} not found in:\n".format(item, str(archive_results)))
                logger.write("failure: {} not found in:\n".format(item, str(archive_results)))
                raise IntegrityValidationException

        if options_dict["-debug"]:
            print("Archive created:\n\t {}".format(time_string()), archive)
            # break out of script if errors, so user can call script again or troubleshoot
            exit_check("Is everything there?")
        print(f"File archive completed. Log available at: {''}")

    else:
        print("no file path specified, or path not found, aborting.\n"
              "For more information, run this again w/ -h.\n"
              "A log file should also exist with further details")
        exit(-1)


if __name__ == '__main__':
    main()
