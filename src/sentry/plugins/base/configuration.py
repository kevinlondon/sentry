from __future__ import absolute_import

import logging

from sentry import options
from sentry.models import ProjectOption

from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.contrib import messages


def default_plugin_config(plugin, project, request):
    NOTSET = object()

    plugin_key = plugin.get_conf_key()
    if project:
        form_class = plugin.project_conf_form
        template = plugin.project_conf_template
    else:
        form_class = plugin.site_conf_form
        template = plugin.site_conf_template

    if form_class is None:
        return HttpResponseRedirect(reverse(
            'sentry-manage-project', args=[project.organization.slug, project.slug]))

    test_results = None

    initials = plugin.get_form_initial(project)
    for field in form_class.base_fields:
        key = '%s:%s' % (plugin_key, field)
        if project:
            value = ProjectOption.objects.get_value(project, key, NOTSET)
        else:
            value = options.get(key)
        if value is not NOTSET:
            initials[field] = value

    form = form_class(
        request.POST if request.POST.get('plugin') == plugin.slug else None,
        initial=initials,
        prefix=plugin_key
    )
    if form.is_valid():
        if 'action_test' in request.POST and plugin.is_testable():
            try:
                test_results = plugin.test_configuration(project)
            except Exception as exc:
                if hasattr(exc, 'read') and callable(exc.read):
                    test_results = '%s\n%s' % (exc, exc.read())
                else:
                    logging.exception('Plugin(%s) raised an error during test',
                                      plugin_key)
                    test_results = 'There was an internal error with the Plugin'
            if not test_results:
                test_results = 'No errors returned'
        else:
            for field, value in form.cleaned_data.iteritems():
                key = '%s:%s' % (plugin_key, field)
                if project:
                    ProjectOption.objects.set_value(project, key, value)
                else:
                    options.set(key, value)

            messages.add_message(
                request, messages.SUCCESS,
                _('Your settings were saved successfully.'))
            return HttpResponseRedirect(request.path)

    # TODO(mattrobenolt): Reliably determine if a plugin is configured
    # if hasattr(plugin, 'is_configured'):
    #     is_configured = plugin.is_configured(project)
    # else:
    #     is_configured = True
    is_configured = True

    return mark_safe(render_to_string(template, {
        'form': form,
        'request': request,
        'plugin': plugin,
        'plugin_description': plugin.get_description() or '',
        'plugin_test_results': test_results,
        'plugin_is_configured': is_configured,
    }, context_instance=RequestContext(request)))
