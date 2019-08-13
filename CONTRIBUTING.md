# Contribution guide

This guide helps you to setup the required tooling to make any valuable contribution to this project.
To contribute to DMJEDI we use the [Anaconda Python distribution](https://www.anaconda.com/distribution/) for Python 3.
We simply chose this Python distribution because of our closeness to data centric workflows.

## Install conda environment (and dependencies)

``` shell
conda create env --file dmjedi
```

Alternatively we have also a requirement.txt for virtualenv and pip users.
If you would like to use [pip with conda](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#pip-in-env) you can do so as well.

``` shell
conda create env --name dmjedi
conda activate dmjedi
conda install pip
pip install -f requirements.txt
```

## Running tests

Before submitting any pull request please make sure that the tests ar working. This makes our lifes a lot easier! :)
Our test runner of choice is Pytest. You can start the tests with the following command:

``` shell
pytest xyz
```

Another way to test DMJEDI is via the [Makefile](Makefile).

## Editor & Code Style

As you can see in the python files we use Google Style [Docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html) and [black](https://black.readthedocs.io/en/stable/) as our linter of choice.
Our Editor of choice is Visual Studio Code with the [Anaconda Extension Pack](https://github.com/Microsoft/vscode-anaconda-extension-pack). Of course you can also use any other text editor which is able to work with Python code as VIM, Emacs, PyCharme et cetera.

[Styleguide](https://google.github.io/styleguide/pyguide.html) to use?
 