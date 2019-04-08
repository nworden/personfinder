#!/usr/bin/python2.7
# encoding=utf-8
#
# Copyright 2010 Google Inc. All Rights Reserved.
"""Tests for indexing.."""

__author__ = 'eyalf@google.com (Eyal Fink)'

import datetime
import logging
import sys
import unittest

from google.appengine.ext import db

import indexing
import model
import text_query


def create_person(given_name, family_name):
    """Creates a Person object for testing."""
    return model.Person.create_original(
        'test',
        given_name=given_name,
        family_name=family_name,
        full_name=('%s %s' % (given_name, family_name)),
        entry_date=datetime.datetime.utcnow())


_BEI = u'\u8c9d'
_CHAN = u'\u9673'
_DI = u'\u68e3'
_KONG = u'\u6e2f'
_MING = u'\u9298'
_SANG = u'\u751f'
_WEN = u'\u6587'
_YU = u'\u807f'
_ZHU = u'\u6731'


class IndexingTests(unittest.TestCase):
    """Test cases for the indexing module."""

    # pylint: disable=no-self-use

    def setUp(self):
        db.delete(model.Person.all())

    def tearDown(self):
        db.delete(model.Person.all())

    def add_persons(self, *persons):
        """Updates index properties and stores each given person."""
        for person in persons:
            indexing.update_index_properties(person)
            db.put(person)

    def get_matches(self, query):
        """Performs a search and returns the names from the results.

        The number of results is limited to 100.

        Args:
            query (str): The search query.

        Returns:
            list: A list of tuples, containing the given and family names for
            each results.
        """
        results = indexing.search('test', text_query.TextQuery(query), 100)
        return [(p.given_name, p.family_name) for p in results]

    def get_ranked(self, results, query):
        """Runs indexing.rank_and_order on the results.

        rank_and_order will be passed 100 as the max_results argument.

        Args:
            results (list): A list of model.Person objects.
            query (TextQuery): A query.

        Returns:
            list: A list of tuples, containing the given and family names for
            the ranked-and-ordered results.
        """
        indexing.rank_and_order(results, text_query.TextQuery(query), 100)
        return [(p.given_name, p.family_name) for p in results]

    def test_rank_and_order(self):
        """Tests indexing.rank_and_order."""
        res = [
            create_person(
                given_name='Bryan',
                family_name='abc',
            ),
            create_person(given_name='Bryan', family_name='abcef'),
            create_person(given_name='abc', family_name='Bryan'),
            create_person(given_name='Bryan abc', family_name='efg')
        ]

        sorted_res = indexing.rank_and_order(res,
                                             text_query.TextQuery('Bryan abc'),
                                             100)
        assert ['%s %s'%(p.given_name, p.family_name) for p in sorted_res] == \
            ['Bryan abc', 'abc Bryan', 'Bryan abc efg', 'Bryan abcef']

        sorted_res = indexing.rank_and_order(res,
                                             text_query.TextQuery('Bryan abc'),
                                             2)
        assert ['%s %s'%(p.given_name, p.family_name) for p in sorted_res] == \
            ['Bryan abc', 'abc Bryan']

        sorted_res = indexing.rank_and_order(res,
                                             text_query.TextQuery('abc Bryan'),
                                             100)
        assert ['%s %s'%(p.given_name, p.family_name) for p in sorted_res] == \
            ['abc Bryan', 'Bryan abc', 'Bryan abc efg', 'Bryan abcef']

        res = [
            create_person(given_name='abc', family_name='efg'),
            create_person(given_name='ABC', family_name='EFG'),
            create_person(given_name='ABC', family_name='efghij')
        ]

        sorted_res = indexing.rank_and_order(res, text_query.TextQuery('abc'),
                                             100)
        assert ['%s %s'%(p.given_name, p.family_name) for p in sorted_res] == \
            ['abc efg', 'ABC EFG', 'ABC efghij']

    def test_cjk_ranking_1(self):
        """One of two tests to check the rank_and_order function for CJK values.
        """
        # This test uses:
        # - Jackie Chan's Chinese name.  His family name is CHAN and his given
        # name is KONG + SANG; the usual Chinese order is CHAN + KONG + SANG.
        # -  I. M. Pei's Chinese name.  His family name is BEI and his given
        # name is YU + MING; the usual Chinese order is BEI + YU + MING.
        persons = [
            create_person(given_name=_CHAN + _KONG + _SANG, family_name='foo'),
            create_person(given_name=_SANG, family_name=_CHAN + _KONG),
            create_person(given_name=_CHAN, family_name=_KONG + _SANG),
            create_person(given_name=_KONG + _SANG, family_name=_CHAN),
            create_person(given_name=_KONG + _CHAN, family_name=_SANG),
            create_person(given_name=_KONG, family_name=_SANG),
            create_person(given_name=_YU + _MING, family_name=_BEI),
        ]

        assert self.get_ranked(persons, _CHAN + _KONG + _SANG) == [
            (_KONG + _SANG, _CHAN),  # surname + given name is best
            (_SANG, _CHAN + _KONG),  # then multi-char surname + given name
            (_CHAN, _KONG + _SANG),  # then surname/given switched
            (_KONG + _CHAN, _SANG),  # then out-of-order match
            (_CHAN + _KONG + _SANG, 'foo'),  # then exact given name match
            (_KONG, _SANG),  # then partial match
            (_YU + _MING, _BEI),  # then nothing match
        ]

        assert self.get_ranked(persons, _CHAN + ' ' + _KONG + _SANG) == [
            (_KONG + _SANG, _CHAN),  # surname + given name is best
            (_CHAN, _KONG + _SANG),  # then surname/given switched
            (_KONG + _CHAN, _SANG),  # then multi-char surname / given switched
            (_SANG, _CHAN + _KONG),  # then out-of-order match
            (_CHAN + _KONG + _SANG, 'foo'),  # then exact given name match
            (_KONG, _SANG),  # then partial match
            (_YU + _MING, _BEI),  # then nothing match
        ]

    def test_cjk_ranking_2(self):
        """One of two tests to check the rank_and_order function for CJK values.
        """
        # This test uses Steven Chu's Chinese name.  His family name is ZHU and his
        # given name is DI + WEN; the usual Chinese order is ZHU + DI + WEN.

        # A test database of 3 records with various permutations of the name.
        persons = [
            create_person(given_name=_WEN, family_name=_ZHU + _DI),
            create_person(given_name=_DI + _WEN, family_name=_ZHU),
            create_person(given_name=_ZHU, family_name=_DI + _WEN),
        ]

        # When the search query is ZHU + DI + WEN:
        assert self.get_ranked(persons, _ZHU + _DI + _WEN) == [
            (_DI + _WEN,
             _ZHU),  # best: treat query as 1-char surname + given name
            (_WEN,
             _ZHU + _DI),  # then: treat as multi-char surname + given name
            (_ZHU, _DI + _WEN),  # then: treat query as given name + surname
        ]

        # When the search query is _ZHU + ' ' + _DI + _WEN (no multi-char surname):
        assert self.get_ranked(persons, _ZHU + ' ' + _DI + _WEN) == [
            (_DI + _WEN,
             _ZHU),  # best: treat query as surname + ' ' + given name
            (_ZHU,
             _DI + _WEN),  # then: treat query as given name + ' ' + surname
            (_WEN, _ZHU + _DI),  # then: match query characters out of order
        ]

    def test_sort_query_words(self):
        """Tests that query words are sorted correctly."""
        # Sorted lexicographically.
        assert indexing.sort_query_words(['CC', 'BB',
                                          'AA']) == ['AA', 'BB', 'CC']
        # Sorted by lengths.
        assert indexing.sort_query_words(['A', 'AA',
                                          'AAA']) == ['AAA', 'AA', 'A']
        # Sorted by popularity.
        assert indexing.sort_query_words([u'川', u'口',
                                          u'良']) == [u'口', u'良', u'川']
        # Test sort key precedence.
        assert indexing.sort_query_words(['CCC', 'BB', 'AA',
                                          'A']) == ['CCC', 'AA', 'BB', 'A']

    def test_search(self):
        """Tests searching."""
        persons = [
            create_person(given_name='Bryan', family_name='abc'),
            create_person(given_name='Bryan', family_name='abcef'),
            create_person(given_name='abc', family_name='Bryan'),
            create_person(given_name='Bryan abc', family_name='efg'),
            create_person(given_name='AAAA BBBB', family_name='CCC DDD')
        ]
        for person in persons:
            indexing.update_index_properties(person)
            db.put(person)

        res = indexing.search('test', text_query.TextQuery('Bryan abc'), 1)
        assert [(p.given_name, p.family_name) for p in res] == [('Bryan',
                                                                 'abc')]

        res = indexing.search('test', text_query.TextQuery('CC AAAA'), 100)
        assert [(p.given_name, p.family_name) for p in res] == \
            [('AAAA BBBB', 'CCC DDD')]

    def test_cjk_first_only(self):
        """Tests with a CJK given name."""
        self.add_persons(
            create_person(given_name=u'\u4f59\u5609\u5e73', family_name='foo'),
            create_person(given_name=u'\u80e1\u6d9b\u5e73', family_name='foo'),
        )

        # Any single character should give a hit.
        assert self.get_matches(u'\u4f59') == [(u'\u4f59\u5609\u5e73', 'foo')]
        assert self.get_matches(u'\u5609') == [(u'\u4f59\u5609\u5e73', 'foo')]
        assert self.get_matches(u'\u5e73') == [(u'\u4f59\u5609\u5e73', 'foo'),
                                               (u'\u80e1\u6d9b\u5e73', 'foo')]

        # Order of characters in the query should not matter.
        assert self.get_matches(u'\u5609\u5e73') == \
            [(u'\u4f59\u5609\u5e73', 'foo')]
        assert self.get_matches(u'\u5e73\u5609') == \
            [(u'\u4f59\u5609\u5e73', 'foo')]
        assert self.get_matches(u'\u4f59\u5609\u5e73') == \
            [(u'\u4f59\u5609\u5e73', 'foo')]

    def test_cjk_last_only(self):
        """Tests with a CJK family name."""
        self.add_persons(
            create_person(given_name='foo', family_name=u'\u4f59\u5609\u5e73'),
            create_person(given_name='foo', family_name=u'\u80e1\u6d9b\u5e73'),
        )

        # Any single character should give a hit.
        assert self.get_matches(u'\u4f59') == \
            [('foo', u'\u4f59\u5609\u5e73')]
        assert self.get_matches(u'\u5609') == \
            [('foo', u'\u4f59\u5609\u5e73')]
        assert self.get_matches(u'\u5e73') == [('foo', u'\u4f59\u5609\u5e73'),
                                               ('foo', u'\u80e1\u6d9b\u5e73')]

        # Order of characters in the query should not matter.
        assert self.get_matches(u'\u5609\u5e73') == \
            [('foo', u'\u4f59\u5609\u5e73')]
        assert self.get_matches(u'\u5e73\u5609') == \
            [('foo', u'\u4f59\u5609\u5e73')]
        assert self.get_matches(u'\u4f59\u5609\u5e73') == \
            [('foo', u'\u4f59\u5609\u5e73')]

    def test_cjk_first_last(self):
        """Tests with a CJK given and family name."""
        self.add_persons(
            create_person(given_name=u'\u5609\u5e73', family_name=u'\u4f59'),
            create_person(given_name=u'\u6d9b\u5e73', family_name=u'\u80e1'),
        )

        # Any single character should give a hit.
        assert self.get_matches(u'\u4f59') == \
            [(u'\u5609\u5e73', u'\u4f59')]
        assert self.get_matches(u'\u5609') == \
            [(u'\u5609\u5e73', u'\u4f59')]
        assert self.get_matches(u'\u5e73') == [(u'\u5609\u5e73', u'\u4f59'),
                                               (u'\u6d9b\u5e73', u'\u80e1')]

        # Order of characters in the query should not matter.
        assert self.get_matches(u'\u5609\u5e73') == \
            [(u'\u5609\u5e73', u'\u4f59')]
        assert self.get_matches(u'\u5e73\u5609') == \
            [(u'\u5609\u5e73', u'\u4f59')]
        assert self.get_matches(u'\u4f59\u5609\u5e73') == \
            [(u'\u5609\u5e73', u'\u4f59')]

    def test_no_query_terms(self):
        """Tests that no exception is thrown if there's no query terms."""
        assert indexing.search('test', text_query.TextQuery(''), 100) == []


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr)
    unittest.main()
