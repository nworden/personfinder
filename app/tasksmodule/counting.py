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

"""Counting tasks."""

import datetime
import time

import django.http
from google.appengine import runtime
from google.appengine.api import datastore_errors
from google.appengine.ext import db
from google.appengine.api import taskqueue

import delete
import tasksmodule.base
import model
import utils


class CountTaskBase(tasksmodule.base.PerRepoTaskBaseView):

    _BATCH_SIZE = 500

    def schedule_task(self, repo, counter_id=None):
        """Schedules a new task.

        Should be implemented by subclasses.
        """
        del self, repo, counter_id  # Unused.
        raise NotImplementedError()

    def get_query(self):
        """Gets the query for items to count.

        Should be implemented by subclasses.
        """
        del self  # unused
        raise NotImplementedError()

    def update_counter(self, counter, record):
        """Updates a counter based on the record.

        Should be implemented by subclasses.
        """
        del self, counter, record  # Unused.
        raise NotImplementedError()

    def setup(self, request, *args, **kwargs):
        super(CountTaskBase, self).setup(request, *args, **kwargs)
        self.params.read_values(post_params={'counter_id': utils.strip})

    def get_repo_list(self):
        return model.Repo.list_active()

    def post(self, request, *args, **kwargs):
        del request, args, kwargs  # Unused.
        query = self.get_query()
        counter_id = self.params.get('counter_id', None)
        if counter_id:
            counter = model.Counter.get_by_id(counter_id)
            query.with_cursor(counter.cursor)
        else:
            counter = model.Counter(repo=repo, scan_name=self.SCAN_NAME)
        batch_count = 0
        try:
            for record in query:
                self.update_counter(counter, record)
                batch_count += 1
                if batch_count == CountTaskBase._BATCH_SIZE:
                    counter.cursor = query.cursor()
                    counter.put()
                    batch_count = 0
        except runtime.DeadlineExceededError:
            self.schedule_task(self.env.repo, counter_id=counter.key().id())
        except datastore_errors.Timeout:
            self.schedule_task(self.env.repo, counter_id=counter.key().id())
        return django.http.HttpResponse('')


class PersonCountTask(CountTaskBase):

    SCAN_NAME = 'person'

    def schedule_task(self, repo, cursor=None, counter_id=None):
        name = '%s-person-count-task-%s' % (repo, int(time.time()*1000))
        path = self.build_absolute_path('/%s/tasks/person_count', repo)
        taskqueue.add(
            name=name, method='POST', url=path, queue_name='counts',
            params={'counter_id': counter_id})

    def get_query(self):
        return model.Person.all().filter('repo =', self.env.repo)

    def update_counter(self, counter, record):
        found = ''
        if record.latest_found is not None:
            found = record.latest_found and 'TRUE' or 'FALSE'
        counter.increment('all')
        counter.increment('original_domain=' + (record.original_domain or ''))
        counter.increment('photo=' + (record.photo_url and 'present' or ''))
        counter.increment('num_notes=%d' % len(record.get_notes()))
        counter.increment('status=' + (record.latest_status or ''))
        counter.increment('found=' + found)
        if record.author_email:  # author e-mail address present?
            counter.increment('author_email')
        if record.author_phone:  # author phone number present?
            counter.increment('author_phone')
        counter.increment(
            'linked_persons=%d' % len(record.get_linked_persons()))


class NoteCountTask(CountTaskBase):

    SCAN_NAME = 'note'

    def schedule_task(self, repo, cursor=None, counter_id=None):
        name = '%s-note-count-task-%s' % (repo, int(time.time()*1000))
        path = self.build_absolute_path('/%s/tasks/note_count', repo)
        taskqueue.add(
            name=name, method='POST', url=path, queue_name='counts',
            params={'counter_id': counter_id})

    def get_query(self):
        return model.Note.all().filter('repo =', self.env.repo)

    def update_counter(self, counter, record):
        author_made_contact = ''
        if record.author_made_contact is not None:
            author_made_contact = (
                record.author_made_contact and 'TRUE' or 'FALSE')
        counter.increment('all')
        counter.increment('status=' + (record.status or ''))
        counter.increment('original_domain=' + (record.original_domain or ''))
        counter.increment('author_made_contact=' + author_made_contact)
        if record.last_known_location:  # last known location specified?
            counter.increment('last_known_location')
        if record.author_email:  # author e-mail address present?
            counter.increment('author_email')
        if record.author_phone:  # author phone number present?
            counter.increment('author_phone')
        if record.linked_person_record_id:  # linked to another person?
            counter.increment('linked_person')
