
PROFILE_NAME=$1
BUCKET_NAME=$2

if [ -z "$PROFILE_NAME" -o -z "$BUCKET_NAME" ]; then
    echo "bash ./test.sh PROFILE_NAME BUCKET_NAME" >&2
    exit 1
fi

mkdir -p var/test/expected
for f in $(ls test/expected); do
    cat test/expected/$f | sed "s/BUCKET_NAME/$BUCKET_NAME/g" > var/test/expected/$f
done

mkdir -p var/test/src
for f in $(ls test/src); do
    cat test/src/$f | sed "s/BUCKET_NAME/$BUCKET_NAME/g" > var/test/src/$f
done

mkdir -p var/test/actual

# reset
aws --profile $PROFILE_NAME s3api delete-bucket-lifecycle --bucket $BUCKET_NAME
aws --profile $PROFILE_NAME s3api delete-bucket-tagging --bucket $BUCKET_NAME

sync-s3-bucket-configurations --profile $PROFILE_NAME get $BUCKET_NAME > var/test/actual/1.json
sync-s3-bucket-configurations --profile $PROFILE_NAME get $BUCKET_NAME --lifecycle > var/test/actual/2.json
sync-s3-bucket-configurations --profile $PROFILE_NAME get $BUCKET_NAME --tag > var/test/actual/3.json

sync-s3-bucket-configurations --profile $PROFILE_NAME put var/test/src/4.json --tag
sync-s3-bucket-configurations --profile $PROFILE_NAME get $BUCKET_NAME > var/test/actual/4.json

diff -ur var/test/expected var/test/actual

