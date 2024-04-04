from fastapi import FastAPI
import uvicorn
import logging
import os
from datetime import datetime


app = FastAPI()


@app.get("/")
async def root():
    logging.info("Hello World")
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    logging.info(f'Hello {name}')
    return {"message": f"Hello {name}"}


def setup_log():
    """
    Example log messages:

    logging.debug("This is a debug message")
    logging.info("This is an info message")
    logging.warning("This is a warning message")
    logging.error("This is an error message")
    logging.critical("This is a critical message")
    """

    current_script_path = os.path.abspath(__file__)

    # Define the logging directory relative to the Heartbeat project directory
    log_directory = os.path.join(os.path.dirname(os.path.dirname(current_script_path)), 'FastAPI', 'logs')

    log_filename = os.path.join(log_directory, datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".log")
    logging.basicConfig(filename=log_filename, level=logging.DEBUG, format='%(levelname)s: %(message)s')


if __name__ == "__main__":
    setup_log()
    uvicorn.run(app, port=8000)
