from ..serializer import Serializable


class Payload(Serializable):
    """
    Payload

    Attributes
    ----------
    content_type : str
        Content type of payload
    content : Any
        Content data
    headers : dict
        Headers of content or headers to get content
    url : str
        Url to get content
    thumb : str
        URL to get thumbnail image
    """
    def __init__(self, *, content_type="image", content=None, headers=None,
                 url=None, thumb=None,):
        """
        Parameters
        ----------
        content_type : str, default "image"
            Content type of payload
        content : Any, default None
            Content data
        headers : dict, default None
            Headers of content or headers to get content
        url : str, default None
            Url to get content
        thumb : str, default None
            URL to get thumbnail image
        """
        self.content_type = content_type
        self.content = content
        self.headers = headers or {}
        self.url = url
        self.thumb = thumb if thumb is not None else url
