
from generic.models import GenericModel, GenericStateModel


def startup():
    """Create urls, models and cie at startup"""

    GenericModel.startup()
