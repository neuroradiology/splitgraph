import re

from splitgraph.commands.misc import make_conn
from splitgraph.commands.object_loading import download_objects, upload_objects
from splitgraph.constants import SPLITGRAPH_META_SCHEMA, SplitGraphException, _log
from splitgraph.meta_handler import get_all_snap_parents, add_new_snap_id, get_remote_for, ensure_metadata_schema, \
    register_objects, set_head, add_remote, register_object_locations, get_external_object_locations


def _get_required_snaps_objects(conn, remote_conn, local_mountpoint, remote_mountpoint):
    local_snap_parents = {snap_id: parent_id for snap_id, parent_id, _, _ in get_all_snap_parents(conn, local_mountpoint)}
    remote_snap_parents = {snap_id: (parent_id, created, comment) for snap_id, parent_id, created, comment in
                           get_all_snap_parents(remote_conn, remote_mountpoint)}

    # We assume here that none of the remote snapshot IDs have changed (are immutable) since otherwise the remote
    # would have created a new snapshot.
    snaps_to_fetch = [s for s in remote_snap_parents if s not in local_snap_parents]
    object_meta = []
    for snap_id in snaps_to_fetch:
        # This is not batched but there shouldn't be that many entries here anyway.
        remote_parent, remote_created, remote_comment = remote_snap_parents[snap_id]
        add_new_snap_id(conn, local_mountpoint, remote_parent, snap_id, remote_created, remote_comment)
        # Get the meta for all objects we'll need to fetch.
        with remote_conn.cursor() as cur:
            cur.execute("""SELECT snap_id, table_name, object_id, format from %s.tables 
                           WHERE mountpoint = %%s AND snap_id = %%s"""
                        % SPLITGRAPH_META_SCHEMA, (remote_mountpoint, snap_id))
            object_meta.extend(cur.fetchall())

    distinct_objects = list(set(o[2] for o in object_meta))
    object_locations = get_external_object_locations(remote_conn, remote_mountpoint, distinct_objects)

    return snaps_to_fetch, object_meta, object_locations


def pull(conn, mountpoint, remote, download_all=False):
    remote_info = get_remote_for(conn, mountpoint, remote)
    if not remote_info:
        raise SplitGraphException("No remote %s found for mountpoint %s!" % (remote, mountpoint))

    remote_conn_string, remote_mountpoint = remote_info
    clone(conn, remote_conn_string, remote_mountpoint, mountpoint, download_all)


def clone(conn, remote_conn_string, remote_mountpoint, local_mountpoint, download_all=False):
    ensure_metadata_schema(conn)
    # Pulls a schema from the remote, including all of its history.

    with conn.cursor() as cur:
        cur.execute("""CREATE SCHEMA IF NOT EXISTS %s""" % cur.mogrify(local_mountpoint))

    _log("Connecting to the remote driver...")
    match = re.match('(\S+):(\S+)@(.+):(\d+)/(\S+)', remote_conn_string)
    remote_conn = make_conn(server=match.group(3), port=int(match.group(4)), username=match.group(1),
                            password=match.group(2), dbname=match.group(5))

    # Get the remote log and the list of objects we need to fetch.
    _log("Gathering remote metadata...")

    # This also registers the new versions locally.
    snaps_to_fetch, object_meta, object_locations = _get_required_snaps_objects(conn, remote_conn, local_mountpoint, remote_mountpoint)

    if not snaps_to_fetch:
        _log("Nothing to do.")
        return

    # Don't actually download any real objects until the user tries to check out a revision.
    if download_all:
        # Check which new objects we need to fetch/preregister.
        # We might already have some objects prefetched
        # (e.g. if a new version of the table is the same as the old version)
        _log("Fetching remote objects...")
        download_objects(conn, local_mountpoint, remote_conn_string, remote_mountpoint,
                         objects_to_fetch=list(set(o[2] for o in object_meta)), object_locations=object_locations)

    # Map the tables to the actual objects no matter whether or not we're downloading them.
    register_objects(conn, local_mountpoint, object_meta)
    register_object_locations(conn, local_mountpoint, object_locations)

    # Don't check anything out, keep the repo bare.
    set_head(conn, local_mountpoint, None)

    if get_remote_for(conn, local_mountpoint) is None:
        add_remote(conn, local_mountpoint, remote_conn_string, remote_mountpoint)


def push(conn, remote_conn_string, remote_mountpoint, local_mountpoint, handler='DB', handler_options={}):
    ensure_metadata_schema(conn)
    # Inverse of pull: uploads missing pack/snap tables to the remote and updates its index.
    # Could actually be done by flipping the arguments in pull but that assumes the remote SG driver can connect
    # to us directly, which might not be the case. Although tunnels?

    # Still, a lot of code here similar to pull.
    _log("Connecting to the remote driver...")
    match = re.match('(\S+):(\S+)@(.+):(\d+)/(\S+)', remote_conn_string)
    remote_conn = make_conn(server=match.group(3), port=int(match.group(4)), username=match.group(1),
                            password=match.group(2), dbname=match.group(5))

    _log("Gathering remote metadata...")
    # This also registers new commits remotely. Should make explicit and move down later on.
    snaps_to_push, object_meta, object_locations = _get_required_snaps_objects(remote_conn, conn, remote_mountpoint, local_mountpoint)

    if not snaps_to_push:
        _log("Nothing to do.")
        return

    new_uploads = upload_objects(conn, local_mountpoint, remote_conn_string, remote_mountpoint, list(set(o[2] for o in object_meta)),
                                 handler=handler, handler_params=handler_options)
    # Register the newly uploaded object locations locally and remotely.
    register_objects(remote_conn, remote_mountpoint, object_meta)
    register_object_locations(remote_conn, remote_mountpoint, object_locations + new_uploads)
    # Kind of have to commit here in any case?
    # A fun bug here: if remote_conn and conn are pointing to the same database (like in the integration test),
    # then updating object_location over conn first locks waiting on remote_conn to commit, which then locks waiting on
    # conn to commit.
    remote_conn.commit()

    register_object_locations(conn, local_mountpoint, new_uploads)