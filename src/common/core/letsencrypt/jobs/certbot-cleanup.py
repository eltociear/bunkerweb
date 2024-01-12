#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os import getenv, sep
from os.path import join
from sys import exit as sys_exit, path as sys_path
from traceback import format_exc

for deps_path in [join(sep, "usr", "share", "bunkerweb", *paths) for paths in (("deps", "python"), ("api",), ("utils",))]:
    if deps_path not in sys_path:
        sys_path.append(deps_path)

from API import API  # type: ignore
from logger import setup_logger  # type: ignore

LOGGER = setup_logger("Lets-encrypt.cleanup", getenv("LOG_LEVEL", "INFO"))
CORE_API = API(getenv("API_ADDR", ""), "job-certbot-cleanup")
CORE_TOKEN = getenv("CORE_TOKEN", None)
status = 0

try:
    token = getenv("CERTBOT_TOKEN", "")

    sent, err, status, resp = CORE_API.request(
        "DELETE",
        "/lets-encrypt/challenge",
        data={"token": token},
        additonal_headers={"Authorization": f"Bearer {CORE_TOKEN}"} if CORE_TOKEN else {},
    )
    if not sent:
        status = 1
        LOGGER.error(f"Can't send API request to {CORE_API.endpoint}/lets-encrypt/challenge : {err}")
    elif status != 200:
        status = 1
        LOGGER.error(f"Error while sending API request to {CORE_API.endpoint}/lets-encrypt/challenge : status = {resp['status']}, msg = {resp['msg']}")
    else:
        LOGGER.info(f"Successfully sent API request to {CORE_API.endpoint}/lets-encrypt/challenge")
except:
    status = 1
    LOGGER.error(f"Exception while running certbot-cleanup.py :\n{format_exc()}")

sys_exit(status)
