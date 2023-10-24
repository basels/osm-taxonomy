## Automatically Constructing a Geospatial Feature Taxonomy from OpenStreetMap Data

### _Note: This work is currently under review._

The `osm-taxonomy` tool enables the automatic generation of a lightweight and structured taxonomy for geographic features using [OpenStreetMap (OSM)](https://www.openstreetmap.org/) data. It leverages innovative algorithms and techniques to analyze OSM datasets and extract hierarchical relationships between tags, providing a comprehensive framework for categorizing and classifying various types of geospatial features. This tool streamlines the taxonomy construction process, addressing the limitations of unstructured tags, and offering a valuable resource for data organization, analysis, and understanding in the field of geospatial research.

### Install requirements:
```commandline
pip3 install -r requirements.txt
```

### Usage
```commandline
usage: generate_taxonomy.py [-h] [--input INPUT] [--threshold THRESHOLD] [--output OUTPUT]

Automatically construct a lightweight taxonomy for geographic features using OpenStreetMap (OSM) data.

optional arguments:
  -h, --help            show this help message and exit
  --input INPUT         OSM dump (xml) input file name.
  --threshold THRESHOLD
                        Minimum frequency threshold per tag.
  --output OUTPUT       Taxonomy tree (json) file name.
```

#### Example
```commandline
$ python generate_taxonomy.py --input tema_port.osm --threshold 10 --output tema_tree.json
Loading OSM (xml) file: tema_port.osm
Keeping just the tagged instances...
Counting...
Generating taxonomy tree with min-threshold=10...
node industrial --> [industrial__landuse (under landuse) & industrial__building (under building)]
removed node industrial
****************************************************************************************************
0
├── amenity
│   ├── bank
│   └── fuel
├── highway
│   ├── residential
│   ├── secondary
│   ├── secondary_link
│   ├── service
│   │   ├── driveway
│   │   └── parking_aisle
│   ├── tertiary
...
```

### Cite this work
_TBD_

### License
This repository is licensed under the [MIT License](https://raw.githubusercontent.com/basels/osm-taxonomy/main/LICENSE).

### Other Repository Contents
This repository includes the following files:

- `data/california_taxonomy.202303.txt`: Textual representation of the taxonomy generated from the California `.osm` dump from March 2023 (based on approximately 10 million tagged instances).
- `data/greece_taxonomy.202303.txt`: Textual representation of the taxonomy generated from the Greece `.osm` snapshot from March 2023 (based on approximately 2 million tagged instances).
