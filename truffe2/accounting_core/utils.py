# -*- coding: utf-8 -*-


class AccountingYearLinked(object):
    """Un object lié à une année comptable. Rend automatiquement l'object innéditable pour les années archivées."""

    @staticmethod
    def do(module, models_module, model_class, cache):
        """Execute code at startup"""

        from django.db import models

        return {
            'accounting_year': models.ForeignKey(cache['accounting_core.models.AccountingYear']),
        }

    def rights_can_EDIT(self, user):

        if not user.is_superuser and self.accounting_year.status in ['3_archived']:
            return False

        if not user.is_superuser and self.accounting_year.status in ['0_preparing'] and not self.rights_peoples_in_EDIT(user, 'TRESORERIE'):
            return False

        return super(AccountingYearLinked, self).rights_can_EDIT(user)

    def rights_can_SHOW(self, user):

        if not user.is_superuser and self.accounting_year.status in ['0_preparing'] and not self.rights_peoples_in_EDIT(user, 'TRESORERIE'):
            return False

        return super(AccountingYearLinked, self).rights_can_SHOW(user)
