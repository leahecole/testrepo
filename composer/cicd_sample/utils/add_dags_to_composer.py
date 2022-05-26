# Copyright 2021 Google LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START composer_cicd_add_dags_to_composer_utility]
import argparse
import glob
import os
from shutil import copytree, ignore_patterns
import tempfile
from typing import List, Tuple

# Imports the Google Cloud client library
from google.cloud import storage


def _create_dags_list(dags_directory: str) -> Tuple[str, List[str]]:
    temp_dir = tempfile.mkdtemp()

    # ignore non-DAG Python files
    files_to_ignore = ignore_patterns("__init__.py", "*_test.py")

    # Copy everything but the ignored files to a temp directory
    copytree(dags_directory, f"{temp_dir}/", ignore=files_to_ignore, dirs_exist_ok=True)

    # The only Python files left in our temp directory are DAG files
    # so we can exclude all non Python files
    dags = glob.glob(f"{temp_dir}/*.py")
    return (temp_dir, dags)


def upload_dags_to_composer(dags_directory: str, bucket_name: str) -> None:
    temp_dir, dags = _create_dags_list(dags_directory)

    if len(dags) > 0:
        # Note - the GCS client library does not currently support batch requests on uploads
        # if you have a large number of files, consider using
        # the Python subprocess module to run gsutil -m cp -r on your dags
        # See https://cloud.google.com/storage/docs/gsutil/commands/cp for more info
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)

        for dag in dags:
            # Remove path to temp dir
            # if/else is a relative directory workaround for our tests
            current_directory = os.listdir()
            if "dags" in current_directory:
                dag = dag.replace(f"{temp_dir}/", "dags/")
            else:
                dag = dag.replace(f"{temp_dir}/", "../dags/")

            # Upload to your bucket
            blob = bucket.blob(dag)
            blob.upload_from_filename(dag)
            print(f"File {dag} uploaded to {bucket_name}/{dag}.")

    else:
        print("No DAGs to upload.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--dags_directory",
        help="Relative path to the source directory containing your DAGs",
    )
    parser.add_argument(
        "--dags_bucket",
        help="Name of the DAGs bucket of your Composer environment without the gs:// prefix",
    )

    args = parser.parse_args()

    upload_dags_to_composer(args.dags_directory, args.dags_bucket)
# [END composer_cicd_add_dags_to_composer_utility]
