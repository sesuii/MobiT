import click

from mobit import page_graph, logic_graph, defect_detection


@click.group()
def cli():
    """
    MobiT - Android UI auto exploration and defect detection agents.\n
    Hint: Make sure you have configured the `config.yaml` for required parameters.
    """
    pass


@cli.command()
def page():
    """Stage 1: Build page relationship graph."""
    click.secho(f"Building page relationship graph...", fg='yellow')
    page_graph.run()

@cli.command()
def logic():
    """Stage 2: Build functional logic graph."""
    click.secho("Building functional logic graph...", fg='green')
    logic_graph.run()


@cli.command()
def defect():
    """Stage 3: Perform defect detection."""
    click.secho("Performing defect detection...", fg='blue')
    defect_detection.run()


@cli.command()
def all():
    """Run all stages sequentially."""
    click.secho(f"Running complete analysis...", fg='cyan')

    # Stage 1: Page relationship graph
    click.secho("Stage 1: Building page relationship graph...", fg='yellow')
    page_graph.run()

    # Stage 2: Functional logic graph
    click.secho("Stage 2: Building functional logic graph...", fg='green')
    logic_graph.run()

    # Stage 3: Defect detection
    click.secho("Stage 3: Performing defect detection...", fg='blue')
    defect_detection.run()

    click.secho("Analysis complete!", fg='cyan')


cli()
