import json
import sys

import boto3
import botocore

def main():
    help_flag, profile, region, action, buckets, json_file, config_types = parse_args()
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
            properties[bucket] = get_properties(s3_resource, bucket, config_types)
        print(json.dumps(properties, sort_keys=True, indent=4, ensure_ascii=False))
    elif action == "put":
        if not json_file and not sys.stdin.isatty():
            properties = json.load(sys.stdin)
        else:
            if not json_file:
                raise Exception(f"json file not specified")
            with open(json_file) as f:
                properties = json.load(f)
        for bucket, prop in properties.items():
            put_properties(s3_resource, bucket, prop, config_types)

def parse_args():
    help_flag = False
    profile = None
    region = None
    action = None
    buckets = []
    json_file = None
    config_types = []
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

    if not action and not help_flag:
        raise Exception(f"Action not specified")

    if len(config_types) == 0:
        config_types = ["lifecycle", "tag", "versioning"]

    return [help_flag, profile, region, action, buckets, json_file, config_types]

def output_help():
    print("""Tool to retrieve and update S3 configurations

Usage:
    $ sync-s3-bucket-configurations [--profile PROFILE_NAME] get [BUCKET_NAME...] [CONFIG_TYPES...]
    $ sync-s3-bucket-configurations [--profile PROFILE_NAME] put JSON_FILE_PATH [CONFIG_TYPES...]

CONFIG_TYPES:
    --lifecycle
    --tag
    --versioning
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

def get_properties(s3_resource, bucket, config_types):
    prop = {}
    for c in config_types:
        if c == "lifecycle":
            prop[c] = get_lifecycle(s3_resource, bucket);
        elif c == "tag":
            prop[c] = get_tag(s3_resource, bucket);
        elif c == "versioning":
            prop[c] = get_versioning(s3_resource, bucket);
    return prop

def put_properties(s3_resource, bucket, prop, config_types):
    for c in config_types:
        if c in prop:
            if c == "lifecycle":
                put_lifecycle(s3_resource, bucket, prop[c])
            if c == "tag":
                put_tag(s3_resource, bucket, prop[c])
            if c == "versioning":
                put_versioning(s3_resource, bucket, prop[c])

def get_lifecycle(s3_resource, bucket):
    bucket_lifecycle = s3_resource.BucketLifecycle(bucket)
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

def put_lifecycle(s3_resource, bucket, new_rules):
    curr_rules = get_lifecycle(s3_resource, bucket)
    if new_rules == curr_rules:
        return
    print(f"update {bucket}'s lifecycle")
    bucket_lifecycle = s3_resource.BucketLifecycle(bucket)
    bucket_lifecycle.put(
        LifecycleConfiguration = {
            'Rules': new_rules,
        }
    )

def get_tag(s3_resource, bucket):
    tagging = s3_resource.BucketTagging(bucket)
    try:
        tag_set = tagging.tag_set
        return tag_set
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchTagSet":
            return []
        raise

def put_tag(s3_resource, bucket, new_tag_set):
    curr_tag_set = get_tag(s3_resource, bucket)
    if new_tag_set == curr_tag_set:
        return
    print(f"update {bucket}'s tag")
    tagging = s3_resource.BucketTagging(bucket)
    tagging.put(
        Tagging = {
            'TagSet': new_tag_set,
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

def put_versioning(s3_resource, bucket, new_config):
    curr_config = get_versioning(s3_resource, bucket)
    if new_config == curr_config:
        return
    print(f"update {bucket}'s versioning")
    handler = s3_resource.BucketVersioning(bucket)
    handler.put(
        VersioningConfiguration = new_config,
    )

