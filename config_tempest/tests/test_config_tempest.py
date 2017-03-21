# -*- coding: utf-8 -*-

# Copyright 2017 Red Hat, Inc.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from config_tempest import config_tempest as tool
from config_tempest.tests.base import BaseConfigTempestTest
from fixtures import MonkeyPatch
import logging
import mock

# disable logging when running unit tests
logging.disable(logging.CRITICAL)


class TestClientManager(BaseConfigTempestTest):

    def setUp(self):
        super(TestClientManager, self).setUp()
        self.conf = self._get_conf("v2.0", "v3")
        self.client = self._get_clients(self.conf)

    def test_get_credentials_v2(self):
        mock_function = mock.Mock()
        function2mock = 'config_tempest.config_tempest.auth.get_credentials'
        self.useFixture(MonkeyPatch(function2mock, mock_function))
        self.client.get_credentials(self.conf, "name", "Tname", "pass")
        mock_function.assert_called_with(
            auth_url=None, fill_in=False, identity_version='v2',
            disable_ssl_certificate_validation='true',
            ca_certs=None, password='pass', tenant_name='Tname',
            username='name')

    def test_get_credentials_v3(self):
        mock_function = mock.Mock()
        function2mock = 'config_tempest.config_tempest.auth.get_credentials'
        self.useFixture(MonkeyPatch(function2mock, mock_function))
        self.client.get_credentials(self.conf, "name", "project_name",
                                    "pass", identity_version='v3')
        mock_function.assert_called_with(
            auth_url=None, fill_in=False, identity_version='v3',
            disable_ssl_certificate_validation='true',
            ca_certs=None, password='pass',
            username='name',
            project_name='project_name',
            domain_name='Default',
            user_domain_name='Default')

    def test_get_auth_provider_keystone_v2(self):
        # check if method returns correct method - KeystoneV2AuthProvider
        mock_function = mock.Mock()
        # mock V2Provider, if other provider is called, it fails
        func2mock = 'config_tempest.config_tempest.auth.KeystoneV2AuthProvider'
        self.useFixture(MonkeyPatch(func2mock, mock_function))
        resp = self.client.get_auth_provider(self.conf, "")
        self.assertEqual(resp, mock_function())
        # check parameters of returned function
        self.client.get_auth_provider(self.conf, "")
        mock_function.assert_called_with('', 'http://172.16.52.151:5000/v2.0',
                                         'true', None)

    def test_get_auth_provider_keystone_v3(self):
        # check if method returns KeystoneV3AuthProvider
        # make isinstance return True
        mockIsInstance = mock.Mock(return_value=True)
        self.useFixture(MonkeyPatch('config_tempest.config_tempest.isinstance',
                                    mockIsInstance))
        mock_function = mock.Mock()
        # mock V3Provider, if other provider is called, it fails
        func2mock = 'config_tempest.config_tempest.auth.KeystoneV3AuthProvider'
        self.useFixture(MonkeyPatch(func2mock, mock_function))
        resp = self.client.get_auth_provider(self.conf, "")
        self.assertEqual(resp, mock_function())
        # check parameters of returned function
        self.client.get_auth_provider(self.conf, "")
        mock_function.assert_called_with('', 'http://172.16.52.151:5000/v3',
                                         'true', None)

    def test_get_identity_version_v2(self):
        resp = self.client.get_identity_version(self.conf)
        self.assertEqual(resp, 'v2')

    def test_get_identity_version_v3(self):
        conf = self._get_conf("v3", "v3")  # uri has to be v3
        resp = self.client.get_identity_version(conf)
        self.assertEqual(resp, 'v3')

    def test_init_manager_as_admin(self):
        mock_function = mock.Mock(return_value={"id": "my_fake_id"})
        func2mock = 'config_tempest.config_tempest.identity.get_tenant_by_name'
        self.useFixture(MonkeyPatch(func2mock, mock_function))
        tool.ClientManager(self.conf, admin=True)
        # check if admin credentials were set
        admin_tenant = self.conf.get("identity", "admin_tenant_name")
        admin_password = self.conf.get("identity", "admin_password")
        self.assertEqual(self.conf.get("identity", "admin_username"), "admin")
        self.assertEqual(admin_tenant, "adminTenant")
        self.assertEqual(admin_password, "adminPass")
        # check if admin tenant id was set
        admin_tenant_id = self.conf.get("identity", "admin_tenant_id")
        self.assertEqual(admin_tenant_id, "my_fake_id")


class TestTempestConf(BaseConfigTempestTest):
    def setUp(self):
        super(TestTempestConf, self).setUp()
        self.conf = tool.TempestConf()

    def test_set_value(self):
        resp = self.conf.set("section", "key", "value")
        self.assertTrue(resp)
        self.assertEqual(self.conf.get("section", "key"), "value")
        self.assertEqual(self.conf.get_defaulted("section", "key"), "value")

    def test_set_value_overwrite(self):
        # set value wihout priority (default: priority=False)
        resp = self.conf.set("section", "key", "value")
        # value should be overwritten, because it wasn't set with priority
        resp = self.conf.set("section", "key", "value")
        self.assertTrue(resp)

    def test_set_value_overwrite_priority(self):
        resp = self.conf.set("sectionPriority", "key", "value", priority=True)
        resp = self.conf.set("sectionPriority", "key", "value")
        self.assertFalse(resp)

    def test_set_value_overwrite_by_priority(self):
        resp = self.conf.set("section", "key", "value")
        resp = self.conf.set("section", "key", "value", priority=True)
        self.assertTrue(resp)

    def test_set_value_overwrite_priority_by_priority(self):
        resp = self.conf.set("sectionPriority", "key", "value", priority=True)
        resp = self.conf.set("sectionPriority", "key", "value", priority=True)
        self.assertTrue(resp)

    def test_get_bool_value(self):
        self.assertTrue(self.conf.get_bool_value("True"))
        self.assertFalse(self.conf.get_bool_value("False"))
        self.assertRaises(ValueError, self.conf.get_bool_value, "no")


class TestConfigTempest(BaseConfigTempestTest):

    FAKE_SERVICES = {
        'compute': {
            'url': 'http://172.16.52.151:8774/v2.1/402486',
            'extensions': ['NMN', 'OS-DCF', 'OS-EXT-AZ', 'OS-EXT-IMG-SIZE'],
            'versions': ['v2.0', 'v2.1']
        },
        'network': {
            'url': 'http://172.16.52.151:9696',
            'extensions': ['default-subnetpools', 'network-ip-availability'],
            'versions': ['v2.0']
        },
        'image': {
            'url': 'http://172.16.52.151:9292',
            'extensions': [],
            'versions': ['v2.4', 'v2.3', 'v2.2']
        },
        'volume': {
            'url': 'http://172.16.52.151:8776/v1/402486',
            'extensions': ['OS-SCH-HNT', 'os-hosts'],
            'versions': ['v1.0', 'v2.0', 'v3.0']
        },
        'identity': {
            'url': 'http://172.16.52.151:5000/v3',
            'versions': ['v3.8', 'v2.0']
        },
        'ec2': {
            'url': 'http://172.16.52.151:5000'
        },
        's3': {
            'url': 'http://172.16.52.151:5000'
        }
    }

    def setUp(self):
        super(TestConfigTempest, self).setUp()
        self.conf = self._get_conf("v2.0", "v3")

    def _mock_get_identity_v3_extensions(self):
        mock_function = mock.Mock(return_value=['FAKE-EXTENSIONS'])
        func2mock = 'config_tempest.api_discovery.get_identity_v3_extensions'
        self.useFixture(MonkeyPatch(func2mock, mock_function))

    def test_configure_boto(self):
        tool.configure_boto(self.conf, self.FAKE_SERVICES)
        expected_url = "http://172.16.52.151:5000"
        self.assertEqual(self.conf.get("boto", "ec2_url"), expected_url)
        self.assertEqual(self.conf.get("boto", "s3_url"), expected_url)

    def test_configure_horizon(self):
        mock_function = mock.Mock(return_value=True)
        self.useFixture(MonkeyPatch('urllib2.urlopen', mock_function))
        tool.configure_horizon(self.conf)
        self.assertEqual(self.conf.get('service_available', 'horizon'), "True")
        self.assertEqual(self.conf.get('dashboard', 'dashboard_url'),
                         "http://172.16.52.151/dashboard/")
        self.assertEqual(self.conf.get('dashboard', 'login_url'),
                         "http://172.16.52.151/dashboard/auth/login/")

    def test_discovered_services(self):
        self._mock_get_identity_v3_extensions()
        tool.configure_discovered_services(self.conf, self.FAKE_SERVICES)
        # check enabled services
        enabled_services = ["image", "volume", "compute", "network"]
        # iterating through tuples = (service_name, codename)
        for service in tool.SERVICE_NAMES.iteritems():
            if service[0] in enabled_services:
                enabled = "True"
            else:
                enabled = "False"
            self.assertEqual(self.conf.get("service_available", service[1]),
                             enabled)

        # check versions
        for service, versions in tool.SERVICE_VERSIONS.iteritems():
            section = service + '-feature-enabled'
            for version in versions:
                # only image v1 is expected to be False
                exp_support = str(not(service == "image" and version == "v1"))
                self.assertEqual(self.conf.get(section, 'api_' + version),
                                 exp_support)

        # check extensions
        for service, ext_key in tool.SERVICE_EXTENSION_KEY.iteritems():
            if service in self.FAKE_SERVICES:
                section = service + '-feature-enabled'
                if service == "identity":
                    exp_ext = ",FAKE-EXTENSIONS"
                else:
                    extensions = self.FAKE_SERVICES[service]['extensions']
                    exp_ext = ','.join(extensions)
                self.assertEqual(self.conf.get(section, 'api_extensions'),
                                 exp_ext)

    def test_discovered_services_volume_service_disabled(self):
        self.conf.set("services", "volume", "False")
        self._mock_get_identity_v3_extensions()
        tool.configure_discovered_services(self.conf, self.FAKE_SERVICES)
        self.assertFalse(self.conf.has_option("service_available", "cinder"))
        self.assertFalse(self.conf.has_option("volume-feature-enabled",
                                              "api_v1"))
        self.assertFalse(self.conf.has_option("volume-feature-enabled",
                                              "api_v2"))


class TestFlavors(BaseConfigTempestTest):
    """Flavors test class

    Tests for create_tempest_flavors and find_or_create_flavor methods.
    """

    CLIENT_MOCK = 'tempest.lib.services.compute.flavors_client.FlavorsClient'
    FLAVORS_LIST = [
        {"id": "Fakeid", "name": "Name"},
        {"id": "MyFakeID", "name": "MyID"}
    ]

    def setUp(self):
        super(TestFlavors, self).setUp()
        self.conf = self._get_conf("v2.0", "v3")
        self.client = self._get_clients(self.conf).flavors

    def _mock_create_tempest_flavor(self, mock_function):
        func2mock = 'config_tempest.config_tempest.find_or_create_flavor'
        self.useFixture(MonkeyPatch(func2mock, mock_function))
        tool.create_tempest_flavors(client=self.client,
                                    conf=self.conf,
                                    allow_creation=True)

    def _mock_find_or_create_flavor(self, return_value, func2mock, flavor_name,
                                    expected_resp, allow_creation=False,
                                    flavor_id=None):
        mock_function = mock.Mock(return_value=return_value)
        self.useFixture(MonkeyPatch(self.CLIENT_MOCK + func2mock,
                                    mock_function))
        resp = tool.find_or_create_flavor(self.client,
                                          flavor_id=flavor_id,
                                          flavor_name=flavor_name,
                                          allow_creation=allow_creation)
        self.assertEqual(resp, expected_resp)

    def test_create_tempest_flavors(self):
        mock_function = mock.Mock(return_value="FakeID")
        self._mock_create_tempest_flavor(mock_function)
        self.assertEqual(self.conf.get('compute', 'flavor_ref'), "FakeID")
        self.assertEqual(self.conf.get('compute', 'flavor_ref_alt'), "FakeID")
        calls = [mock.call(self.client, None, 'm1.nano', True, ram=64),
                 mock.call(self.client, None, 'm1.micro', True, ram=128)]
        mock_function.assert_has_calls(calls, any_order=True)

    def test_create_tempest_flavors_overwrite(self):
        mock_function = mock.Mock(return_value="FakeID")
        self.conf.set('compute', 'flavor_ref', "FAKE_ID")
        self.conf.set('compute', 'flavor_ref_alt', "FAKE_ID")
        self._mock_create_tempest_flavor(mock_function)
        calls = [mock.call(self.client, "FAKE_ID", 'm1.nano', True, ram=64),
                 mock.call(self.client, "FAKE_ID", 'm1.micro', True, ram=128)]
        mock_function.assert_has_calls(calls, any_order=True)

    def test_create_flavor_not_allowed(self):
        exc = Exception
        self.assertRaises(exc,
                          tool.find_or_create_flavor,
                          client=self.client,
                          flavor_id="id",
                          flavor_name="name",
                          allow_creation=False)

    def test_create_flavor(self):
        return_value = {"flavor": {"id": "MyFakeID", "name": "MyID"}}
        # mock list_flavors() to return empty list
        mock_function = mock.Mock(return_value={"flavors": []})
        self.useFixture(MonkeyPatch(self.CLIENT_MOCK + '.list_flavors',
                                    mock_function))
        self._mock_find_or_create_flavor(return_value=return_value,
                                         func2mock='.create_flavor',
                                         flavor_name="MyID",
                                         expected_resp="MyFakeID",
                                         allow_creation=True)

    def test_find_flavor_by_id(self):
        return_value = {"flavors": self.FLAVORS_LIST}
        self._mock_find_or_create_flavor(return_value=return_value,
                                         func2mock='.list_flavors',
                                         flavor_id="MyFakeID",
                                         flavor_name=None,
                                         expected_resp="MyFakeID")

    def test_find_flavor_by_name(self):
        return_value = {"flavors": self.FLAVORS_LIST}
        self._mock_find_or_create_flavor(return_value=return_value,
                                         func2mock='.list_flavors',
                                         flavor_name="MyID",
                                         expected_resp="MyFakeID")
