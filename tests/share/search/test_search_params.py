import dataclasses

from django.test import SimpleTestCase

from share.search.search_params import (
    Textsegment,
    SearchFilter,
)
from trove.util.queryparams import QueryparamName
from trove.vocab.namespaces import OSFMAP, RDF, DCTERMS


class TestTextsegment(SimpleTestCase):
    def test_empty(self):
        for _empty_input in ('', '""', '*', '-', '-""'):
            _empty = Textsegment.split_str(_empty_input)
            self.assertIsInstance(_empty, frozenset)
            self.assertFalse(_empty)

    def test_fuzz(self):
        _fuzzword = Textsegment.split_str('woord')
        self.assertIsInstance(_fuzzword, frozenset)
        self.assertEqual(_fuzzword, frozenset((
            Textsegment('woord', is_fuzzy=True, is_negated=False, is_openended=True),
        )))
        _fuzzphrase = Textsegment.split_str('wibbleplop worble polp elbbiw')
        self.assertIsInstance(_fuzzphrase, frozenset)
        self.assertEqual(_fuzzphrase, frozenset((
            Textsegment('wibbleplop worble polp elbbiw', is_fuzzy=True, is_negated=False, is_openended=True),
        )))

    def test_exact(self):
        _exactword = Textsegment.split_str('"woord"')
        self.assertIsInstance(_exactword, frozenset)
        self.assertEqual(_exactword, frozenset((
            Textsegment('woord', is_fuzzy=False, is_negated=False, is_openended=False),
        )))
        _exactphrase = Textsegment.split_str('"wibbleplop worble polp elbbiw"')
        self.assertIsInstance(_exactphrase, frozenset)
        self.assertEqual(_exactphrase, frozenset((
            Textsegment('wibbleplop worble polp elbbiw', is_fuzzy=False, is_negated=False, is_openended=False),
        )))
        _openphrase = Textsegment.split_str('"wibbleplop worble polp elbbiw')
        self.assertIsInstance(_openphrase, frozenset)
        self.assertEqual(_openphrase, frozenset((
            Textsegment('wibbleplop worble polp elbbiw', is_fuzzy=False, is_negated=False, is_openended=True),
        )))

    def test_minus(self):
        _minusword = Textsegment.split_str('-woord')
        self.assertIsInstance(_minusword, frozenset)
        self.assertEqual(_minusword, frozenset((
            Textsegment('woord', is_fuzzy=False, is_negated=True, is_openended=False),
        )))
        _minusexactword = Textsegment.split_str('-"woord droow"')
        self.assertIsInstance(_minusexactword, frozenset)
        self.assertEqual(_minusexactword, frozenset((
            Textsegment('woord droow', is_fuzzy=False, is_negated=True, is_openended=False),
        )))
        _minustwo = Textsegment.split_str('abc -def -g hi there')
        self.assertIsInstance(_minustwo, frozenset)
        self.assertEqual(_minustwo, frozenset((
            Textsegment('def', is_fuzzy=False, is_negated=True, is_openended=False),
            Textsegment('g', is_fuzzy=False, is_negated=True, is_openended=False),
            Textsegment('hi there', is_fuzzy=True, is_negated=False, is_openended=True),
            Textsegment('abc', is_fuzzy=True, is_negated=False, is_openended=False),
        )))

    def test_combo(self):
        _combo = Textsegment.split_str('wibbleplop -"worble polp" elbbiw -but "exactly')
        self.assertIsInstance(_combo, frozenset)
        self.assertEqual(_combo, frozenset((
            Textsegment('worble polp', is_fuzzy=False, is_negated=True, is_openended=False),
            Textsegment('elbbiw', is_fuzzy=True, is_negated=False, is_openended=False),
            Textsegment('wibbleplop', is_fuzzy=True, is_negated=False, is_openended=False),
            Textsegment('but', is_fuzzy=False, is_negated=True, is_openended=False),
            Textsegment('exactly', is_fuzzy=False, is_negated=False, is_openended=True),
        )))


class TestSearchFilter(SimpleTestCase):
    def test_from_param(self):
        _cases = {
            ('foo[resourceType]', 'Project'): SearchFilter(
                property_path=(RDF.type,),
                value_set=frozenset([OSFMAP.Project]),
                operator=SearchFilter.FilterOperator.ANY_OF,
            ),
            ('foo[urn:foo][none-of]', 'urn:bar,urn:baz'): SearchFilter(
                property_path=('urn:foo',),
                value_set=frozenset(['urn:bar', 'urn:baz']),
                operator=SearchFilter.FilterOperator.NONE_OF,
            ),
            ('foo[http://foo.example/prop1,http://foo.example/prop2]', 'resourceType'): SearchFilter(
                property_path=('http://foo.example/prop1', 'http://foo.example/prop2',),
                value_set=frozenset([RDF.type]),
                operator=SearchFilter.FilterOperator.ANY_OF,
            ),
            ('foo[dateCreated]', '2000'): SearchFilter(
                property_path=(DCTERMS.created,),
                value_set=frozenset(['2000']),
                operator=SearchFilter.FilterOperator.AT_DATE,
            ),
            ('foo[isPartOf,dateModified][after]', '2000-01-01'): SearchFilter(
                property_path=(DCTERMS.isPartOf, DCTERMS.modified,),
                value_set=frozenset(['2000-01-01']),
                operator=SearchFilter.FilterOperator.AFTER,
            ),
            ('foo[dateWithdrawn][before]', '2000-01-01'): SearchFilter(
                property_path=(OSFMAP.dateWithdrawn,),
                value_set=frozenset(['2000-01-01']),
                operator=SearchFilter.FilterOperator.BEFORE,
            ),
            ('foo[creator][is-present]', ''): SearchFilter(
                property_path=(DCTERMS.creator,),
                value_set=frozenset(),
                operator=SearchFilter.FilterOperator.IS_PRESENT,
            ),
            ('foo[creator,creator,creator][is-absent]', 'nothing'): SearchFilter(
                property_path=(DCTERMS.creator, DCTERMS.creator, DCTERMS.creator,),
                value_set=frozenset(),
                operator=SearchFilter.FilterOperator.IS_ABSENT,
            ),
        }
        for (_paramname, _paramvalue), _searchfilter in _cases.items():
            _actualfilter = SearchFilter.from_filter_param(
                QueryparamName.from_str(_paramname),
                _paramvalue,
            )
            _expectedfilter = dataclasses.replace(
                _searchfilter,
                original_param_name=_paramname,
                original_param_value=_paramvalue,
            )
            self.assertEqual(_expectedfilter, _actualfilter)