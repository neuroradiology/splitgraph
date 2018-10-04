from psycopg2._json import Json
from psycopg2.sql import SQL, Identifier

from splitgraph.constants import SPLITGRAPH_META_SCHEMA


def store_import_provenance(conn, mountpoint, image_hash, source_mountpoint, source_hash, tables,
                            table_aliases, table_queries):
    with conn.cursor() as cur:
        cur.execute(SQL("""UPDATE {}.snap_tree SET provenance_type = %s, provenance_data = %s WHERE
                            mountpoint = %s AND snap_id = %s""").format(Identifier(SPLITGRAPH_META_SCHEMA)),
                    ("IMPORT", Json({
                        'source': source_mountpoint,
                        'source_hash': source_hash,
                        'tables': tables,
                        'table_aliases': table_aliases,
                        'table_queries': table_queries}), mountpoint, image_hash))


def store_sql_provenance(conn, mountpoint, image_hash, sql):
    with conn.cursor() as cur:
        cur.execute(SQL("""UPDATE {}.snap_tree SET provenance_type = %s, provenance_data = %s WHERE
                            mountpoint = %s AND snap_id = %s""").format(Identifier(SPLITGRAPH_META_SCHEMA)),
                    ('SQL', Json(sql), mountpoint, image_hash))


def store_mount_provenance(conn, mountpoint, image_hash):
    # We don't store the details of images that come from an sg MOUNT command since those are assumed to be based
    # on an inaccessible db
    with conn.cursor() as cur:
        cur.execute(SQL("""UPDATE {}.snap_tree SET provenance_type = %s, provenance_data = %s WHERE
                            mountpoint = %s AND snap_id = %s""").format(Identifier(SPLITGRAPH_META_SCHEMA)),
                    ('MOUNT', None, mountpoint, image_hash))


def store_from_provenance(conn, mountpoint, image_hash, source):
    with conn.cursor() as cur:
        cur.execute(SQL("""UPDATE {}.snap_tree SET provenance_type = %s, provenance_data = %s WHERE
                            mountpoint = %s AND snap_id = %s""").format(Identifier(SPLITGRAPH_META_SCHEMA)),
                    ('FROM', Json(source), mountpoint, image_hash))