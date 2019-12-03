import requests
from objson import Serializable


class Payload(Serializable):
    """
    Payload

    Attributes
    ----------
    content_type : str
        Content type of payload
    url : str
        Url to get content
    thumb : str
        URL to get thumbnail image
    headers : dict
        HTTP Headers required for getting content
    content : Any
        Content itself
    """
    def __init__(self, content_type="image", url=None, thumb=None,
                 headers=None, content=None):
        """
        Parameters
        ----------
        content_type : str, default "image"
            Content type of payload
        url : str, default None
            Url to get content
        thumb : str, default None
            URL to get thumbnail image
        headers : dict, default None
            HTTP Headers required for getting content
        content : Any, default None
            Content itself
        """
        self.content_type = content_type
        self.url = url
        self.thumb = thumb if thumb is not None else url
        self.headers = headers or {}
        self.content = content

    def get(self, set_content=False):
        """
        Get content data from url

        Parameters
        ----------
        set_content : bool, default False
            If True, set content data to content property

        Returns
        -------
        content : Any
            Content
        """
        data = requests.get(self.url, headers=self.headers, timeout=60).content
        if set_content:
            self.content = data
        return data

    def save(self, filepath):
        """
        Save content data to file

        Parameters
        ----------
        filepath : str
            File path to save content
        """
        data = self.get()
        with open(filepath, "wb") as f:
            f.write(data)
