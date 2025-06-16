from logzero import logger
from app.settings import (CONNECTION_TIMEOUT, DRY_RUN, PRESENTATION_CONNECTION_STRING, PROTAGONIST_CONNECTION_STRING, ASSET_SPLIT_SIZE)
from app.database import connect_to_postgres, get_connection_config

import os


def update_manifest_column():
    presentation_connection_info = get_connection_config(connection_string=PRESENTATION_CONNECTION_STRING)
    protagonist_connection_info = get_connection_config(connection_string=PROTAGONIST_CONNECTION_STRING)

    pres_conn = connect_to_postgres(connection_info=presentation_connection_info, connection_timeout=CONNECTION_TIMEOUT)
    protag_conn = connect_to_postgres(connection_info=protagonist_connection_info, connection_timeout=CONNECTION_TIMEOUT)

    __run_sql(pres_conn, protag_conn)


def __get_assets_to_update(conn):
    cur = conn.cursor()

    cur.execute(f"""
                SELECT asset_id,manifest_id 
                FROM canvas_paintings 
                WHERE asset_id IS NOT NULL;
            """)

    return cur.fetchall()


def generate_split_asset_string(split_assets):
    asset_string = ""

    for asset in split_assets:
        asset_string += f"('{asset[0]}', '{asset[1]}')," + os.linesep
    return asset_string[:-1 - len(os.linesep)]


def __update_protagonist(assets: [], conn):
    cur = conn.cursor()

    logger.info(f"updating {len(assets)} assets with a manifest in protagonist")

    for i in range(0, len(assets), ASSET_SPLIT_SIZE):
        split_assets = assets[i:i + ASSET_SPLIT_SIZE]

        asset_string = generate_split_asset_string(split_assets)

        cur.execute(f"""
                        UPDATE "Images"
                        SET "Manifests" = ARRAY(SELECT DISTINCT UNNEST("Manifests" || t.new_manifest))
                        FROM (
                                VALUES {asset_string}
                             ) AS t(id, new_manifest) WHERE "Id" = t.id;
                    """)



def __run_sql(pres_conn, protag_conn):
    assets = __get_assets_to_update(pres_conn)

    __update_protagonist(assets, protag_conn)

    if DRY_RUN:
        logger.info(f"DRY RUN ENABLED.  Changes have not been committed to the database.")
    else:
        pres_conn.commit()

if __name__ == '__main__':
    update_manifest_column()

