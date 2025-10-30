from logzero import logger
from app.settings import (CONNECTION_TIMEOUT, DRY_RUN, PRESENTATION_CONNECTION_STRING, PROTAGONIST_BASE_URL,
                          ASSET_SPLIT_SIZE, DLCS_API_AUTH, EXIT_ON_ERROR, HIGH_WATER_MARK)
from app.database import connect_to_postgres, get_connection_config

import os
import collections
import requests
import urllib.parse
import time


def GetCustomers(conn):
    cur = conn.cursor()

    cur.execute(f"""
                    SELECT DISTINCT ON (customer_id)
                        customer_id
                    FROM canvas_paintings;
                """)

    customers = cur.fetchall()
    customer_list = []

    for customer in customers:
        customer_list.append(customer[0])
    logger.info(f"found the following customers to update: {customer_list}")

    return customer_list


def update_manifest_column():
    presentation_connection_info = get_connection_config(connection_string=PRESENTATION_CONNECTION_STRING)

    pres_conn = connect_to_postgres(connection_info=presentation_connection_info, connection_timeout=CONNECTION_TIMEOUT)

    _run_sql(pres_conn)


def _get_assets_to_update(conn, customer: int) -> collections.defaultdict[str, (list, str)]:
    cur = conn.cursor()

    cur.execute(f"""
                SELECT asset_id,manifest_id,modified
                FROM canvas_paintings 
                WHERE asset_id IS NOT NULL
                AND modified > '{HIGH_WATER_MARK}'
                AND customer_id = {customer}
                ORDER BY modified;
            """)

    assets = cur.fetchall()
    # creates a defaultdict[str, (list, str)] - key = manifest_id, value = ([asset_id], modified)
    # defaultdict requires something "callable", which a tuple isn't, so calling through a lambda allows this to happen
    manifest_dictionary = collections.defaultdict(lambda: ([], ''))

    for asset in assets:
        if asset[1] in manifest_dictionary:
            value = manifest_dictionary[asset[1]]
            value[0].append(asset[0])
            manifest_dictionary[asset[1]] = value
        else:
            manifest_dictionary[asset[1]] = ([asset[0]], asset[2])

    return manifest_dictionary


def generate_split_asset_string(split_assets):
    asset_string = ""

    for asset in split_assets:
        asset_string += f"('{asset[0]}', '{asset[1]}')," + os.linesep
    return asset_string[:-1 - len(os.linesep)]


def _update_protagonist(manifests: collections.defaultdict[str, (list, str)]):
    logger.info(f"updating {len(manifests)} manifests from presentation in protagonist")

    if DRY_RUN:
        logger.info("running in dry run mode, manifests will not actually be updated")

    for iteration, manifest in enumerate(manifests):
        assets_and_modified_date = manifests[manifest]
        just_assets = assets_and_modified_date[0]
        for i in range(0, len(just_assets), ASSET_SPLIT_SIZE):
            # get assets between i and i + ASSET_SPLIT_SIZE
            split_assets = just_assets[i: i + ASSET_SPLIT_SIZE]

            # grabs the customer id from the first asset
            customer_id = split_assets[0].split('/')[0]

            protagonist_url = _build_url(PROTAGONIST_BASE_URL, f'/customers/{customer_id}/allImages')

            asset_ids = []
            for split_asset in split_assets:
                asset_id = {'id': split_asset}
                asset_ids.append(asset_id)

            # pause 300ms on every 10th manifest to allow API to catch up
            if iteration % 10 == 0 and iteration != 0:
                time.sleep(0.3)

            member_data = {
                'member': asset_ids,
                'field': 'manifests',
                'value': [manifest],
                'operation': 'add'
            }

            logger.debug(f"updating manifest {manifest} with assets {split_assets} with a modified date of {assets_and_modified_date[1]}")

            if not DRY_RUN:
                response = requests.patch(protagonist_url,
                                          json=member_data,
                                          headers={
                                              "Authorization": f"Basic {DLCS_API_AUTH}"})

                if not response.ok:
                    logger.error(f"response does not indicate success for manifest {manifest} - {response.text}, with a modified date {assets_and_modified_date[1]}")
                    if EXIT_ON_ERROR:
                        exit()
    logger.info(f"updated {len(manifests)} manifests")


def _build_url(base_url, path):
    url_parts = list(urllib.parse.urlparse(base_url))
    url_parts[2] = path
    return urllib.parse.urlunparse(url_parts)


def _run_sql(pres_conn):

    customers = GetCustomers(pres_conn)

    for customer in customers:
        manifests = _get_assets_to_update(pres_conn, customer)

        _update_protagonist(manifests)


if __name__ == '__main__':
    update_manifest_column()
