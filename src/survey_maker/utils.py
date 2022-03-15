import os


class Chdir:
    """Class which allows moving to a directory, do something, and move back when done

    Parameters
    ----------
    new_path: str
        Location where you want to do something

    """

    def __init__(self, new_path):
        self.new_path = new_path

    def __enter__(self):
        self.saved_path = os.getcwd()
        os.chdir(self.new_path)
        return self

    def __exit__(self, *args):
        os.chdir(self.saved_path)
