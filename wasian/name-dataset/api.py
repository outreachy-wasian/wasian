from names_dataset import NameDataset

def main():  # pragma: no cover
    """
    The main function executes on commands:
    `python -m wasian` and `$ wasian `.

    This is your program's entry point.

    You can change this function to do whatever you want.
    Examples:
        * Run a test suite
        * Run a server
        * Do some other stuff
        * Run a command line application (Click, Typer, ArgParse)
        * List all available tasks
        * Run an application (Flask, FastAPI, Django, etc.)
    """

    nd = NameDataset()

    surname = nd.get_top_names(use_first_names=False)

    print(surname)
