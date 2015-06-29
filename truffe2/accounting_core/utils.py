# -*- coding: utf-8 -*-


class AccountingYearLinked(object):
    """Un objet lié à une année comptable. Rend automatiquement l'objet inéditable pour les années archivées."""

    @staticmethod
    def do(module, models_module, model_class, cache):
        """Execute code at startup"""

        from django.db import models

        return {
            'accounting_year': models.ForeignKey(cache['accounting_core.models.AccountingYear']),
        }

    def rights_can_EDIT(self, user):

        try:
            if not user.is_superuser and self.accounting_year.status in ['3_archived']:
                return False

            if not user.is_superuser and self.accounting_year.status in ['0_preparing'] and not self.rights_in_root_unit(user, 'TRESORERIE'):
                return False
        except:  # There may be no accounting_year
            pass

        return super(AccountingYearLinked, self).rights_can_EDIT(user)

    def rights_can_SHOW(self, user):

        try:
            if not user.is_superuser and self.accounting_year.status in ['0_preparing'] and not self.rights_in_root_unit(user, 'TRESORERIE'):
                return False
        except:  # There may be no accounting_year
            pass

        return super(AccountingYearLinked, self).rights_can_SHOW(user)
