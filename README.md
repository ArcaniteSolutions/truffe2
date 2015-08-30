Truffe 2
========

Truffe 2 is the new intranet for AGEPoly - The EPFL's students' association.

## License

Truffe 2 is licensed under the [BSD](http://opensource.org/licenses/BSD-2-Clause) license. Check LICENSE.md

## Authors

### Core developpers

* [Maximilien Cuony](https://github.com/the-glu)
* [Lionel Martin](https://github.com/lionel-martin)

### Contributors

* Cedric Cook (Fixed a typo)

## Development

This is a standard django project. Python requirements are stored in `truffe2/data/pip-reqs.txt`.

You will need access to tequila (EPFL internal network is enough) to login.

No initial database is provided. To begin, grant yourself admin rights in the database after a first login, and create at least one unit.

South is used for migrations. Be careful, some models are created dynamically !

You will need a `truffe2/app/settingsLocal.py` file with your local settings (database, etc.). A template is provided in `truffe2/app/settingsLocal.py.dist`

Deployment scripts using fabric are located in the `Deployment` folder.
