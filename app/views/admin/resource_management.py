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
from google.appengine.ext import db

import config
import resources
import utils
import views.admin.base


class AdminResourcesIndexView(views.admin.base.AdminBaseView):
    """The admin resources view."""

    ACTION_ID = 'admin/resources_index'

    def setup(self, request, *args, **kwargs):
        super(AdminResourcesIndexView, self).setup(request, *args, **kwargs)
        self.params.read_values(
            post_params={
                'bundle_name': utils.strip,
                'operation': utils.strip,
            })

    @views.admin.base.enforce_superadmin_admin_level
    def get(self, request, *args, **kwargs):
        """Serves GET requests."""
        del request, args, kwargs  # Unused.
        default_bundle_name = self.env.config.get(
            'default_resource_bundle', '1')
        bundle_info = []
        for bundle in resources.ResourceBundle.all():
            name = bundle.key().name()
            bundle_info.append({
                'name': name,
                'url': self.build_absolute_uri(
                    '/global/admin/resources/%s' % name),
                'is_default': name == default_bundle_name,
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
        if self.params.operation == 'create':
            return self._create_new_bundle()
        elif self.params.operation == 'make_default':
            return self._make_bundle_default()
        elif self.params.operation == 'delete':
            return self._delete_bundle()
        return self.error(400)

    def _create_new_bundle(self):
        name = self.params.bundle_name
        if resources.ResourceBundle.get_by_key_name(name):
            return self.error(400, 'A bundle with that name already exists.')
        resources.ResourceBundle(key_name=name).put()
        return django.shortcuts.redirect(self.build_absolute_uri(
            '/global/admin/resources/%s' % name))

    def _make_bundle_default(self):
        name = self.params.bundle_name
        if not resources.ResourceBundle.get_by_key_name(name):
            return self.error(400, 'That bundle doesn\'t exist.')
        config.set(default_resource_bundle=name)
        return django.shortcuts.redirect(self.build_absolute_uri())

    def _delete_bundle(self):
        bundle = resources.ResourceBundle.get_by_key_name(
            self.params.bundle_name)
        if not bundle:
            return self.error(400, 'That bundle doesn\'t exist.')
        db.delete(bundle.list_resources())
        bundle.delete()
        return django.shortcuts.redirect(self.build_absolute_uri())


class AdminResourcesBundleView(views.admin.base.AdminBaseView):

    ACTION_ID = 'admin/resources_bundle'

    def setup(self, request, *args, **kwargs):
        super(AdminResourcesBundleView, self).setup(request, *args, **kwargs)
        self._bundle_name = kwargs['bundle']
        self.params.read_values(
            post_params={
                'language': utils.strip,
                'operation': utils.strip,
                'resource_name': utils.validate_resource_name,
            })

    @views.admin.base.enforce_superadmin_admin_level
    def get(self, request, *args, **kwargs):
        bundle = resources.ResourceBundle.get_by_key_name(self._bundle_name)
        resource_info = {}
        for resource_key in bundle.list_resources():
            if ':' in resource_key:
                name, lang = resource_key.split(':')
            else:
                name = resource_key
                lang = None
            if name not in resource_info:
                resource_info[name] = {
                    'default_url': self.build_absolute_uri(
                        '/global/admin/resources/%s/%s' % (
                            self._bundle_name, name)),
                    'lang_links': [],
                }
            if lang:
                resource_info[name]['lang_links'].append({
                    'lang': lang,
                    'url': self.build_absolute_uri(
                        '/global/admin/resources/%s/%s' % (
                            self._bundle_name, name),
                        params={'resource_lang': lang}),
                })
        resource_list = []
        for name in sorted(resource_info.keys()):
            info = resource_info[name]
            resource_list.append({
                'name': name,
                'default_url': info['default_url'],
                'lang_links': sorted(
                    info['lang_links'], key=lambda ll: ll['lang']),
            })
        return self.render(
            'admin_resources_bundle.html',
            bundle_name=self._bundle_name,
            resources=resource_list,
            xsrf_token=self.xsrf_tool.generate_token(
                self.env.user.user_id(), self.ACTION_ID))

    @views.admin.base.enforce_superadmin_admin_level
    def post(self, request, *args, **kwargs):
        del request, args, kwargs  # Unused.
        self.enforce_xsrf(self.ACTION_ID)
        if self.params.operation == 'add_language':
            return self._add_language()
        elif self.params.operation == 'delete':
            return self._delete()
        elif self.params.operation == 'create':
            return self._create()
        return self.error(400)

    def _add_language(self):
        return django.shortcuts.redirect(self.build_absolute_uri(
            '/global/admin/resources/%s/%s' % (
                self._bundle_name, self.params.resource_name),
            params={'resource_lang': self.params.language}))

    def _delete(self):
        to_delete = []
        for resource in resources.Resource.all().ancestor(
                resources.ResourceBundle.get_by_key_name(self._bundle_name)):
            resource_key = resource.key().name()
            if ':' in resource_key:
                name, _ = resource_key.split(':')
            else:
                name = resource_key
            if name == self.params.resource_name:
                to_delete.append(resource)
        db.delete(to_delete)
        return django.shortcuts.redirect(self.build_absolute_uri())

    def _create(self):
        return django.shortcuts.redirect(self.build_absolute_uri(
            '/global/admin/resources/%s/%s' % (
                self._bundle_name, self.params.resource_name)))


class AdminResourcesFileView(views.admin.base.AdminBaseView):

    ACTION_ID = 'admin/resources_file'

    def setup(self, request, *args, **kwargs):
        super(AdminResourcesFileView, self).setup(request, *args, **kwargs)
        self._bundle_name = kwargs['bundle']
        self._resource_name = kwargs['resource_name']
        self.params.read_values(
            get_params={
                'resource_lang': utils.strip,
            },
            post_params={
                'cache_seconds': utils.validate_cache_seconds,
                'operation': utils.strip,
                'resource_lang': utils.strip,
            },
            file_params={
                'content': lambda value: value,
            })

    @views.admin.base.enforce_superadmin_admin_level
    def get(self, request, *args, **kwargs):
        return self.render(
            'admin_resources_file.html',
            bundle_name=self._bundle_name,
            resource_name=self._resource_name,
            resource_lang=self.params.resource_lang,
            url=self.build_absolute_uri(
                '/global/static/%s' % self._resource_name,
                params={'lang': self.params.resource_lang}),
            xsrf_token=self.xsrf_tool.generate_token(
                self.env.user.user_id(), self.ACTION_ID))

    @views.admin.base.enforce_superadmin_admin_level
    def post(self, request, *args, **kwargs):
        del request, args, kwargs  # Unused.
        self.enforce_xsrf(self.ACTION_ID)
        if self.params.operation == 'upload':
            return self._upload()
        elif self.params.operation == 'delete':
            return self._delete()
        return self.error(400)

    def _upload(self):
        bundle = resources.ResourceBundle(key_name=self._bundle_name)
        key_name = self._resource_name
        if self.params.resource_lang:
            key_name += ':%s' % self.params.resource_lang
        uploaded_content = b''
        for chunk in self.params.content.chunks():
            uploaded_content += chunk
        resources.Resource(
            parent=bundle,
            key_name=key_name,
            content=uploaded_content,
            cache_seconds=self.params.cache_seconds).put()
        return django.shortcuts.redirect(self.build_absolute_uri(
            '/global/admin/resources/%s/%s' % (
                self._bundle_name, self._resource_name),
            params={'resource_lang': self.params.resource_lang}))

    def _delete(self):
        if not self.params.resource_lang:
            return self.error(400)
        bundle = resources.ResourceBundle(key_name=self._bundle_name)
        key_name = '%s:%s' % (self._resource_name, self.params.resource_lang)
        resource = resources.Resource(parent=bundle, key_name=key_name)
        if not resource:
            return self.error(400)
        resource.delete()
        return django.shortcuts.redirect(self.build_absolute_uri())
