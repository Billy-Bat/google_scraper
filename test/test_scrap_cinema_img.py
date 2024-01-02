#!/usr/bin/python3
# -*- coding: utf-8 -*-

from pathlib import Path
import pandas as pd
from google_scraper.scraper import GoogleScraper
from google_scraper.utils.multithread import multithread_callable, chunks_input
from google_scraper.utils.utils import get_img_from_bytes
from typing import List, Dict, Tuple
import pprint

Options = [
    # "-headless",  # Remove if you debug
    "--log-level=0",
]

NB_WORKERS = 8
CURRENT_FOLDER = str(Path(__file__).parent)

if __name__ == """__main__""":
    input_dataframe = pd.read_csv(CURRENT_FOLDER + "/data/input/cinema_paris.csv")
    all_search_strings = []
    for _, row in input_dataframe.iterrows():
        # if row["nom"] == "MK2 Bastille côté Faubourg Saint-Antoine":
        all_search_strings.append(f'{row["nom"]} Cinema Paris')

    input_chunks = list(chunks_input(all_search_strings, NB_WORKERS))

    def process_chunk(chunk_search_str: List[str]) -> Dict[str, Tuple[str]]:
        chunk_result = {}
        with GoogleScraper(extra_options=Options) as scraper:
            scraper.validate_google_cookies()
            for search_str in chunk_search_str:
                try:
                    chunk_result[search_str] = scraper.get_img_for_search_string(
                        search_str=search_str
                    )
                except Exception as e:
                    print(f"Error for {search_str}: {e}")
        return chunk_result

    pprint.pprint(input_chunks)
    # You might get throttled !
    full_result: List[Dict[str, Tuple[float, float]]] = multithread_callable(
        func=process_chunk,
        kwargs_list=[{"chunk_search_str": chunk} for chunk in input_chunks[0:10]],
        nb_workers=NB_WORKERS,
    )

    desired_format = "png"
    from PIL import Image

    for chunk_res in full_result:
        for key, value in chunk_res.items():
            if value is None:
                continue
            img: Image = get_img_from_bytes(value)
            img.save(
                Path(__file__).parent
                / "data/output/img"
                / "{}.{}".format(key, desired_format)
            )
