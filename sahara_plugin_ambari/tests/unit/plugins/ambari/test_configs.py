# Copyright (c) 2015 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import collections
from unittest import mock


from sahara_plugin_ambari.plugins.ambari import configs
from sahara_plugin_ambari.tests.unit import base


class AmbariConfigsTestCase(base.SaharaTestCase):
    def setUp(self):
        super(AmbariConfigsTestCase, self).setUp()
        configs.load_configs("2.3")
        self.ng = mock.Mock()
        self.ng.node_configs = {}
        self.ng.cluster = mock.Mock()
        self.ng.cluster.hadoop_version = "2.3"
        self.instance = mock.Mock()
        self.instance.node_group = self.ng
        self.instance.storage_paths = mock.Mock()
        self.instance.storage_paths.return_value = ["/data1", "/data2"]

    def assertConfigEqual(self, expected, actual):
        self.assertEqual(len(expected), len(actual))
        cnt_ex = collections.Counter()
        cnt_act = collections.Counter()
        for i, ex in enumerate(expected):
            for j, act in enumerate(actual):
                if ex == act:
                    cnt_ex[i] += 1
                    cnt_act[j] += 1
        self.assertEqual(len(expected), len(cnt_ex))
        self.assertEqual(len(actual), len(cnt_act))

    def test_get_service_to_configs_map(self):
        self.assertIsNone(configs.SERVICES_TO_CONFIGS_MAP)
        configs_map = configs.get_service_to_configs_map()
        configs_expected = {
            'ZooKeeper': ['zoo.cfg', 'zookeeper-env'],
            'Knox': ['knox-env', 'ranger-knox-plugin-properties',
                     'gateway-site'],
            'YARN': ['yarn-site', 'mapred-env', 'yarn-env',
                     'capacity-scheduler', 'mapred-site'],
            'general': ['cluster-env'], 'Flume': ['flume-env'],
            'Ambari': ['ams-hbase-policy', 'ams-site', 'ams-env',
                       'ams-hbase-site', 'ams-hbase-env',
                       'ams-hbase-security-site'],
            'HDFS': ['core-site', 'ranger-hdfs-plugin-properties',
                     'hadoop-policy', 'hdfs-site', 'hadoop-env'],
            'Ranger': ['ranger-env', 'admin-properties',
                       'usersync-properties', 'ranger-site'],
            'Spark': ['spark-defaults', 'spark-env'],
            'Hive': ['hive-env', 'hive-site', 'hiveserver2-site',
                     'ranger-hive-plugin-properties'],
            'Storm': ['ranger-storm-plugin-properties', 'storm-site',
                      'storm-env'],
            'Oozie': ['oozie-env', 'oozie-site', 'tez-site'],
            'HBase': ['ranger-hbase-plugin-properties', 'hbase-env',
                      'hbase-site', 'hbase-policy'],
            'Sqoop': ['sqoop-env'], 'Kafka': ['kafka-broker', 'kafka-env'],
            'Falcon': ['falcon-startup.properties',
                       'falcon-runtime.properties', 'falcon-env']
        }
        for (key, item) in configs_map.items():
            item.sort()
        for (key, item) in configs_expected.items():
            item.sort()
        self.assertEqual(configs_map, configs_expected)
        self.assertIsNotNone(configs.SERVICES_TO_CONFIGS_MAP)

    def test_get_instance_params_default(self):
        instance_configs = configs.get_instance_params(self.instance)
        expected = [
            {
                "hdfs-site": {
                    "dfs.datanode.data.dir":
                    "/data1/hdfs/data,/data2/hdfs/data",
                    "dfs.journalnode.edits.dir":
                    "/data1/hdfs/journalnode,/data2/hdfs/journalnode",
                    "dfs.namenode.checkpoint.dir":
                    "/data1/hdfs/namesecondary,/data2/hdfs/namesecondary",
                    "dfs.namenode.name.dir":
                    "/data1/hdfs/namenode,/data2/hdfs/namenode"
                }
            },
            {
                "yarn-site": {
                    "yarn.nodemanager.local-dirs":
                    "/data1/yarn/local,/data2/yarn/local",
                    "yarn.nodemanager.log-dirs":
                    "/data1/yarn/log,/data2/yarn/log",
                    "yarn.timeline-service.leveldb-timeline-store.path":
                    "/data1/yarn/timeline,/data2/yarn/timeline"
                }
            },
            {
                "oozie-site": {
                    "oozie.service.AuthorizationService.security.enabled":
                    "false"
                }
            }
        ]
        self.assertConfigEqual(expected, instance_configs)

    def test_get_instance_params(self):
        self.ng.node_configs = {
            "YARN": {
                "mapreduce.map.java.opts": "-Dk=v",
                "yarn.scheduler.minimum-allocation-mb": "256"
            }
        }
        instance_configs = configs.get_instance_params(self.instance)
        expected = [
            {
                "hdfs-site": {
                    "dfs.datanode.data.dir":
                    "/data1/hdfs/data,/data2/hdfs/data",
                    "dfs.journalnode.edits.dir":
                    "/data1/hdfs/journalnode,/data2/hdfs/journalnode",
                    "dfs.namenode.checkpoint.dir":
                    "/data1/hdfs/namesecondary,/data2/hdfs/namesecondary",
                    "dfs.namenode.name.dir":
                    "/data1/hdfs/namenode,/data2/hdfs/namenode"
                }
            },
            {
                "mapred-site": {
                    "mapreduce.map.java.opts": "-Dk=v"
                }
            },
            {
                "yarn-site": {
                    "yarn.nodemanager.local-dirs":
                    "/data1/yarn/local,/data2/yarn/local",
                    "yarn.nodemanager.log-dirs":
                    "/data1/yarn/log,/data2/yarn/log",
                    "yarn.scheduler.minimum-allocation-mb": "256",
                    "yarn.timeline-service.leveldb-timeline-store.path":
                    "/data1/yarn/timeline,/data2/yarn/timeline"
                }
            },
            {
                "oozie-site": {
                    "oozie.service.AuthorizationService.security.enabled":
                    "false"
                }
            }
        ]
        self.assertConfigEqual(expected, instance_configs)
