# -*- coding: utf-8 -*-

from django.db import models
from generic.models import GenericModel, GenericStateModel, GenericStateRootModerable, GenericStateUnitValidable, FalseFK, GenericGroupsValidableModel, GenericGroupsModerableModel, GenericGroupsModel, GenericContactableModel, GenericModelWithFiles, GenericExternalUnitAllowed, GenericDelayValidable, GenericDelayValidableInfo, SearchableModel, ModelUsedAsLine, GenericModelWithLines
from django.utils.translation import ugettext_lazy as _
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.timezone import localtime
from django.core.urlresolvers import reverse

from rights.utils import UnitEditableModel, UnitExternalEditableModel, AutoVisibilityLevel


class _WebsiteNews(GenericModel, GenericGroupsModerableModel, GenericGroupsModel, GenericContactableModel, GenericStateRootModerable, GenericStateModel, UnitEditableModel, SearchableModel):

    class MetaRightsUnit(UnitEditableModel.MetaRightsUnit):
        access = 'COMMUNICATION'
        moderation_access = 'COMMUNICATION'

    title = models.CharField(_(u'Titre'), max_length=255)
    title_en = models.CharField(_(u'Titre anglais'), max_length=255, blank=True, null=True)
    content = models.TextField(_(u'Contenu'))
    content_en = models.TextField(_(u'Contenu anglais'), blank=True, null=True)
    url = models.URLField(max_length=255)
    unit = FalseFK('units.models.Unit')

    start_date = models.DateTimeField(_(u'Date début'), blank=True, null=True)
    end_date = models.DateTimeField(_(u'Date fin'), blank=True, null=True)

    class MetaData:
        list_display = [
            ('title', _('Titre')),
            ('start_date', _(u'Date début')),
            ('end_date', _('Date fin')),
            ('status', _('Statut')),
        ]
        details_display = list_display + [('content', _('Contenu')), ('url', _('URL')), ('title_en', _('Titre anglais')), ('content_en', _('Contenu anglais'))]
        filter_fields = ('title', 'status')

        base_title = _('News AGEPoly')
        list_title = _(u'Liste de toutes les news sur le site de l\'AGEPoly')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-bullhorn'

        default_sort = "[3, 'desc']"  # end_date

        menu_id = 'menu-communication-websitenews'

        datetime_fields = ['start_date', 'end_date']

        has_unit = True

        help_list = _(u"""Les news du site de l'AGEPoly sont les nouvelles affichées sur toutes les pages du site de l'AGEPoly.
                        Elles sont soumises à modération par le responsable communication de l'AGEPoly avant d'être visibles.""")

    class MetaEdit:
        datetime_fields = ('start_date', 'end_date')

    class MetaSearch(SearchableModel.MetaSearch):

        extra_text = u""

        fields = [
            'title',
            'title_en',
            'content',
            'content_en',
            'url',
        ]

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.title


class _AgepSlide(GenericModel, GenericGroupsModerableModel, GenericGroupsModel, GenericContactableModel, GenericStateRootModerable, GenericStateModel, UnitEditableModel, SearchableModel):

    class MetaRightsUnit(UnitEditableModel.MetaRightsUnit):
        access = 'COMMUNICATION'
        moderation_access = 'COMMUNICATION'

    title = models.CharField(_(u'Titre'), max_length=255)
    picture = models.ImageField(_(u'Image'), help_text=_(u'Pour des raisons de qualité, il est fortement recommandé d\'envoyer une image en HD (1920x1080)'), upload_to='uploads/slides/')
    unit = FalseFK('units.models.Unit')

    start_date = models.DateTimeField(_(u'Date de début'), blank=True, null=True)
    end_date = models.DateTimeField(_(u'Date de fin'), blank=True, null=True)

    class MetaData:
        list_display = [
            ('title', _('Titre')),
            ('start_date', _(u'Date début')),
            ('end_date', _('Date fin')),
            ('status', _('Statut')),
        ]
        details_display = list_display + [('picture', _('Image')), ('get_image_warning', '')]
        filter_fields = ('title', 'status')

        base_title = _(u'Slide à l\'AGEPoly')
        list_title = _(u'Liste de tous les slides à l\'AGEPoly')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-bullhorn'

        default_sort = "[3, 'desc']"  # end_date

        menu_id = 'menu-communication-agepslide'

        datetime_fields = ['start_date', 'end_date']
        images_fields = ['picture', ]
        safe_fields = ['get_image_warning', ]

        has_unit = True

        help_list = _(u"""Les slides à l'AGEPoly sont affichés de manière aléatoire sur les écrans à l'AGEPoly.
            Ils sont soumis à modération par le responsable communication de l'AGEPoly avant d'être visibles.""")

    class MetaEdit:
        datetime_fields = ('start_date', 'end_date')

    class MetaSearch(SearchableModel.MetaSearch):

        extra_text = u"écrans"

        fields = [
            'title',
        ]

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.title

    def get_image_warning(self):
        if self.picture.height < 1080 or self.picture.width < 1920:
            return _(u'<span class="text-warning"><i class="fa fa-warning"></i> Les dimensions de l\'image sont trop petites ! ({}x{} contre 1920x1080 recommandé)'.format(self.picture.width, self.picture.height))


class _Logo(GenericModel, GenericModelWithFiles, AutoVisibilityLevel, UnitEditableModel, SearchableModel):

    class MetaRightsUnit(UnitEditableModel.MetaRightsUnit):
        access = 'COMMUNICATION'

    name = models.CharField(max_length=255)
    unit = FalseFK('units.models.Unit')

    class MetaData:
        list_display = [
            ('name', _('Nom')),
        ]
        details_display = list_display + [('get_visibility_level_display', _(u'Visibilité')), ]
        filter_fields = ('name', )

        base_title = _(u'Logo')
        list_title = _(u'Liste de tous les logos')
        files_title = _(u'Fichiers')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-picture-o'

        default_sort = "[1, 'asc']"  # name

        menu_id = 'menu-communication-logo'

        has_unit = True

        help_list = _(u"""Les logos de ton unité.
            Tu peux rendre public les logos, ce qui est recommandé afin d'aider les autres unités lors de constructions graphiques (ex: agenda) ou ton propre comité.
            Un logo peut comporter plusieurs fichiers : ceci te permet d'uploader différents formats pour un même fichier !""")

    class MetaEdit:
        files_title = _(u'Fichiers')
        files_help = _(u'Envoie le ou les fichiers de ton logo. Le système te permet d\'envoyer plusieurs fichiers pour te permettre d\'envoyer des formats différents.')

    class MetaSearch(SearchableModel.MetaSearch):
        extra_text = u""
        index_files = True

        fields = [
            'name',
        ]

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name

    def get_best_image(self):
        """Try to find a suitable file for thumbnail"""

        for f in self.files.all():
            if f.is_picture():
                return f

        return f

class _Display(GenericModel, GenericGroupsModel, UnitEditableModel, GenericDelayValidableInfo, SearchableModel):

    class MetaRightsUnit(UnitEditableModel.MetaRightsUnit):
        access = 'COMMUNICATION'

    title = models.CharField(_('Titre'), max_length=255)
    description = models.TextField()
    unit = FalseFK('units.models.Unit')

    active = models.BooleanField(_('Actif'), help_text=_(u'Pour désactiver temporairement la posibilité de réserver.'), default=True)

    conditions = models.TextField(_(u'Conditions de réservation'), help_text=_(u'Si tu veux préciser les conditions de réservations pour l\'affichage. Tu peux par exemple mettre un lien vers un contrat.'), blank=True)

    allow_externals = models.BooleanField(_(u'Autoriser les externes'), help_text=_(u'Permet aux externes (pas dans l\'AGEPoly) de réserver l\'affichage.'), default=False)
    conditions_externals = models.TextField(_(u'Conditions de réservation pour les externes'), help_text=_(u'Si tu veux préciser des informations sur la réservation de l\'affichage pour les externes. Remplace le champ \'Conditions\' pour les externe si rempli.'), blank=True)

    allow_calendar = models.BooleanField(_(u'Autoriser tout le monde à voir le calendrier'), help_text=_(u'Permet à tout le monde d\'afficher le calendrier des réservations de l\'affichage'), default=True)
    allow_external_calendar = models.BooleanField(_(u'Autoriser les externes à voir le calendrier'), help_text=_(u'Permet aux externes d\'afficher le calendrier des réservations de l\'affichage. Le calendrier doit être visible.'), default=True)

    class MetaData:
        list_display = [
            ('title', _('Titre')),
            ('active', _('Actif')),
            ('allow_externals', _('Autoriser les externes')),
        ]

        details_display = list_display + [
            ('description', _('Description')),
            ('conditions', _('Conditions')),
            ('conditions_externals', _('Conditions pour les externes')),
            ('max_days', _(u'Nombre maximum de jours de réservation')),
            ('max_days_externals', _(u'Nombre maximum de jours de réservation (externes)')),
            ('minimum_days_before', _(u'Nombre de jours minimum avant réservation')),
            ('minimum_days_before_externals', _(u'Nombre de jours minimum avant réservation (externes)')),
            ('maximum_days_before', _(u'Nombre de jours maximum avant réservation')),
            ('maximum_days_before_externals', _(u'Nombre de jours maximum avant réservation (externes)')),
        ]
        filter_fields = ('title', 'description', 'conditions', 'conditions_externals')

        base_title = _(u'Affichage')
        list_title = _(u'Liste de tout les affichages réservables')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-clipboard'

        default_sort = "[1, 'asc']"  # title

        menu_id = 'menu-communication-display'

        yes_or_no_fields = ['active', 'allow_externals']
        html_fields = ('description', 'conditions', 'conditions_externals')

        has_unit = True

        help_list = _(u"""La liste des affichages réservables, gérés par l'unité active. N'importe quelle unité peut mettre à disposition des affichages et est responsable de la modération des réservations.""")

    class MetaEdit:
        html_fields = ('description', 'conditions', 'conditions_externals')

    class MetaSearch(SearchableModel.MetaSearch):

        extra_text = u"display"

        fields = [
            'title',
            'description',
            'conditions',
        ]

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.title

class _DisplayReservation(GenericModel, GenericDelayValidable, GenericGroupsValidableModel, GenericGroupsModel, GenericContactableModel, GenericStateUnitValidable, GenericStateModel, GenericExternalUnitAllowed, UnitExternalEditableModel, SearchableModel):

    class MetaRightsUnit(UnitExternalEditableModel.MetaRightsUnit):
        access = 'COMMUNICATION'
        moderation_access = 'COMMUNICATION'

    display = FalseFK('communication.models.Display', verbose_name=_('Affichage'))

    title = models.CharField(_('Titre'), max_length=255)

    start_date = models.DateTimeField(_(u'Date de début'))
    end_date = models.DateTimeField(_(u'Date de fin'))

    reason = models.TextField(help_text=_(u'Explique pourquoi tu as besoin (manifestation par ex.)'))
    remarks = models.TextField(_('Remarques'), blank=True, null=True)

    class MetaData:

        list_display_base = [
            ('title', _('Titre')),
            ('get_unit_name', _(u'Nom de l\'unité')),
            ('start_date', _(u'Date début')),
            ('end_date', _('Date fin')),
            ('status', _('Statut')),
        ]

        list_display = [list_display_base[0]] + [('display', _(u'Affichage')), ] + list_display_base[1:]
        list_display_related = [list_display_base[0]] + [('get_display_link', _(u'Affichage')), ] + list_display_base[1:] + [('get_conflits_list', _(u'Conflits')), ]

        forced_widths = {
            '1': '15%',
            '2': '25%',
            '4': '150px',  # start date
            '5': '150px',  # end date
        }

        forced_widths_related = {
            '1': '15%',
            '2': '25%',
            '4': '90px',  # start date on two lines
            '5': '90px',  # end date on two lines
            '7': '80px',  # conflicts list nicely wide
        }

        details_display = list_display_base + [('get_display_infos', _(u'Affichage')), ('reason', _('Raison')), ('remarks', _('Remarques')), ('get_conflits', _('Conflits'))]
        filter_fields = ('title', 'status', 'display__title')

        base_title = _(u'Réservation des affichages')
        list_title = _(u'Liste de toutes les réservations d\'affichage')
        list_related_title = _(u'Liste de toutes les réservations d\'affichage de mon unité')
        calendar_title = _(u'Calendrier de mes réservations d\'affichage')
        calendar_related_title = _(u'Calendrier des réservations d\'un affichage de mon unité')
        calendar_specific_title = _(u'Calendrier des réservations d\'affichage')
        base_icon = 'fa fa-list'
        elem_icon = 'fa fa-clipboard'

        safe_fields = ['get_unit_name', 'get_display_link', 'get_conflits_list']

        default_sort = "[4, 'desc']"  # end_date

        menu_id = 'menu-communication-display-reservation'
        menu_id_related = 'menu-communication-display-reservation-related'
        menu_id_calendar = 'menu-communication-display-reservation-calendar'
        menu_id_calendar_related = 'menu-communication-display-reservation-calendar-related'
        menu_id_directory = 'menu-communication-display-reservation-directory'

        has_unit = True

        html_fields = ('get_display_infos', 'get_conflits')
        datetime_fields = ('start_date', 'end_date')

        related_name = _(u'Affichage')

        help_list = _(u"""Les réservation d\'affichage.
            Les réservations sont soumises à modération par l'unité liée à l\'affichage.
            Tu peux gérer ici la liste de tes réservations pour l'unité active (ou une unité externe).""")
        help_list_related = _(u"""Les réservation d\'affichage de l'unité.                                                                                                                                                                                                                                                                                                                Les réservations sont soumises à modération par l'unité liée à l\'affichage.                                                                                                                                                        Tu peux gérer ici la liste de réservation d\'affichage de l'unité active.""")

        help_calendar_specific = _(u"""Les réservation d'un type d\'affichage particulier.""")

        trans_sort = {'get_unit_name': 'unit__name', 'get_display_link': 'display__title'}
        not_sortable_columns = ['get_conflits_list', ]

    class MetaEdit:
        datetime_fields = ('start_date', 'end_date')

        only_if = {
            'remarks': lambda (obj, user): obj.status == '2_online' and obj.rights_can('VALIDATE', user),
            'display': lambda (obj, user): obj.status == '0_draft',
        }

    class MetaSearch(SearchableModel.MetaSearch):

        extra_text = u""

        fields = [
            'display',
            'title',
            'reason',
            'remarks',
        ]

    class Meta:
        abstract = True

    class MetaState(GenericStateUnitValidable.MetaState):
        unit_field = 'display.unit'
        linked_model = 'communication.models.Display'

    def __unicode__(self):
        return self.title

    def genericFormExtraClean(self, data, form):
        """Check if selected displays are available"""
        from django import forms

        if 'display' in form.fields:

            if 'display' not in data or not data['display'].active or data['display'].deleted:
                raise forms.ValidationError(_('Affichage non disponible'))

            if not self.unit and not data['display'].allow_externals:
                raise forms.ValidationError(_('Affichage non disponible pour les externes'))
        else:
            raise forms.ValidationError(_(u'Il ne faut pas laisser de ligne vide !'))

        if 'start_date' in data and 'end_date' in data and data['start_date'] > data['end_date']:
            raise forms.ValidationError(_(u'La date de fin ne peut pas être avant la date de début !'))

    def get_display_infos(self):
        """Affiche les infos sur les affichages pour une réserversation"""

        tpl = mark_safe(u'<div style="margin-top: 5px;">{}, {} <span class="label label-info">{}</span></div>'.format(escape(self.display.title), _(u'gérée par'), escape(self.display.unit.name)))

        return tpl

    def get_conflits(self):

        liste = self.display.displayreservation_set.exclude(pk=self.pk).exclude(deleted=True).filter(
            status__in=['1_asking', '2_online'], end_date__gt=self.start_date, start_date__lt=self.end_date)

        if not liste:
            return mark_safe('<span class="txt-color-green"><i class="fa fa-check"></i> {}</span>'.format(_('Pas de conflits !')))
        else:
            retour = u'<span class="txt-color-red"><i class="fa fa-warning"></i> {}</span><ul>'.format(_(u'Il y a d\'autres réservations en même temps !'))

            for elem in liste:
                retour = u'{}<li><span class="label label-{}"><i class="{}"></i> {}</span>'.format(retour, elem.status_color(), elem.status_icon(), elem.get_status_display())
                retour = u'{} {} pour l\'unité {}'.format(retour, elem, elem.get_unit_name())
                retour = u'{} <span data-toggle="tooltip" data-placement="right" title="Du {} au {}"><i class="fa fa-clock-o"></i></span></li>'.format(retour, localtime(elem.start_date), localtime(elem.end_date))

            retour = u'{}</ul>'.format(retour)

            return retour

    def get_display_link(self):
        return '<a href="{}">{}</a>'.format(reverse('communication.views.display_show', args=(self.display.pk,)), self.display)

    def get_conflits_list(self):

        liste = self.display.displayreservation_set.exclude(pk=self.pk).exclude(deleted=True).filter(
            status__in=['1_asking', '2_online'], end_date__gt=self.start_date, start_date__lt=self.end_date)

        if not liste:
            return '<span class="txt-color-green"><i class="fa fa-check"></i></span>'
        else:

            retour = u'<ul>'

            for elem in liste:
                unit = escape(elem.unit) if elem.unit else escape(elem.unit_blank_name)

                retour = u'{}<li><span>{} ({}) [{}]<br>'.format(retour, escape(elem), unit, elem.get_status_display())
                retour = u'{}du {}<br>au {}</span></li>'.format(retour, localtime(elem.start_date), localtime(elem.end_date))

            retour = u'{}</ul>'.format(retour)

            return u'<span class="txt-color-red conflicts-tooltip-parent" rel="tooltip" data-placement="bottom" data-html="true" title="{}"><i class="fa fa-warning"></i></span>'.format(retour)            
