from taxo_utils import *

import argparse
import random
import json
import warnings
warnings.filterwarnings("ignore")

SEED = 42
random.seed(SEED)
tqdm.pandas()


# -------- main --------------


def main(args):

    # load data
    log.info(f'Loading OSM (xml) file: {args.input}')
    g_osm_data = get_osm_dictionary_from_xml(args.input)

    log.info('Keeping just the tagged instances...')
    g_osm_tagged_data = {k: v for (k, v) in g_osm_data.items() if 'tags' in v}
    del g_osm_data

    # counters for taxonomy decisions
    log.info('Counting...')
    update_global_key_value_tag_counter(g_osm_tagged_data)
    g_new_osm_dict = build_new_structured_osm_dictionary(g_osm_tagged_data)
    del g_osm_tagged_data

    # processed data to DataFrame
    g_osm_tagged_map = map(lambda x: (x[0],
                                      x[1]['tags'][MAIN_LABEL], x[1]['tags'][SEC_LABEL], x[1]['tags'][THI_LABEL]),
                           g_new_osm_dict.items())
    g_osm_tagged_df = pd.DataFrame(g_osm_tagged_map, columns=['osm_id', MAIN_LABEL, SEC_LABEL, THI_LABEL])
    g_osm_tagged_df.set_index('osm_id', inplace=True)
    del g_osm_tagged_map

    # generate taxonomy tree from DataFrame
    log.info('Generating taxonomy tree...')
    g_taxo_tree = get_taxo_tree(g_osm_tagged_df, 10)
    # g_taxo_tree.remove_invalid_tags(['unclassified', 'unofficial', 'multipolygon']) # example for additional filtering
    g_taxo_tree.build_taxonomy_tree()

    # save tree to json file
    log.info(f'Saving to file: {args.output}')
    with open(args.output, "w") as f:
        json.dump(tree_to_dict(g_taxo_tree.tree, 0), f)

    ##### load tree from json file #####
    # with open("tree.json", "r") as f:
    #     tree_dict = json.load(f)
    # taxo_tree = Tree()
    # dict_to_tree(taxo_tree, tree_dict)
    # print(taxo_tree)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automatically construct a lightweight taxonomy for geographic features using OpenStreetMap (OSM) data.")
    parser.add_argument("--input", type=str, help="OSM dump (xml) input file name.")
    parser.add_argument("--output", type=str, default='tree.json', help="Taxonomy tree (json) file name.")

    args = parser.parse_args()
    main(args)