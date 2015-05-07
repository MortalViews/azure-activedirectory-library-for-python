#-------------------------------------------------------------------------
#
# Copyright Microsoft Open Technologies, Inc.
#
# All Rights Reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http: *www.apache.org/licenses/LICENSE-2.0
#
# THIS CODE IS PROVIDED *AS IS* BASIS, WITHOUT WARRANTIES OR CONDITIONS
# OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT LIMITATION
# ANY IMPLIED WARRANTIES OR CONDITIONS OF TITLE, FITNESS FOR A
# PARTICULAR PURPOSE, MERCHANTABILITY OR NON-INFRINGEMENT.
#
# See the Apache License, Version 2.0 for the specific language
# governing permissions and limitations under the License.
#
#--------------------------------------------------------------------------

import sys
import requests
import httpretty

try:
    import unittest2 as unittest
except ImportError:
    import unittest

try:
    from unittest import mock
except ImportError:
    import mock

import adal
from tests import util

from tests.util import parameters as cp

try:
    from urllib.parse import urlparse

except ImportError:
    from urlparse import urlparse


class TestAuthenticationParameters(unittest.TestCase):


    def run_data(self, test_data, test_func):

        for index, test_case in enumerate(test_data):
            parameters = None
            error = None
            test_input = test_case[0]
            test_params = test_case[1]

            try:
                parameters = test_func(test_input)
            except Exception as exp:
                error = exp

            prefix = "Test case: {0} - ".format(index)
            if test_params:
                self.assertIsNone(error, "{0}Parse failed but should have succeeded. {1}".format(prefix, error))
                self.assertEqual(parameters.authorization_uri, test_params.get('authorizationUri'),
                                 "{0}Parsed authorizationUri did not match expected value.: {1}".format(prefix, parameters.authorization_uri))
                self.assertEqual(parameters.resource, test_params.get('resource'),
                                 "{0}Parsed resource  did not match expected value.: {1}".format(prefix, parameters.resource))
            else:
                self.assertIsNotNone(error, "{0}Parse succeeded but should have failed.".format(prefix))

            
    def test_create_from_header(self):

        test_data = [
          [
            'Bearer authorization_uri="foobar,lkfj,;l,", fruitcake="f",resource="clark, &^()- q32,shark" , f="foo"',
            {
              'authorizationUri' : 'foobar,lkfj,;l,',
              'resource' : 'clark, &^()- q32,shark',
            }
          ],
          [
            'Bearer  resource="clark, &^()- q32,shark", authorization_uri="foobar,lkfj,;l,"',
            {
              'authorizationUri' : 'foobar,lkfj,;l,',
              'resource' : 'clark, &^()- q32,shark',
            }
          ],
          [
            'Bearer authorization_uri="' + cp['authorityTenant'] + '", resource="' + cp['resource'] + '"',
            {
              'authorizationUri' : cp['authorityTenant'],
              'resource' : cp['resource'],
            }
          ],
          [
            'Bearer authorization_uri="' + cp['authorizeUrl'] + '", resource="' + cp['resource'] + '"',
            {
              'authorizationUri' : cp['authorizeUrl'],
              'resource' : cp['resource'],
            }
          ],
          # Add second = sign on first pair.
          [
            'Bearer authorization_uri=="foobar,lkfj,;l,", resource="clark, &^()- q32,shark",fruitcake="f" , f="foo"',
            None
          ],
          # Add second = sign on second pair.
          [
            'Bearer authorization_uri="foobar,lkfj,;l,", resource=="clark, &^()- q32,shark",fruitcake="f" , f="foo"',
            None
          ],
          # Add second quote on first pair.
          [
            'Bearer authorization_uri=""foobar,lkfj,;l,", resource="clark, &^()- q32,shark",fruitcake="f" , f="foo"',
            None
          ],
          # Add second quote on second pair.
          [
            'Bearer authorization_uri=foobar,lkfj,;l,", resource="clark, &^()- q32,shark"",fruitcake="f" , f="foo"',
            None
          ],
          # Add trailing quote.
          [
            'Bearer authorization_uri=foobar,lkfj,;l,", resource="clark, &^()- q32,shark",fruitcake="f" , f="foo""',
            None
          ],
          # Add trailing comma at end of string.
          [
            'Bearer authorization_uri=foobar,lkfj,;l,", resource="clark, &^()- q32,shark",fruitcake="f" , f="foo",',
            None
          ],
          # Add second comma between 2 and 3 pairs.
          [
            'Bearer authorization_uri=foobar,lkfj,;l,", resource="clark, &^()- q32,shark",fruitcake="f" ,, f="foo"',
            None
          ],
          # Add second comma between 1 and 2 pairs.
          [
            'Bearer authorization_uri=foobar,lkfj,;l,", , resource="clark, &^()- q32,shark",fruitcake="f" , f="foo"',
            None
          ],
          # Add random letter between Bearer and first pair.
          [
            'Bearer  f authorization_uri=foobar,lkfj,;l,", resource="clark, &^()- q32,shark",fruitcake="f" , f="foo"',
            None
          ],
          # Add random letter between 2 and 3 pair.
          [
            'Bearer  authorization_uri=foobar,lkfj,;l,", a resource="clark, &^()- q32,shark",fruitcake="f" , f="foo"',
            None
          ],
          # Add random letter between 3 and 2 pair.
          [
            'Bearer  authorization_uri=foobar,lkfj,;l,", resource="clark, &^()- q32,shark",fruitcake="f" a, f="foo"',
            None
          ],
          # Mispell Bearer
          [
            'Berer authorization_uri=foobar,lkfj,;l,", resource="clark, &^()- q32,shark",fruitcake="f" , f="foo"',
            None
          ],
          # Missing resource.
          [
            'Bearer authorization_uri="foobar,lkfj,;l,"',
            {
              'authorizationUri' : 'foobar,lkfj,;l,'
            }
          ],
          # Missing authoritzation uri.
          [
            'Bearer resource="clark, &^()- q32,shark",fruitcake="f" , f="foo"',
            None
          ],
          # Boris's test.
          [
            'Bearer foo="bar" ANYTHING HERE, ANYTHING PRESENT HERE, foo1="bar1"',
            None
          ],
          [
            'Bearerauthorization_uri="authuri", resource="resourceHere"',
            None
          ],
        ]
        self.run_data(test_data, adal.authentication_parameters.create_authentication_parameters_from_header)

    def test_create_from_response(self):

        test_data = [
          [
            mock.Mock(status_code=401, headers={ 'www-authenticate' : 'Bearer authorization_uri="foobar,lkfj,;l,", fruitcake="f",resource="clark, &^()- q32,shark" , f="foo"' }),
            {
              'authorizationUri' : 'foobar,lkfj,;l,',
              'resource' : 'clark, &^()- q32,shark',
            }
          ],
          [
            mock.Mock(status_code=200, headers={ 'www-authenticate' : 'Bearer authorization_uri="foobar,lkfj,;l,", fruitcake="f",resource="clark, &^()- q32,shark" , f="foo"' }),
            None
          ],
          [
            mock.Mock(status_code=401),
            None
          ],
          [
            mock.Mock(status_code=401, headers={ 'foo' : 'this is not the www-authenticate header' }),
            None
          ],
          [
            mock.Mock(status_code=401, headers={ 'www-authenticate' : 'Berer authorization_uri=foobar,lkfj,;l,", resource="clark, &^()- q32,shark",fruitcake="f" , f="foo"' }),
            None
          ],
          [
            mock.Mock(status_code=401, headers={ 'www-authenticate' : None }),
            None
          ],
          [
            mock.Mock(headers={ 'www-authenticate' : None }),
            None
          ],
          [
            None,
            None
          ]
        ]

        self.run_data(test_data, adal.authentication_parameters.create_authentication_parameters_from_response)

    @httpretty.activate
    def test_create_from_url_happy_string_url(self):
        testHost = 'https://this.is.my.domain.com'
        testPath = '/path/to/resource'
        testQuery = 'a=query&string=really'
        testUrl = testHost + testPath + '?' + testQuery

        httpretty.register_uri(httpretty.GET, uri=testUrl, body='foo', status=401, **{'www-authenticate':'Bearer authorization_uri="foobar,lkfj,;l,", fruitcake="f",resource="clark, &^()- q32,shark" , f="foo"'})

        def _callback(err, parameters):
            self.assertIsNone(err, "An error was raised during function {0}".format(err))
            test_params = {
                'authorizationUri' : 'foobar,lkfj,;l,',
                'resource' : 'clark, &^()- q32,shark',
            }
            self.assertEqual(parameters.authorization_uri, test_params['authorizationUri'],
                                'Parsed authorizationUri did not match expected value.: {0}'.format(parameters.authorization_uri))
            self.assertEqual(parameters.resource, test_params['resource'],
                                'Parsed resource  did not match expected value.: {0}'.format(parameters.resource))
        adal.authentication_parameters.create_authentication_parameters_from_url(testUrl, _callback, None)

        req = httpretty.last_request()
        util.match_standard_request_headers(req)

    @httpretty.activate
    def test_create_from_url_happy_path_url_object(self):
        testHost = 'https://this.is.my.domain.com'
        testPath = '/path/to/resource'
        testQuery = 'a=query&string=really'
        testUrl = testHost + testPath + '?' + testQuery

        httpretty.register_uri(httpretty.GET, uri=testUrl, body='foo', status=401, **{'www-authenticate':'Bearer authorization_uri="foobar,lkfj,;l,", fruitcake="f",resource="clark, &^()- q32,shark" , f="foo"'})

        url_obj = urlparse(testUrl)

        def _callback(err, parameters):
            self.assertIsNone(err, "An error was raised during function {0}".format(err))
            test_params = {
                'authorizationUri' : 'foobar,lkfj,;l,',
                'resource' : 'clark, &^()- q32,shark',
            }
            self.assertEqual(parameters.authorization_uri, test_params['authorizationUri'],
                                'Parsed authorizationUri did not match expected value.: {0}'.format(parameters.authorization_uri))
            self.assertEqual(parameters.resource, test_params['resource'],
                                'Parsed resource  did not match expected value.: {0}'.format(parameters.resource))

        adal.authentication_parameters.create_authentication_parameters_from_url(url_obj, _callback)

        req = httpretty.last_request()
        util.match_standard_request_headers(req)

    def test_create_from_url_bad_object(self):
        
        def _callback(err, resp):
            self.assertIsNotNone(err, "Did not receive expected error.")

        adal.authentication_parameters.create_authentication_parameters_from_url({}, _callback)

    def test_create_from_url_not_passed(self):

        def _callback(err, resp):
            self.assertIsNotNone(err, "Did not receive expected error.")

        adal.authentication_parameters.create_authentication_parameters_from_url(None, _callback)

    @httpretty.activate
    def test_create_from_url_no_header(self):
        testHost = 'https://this.is.my.domain.com'
        testPath = '/path/to/resource'
        testQuery = 'a=query&string=really'
        testUrl = testHost + testPath + '?' + testQuery

        httpretty.register_uri(httpretty.GET, uri=testUrl, body='foo', status=401)

        def _callback(err, resp):
            self.assertIsNotNone(err, "Did not receive expected error.")
            self.assertTrue(err.message.find('header') >= 0, 'Error did not include message about missing header')

        adal.authentication_parameters.create_authentication_parameters_from_url(testUrl, _callback)

        req = httpretty.last_request()
        util.match_standard_request_headers(req)

    def test_create_from_url_network_error(self):

        def _callback(err, resp):
            self.assertIsNotNone(err, "Did not receive expected error.")

        adal.authentication_parameters.create_authentication_parameters_from_url('https://0.0.0.0/foobar', _callback)

if __name__ == '__main__':
    unittest.main()