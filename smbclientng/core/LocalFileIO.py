#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File name          : LocalFileIO.py
# Author             : Podalirius (@podalirius_)
# Date created       : 23 may 2024


import os
import ntpath
from rich.progress import BarColumn, DownloadColumn, Progress, TextColumn, TimeRemainingColumn, TransferSpeedColumn


class LocalFileIO(object):
    """
    Class LocalFileIO is designed to handle local file input/output operations within the smbclient-ng tool.
    It provides functionalities to open, read, write, and manage progress of file operations based on the expected size of the file.

    Attributes:
        mode (str): The mode in which the file should be opened (e.g., 'rb', 'wb').
        path (str): The path to the file that needs to be handled.
        expected_size (int, optional): The expected size of the file in bytes. This is used to display progress.
        debug (bool): Flag to enable debug mode which provides additional output during operations.

    Methods:
        __init__(self, mode, path=None, expected_size=None, debug=False): Initializes the LocalFileIO instance.
        write(self, data): Writes data to the file and updates the progress bar if expected size is provided.
        read(self, size): Reads data from the file up to the specified size and updates the progress bar if expected size is provided.
    """

    def __init__(self, mode, path=None, expected_size=None, debug=False):
        super(LocalFileIO, self).__init__()

        self.mode = mode
        self.path = path.replace(ntpath.sep, '/')
        self.dir = None
        self.debug = False
        self.expected_size = expected_size

        # Write to local (read remote)
        if self.mode in ["wb"]:
            self.dir = './' + os.path.dirname(self.path)

            if not os.path.exists(self.dir):
                if self.debug:
                    print("[debug] Creating local directory '%s'" % self.dir)
                os.makedirs(self.dir)

            if self.debug:
                print("[debug] Openning local '%s' with mode '%s'" % (self.path, self.mode))

            self.fd = open(self.path, self.mode)

        # Write to remote (read local)
        elif self.mode in ["rb"]:
            if ntpath.sep in self.path:
                self.dir = os.path.dirname(self.path)

            if self.debug:
                print("[debug] Openning local '%s' with mode '%s'" % (self.path, self.mode))

            self.fd = open(self.path, self.mode)

            if self.expected_size is None:
                self.expected_size = os.path.getsize(filename=self.path)

        # Create progress bar
        if self.expected_size is not None:
            self.__progress = Progress(
                TextColumn("[bold blue]{task.description}", justify="right"),
                BarColumn(bar_width=None),
                "[progress.percentage]{task.percentage:>3.1f}%",
                "•",
                DownloadColumn(),
                "•",
                TransferSpeedColumn(),
                "•",
                TimeRemainingColumn(),
            )
            self.__progress.start()
            self.__task = self.__progress.add_task(
                description="'%s'" % os.path.basename(self.path),
                start=True,
                total=self.expected_size,
                visible=True
            )

    def write(self, data):
        """
        Writes data to the file.

        This method writes the specified data to the file and updates the progress bar with the amount of data written if the expected size is set.

        Args:
            data (bytes): The data to be written to the file.

        Returns:
            int: The number of bytes written.
        """

        if self.expected_size is not None:
            self.__progress.update(self.__task, advance=len(data))
        return self.fd.write(data)
    
    def read(self, size):
        """
        Reads a specified amount of data from the file.

        This method reads data from the file based on the size specified. It also updates the progress bar with the amount of data read if the expected size is set.

        Args:
            size (int): The number of bytes to read from the file.

        Returns:
            bytes: The data read from the file.
        """

        read_data = self.fd.read(size)
        if self.expected_size is not None:
            self.__progress.update(self.__task, advance=len(read_data))
        return read_data

    def close(self, remove=False):
        """
        Closes the file descriptor and optionally removes the file.

        This method ensures that the file descriptor is properly closed and the file is removed if specified.
        It also stops the progress bar if it was initiated and cleans up the object by deleting it.

        Args:
            remove (bool): If True, the file at the path will be removed after closing the file descriptor.
        """

        self.fd.close()

        if remove:
            os.remove(path=self.path)

        if self.expected_size is not None:
            self.__progress.stop()
        
        del self

    def set_error(self, message):
        """
        Sets an error message in the progress bar's description and modifies the progress bar to show only essential columns.

        This method is used to communicate error states or important messages directly in the progress bar interface.
        It updates the task description with the provided message and simplifies the progress bar to show only the text
        and download columns, removing other elements like speed and time remaining which may not be relevant in an error state.

        Args:
            message (str): The error or status message to display in the progress bar.
        """

        self.__progress.tasks[0].description = message
        self.__progress.columns = [
            TextColumn("[bold blue]{task.description}", justify="right"),
            BarColumn(bar_width=None),
            "•",
            DownloadColumn(),
        ]
        self.__progress.update(self.__task, advance=0)