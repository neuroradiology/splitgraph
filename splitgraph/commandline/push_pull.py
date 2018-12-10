import json
import sys

import click

import splitgraph as sg


@click.command(name='pull')
@click.argument('repository', type=sg.to_repository)
@click.option('-d', '--download-all', help='Download all objects immediately instead on checkout.')
def pull_c(repository, download_all):
    """
    Pull changes from an upstream repository.
    """
    sg.pull(repository, download_all)


@click.command(name='clone')
@click.argument('remote_repository', type=sg.to_repository)
@click.argument('local_repository', required=False, type=sg.to_repository)
@click.option('-r', '--remote', help='Alias or full connection string for the remote driver')
@click.option('-d', '--download-all', help='Download all objects immediately instead on checkout.',
              default=False, is_flag=True)
def clone_c(remote_repository, local_repository, remote, download_all):
    """
    Clone a remote Splitgraph repository into a local one.

    The lookup path for the repository is governed by the SG_REPO_LOOKUP and SG_REPO_LOOKUP_OVERRIDE
    config parameters and can be overriden by the command line --remote option.
    """

    sg.clone(remote_repository, remote_driver=remote,
             local_repository=local_repository, download_all=download_all)


@click.command(name='push')
@click.argument('repository', type=sg.to_repository)
@click.argument('remote_repository', required=False, type=sg.to_repository)
@click.option('-r', '--remote', help='Alias or full connection string for the remote driver')
@click.option('-h', '--upload-handler', help='Where to upload objects (FILE or DB for the remote itself)', default='DB')
@click.option('-o', '--upload-handler-options', help="""For FILE, e.g. '{"path": /mnt/sgobjects}'""", default="{}")
def push_c(repository, remote_repository, remote, upload_handler, upload_handler_options):
    """
    Push changes from a local repository to the upstream.

    The actual destination is decided as follows:

      * Remote driver: `remote` argument (either driver alias as specified in the config or a connection string,
        then the upstream configured for the repository.

      * Remote repository: `remote_repository` argument, then the upstream configured for the repository, then
        the same name as the repository.
    """
    sg.push(repository, remote, remote_repository, handler=upload_handler,
            handler_options=json.loads(upload_handler_options))


@click.command(name='publish')
@click.argument('repository', type=sg.to_repository)
@click.argument('tag')
@click.option('-r', '--readme', type=click.File('r'))
@click.option('--skip-provenance', is_flag=True, help='Don''t include provenance in the published information.')
@click.option('--skip-previews', is_flag=True, help='Don''t include table previews in the published information.')
def publish_c(repository, tag, readme, skip_provenance, skip_previews):
    """
    Publish tagged Splitgraph images to the catalog.

    Only images with a tag can be published. The image must have been pushed
    to the registry beforehand with `sgr push`.
    """
    if readme:
        readme = readme.read()
    else:
        readme = ""
    sg.publish(repository, tag, readme=readme, include_provenance=not skip_provenance,
               include_table_previews=not skip_previews)


@click.command(name='upstream')
@click.argument('repository', type=sg.to_repository)
@click.option('-s', '--set', 'set_to',
              help="Set the upstream to a driver alias + repository", type=(str, sg.to_repository), default=("", None))
@click.option('-r', '--reset', help="Delete the upstream", is_flag=True, default=False)
def upstream_c(repository, set_to, reset):
    """
    Get or set the upstream for a repository.

    This shows the default repository used for pushes and pulls as well as allows to change it to a different
    remote driver and repository.

    The remote driver alias must exist in the config file.

    Examples:

        sgr upstream my/repo --set splitgraph.com username/repo

    Sets the upstream for `my/repo` to `username/repo` existing on the `splitgraph.com` driver

        sgr upstream my/repo --reset

    Removes the upstream for `my/repo`.

        sgr upstream my/repo

    Shows the current upstream for `my/repo`.
    """
    # surely there's a better way of finding out whether --set isn't specified
    if set_to != ("", None) and reset:
        raise click.BadParameter("Only one of --set and --reset can be specified!")

    if reset:
        if sg.get_upstream(repository):
            sg.delete_upstream(repository)
            print("Deleted upstream for %s." % repository.to_schema())
        else:
            print("%s has no upstream to delete!" % repository.to_schema())
            sys.exit(1)
        return

    if set_to == ("", None):
        upstream = sg.get_upstream(repository)
        if upstream:
            driver, remote_repo = upstream
            print("%s is tracking %s:%s." % (repository.to_schema(), driver, remote_repo.to_schema()))
        else:
            print("%s has no upstream." % repository.to_schema())
    else:
        driver, remote_repo = set_to
        try:
            sg.get_remote_connection_params(driver)
        except KeyError:
            print("Remote driver '%s' does not exist in the configuration file!" % driver)
            sys.exit(1)
        sg.set_upstream(repository, driver, remote_repo)
        print("%s set to track %s:%s." % (repository.to_schema(), driver, remote_repo.to_schema()))