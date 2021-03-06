import React from "react";
import Reflux from "reflux";

import api from "../../api";
import ConfigStore from "../../stores/configStore";
import OrganizationHomeContainer from "../../components/organizations/homeContainer";
import OrganizationState from "../../mixins/organizationState";
import TeamStore from "../../stores/teamStore";
import {sortArray} from "../../utils";

import ExpandedTeamList from "./expandedTeamList";
import SlimTeamList from "./slimTeamList";
import OrganizationStatOverview from "./organizationStatOverview";

var OrganizationTeams = React.createClass({
  mixins: [
    OrganizationState,
    Reflux.listenTo(TeamStore, "onTeamListChange")
  ],

  contextTypes: {
    router: React.PropTypes.func
  },

  getInitialState() {
    return {
      activeNav: 'your-teams',
      teamList: sortArray(TeamStore.getAll(), function(o) {
        return o.name;
      }),
      projectStats: {},
    };
  },

  componentWillMount() {
    this.fetchStats();
  },

  // TODO(dcramer): handle updating project stats when items change
  fetchStats() {
    api.request(this.getOrganizationStatsEndpoint(), {
      query: {
        since: new Date().getTime() / 1000 - 3600 * 24,
        stat: 'received',
        group: 'project'
      },
      success: (data) => {
        this.setState({
          projectStats: data
        });
      }
    });
  },

  getOrganizationStatsEndpoint() {
    var router = this.context.router;
    var params = router.getCurrentParams();
    return '/organizations/' + params.orgId + '/stats/';
  },

  onTeamListChange() {
    var newTeamList = TeamStore.getAll();

    this.setState({
      teamList: sortArray(newTeamList, function(o) {
        return o.name;
      })
    });

    this.fetchStats();
  },

  toggleTeams(nav) {
    this.setState({
      activeNav: nav
    });
  },

  render() {
    var access = this.getAccess();
    var features = this.getFeatures();
    var org = this.getOrganization();
    var urlPrefix = ConfigStore.get('urlPrefix') + '/organizations/' + org.slug;

    var activeNav = this.state.activeNav;
    var allTeams = this.state.teamList;
    var activeTeams = this.state.teamList.filter((team) => team.isMember);

    return (
      <OrganizationHomeContainer>
        <div className="row">
          <div className="col-md-9">
            <div className="team-list">
              <div className="pull-right">
                <a href={urlPrefix + '/projects/new/'} className="btn btn-primary btn-sm"
                   style={{marginRight: 5}}>
                  <span className="icon-plus" /> Project
                </a>
                <a href={urlPrefix + '/teams/new/'} className="btn btn-primary btn-sm">
                  <span className="icon-plus" /> Team
                </a>
              </div>
              <ul className="nav nav-tabs border-bottom">
                <li className={activeNav === "your-teams" && "active"}>
                  <a onClick={this.toggleTeams.bind(this, "your-teams")}>Your Teams</a>
                </li>
                <li className={activeNav === "all-teams" && "active"}>
                  <a onClick={this.toggleTeams.bind(this, "all-teams")}>All Teams</a>
                </li>
              </ul>
              {activeNav == 'your-teams' ?
                <ExpandedTeamList
                    organization={org} teamList={activeTeams}
                    projectStats={this.state.projectStats} />
              :
                <SlimTeamList
                  organization={org} teamList={allTeams}
                  openMembership={features.has('open-membership') || access.has('org:write')} />
              }
            </div>
          </div>
          <OrganizationStatOverview className="col-md-3 stats-column" />
        </div>
      </OrganizationHomeContainer>
    );
  }
});

export default OrganizationTeams;
