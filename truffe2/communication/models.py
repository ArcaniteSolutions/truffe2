# -*- coding: utf-8 -*-

from django.db import models
from generic.models import GenericModel, GenericStateModel, GenericStateRootModerable, FalseFK, GenericGroupsModerableModel, GenericGroupsModel, GenericContactableModel, GenericModelWithFiles
from django.utils.translation import ugettext_lazy as _

from rights.utils import UnitEditableModel, AutoVisibilityLevel


class _WebsiteNews(GenericModel, GenericGroupsModerableModel, GenericGroupsModel, GenericContactableModel, GenericStateRootModerable, GenericStateModel, UnitEditableModel):

    class MetaRightsUnit(UnitEditableModel.MetaRightsUnit):
        access = 'COMMUNICATION'
        moderation_access = 'COMMUNICATION'

    title = models.CharField(_(u'Titre'), max_length=255)
    content = models.TextField(_(u'Contenu'))
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
        details_display = list_display + [('content', _('Contenu')), ('url', _('URL'))]
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

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.title


class _AgepSlide(GenericModel, GenericGroupsModerableModel, GenericGroupsModel, GenericContactableModel, GenericStateRootModerable, GenericStateModel, UnitEditableModel):

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

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.title

    def get_image_warning(self):
        if self.picture.height < 1080 or self.picture.width < 1920:
            return _(u'<span class="text-warning"><i class="fa fa-warning"></i> Les dimensions de l\'image sont trop petites ! ({}x{} contre 1920x1080 recommandé)'.format(self.picture.width, self.picture.height))


class _Logo(GenericModel, GenericModelWithFiles, AutoVisibilityLevel, UnitEditableModel):

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
