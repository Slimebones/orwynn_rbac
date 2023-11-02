import argparse

from orwynn.boot import Boot
from orwynn.server import Server, ServerEngine


async def run_server(
    boot: Boot,
) -> None:
    """
    Run server with options provided from command line.

    Temporary method until Orwynn implements CLI and/or similar runner.
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Orwynn Server Runner",
    )

    parser.add_argument("host", type=str, help="host to serve on")
    parser.add_argument("port", type=int, help="port to serve on")

    namespace: argparse.Namespace = parser.parse_args()

    await Server(
        engine=ServerEngine.Uvicorn,
        boot=boot,
    ).serve(
        host=namespace.host,
        port=namespace.port,
    )
