"""
sentry.web.frontend.projects.plugins
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from django.contrib import messages
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.utils.translation import ugettext_lazy as _

from sentry.constants import MEMBER_ADMIN
from sentry.plugins import plugins
from sentry.web.decorators import has_access
from sentry.web.helpers import render_to_response


@has_access(MEMBER_ADMIN)
@csrf_protect
def manage_plugins(request, organization, project):
    if request.POST:
        enabled = set(request.POST.getlist('plugin'))
        for plugin in plugins.all(version=None):
            if plugin.can_enable_for_projects():
                if plugin.slug in enabled:
                    plugin.enable(project)
                else:
                    plugin.disable(project)

        messages.add_message(
            request, messages.SUCCESS,
            _('Your settings were saved successfully.'))

        return HttpResponseRedirect(request.path)

    context = csrf(request)
    context.update({
        'organization': organization,
        'team': project.team,
        'page': 'plugins',
        'project': project,
    })

    return render_to_response('sentry/projects/plugins/list.html', context, request)


@has_access(MEMBER_ADMIN)
@csrf_protect
def configure_project_plugin(request, organization, project, slug):
    try:
        plugin = plugins.get(slug)
    except KeyError:
        return HttpResponseRedirect(reverse('sentry-manage-project', args=[project.organization.slug, project.slug]))

    if not plugin.can_enable_for_projects():
        return HttpResponseRedirect(reverse('sentry-manage-project', args=[project.organization.slug, project.slug]))

    view = plugin.configure(request, project=project)
    if isinstance(view, HttpResponse):
        return view

    context = csrf(request)
    context.update({
        'organization': organization,
        'team': project.team,
        'page': 'plugin',
        'title': plugin.get_title(),
        'view': view,
        'project': project,
        'plugin': plugin,
        'plugin_is_enabled': plugin.is_enabled(project),
    })

    return render_to_response('sentry/projects/plugins/configure.html',
                              context, request)


@has_access(MEMBER_ADMIN)
@csrf_protect
def reset_project_plugin(request, organization, project, slug):
    try:
        plugin = plugins.get(slug)
    except KeyError:
        return HttpResponseRedirect(reverse('sentry-configure-project-plugin', args=[project.organization.slug, project.slug, slug]))

    if not plugin.is_enabled(project):
        return HttpResponseRedirect(reverse('sentry-configure-project-plugin', args=[project.organization.slug, project.slug, slug]))

    plugin.reset_options(project=project)

    return HttpResponseRedirect(reverse('sentry-configure-project-plugin', args=[project.organization.slug, project.slug, slug]))


@has_access(MEMBER_ADMIN)
@csrf_protect
def enable_project_plugin(request, organization, project, slug):
    try:
        plugin = plugins.get(slug)
    except KeyError:
        return HttpResponseRedirect(reverse('sentry-manage-project-plugins', args=[project.organization.slug, project.slug]))

    redirect_to = reverse('sentry-configure-project-plugin', args=[project.organization.slug, project.slug, slug])

    if plugin.is_enabled(project) or not plugin.can_enable_for_projects():
        return HttpResponseRedirect(redirect_to)

    plugin.enable(project)

    return HttpResponseRedirect(redirect_to)


@has_access(MEMBER_ADMIN)
@csrf_protect
def disable_project_plugin(request, organization, project, slug):
    try:
        plugin = plugins.get(slug)
    except KeyError:
        return HttpResponseRedirect(reverse('sentry-manage-project-plugins', args=[project.organization.slug, project.slug]))

    redirect_to = reverse('sentry-configure-project-plugin', args=[project.organization.slug, project.slug, slug])

    if not (plugin.can_disable and plugin.is_enabled(project) and plugin.can_enable_for_projects()):
        return HttpResponseRedirect(redirect_to)

    plugin.disable(project)

    return HttpResponseRedirect(redirect_to)
