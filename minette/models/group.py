from ..serializer import Serializable


class Group(Serializable):
    """
    Group

    Attributes
    ----------
    id : str
        ID of group
    type : str
        Type of group
    """
    def __init__(self, id=None, type=None):
        """
        Parameters
        ----------
        id : str, default None
            ID of group
        type : str, default None
            Type of group
        """
        self.id = id
        self.type = type
