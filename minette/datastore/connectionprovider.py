""" Base class for ConnectionProvider """
from abc import ABC, abstractmethod


class ConnectionProvider(ABC):
    """
    Base class for ConnectionProvider

    Attributes
    ----------
    connection_str : str
        Connection string
    """

    def __init__(self, connection_str, **kwargs):
        """
        Parameters
        ----------
        connection_str : str
            Connection string
        """
        self.connection_str = connection_str

    @abstractmethod
    def get_connection(self):
        """
        Get connection

        Returns
        -------
        connection : Connection
            Database connection
        """
        pass

    def get_prepare_params(self):
        """
        Get parameters for preparing tables

        Returns
        -------
        prepare_params : tuple or None
            Parameters for preparing tables
        """
        return None
