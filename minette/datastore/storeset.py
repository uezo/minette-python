""" Base class for set of data stores and connection provider for them """


class StoreSet:
    connection_provider = None
    context_store = None
    user_store = None
    messagelog_store = None
