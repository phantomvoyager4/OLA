from fetch_champions import fc
from fetch_icon import fi
from fetch_items import fi2
from fetch_runes import fr
from fetch_summoners import fs

def run_all_scripts():
    funcs = [fc, fi, fi2, fr, fs]
    for fun in funcs:
        fun()

if __name__ == "__main__":
    run_all_scripts()