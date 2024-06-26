#!/usr/bin/python3
# -*- coding: utf-8 -*-

from pathlib import Path
import pandas as pd
from google_scraper.scraper import GoogleScraper
from google_scraper.utils.multithread import multithread_callable, chunks_input
from typing import List, Dict, Tuple
import pprint

Options = [
    "-headless",  # Remove if you debug
    "--log-level=0",
]

NB_WORKERS = 8
CURRENT_FOLDER = str(Path(__file__).parent)


if __name__ == """__main__""":
    input_dataframe = pd.read_csv(CURRENT_FOLDER + "/data/input/cinema_paris.csv")
    all_search_strings = []
    for _, row in input_dataframe.iterrows():
        all_search_strings.append(f'{row["nom"]} Cinema Paris')

    input_chunks = list(chunks_input(all_search_strings, NB_WORKERS))

    def process_chunk(chunk_search_str: List[str]) -> Dict[str, Tuple[str]]:
        chunk_result = {}
        with GoogleScraper(extra_options=Options) as scraper:
            scraper.validate_google_cookies()
            for search_str in chunk_search_str:
                chunk_result[search_str] = scraper.get_maps_coordinates(
                    search_str=search_str
                )
                address = scraper.get_maps_address(search_str=search_str)
                raise ValueError("Stop")
        return chunk_result

    pprint.pprint(input_chunks)
    full_result: List[Dict[str, Tuple[float, float]]] = multithread_callable(
        func=process_chunk,
        kwargs_list=[{"chunk_search_str": chunk} for chunk in input_chunks],
        nb_workers=NB_WORKERS,
    )

    full_dict = {}
    for result in full_result:
        full_dict.update(result)
    pprint.pprint(full_dict)

    pd.DataFrame.from_dict(full_dict, orient="index").to_csv(
        path_or_buf=str(Path(__file__).parent) + "/data/output/cinema_paris.csv",
        sep=";",
        quotechar='"',
        index=True,
        index_label="name",
        header=["lat", "long"],
    )
