import base64

from logzero import logger
from app.settings import (CONNECTION_TIMEOUT, DRY_RUN, PRESENTATION_CONNECTION_STRING, PROTAGONIST_BASE_URL,
                          ASSET_SPLIT_SIZE, DLCS_API_AUTH, EXIT_ON_ERROR)
from app.database import connect_to_postgres, get_connection_config

import os
import collections
import requests
import urllib.parse
import sys


def update_manifest_column():
    presentation_connection_info = get_connection_config(connection_string=PRESENTATION_CONNECTION_STRING)

    pres_conn = connect_to_postgres(connection_info=presentation_connection_info, connection_timeout=CONNECTION_TIMEOUT)

    __run_sql(pres_conn)


def __get_assets_to_update(conn) -> collections.defaultdict[str, list]:
    cur = conn.cursor()

    # todo: high water mark

    cur.execute(f"""
                SELECT asset_id,manifest_id 
                FROM canvas_paintings 
                WHERE asset_id IS NOT NULL
                ORDER BY modified;
            """)

    assets = cur.fetchall()
    manifest_dictionary = collections.defaultdict(list)

    for asset in assets:
        manifest_dictionary[asset[1]].append(asset[0])

    return manifest_dictionary


def generate_split_asset_string(split_assets):
    asset_string = ""

    for asset in split_assets:
        asset_string += f"('{asset[0]}', '{asset[1]}')," + os.linesep
    return asset_string[:-1 - len(os.linesep)]


def __update_protagonist(manifests: collections.defaultdict[str, list]):
    logger.info(f"updating {len(manifests)} manifests with a manifest in protagonist")

    for manifest in manifests:
        values = manifests[manifest]
        for i in range(0, len(values), ASSET_SPLIT_SIZE):
            split_assets = values[i: i + ASSET_SPLIT_SIZE]

            customer_id = split_assets[0].split('/')[0]

            protagonist_url = __build_url(PROTAGONIST_BASE_URL, f'/customers/{customer_id}/allImages')

            asset_ids = []
            for split_asset in split_assets:
                asset_id = {'id': split_asset}
                asset_ids.append(asset_id)

            # todo pause 300ms on every 10th manifest

            member_data = {
                'member': asset_ids,
                'field': 'manifests',
                'value': [manifest],
                'operation': 'add'
            }

            if not DRY_RUN:
                response = requests.patch(protagonist_url,
                                  json=member_data,
                                  headers={
                    "Authorization": f"Basic {DLCS_API_AUTH}"})

                if not response.ok:
                    logger.error(f"response does not indicate success for manifest {manifest} - {response.text}")
                    if EXIT_ON_ERROR:
                        sys.exit()

        # todo: add some extra logging at the end


def __build_url(base_url, path):
    url_parts = list(urllib.parse.urlparse(base_url))
    url_parts[2] = path
    return urllib.parse.urlunparse(url_parts)


def __run_sql(pres_conn):
    manifests = __get_assets_to_update(pres_conn)

    __update_protagonist(manifests)


if __name__ == '__main__':
    update_manifest_column()
