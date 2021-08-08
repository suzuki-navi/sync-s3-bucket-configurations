# sync-s3-bucket-configurations

Tool to retrieve and update S3 configurations.

## Installation

    $ pip install git+https://github.com/suzuki-navi/sync-s3-bucket-configurations

## Usage

    $ sync-s3-bucket-configurations [--profile PROFILE_NAME] get [BUCKET_NAME...] [CONFIG_TYPES...]
    $ sync-s3-bucket-configurations [--profile PROFILE_NAME] put JSON_FILE_PATH [CONFIG_TYPES...]

getコマンドは、バケット名を指定して、そのバケットについての設定値をJSONで標準出力します。
複数のバケット名も指定できます。バケット名を省略すると、すべてのS3バケットを出力します。

putコマンドは、JSONファイルを指定して、JSONに書かれている設定値が実際と異なる場合にバケットの設定を更新します。

JSONファイルのフォーマットはgetコマンドとputコマンドとで同一です。

CONFIG_TYPESは以下のいずれかを複数指定できます。省略時はすべて指定されたものとします。

    --lifecycle
    --tag

getコマンドでは、CONFIG_TYPESで指定された設定値のみを出力します。

putコマンドでは、CONFIG_TYPESで指定された設定値のみを更新します。
CONFIG_TYPESで指定されていてもJSONファイルに設定値が書かれていなければなにもしません。


## Development

    $ pip install -e .

## License

The gem is available as open source under the terms of the [MIT License](https://opensource.org/licenses/MIT).

