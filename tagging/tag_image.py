#!/usr/bin/env python3
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import argparse
import logging

import plumbum

from tagging.docker_runner import DockerRunner
from tagging.get_taggers_and_manifests import get_taggers_and_manifests
from tagging.tags_prefix import get_tags_prefix

docker = plumbum.local["docker"]

LOGGER = logging.getLogger(__name__)


def tag_image(short_image_name: str, owner: str, tags_prefix: str) -> None:
    """
    Tags <owner>/<short_image_name>:latest with the tags reported by all taggers
    for the given image.
    """
    LOGGER.info(f"Tagging image: {short_image_name}")
    taggers, _ = get_taggers_and_manifests(short_image_name)

    image = f"{owner}/{short_image_name}:latest"

    with DockerRunner(image) as container:
        for tagger in taggers:
            tagger_name = tagger.__class__.__name__
            tag_value = tagger.tag_value(container)
            LOGGER.info(
                f"Applying tag, tagger_name: {tagger_name} tag_value: {tag_value}"
            )
            docker[
                "tag", image, f"{owner}/{short_image_name}:{tags_prefix}{tag_value}"
            ]()
    if tags_prefix != "":
        LOGGER.info("Changing :latest tag to include tags_prefix")
        docker["tag", image, f"{owner}/{short_image_name}:{tags_prefix}latest"]()
        docker["rmi", image]()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--short-image-name",
        required=True,
        help="Short image name to apply tags for",
    )
    arg_parser.add_argument("--owner", default="jupyter", help="Owner of the image")
    args = arg_parser.parse_args()

    tags_prefix = get_tags_prefix()

    tag_image(args.short_image_name, args.owner, tags_prefix)
