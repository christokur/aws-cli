# python-toolbag v0.25.7


## Dependency problems

1. 
        python-toolbag --> awscli
        awscli --> ruamel.yaml.clib
        ruamel.yaml.clib --> python < 3.12

    To solve we must first make awscli compatible with python 3.12, then we can update python-toolbag.

2.      awscli --> cruft + cookiecutter-python-project
        cookiecutter-python-project --> python extension from python-toolbag
        python-toolbag --> awscli
        awscli --> ruamel.yaml.clib
        ruamel.yaml.clib --> python < 3.12

    To solve we must first make awscli compatible with python 3.12.