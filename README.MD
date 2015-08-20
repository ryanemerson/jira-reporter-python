# Jira Reporter Script

A simple script to retrieve a summary of JIRA issues associated with a specified username.

## Installation

Works with Python 2.7 and 3.4.  Requires pip to be installed.

```bash
> git clone git@github.com:ryanemerson/jira-reporter.git
> cd jira-reporter
> pip install -r requirements.txt
```

## Running

```bash
> python jira-reporter.py <username>
```

### Optional Arguments
A list of all available arguments can be found by passing the ```--help``` or ```-h``` flag.  


## Virtualenv
In order not to polute your global python install, it is best to utilise virtualenv and install as follows:
```bash
> git clone git@github.com:ryanemerson/jira-reporter.git
> cd jira-reporter
> virtualenv venv
> source venv/bin/activate
> pip install -r requirements.txt
> python jira-reporter.py <username>
```

Ensure that everytime you run jira-reporter.py you are within the virtualenv.