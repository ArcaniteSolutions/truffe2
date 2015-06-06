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
