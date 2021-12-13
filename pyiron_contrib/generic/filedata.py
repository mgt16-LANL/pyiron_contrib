"""Generic File Object."""

# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
import posixpath
import shutil

from abc import ABC, abstractmethod
import os
from os import path

from pyiron_base import GenericJob, state
from pyiron_base.generic.filedata import FileDataTemplate as BaseFileDataTemplate, load_file, FileData
from pyiron_base.interfaces.has_groups import HasGroups

__author__ = "Niklas Siemer"
__copyright__ = (
    "Copyright 2020, Max-Planck-Institut für Eisenforschung GmbH - "
    "Computational Materials Design (CM) Department"
)
__version__ = "0.1"
__maintainer__ = "Niklas Siemer"
__email__ = "siemer@mpie.de"
__status__ = "development"
__date__ = "Feb 02, 2021"


class FileDataTemplate(BaseFileDataTemplate, ABC):
    def __init__(self):
        self._metadata = None

    @staticmethod
    def _get_filetype_from_filename(filename):
        filetype = os.path.splitext(filename)[1]
        if filetype == '' or filetype == '.':
            filetype = None
        else:
            filetype = filetype[1:]
        return filetype

    def _get_metadata(self):
        return self._metadata

    def _set_metadata(self, metadata):
        self._metadata = metadata

    @property
    def metadata(self):
        return self._get_metadata()

    @metadata.setter
    def metadata(self, metadata):
        self._set_metadata(metadata)


class StorageInterface(HasGroups, ABC):
    """File handling in different storage interfaces"""

    @abstractmethod
    def upload_file(self, file, metadata=None, filename=None):
        """Upload the provided files to the storage"""

    @abstractmethod
    def remove_file(self, file):
        """Removes specified files from the storage"""

    @abstractmethod
    def __getitem__(self, item):
        """Return stored file as Subclass of FileDataTemplate"""

    @property
    def requires_metadata(self):
        return False

    def setup_storage(self):
        pass

    def parse_metadata(self, metadata):
        return metadata

    @abstractmethod
    def validate_metadata(self, metadata, raise_error=True):
        """Check metadata for validity and provide valid metadata back.

        Args:
            metadata: the meta data object to check
            raise_error: if raise_error is True, errors are raised. Otherwise, silently returning None.
        Raises:
            ValueError: if the metadata is not valid and raise_error.
        Returns:
            object: valid meta data or None if metadata is not valid and not raise_error.
        """


class LocalStorage(StorageInterface):
    """The local storage operates on the usual working directory of the job"""

    def __init__(self, job: GenericJob):
        self._job = job

    def validate_metadata(self, metadata, raise_error=True):
        state.logger("Storing metadata for LocalStorage is currently handled only on the job level.")
        return metadata

    def upload_file(self, file, _metadata=None, filename=None):
        filename = filename or os.path.basename(file)
        shutil.copy(file, os.path.join(self._job.working_directory, filename))

    def remove_file(self, file):
        os.remove(os.path.join(self._job.working_directory, file))

    def setup_storage(self):
        self._job._create_working_directory()

    def __getitem__(self, item):
        if item in self.list_nodes():
            file_name = posixpath.join(self._job.working_directory, f"{item}")
            if hasattr(self._job, '_stored_files'):
                metadata = self._job._stored_files[item]
            else:
                metadata = None
            return FileData(file=file_name, metadata=metadata)
        pass

    def _list_groups(self):
        """Every files is expected to be stored in the working directory - thus, no nesting of groups."""
        return []

    def _list_nodes(self):
        return self._job.list_files()
