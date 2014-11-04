from __future__ import absolute_import

from django.core.urlresolvers import reverse

from sentry.models import (
    AuditLogEntry, AuditLogEntryEvent, OrganizationMember,
    OrganizationMemberType
)
from sentry.testutils import TestCase


class OrganizationMemberSettingsTest(TestCase):
    def test_renders_with_context(self):
        organization = self.create_organization(name='foo', owner=self.user)
        team_1 = self.create_team(name='foo', organization=organization)
        team_2 = self.create_team(name='bar', organization=organization)

        user = self.create_user('bar@example.com')
        member = OrganizationMember.objects.create(
            organization=organization,
            user=user,
            type=OrganizationMemberType.MEMBER,
            has_global_access=False,
        )
        member.teams.add(team_2)

        path = reverse('sentry-organization-member-settings',
                       args=[organization.id, member.id])

        self.login_as(self.user)

        resp = self.client.get(path)

        assert resp.status_code == 200

        self.assertTemplateUsed(resp, 'sentry/organization-member-settings.html')

        assert resp.context['organization'] == organization
        assert resp.context['member'] == member
        assert resp.context['form']

    def test_basic_saving(self):
        organization = self.create_organization(name='foo', owner=self.user)
        team_1 = self.create_team(name='foo', organization=organization)
        team_2 = self.create_team(name='bar', organization=organization)

        user = self.create_user('bar@example.com')
        member = OrganizationMember.objects.create(
            organization=organization,
            user=user,
            type=OrganizationMemberType.MEMBER,
            has_global_access=False,
        )

        path = reverse('sentry-organization-member-settings',
                       args=[organization.id, member.id])

        self.login_as(self.user)

        resp = self.client.post(path, {
            'has_global_access': True,
            'type': OrganizationMemberType.ADMIN,
        })

        assert resp.status_code == 302

        member = OrganizationMember.objects.get(id=member.id)

        assert member.has_global_access is True
        assert member.type == OrganizationMemberType.ADMIN

        ale = AuditLogEntry.objects.get(
            organization=organization,
            event=AuditLogEntryEvent.MEMBER_EDIT,
        )

        assert ale.actor == self.user
        assert ale.target_object == member.id
        assert ale.target_user == user
        assert ale.data