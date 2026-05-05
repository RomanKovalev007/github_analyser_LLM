import asyncio
import click
from dotenv import load_dotenv

load_dotenv()

from agent.agent import run_agent


@click.command()
@click.argument("repo_url")
@click.option("--question", "-q", prompt="Your question", help="Question about the repository")
def main(repo_url: str, question: str):
    """Analyze a GitHub repository and answer questions about it."""
    click.echo(f"\nAnalyzing: {repo_url}")
    click.echo(f"Question: {question}\n")
    click.echo("Thinking...\n")

    answer = asyncio.run(run_agent(repo_url, question))

    click.echo("=" * 60)
    click.echo(answer)
    click.echo("=" * 60)


if __name__ == "__main__":
    main()
