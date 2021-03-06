from django.test import TestCase, RequestFactory, Client
from django.http import HttpResponse, StreamingHttpResponse
from django.core.management import call_command
import json
import os
import pprint

from . import test_fixtures_set

'''

Test the /lookup/name endpoint

'''

REF_FILE_PATH = os.path.join(os.path.dirname(__file__), 'references')
WRITE_REFS = False

class LookupNameTestCase(TestCase):
    test_fixtures = test_fixtures_set

    def setUp(self):
        for fixture in self.test_fixtures:
            full_fixture = 'tark/tests/test-data/' + fixture
            print "Loading fixture {}".format(full_fixture)
            call_command('loaddata', full_fixture, verbosity=1)

        self.factory = RequestFactory()

    def testLookupNameGene(self):
        print "Testing Lookup Gene"

        genes = ['IRAK4', 'IRAK2']
        assemblies = {'GCA_000001405.22':'GRCh38', 'GCA_000001405.14':'GRCh37'}

        self.doJsonLookupTest('gene', genes, assemblies, WRITE_REFS)

        self.doJsonPostTest('gene', genes, WRITE_REFS)

    def testLookupNameTranscript(self):
        print "Testing Lookup Transcript"

        transcripts = ['IRAK4', 'IRAK2', 'BRCA2']

        self.doJsonLookupTest('transcript', transcripts, None, WRITE_REFS)

        self.doFastaLookupTest('transcript', transcripts, WRITE_REFS)

        self.doJsonPostTest('transcript', transcripts, WRITE_REFS)

    def doFastaLookupTest(self, feature_type, features, write_ref = False):
        print "\tdoFastaLookupTest ({})".format(feature_type)
        c = Client()
        
        base_url = "/tark/lookup/name/{}/?name={}"

        if write_ref:
            refs = {}
        else:
            json_file = open( os.path.join( REF_FILE_PATH, "{}_name_fasta_reference.json".format(feature_type) ) )
            refs = json.load(json_file)

        for feature in features:
            if write_ref:
                refs[feature] = {}

            url = base_url.format(feature_type, feature)

            response = c.get(url, {}, HTTP_ACCEPT='text/x-fasta')
            content = ''.join(self.fetchContent(response))
            if write_ref:
                refs[feature] = content
            else:
                self.assertEquals(refs[feature], content, "Retrieved {} for {} (fasta) don't match".format(feature_type, feature))

        if write_ref:
            self.writeRef( "{}_name_fasta_reference.json".format(feature_type), refs )


    def doJsonLookupTest(self, feature_type, features, assemblies, write_ref = False):
        print "\tdoJsonLookupTest ({})".format(feature_type)
        c = Client()
        
        base_url = "/tark/lookup/name/{}/?name={}"

        if write_ref:
            refs = {}
        else:
            json_file = open( os.path.join( REF_FILE_PATH, "{}_name_json_reference.json".format(feature_type) ) )
            refs = json.load(json_file)

        for feature in features:
            if write_ref:
                refs[feature] = {}

            url = base_url.format(feature_type, feature)

            response = c.get(url)
            content = json.loads(''.join(self.fetchContent(response)))
            if write_ref:
                refs[feature]['ref'] = content
            else:
                self.assertEquals( refs[feature]['ref'], content, "Retrieved {} for {} don't match".format(feature_type, feature) )

            response = c.get(url + '&expand=1')
            content = json.loads(''.join(self.fetchContent(response)))
            if write_ref:
                refs[feature]['ref_expanded'] = content
            else:
                self.assertEquals( refs[feature]['ref_expanded'], content, "Retrieved {} for {} (expanded) don't match".format(feature_type, feature) )

            response = c.get(url + '&skip_sequence=1')
            content = json.loads(''.join(self.fetchContent(response)))
            if write_ref:
                refs[feature]['ref_skip_sequence'] = content
            else:
                self.assertEquals( refs[feature]['ref_skip_sequence'], content, "Retrieved {} for {} (skip_sequence) don't match".format(feature_type, feature) )

            response = c.get(url + '&skip_sequence=1&expand=1')
            content = json.loads(''.join(self.fetchContent(response)))
            if write_ref:
                refs[feature]['ref_skip_sequence_expanded'] = content
            else:
                self.assertEquals( refs[feature]['ref_skip_sequence_expanded'], content, "Retrieved {} for {} (skip_sequence, expanded) don't match".format(feature_type, feature) )

            for assembly in assemblies or []:
                response = c.get(url + '&assembly={}'.format(assembly))
                record = self.fetchRecord(refs[feature]['ref'], u'assembly', assemblies[assembly]);
                content = json.loads(''.join(self.fetchContent(response)))
                if not write_ref:
                    self.assertEquals(record, content, "Retrieved {} for {}, assembly {} don't match".format(feature_type, feature, assembly))

        if write_ref:
            self.writeRef( "{}_name_json_reference.json".format(feature_type), refs )

    def doJsonPostTest(self, feature_type, features, write_ref = False):
        print "\tdoJsonPostTest ({})".format(feature_type)
        c = Client()

        url = "/tark/lookup/name/{}/".format(feature_type)

        if write_ref:
            refs = {}
        else:
            json_file = open( os.path.join( REF_FILE_PATH, "{}_name_post_json_reference.json".format(feature_type) ) )
            refs = json.load(json_file)

        features_data = {'name': features}

        response = c.post(url, json.dumps(features_data),
                          content_type='application/json')
        content = json.loads(''.join(self.fetchContent(response)))

        if write_ref:
            self.writeRef( "{}_name_post_json_reference.json".format(feature_type), content )
        else:
            self.assertEquals( refs, content, "Retrieved {} via POST don't match".format(feature_type) )


    def fetchContent(self, response):
        if type(response) == StreamingHttpResponse:
            return response.streaming_content
        else:
            return response.content

    def fetchRecord(self, structure, key, value):
        for rec in structure:
            if rec.get(key, None) == value:
                return [rec]

        return []

    def writeRef(self, filename, refs):
        outfile_name = os.path.join( REF_FILE_PATH, filename )
        print "\tWriting reference outfile {}".format(outfile_name)
        with open(outfile_name, 'w') as outfile:
            json.dump(refs, outfile, sort_keys=True, indent=4)
