## Automatically Constructing a Geospatial Feature Taxonomy from OpenStreetMap Data

The `osm-taxonomy` tool enables the automatic generation of a lightweight and structured taxonomy for geographic features using [OpenStreetMap (OSM)](https://www.openstreetmap.org/) data. It leverages innovative algorithms and techniques to analyze OSM datasets and extract hierarchical relationships between tags, providing a comprehensive framework for categorizing and classifying various types of geospatial features. This tool streamlines the taxonomy construction process, addressing the limitations of unstructured tags, and offering a valuable resource for data organization, analysis, and understanding in the field of geospatial research.

### Install requirements:
```commandline
pip install -e .
```

### Usage
```commandline
usage: generate_taxonomy.py [-h] --input INPUT [--output OUTPUT] [--threshold THRESHOLD] [--blacklist BLACKLIST]

Automatically construct a lightweight taxonomy for geographic features using OpenStreetMap (OSM) data.

optional arguments:
  -h, --help            show this help message and exit
  --input INPUT         OSM dump (xml) input filename.
  --output OUTPUT       Taxonomy tree (json) filename.
  --threshold THRESHOLD
                        Minimum frequency threshold per tag.
  --blacklist BLACKLIST
                        (txt) file with tags to ignore (one per line, as seen on OSM).
```

#### Example
```commandline
$ python generate_taxonomy.py --input data/osm_example.osm --threshold 10 --output example_tree.json --blacklist data/blacklist_example.txt
Loading additional terms to ignore (from file data/blacklist_example.txt)...
  the following tags will be ignored: [...]
Loading OSM (xml) file data/osm_example.osm...
   100% |████████████████████████████████|   37.55MB/s eta 00:00:00
Setting minimum threshold=10...
   100% |████████████████████████████████|   1865/1865 [00:00<00:00, 909367.24it/s]
Generating taxonomy tree...
node industrial --> [industrial__landuse (under landuse) & industrial__building (under building)]
removed node industrial
****************************************************************************************************
...
├── building
│   ├── house
│   └── industrial__building
├── highway
│   ├── residential
│   ├── service
│   │   ├── driveway
│   │   └── parking_aisle
├── landuse
│   └── industrial__landuse
├── natural
│   ├── coastline
│   └── tree
...
Saving to file: example_tree.json
```

### Cite this work
If you would like to cite this work in a paper or a presentation, the following is recommended (BibTeX entry):
```commandline
@inproceedings{shbita2024automatically,
  title={Automatically Constructing Geospatial Feature Taxonomies from OpenStreetMap Data},
  author={Shbita, Basel and Knoblock, Craig A},
  booktitle={2024 IEEE 18th International Conference on Semantic Computing (ICSC)},
  pages={208--211},
  year={2024},
  organization={IEEE}
}
```

### License
This repository is licensed under the [MIT License](https://raw.githubusercontent.com/basels/osm-taxonomy/main/LICENSE).

### Other Repository Contents
This repository includes the following files:
- `data/osm_example.osm`: example OpenStreetMap (OSM) dump file.
- `data/blacklist_example.txt`: example text file with terms you can use that can be ignored.
- `data/california_taxonomy.202303.txt`: Textual representation of the taxonomy generated from the California `.osm` dump from March 2023 (based on approximately 10 million tagged instances).
- `data/greece_taxonomy.202303.txt`: Textual representation of the taxonomy generated from the Greece `.osm` snapshot from March 2023 (based on approximately 2 million tagged instances).
