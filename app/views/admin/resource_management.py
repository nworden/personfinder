# Copyright 2019 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The admin resources pages."""

import django.shortcuts

import config
import const
import model
import resources
import utils
import views.admin.base


class AdminResourcesIndexView(views.admin.base.AdminBaseView):
    """The admin resources view."""

    ACTION_ID = 'admin/resources_index'

    def setup(self, request, *args, **kwargs):
        super(AdminResourcesIndexView, self).setup(request, *args, **kwargs)
        self.params.read_values(
            get_params={'resource_bundle': utils.strip},
            post_params={'bundle_name': utils.strip})

    @views.admin.base.enforce_superadmin_admin_level
    def get(self, request, *args, **kwargs):
        """Serves GET requests."""
        del request, args, kwargs  # Unused.
        bundle_info = []
        for bundle in resources.ResourceBundle.all():
            name = bundle.key().name()
            bundle_info.append({
                'name': name,
                'url': self.build_absolute_uri(
                    '/global/admin/resources/%s' % name),
            })
        return self.render(
            'admin_resources_index.html',
            existing_bundles=bundle_info,
            xsrf_token=self.xsrf_tool.generate_token(
                self.env.user.user_id(), self.ACTION_ID))

    @views.admin.base.enforce_superadmin_admin_level
    def post(self, request, *args, **kwargs):
        """Serves POST requests, creating a new resource bundle."""
        del request, args, kwargs  # Unused.
        self.enforce_xsrf(self.ACTION_ID)
        name = self.params.bundle_name
        if resources.ResourceBundle.get_by_key_name(name):
            return self.error(400, 'A bundle with that name already exists.')
        resources.ResourceBundle(key_name=name).put()
        return django.shortcuts.redirect(self.build_absolute_uri(
            '/global/admin/resources/%s' % name))
