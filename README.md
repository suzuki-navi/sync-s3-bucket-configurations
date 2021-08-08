# sync-s3-bucket-configurations

Tool to retrieve and update S3 configurations.

## Installation

    $ pip install git+https://github.com/suzuki-navi/sync-s3-bucket-configurations

## Usage

    $ sync-s3-bucket-configurations [--profile PROFILE_NAME] get [BUCKET_NAME]
    $ sync-s3-bucket-configurations [--profile PROFILE_NAME] put JSON_FILE_PATH

getコマンドは、バケット名を指定して、そのバケットについての設定値をJSONで標準出力します。
複数のバケット名も指定できます。バケット名を省略すると、すべてのS3バケットを出力します。

putコマンドは、JSONファイルを指定して、JSONに書かれている設定値が実際と異なる場合にバケットの設定を更新します。

JSONファイルのフォーマットはgetコマンドとputコマンドとで同一です。


## Development

    $ pip install -e .

## License

The gem is available as open source under the terms of the [MIT License](https://opensource.org/licenses/MIT).

