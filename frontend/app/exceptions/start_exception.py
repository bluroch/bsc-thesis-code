class StartException(Exception):
    """
    An exception for errors on startup.
    """

    def __init__(
        self,
        message="An error happened during starting the application, please check your settings!",
    ):
        super().__init__(message)
