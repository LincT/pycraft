#!/usr/bin/env python3
# standard libraries included in python
import datetime
import os
import subprocess
import sys
import tarfile
import shutil
import math
import argparse  # TODO
from collections import namedtuple

# local file imports
from core.LogIO import LogHandler
from core.Custom_Errors import *
from core.FileIO import FileIO

# directories defined at execution
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
current_dir = os.getcwd()
log_dir = f"{current_dir}{os.path.sep}logs"

# status message output constants
SUCCESS = 'Backup Succeeded!'
FAIL = 'Backup Failure! \nPlease notify an Admin'
DEBUG = True

# global logger setup
if FileIO.verify_dir(log_dir) != 1:
    FileIO.mkdir(log_dir)
logger = LogHandler(file_name=f"{log_dir}{os.path.sep}py_backup_util_log.txt", logging_level="info")
logger.write("logging initialized", "info")


def verify_backup_directory(backup_directory: str) -> bool:
    verify_path = FileIO.verify_dir(backup_directory)
    
    if verify_path == 1:
        logger.write("Directory successfully found.")
        return True
    else:
        logger.write("No path found, creating")
        created = FileIO.mkdir(backup_directory)
        if created != -1:
            logger.write("path created, using \n\t{}".format(backup_directory))
            return True
        else:
            logger.write("{}\nDirectory creation error, aborting".format(logger.timestamp()))
            
            sys.exit(1)  # Emergency Exit


def parse_sub_process(command: str, ) -> [str]:  # get command, return list of strings
    # execute the command, return any output (formatted in utf-8),
    # this makes searching for newlines easier, as well as strip() can remove dead-space even easier
    # tl;dr strings to use builtins
    result = bytes(subprocess.Popen([command], stdout=subprocess.PIPE, shell=True).communicate()[0]).decode("utf-8")
    
    # turn multi line responses into lists so we can iterate over them more easily
    result_list = [(str(each).strip()) for each in str(result).split("\n")
                   if len(str(each).strip(r"\r").strip()) != 0]
    return result_list


def docker_cmd_format(cmd: str, container_name: str) -> str:
    # sudo -H -u root screen -S minecraft -p 0 -X stuff "$CMDPAUSE^M"
    return f"docker exec -i {container_name} /bin/bash -c \"echo '{cmd}' > /tmp/server_stdin.fifo\""


def world_echo(container_name: str, msg: str):
    for each in msg.split("\n"):
        command = docker_cmd_format(f"say {each}", container_name)
        parse_sub_process(command)


def world_save_pause(container_name: str):
    # stop saving on server
    # pipe to session to stop saving while taking backup
    command_pause = "/save-off"
    command = docker_cmd_format(command_pause, container_name)
    parse_sub_process(command)


def world_save_resume(container_name: str):
    # pipe to session "/save-on"
    command_resume = "/save-on"
    command = docker_cmd_format(command_resume, container_name)
    parse_sub_process(command)


def list_containers() -> list:
    # docker container ls --format "{{.Names}}"
    # docker container ls --format "{{.Image}}" | grep minecraft-server
    pass


def tar_archive(name: str, mode: str, source: str, recursive: bool = True) -> list:
    # return list as we care about representations of the members, not the actual items themselves
    # 28176904 & 4180384
    # the actual archive creation/compression line using tar
    # tar using options:
    # c - CREATE, z - filter through gzip, v - verbose, f - --file = ARCHIVE use file or device ARCHIVE
    with tarfile.open(name=name, mode=mode) as archive:
        archive.add(source, recursive=recursive)
        return archive.getmembers()


def archive_validation(backup_filename: str, mode: str, source_dir: str, backup_dir: str) -> bool:
    archive = tar_archive(
        name=FileIO.path_join(backup_dir, backup_filename),
        # x:gz Create tarfile w/ gzip compression. FileExistsError exception if file exists.
        # w:gz Create/overwrite tarfile w/ gzip compression.
        mode=mode,  # 'w:gz' if options_dict["-overwrite"] else 'x:gz',
        source=source_dir,
        recursive=True
    )
    if DEBUG:
        print(archive)
    
    # write results to log file in a formatted text block
    archive_results = f"\n\tArchive created:{backup_filename}"
    source_files = FileIO.long_list_files(source_dir)
    # DONE: refine logic to verify contents and name automatically
    for each in archive:
        archive_results += f"\n\t{str(each)}"
        logger.write(archive_results)
    
    for each in source_files:
        item = str(each).split()[1]
        if item not in str(archive_results):
            fail_message = "failure: {} not found in:\n".format(item, str(archive_results))
            print(fail_message)
            logger.write(fail_message)
            raise IntegrityValidationException
        else:
            return True


def sizeof_fmt(num):
    block = 1024  # assumes standard block size, future me will need to automate this
    unit = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB"]
    while num > block:
        num = num/block
        unit.pop(0)
    return f"{math.ceil(num)} {unit[0]}"


def get_max_file_size(target_dir: str):
    max_value = 0
    for each in os.listdir(target_dir):
        full_dir = os.path.join(target_dir, each)
        size = os.path.getsize(full_dir)
        if size > max_value:
            max_value = size
        if DEBUG:
            print(f"{each}\n\t{size}")
    return max_value


def do_backup(container: str, backup_filename: str, mode: str, source_dir: str, save_dir: str):
    # pause world saving
    world_save_pause(container)
    start_message = f"Backup starting at {datetime.datetime.utcnow().strftime('%Y-%b-%d-%H.%M.%S')} UTC"
    if DEBUG:
        print(start_message)
    world_echo(container, start_message)
    
    # tar file
    # zip world
    if archive_validation(backup_filename, mode, source_dir, save_dir):
        print(SUCCESS)
        world_echo(container, SUCCESS)
    else:
        print(FAIL)
        world_echo(container, FAIL)
    
    # resume saving to server (preferably after zip concludes)
    world_save_resume(container)
    end_message = f"Backup complete at {datetime.datetime.utcnow().strftime('%Y-%b-%d-%H.%M.%S')} UTC"
    world_echo(container, end_message)
    if DEBUG:
        print(end_message)


def help_info():
    help_msg = """
    A simple script to backup the minecraft world
    Prerequisites: install tar
    """
    print(help_msg)
    exit(0)


def main():
    
    # TODO argparse container name, world_dir, log_dir, debug, help info et al
    # Maybe do as config file
    container = "minecraft18_mc-server_1"
    source_dir = f"{current_dir}{os.path.sep}minecraft_data"
    save_dir = f"{current_dir}{os.path.sep}world_backups"
    backup_directory_verified = verify_backup_directory(save_dir)
    if DEBUG:
        print(f"backup directory verified:{backup_directory_verified}")
    # get the date as a string i.e $(date +%Y-%b-%d-%H.%M.%S)
    date_string = datetime.datetime.utcnow().strftime('%Y-%b-%d-%H.%M.%S')
    backup_filename = f"{date_string}.tar.gz"
    
    # TODO: user defined overwrite or write protected if exists
    mode = "w:gz"
    try:
        max_file_size = get_max_file_size(save_dir)
        if DEBUG:
            
            print(f"required space: {sizeof_fmt(max_file_size)}")
            print(f"backup space available:{shutil.disk_usage(save_dir).free >= (max_file_size * 2)}")
        if shutil.disk_usage(save_dir).free >= (max_file_size * 2):
            world_echo(container, "free space verified for backups, attempting backup")
            do_backup(container, backup_filename, mode, source_dir, save_dir)
        else:
            world_echo(container, "Lacking disk space, please cleanup backups or increase partition")
        
    except Exception as e:
        world_save_resume(container)
        world_echo(container, "Aborting backup\nResumed saving world\nError during backup")
        logger.write(str(e.with_traceback))


if __name__ == '__main__':
    main()
