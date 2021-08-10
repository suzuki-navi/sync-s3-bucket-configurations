import json
import sys

import boto3
import botocore

def main():
    help_flag, profile, region, action, buckets, json_file, config_types, dry_run = parse_args()
    session = boto3_session(profile, region)
    s3_client = session.client("s3")
    s3_resource = session.resource("s3")

    if help_flag:
        output_help()
        return

    if len(buckets) == 0:
        buckets = list_buckets(s3_client)

    if action == "get":
        properties = {}
        for bucket in buckets:
            properties[bucket] = get_properties(s3_client, s3_resource, bucket, config_types)
        print(json.dumps(properties, sort_keys=True, indent=4, ensure_ascii=False))
    elif action == "put":
        if not json_file and not sys.stdin.isatty():
            properties = json.load(sys.stdin)
        else:
            if not json_file:
                raise Exception(f"json file not specified")
            with open(json_file) as f:
                properties = json.load(f)
        if dry_run:
            print("dry run")
        for bucket, prop in properties.items():
            put_properties(s3_client, s3_resource, bucket, prop, config_types, dry_run)

def parse_args():
    help_flag = False
    profile = None
    region = None
    action = None
    buckets = []
    json_file = None
    config_types = []
    dry_run = False
    argCount = len(sys.argv)
    i = 1
    while i < argCount:
        a = sys.argv[i]
        if a == "--help":
            help_flag = True
        elif a == "--profile":
            if i + 1 >= argCount:
                raise Exception(f"{a} needs parameter")
            i += 1
            profile = sys.argv[i]
        elif a == "--region":
            if i + 1 >= argCount:
                raise Exception(f"{a} needs parameter")
            i += 1
            region = sys.argv[i]
        elif a == "--lifecycle":
            config_types.append("lifecycle")
        elif a == "--tag":
            config_types.append("tag")
        elif a == "--versioning":
            config_types.append("versioning")
        elif a == "--metrics":
            config_types.append("metrics")
        elif a == "--analytics":
            config_types.append("analytics")
        elif a == "--inventory":
            config_types.append("inventory")
        elif a == "--logging":
            config_types.append("logging")
        elif a == "--all":
            config_types.append("all")
        elif a == "--dry-run":
            dry_run = True
        elif not action:
            if a == "get":
                action = a
            elif a == "put":
                action = a
            else:
                raise Exception(f"Unknown action: {a}")
        elif action == "get":
            buckets.append(a)
        elif action == "put":
            if not json_file:
                json_file = a
            else:
                raise Exception("Unknown parameter: {a}")
        i += 1

    if not action:
        help_flag = True

    if len(config_types) == 0 and action == "put":
        raise Exception("CONFIG_TYPES not specified")

    if len(config_types) == 0 and action == "get" or "all" in config_types:
        config_types = ["lifecycle", "tag", "versioning", "metrics", "analytics", "inventory", "logging"]

    return [help_flag, profile, region, action, buckets, json_file, config_types, dry_run]

def output_help():
    print("""Tool to retrieve and update S3 configurations

Usage:
    $ sync-s3-bucket-configurations [--profile PROFILE_NAME] get [BUCKET_NAME...] [CONFIG_TYPES...]
    $ sync-s3-bucket-configurations [--profile PROFILE_NAME] put JSON_FILE_PATH [CONFIG_TYPES...] [--dry-run]

CONFIG_TYPES:
    --lifecycle
    --tag
    --versioning
    --metrics
    --analytics
    --inventory
    --logging
    --all
""")

def boto3_session(profile, region):
    session = boto3.session.Session(profile_name = profile, region_name = region)
    return session

def list_buckets(s3_client):
    result = []
    res = s3_client.list_buckets()
    for elem in res['Buckets']:
        result.append(elem['Name'])
    return result

def get_properties(s3_client, s3_resource, bucket, config_types):
    prop = {}
    for c in config_types:
        if c == "lifecycle":
            prop[c] = get_lifecycle(s3_resource, bucket);
        elif c == "tag":
            prop[c] = get_tag(s3_resource, bucket);
        elif c == "versioning":
            prop[c] = get_versioning(s3_resource, bucket);
        elif c == "metrics":
            prop[c] = get_metrics(s3_client, bucket);
        elif c == "analytics":
            prop[c] = get_analytics(s3_client, bucket);
        elif c == "inventory":
            prop[c] = get_inventory(s3_client, bucket);
        elif c == "logging":
            prop[c] = get_logging(s3_client, bucket);
    return prop

def put_properties(s3_client, s3_resource, bucket, prop, config_types, dry_run):
    for c in config_types:
        if not c in prop:
            continue
        if c == "lifecycle":
            put_lifecycle(s3_resource, bucket, prop[c], dry_run)
        if c == "tag":
            put_tag(s3_resource, bucket, prop[c], dry_run)
        if c == "versioning":
            put_versioning(s3_resource, bucket, prop[c], dry_run)
        if c == "metrics":
            put_metrics(s3_client, bucket, prop[c], dry_run)
        if c == "analytics":
            put_analytics(s3_client, bucket, prop[c], dry_run)
        if c == "inventory":
            put_inventory(s3_client, bucket, prop[c], dry_run)
        if c == "logging":
            put_logging(s3_client, bucket, prop[c], dry_run)

def get_lifecycle(s3_resource, bucket):
    bucket_lifecycle = s3_resource.BucketLifecycleConfiguration(bucket)
    try:
        rules = bucket_lifecycle.rules

        # getするとPrefixがない場合があるのにputするときには必須なので、付けておく
        for rule in rules:
            if not "Prefix" in rule:
                rule["Prefix"] = ""

        return rules
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchLifecycleConfiguration":
            return []
        raise

def put_lifecycle(s3_resource, bucket, new_rules, dry_run):
    curr_rules = get_lifecycle(s3_resource, bucket)
    if new_rules == curr_rules:
        return
    print(f"update {bucket}'s lifecycle")
    if dry_run:
        return
    bucket_lifecycle = s3_resource.BucketLifecycleConfiguration(bucket)
    bucket_lifecycle.put(
        LifecycleConfiguration = {
            'Rules': new_rules,
        }
    )

def get_tag(s3_resource, bucket):
    tagging = s3_resource.BucketTagging(bucket)
    try:
        tag_set = tag_list_to_dict(tagging.tag_set)
        return tag_set
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchTagSet":
            return {}
        raise

def put_tag(s3_resource, bucket, new_tag_set, dry_run):
    curr_tag_set = get_tag(s3_resource, bucket)
    if new_tag_set == curr_tag_set:
        return
    print(f"update {bucket}'s tag")
    if dry_run:
        return
    tagging = s3_resource.BucketTagging(bucket)
    tagging.put(
        Tagging = {
            'TagSet': tag_dict_to_list(new_tag_set),
        }
    )

def get_versioning(s3_resource, bucket):
    handler = s3_resource.BucketVersioning(bucket)
    mfa_delete = handler.mfa_delete
    status = handler.status
    if not mfa_delete:
        mfa_delete = 'Disabled'
    if not status:
        status = 'Disabled'
    return {
        'MFADelete': mfa_delete,
        'Status': status,
    }

def put_versioning(s3_resource, bucket, new_config, dry_run):
    curr_config = get_versioning(s3_resource, bucket)
    if new_config == curr_config:
        return
    print(f"update {bucket}'s versioning")
    if dry_run:
        return
    handler = s3_resource.BucketVersioning(bucket)
    handler.put(
        VersioningConfiguration = new_config,
    )

def get_metrics(s3_client, bucket):
    res = s3_client.list_bucket_metrics_configurations(
        Bucket = bucket,
    )
    metrics = []
    while True:
        if 'MetricsConfigurationList' in res:
            for elem in res['MetricsConfigurationList']:
                metrics.append(elem)
        if not 'ContinuationToken' in res:
            break
        res = s3_client.list_bucket_metrics_configurations(
            Bucket = bucket,
            ContinuationToken = res['ContinuationToken']
        )
    return metrics

def put_metrics(s3_client, bucket, new_metrics, dry_run):
    curr_metrics = get_metrics(s3_client, bucket)
    curr_metrics = configurations_to_dict(curr_metrics)
    new_metrics = configurations_to_dict(new_metrics)
    if new_metrics == curr_metrics:
        return
    print(f"update {bucket}'s metrics")
    if dry_run:
        return
    for id, elem in new_metrics.items():
        if id in curr_metrics and elem == curr_metrics[id]:
            continue
        s3_client.put_bucket_metrics_configuration(
            Bucket = bucket,
            Id = id,
            MetricsConfiguration = elem,
        )
    for id, elem in curr_metrics.items():
        if id in new_metrics:
            continue
        s3_client.delete_bucket_metrics_configuration(
            Bucket = bucket,
            Id = id,
        )

def get_analytics(s3_client, bucket):
    res = s3_client.list_bucket_analytics_configurations(
        Bucket = bucket,
    )
    analytics = []
    while True:
        if 'AnalyticsConfigurationList' in res:
            for elem in res['AnalyticsConfigurationList']:
                analytics.append(elem)
        if not 'ContinuationToken' in res:
            break
        res = s3_client.list_bucket_analytics_configurations(
            Bucket = bucket,
            ContinuationToken = res['ContinuationToken']
        )
    return analytics

def put_analytics(s3_client, bucket, new_analytics, dry_run):
    curr_analytics = get_analytics(s3_client, bucket)
    curr_analytics = configurations_to_dict(curr_analytics)
    new_analytics = configurations_to_dict(new_analytics)
    if new_analytics == curr_analytics:
        return
    print(f"update {bucket}'s analytics")
    if dry_run:
        return
    for id, elem in new_analytics.items():
        if id in curr_analytics and elem == curr_analytics[id]:
            continue
        s3_client.put_bucket_analytics_configuration(
            Bucket = bucket,
            Id = id,
            AnalyticsConfiguration = elem,
        )
    for id, elem in curr_analytics.items():
        if id in new_analytics:
            continue
        s3_client.delete_bucket_analytics_configuration(
            Bucket = bucket,
            Id = id,
        )

def get_inventory(s3_client, bucket):
    res = s3_client.list_bucket_inventory_configurations(
        Bucket = bucket,
    )
    inventory = []
    while True:
        if 'InventoryConfigurationList' in res:
            for elem in res['InventoryConfigurationList']:
                inventory.append(elem)
        if not 'ContinuationToken' in res:
            break
        res = s3_client.list_bucket_inventory_configurations(
            Bucket = bucket,
            ContinuationToken = res['ContinuationToken']
        )
    return inventory

def put_inventory(s3_client, bucket, new_inventory, dry_run):
    curr_inventory = get_inventory(s3_client, bucket)
    curr_inventory = configurations_list_to_dict(curr_inventory)
    new_inventory = configurations_list_to_dict(new_inventory)
    if new_inventory == curr_inventory:
        return
    print(f"update {bucket}'s inventory")
    if dry_run:
        return
    for id, elem in new_inventory.items():
        if id in curr_inventory and elem == curr_inventory[id]:
            continue
        s3_client.put_bucket_inventory_configuration(
            Bucket = bucket,
            Id = id,
            InventoryConfiguration = elem,
        )
    for id, elem in curr_inventory.items():
        if id in new_inventory:
            continue
        s3_client.delete_bucket_inventory_configuration(
            Bucket = bucket,
            Id = id,
        )

def get_logging(s3_client, bucket):
    res = s3_client.get_bucket_logging(
        Bucket = bucket,
    )
    if 'LoggingEnabled' in res:
        return res['LoggingEnabled']
    else:
        return {}

def put_logging(s3_client, bucket, new_config, dry_run):
    curr_config = get_logging(s3_client, bucket)
    if new_config == curr_config:
        return
    print(f"update {bucket}'s analytics")
    if dry_run:
        return
    if new_config == {}:
        s3_client.put_bucket_logging(
            Bucket = bucket,
            BucketLoggingStatus = {},
        )
    else:
        s3_client.put_bucket_logging(
            Bucket = bucket,
            BucketLoggingStatus = {
                'LoggingEnabled': new_config,
            },
        )

################################################################################
# boto3から得られるJSONを扱いやすい形式に変換するツール
################################################################################

def configurations_list_to_dict(config_list):
    result = {}
    for elem in config_list:
        result[elem['Id']] = elem
    return result

def tag_list_to_dict(tag_list):
    result = {}
    for elem in tag_list:
        result[elem['Key']] = elem['Value']
    return result

def tag_dict_to_list(tag_dict):
    result = []
    for key, value in tag_dict.items():
        result.append({'Key': key, 'Value': value})
    return result

