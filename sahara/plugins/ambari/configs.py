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


from oslo_serialization import jsonutils
import six

from sahara.plugins.ambari import common
from sahara.plugins import provisioning
from sahara.swift import swift_helper
from sahara.utils import files


configs = {}
obj_configs = {}
cfg_process_map = {
    "ams-env": common.AMBARI_SERVICE,
    "ams-hbase-env": common.AMBARI_SERVICE,
    "ams-hbase-policy": common.AMBARI_SERVICE,
    "ams-hbase-security-site": common.AMBARI_SERVICE,
    "ams-hbase-site": common.AMBARI_SERVICE,
    "ams-site": common.AMBARI_SERVICE,
    "capacity-scheduler": common.YARN_SERVICE,
    "cluster-env": "general",
    "core-site": common.HDFS_SERVICE,
    "hadoop-env": common.HDFS_SERVICE,
    "hadoop-policy": common.HDFS_SERVICE,
    "hdfs-site": common.HDFS_SERVICE,
    "hive-env": common.HIVE_SERVICE,
    "hive-site": common.HIVE_SERVICE,
    "hiveserver2-site": common.HIVE_SERVICE,
    "oozie-env": common.OOZIE_SERVICE,
    "oozie-site": common.OOZIE_SERVICE,
    "mapred-env": common.YARN_SERVICE,
    "mapred-site": common.YARN_SERVICE,
    "ranger-hdfs-plugin-properties": common.RANGER_SERVICE,
    "tez-site": common.OOZIE_SERVICE,
    "yarn-env": common.YARN_SERVICE,
    "yarn-site": common.YARN_SERVICE,
    "zoo.cfg": common.ZOOKEEPER_SERVICE,
    "zookeeper-env": common.ZOOKEEPER_SERVICE
}


ng_confs = [
    "dfs.datanode.data.dir",
    "dtnode_heapsize",
    "mapreduce.map.java.opts",
    "mapreduce.map.memory.mb",
    "mapreduce.reduce.java.opts",
    "mapreduce.reduce.memory.mb",
    "mapreduce.task.io.sort.mb",
    "nodemanager_heapsize",
    "yarn.app.mapreduce.am.command-opts",
    "yarn.app.mapreduce.am.resource.mb",
    "yarn.nodemanager.resource.cpu-vcores",
    "yarn.nodemanager.resource.memory-mb",
    "yarn.scheduler.maximum-allocation-mb",
    "yarn.scheduler.minimum-allocation-mb"
]


hdp_repo_cfg = provisioning.Config(
    "HDP repo URL", "general", "cluster", priority=1, default_value="")
hdp_utils_repo_cfg = provisioning.Config(
    "HDP-UTILS repo URL", "general", "cluster", priority=1, default_value="")


def _get_service_name(service):
    return cfg_process_map.get(service, service)


def _get_config_group(group, param, plugin_version):
    for section, process in six.iteritems(cfg_process_map):
        if process == group and param in configs[plugin_version][section]:
            return section


def _get_param_scope(param):
    if param in ng_confs:
        return "node"
    else:
        return "cluster"


def load_configs(version):
    if obj_configs.get(version):
        return obj_configs[version]
    cfg_path = "plugins/ambari/resources/configs-%s.json" % version
    vanilla_cfg = jsonutils.loads(files.get_file_text(cfg_path))
    configs[version] = vanilla_cfg
    sahara_cfg = [hdp_repo_cfg, hdp_utils_repo_cfg]
    for service, confs in vanilla_cfg.items():
        for k, v in confs.items():
            sahara_cfg.append(provisioning.Config(
                k, _get_service_name(service), _get_param_scope(k),
                default_value=v))
    obj_configs[version] = sahara_cfg
    return sahara_cfg


def _get_config_value(cluster, key):
    return cluster.cluster_configs.get("general", {}).get(key.name,
                                                          key.default_value)


def get_hdp_repo_url(cluster):
    return _get_config_value(cluster, hdp_repo_cfg)


def get_hdp_utils_repo_url(cluster):
    return _get_config_value(cluster, hdp_utils_repo_cfg)


def _serialize_ambari_configs(configs):
    return list(map(lambda x: {x: configs[x]}, configs))


def _create_ambari_configs(sahara_configs, plugin_version):
    configs = {}
    for service, params in six.iteritems(sahara_configs):
        for k, v in six.iteritems(params):
            group = _get_config_group(service, k, plugin_version)
            configs.setdefault(group, {})
            configs[group].update({k: v})
    return configs


def _make_paths(dirs, suffix):
    return ",".join([d + suffix for d in dirs])


def get_ng_params(node_group):
    configs = _create_ambari_configs(node_group.node_configs,
                                     node_group.cluster.hadoop_version)
    storage_paths = node_group.storage_paths()
    configs.setdefault("hdfs-site", {})
    configs["hdfs-site"]["dfs.datanode.data.dir"] = _make_paths(
        storage_paths, "/hdfs/data")
    configs["hdfs-site"]["dfs.journalnode.edits.dir"] = _make_paths(
        storage_paths, "/hdfs/journalnode")
    configs["hdfs-site"]["dfs.namenode.checkpoint.dir"] = _make_paths(
        storage_paths, "/hdfs/namesecondary")
    configs["hdfs-site"]["dfs.namenode.name.dir"] = _make_paths(
        storage_paths, "/hdfs/namenode")
    configs.setdefault("yarn-site", {})
    configs["yarn-site"]["yarn.nodemanager.local-dirs"] = _make_paths(
        storage_paths, "/yarn/local")
    configs["yarn-site"]["yarn.nodemanager.log-dirs"] = _make_paths(
        storage_paths, "/yarn/log")
    configs["yarn-site"][
        "yarn.timeline-service.leveldb-timeline-store.path"] = _make_paths(
            storage_paths, "/yarn/timeline")

    return _serialize_ambari_configs(configs)


def get_cluster_params(cluster):
    configs = _create_ambari_configs(cluster.cluster_configs,
                                     cluster.hadoop_version)
    swift_configs = {x["name"]: x["value"]
                     for x in swift_helper.get_swift_configs()}
    configs.setdefault("core-site", {})
    configs["core-site"].update(swift_configs)
    return _serialize_ambari_configs(configs)
